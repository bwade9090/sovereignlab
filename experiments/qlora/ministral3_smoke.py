"""Preflight and execute one paid-GPU QLoRA optimizer step for Ministral 3."""

import argparse
import json
import math
import sys
import time
from pathlib import Path
from urllib.request import urlopen

MODEL_ID = "mistralai/Ministral-3-3B-Instruct-2512-BF16"
MODEL_REVISION = "b6d637bef2393152b3da2b2fde72eecdee30557e"
EXPECTED_ARCHITECTURE = "Mistral3ForConditionalGeneration"
DEFAULT_FIXTURE = Path(__file__).with_name("fixtures") / "compatibility.jsonl"
DEFAULT_OUTPUT = Path("artifacts/qlora/ministral3-3b-compatibility")


def load_examples(path: Path) -> tuple[dict[str, object], ...]:
    """Load a tiny synthetic route fixture with strict chat-shape checks."""

    examples: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            example = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSONL at line {line_number}") from error
        messages = example.get("messages") if isinstance(example, dict) else None
        if not isinstance(messages, list) or len(messages) < 2:
            raise ValueError(f"line {line_number} requires at least two messages")
        for message in messages:
            if (
                not isinstance(message, dict)
                or message.get("role") not in {"system", "user", "assistant"}
                or not isinstance(message.get("content"), str)
                or not message["content"].strip()
            ):
                raise ValueError(f"line {line_number} contains an invalid message")
        if messages[-1]["role"] != "assistant":
            raise ValueError(f"line {line_number} must end with an assistant target")
        examples.append(example)
    if not examples:
        raise ValueError("compatibility fixture contains no examples")
    return tuple(examples)


def fetch_model_metadata() -> tuple[dict[str, object], dict[str, object]]:
    """Read only pinned public Hub metadata and config; never download weights."""

    metadata_url = f"https://huggingface.co/api/models/{MODEL_ID}/revision/{MODEL_REVISION}"
    config_url = f"https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}/config.json"
    with urlopen(metadata_url, timeout=30) as response:
        metadata = json.load(response)
    with urlopen(config_url, timeout=30) as response:
        config = json.load(response)
    return metadata, config


def validate_preflight(
    examples: tuple[dict[str, object], ...],
    metadata: dict[str, object],
    config: dict[str, object],
) -> dict[str, object]:
    """Fail closed if the pinned public checkpoint contract has drifted."""

    if metadata.get("sha") != MODEL_REVISION:
        raise ValueError("Hub revision does not match the pinned commit")
    if metadata.get("private") is not False or metadata.get("gated") not in {False, "false"}:
        raise ValueError("compatibility checkpoint must remain public and ungated")
    card_data = metadata.get("cardData")
    if not isinstance(card_data, dict) or card_data.get("license") != "apache-2.0":
        raise ValueError("compatibility checkpoint license is not the recorded Apache-2.0")
    files = {
        item.get("rfilename") for item in metadata.get("siblings", []) if isinstance(item, dict)
    }
    required_files = {"config.json", "model.safetensors.index.json", "tokenizer.json"}
    if not required_files.issubset(files):
        raise ValueError("compatibility checkpoint is missing required files")
    architectures = config.get("architectures")
    if architectures != [EXPECTED_ARCHITECTURE] or config.get("model_type") != "mistral3":
        raise ValueError("compatibility checkpoint architecture has drifted")
    text_config = config.get("text_config")
    vision_config = config.get("vision_config")
    if (
        not isinstance(text_config, dict)
        or text_config.get("hidden_size") != 3072
        or text_config.get("num_hidden_layers") != 26
        or not isinstance(vision_config, dict)
        or vision_config.get("hidden_size") != 1024
        or vision_config.get("num_hidden_layers") != 24
    ):
        raise ValueError("compatibility checkpoint dimensions have drifted")
    return {
        "status": "preflight_passed",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "architecture": EXPECTED_ARCHITECTURE,
        "example_count": len(examples),
        "weights_downloaded": False,
        "external_cost_usd": 0.0,
    }


def run_gpu_step(
    examples: tuple[dict[str, object], ...],
    *,
    output_dir: Path,
) -> dict[str, object]:
    """Run exactly one NF4 QLoRA optimizer step and save adapter-only output."""

    try:
        import bitsandbytes
        import peft
        import torch
        import transformers
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import (
            BitsAndBytesConfig,
            Mistral3ForConditionalGeneration,
            MistralCommonBackend,
        )
    except ImportError as error:
        raise RuntimeError(
            "install experiments/qlora/requirements.txt in the isolated GPU environment"
        ) from error

    if not torch.cuda.is_available():
        raise RuntimeError("the paid compatibility step requires a CUDA GPU")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("the selected compatibility path requires CUDA BF16 support")

    started = time.monotonic()
    torch.manual_seed(20260717)
    torch.cuda.manual_seed_all(20260717)
    torch.cuda.reset_peak_memory_stats()
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_storage=torch.uint8,
    )
    tokenizer = MistralCommonBackend.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = Mistral3ForConditionalGeneration.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        quantization_config=quantization,
        dtype=torch.bfloat16,
        device_map={"": torch.cuda.current_device()},
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=False)
    model = get_peft_model(
        model,
        LoraConfig(
            r=8,
            lora_alpha=16,
            lora_dropout=0.0,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules="all-linear",
            exclude_modules=r".*(?:vision_tower|multi_modal_projector).*",
        ),
    )
    trainable = [
        (name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad
    ]
    if not trainable or any(
        "vision_tower" in name or "multi_modal_projector" in name for name, _ in trainable
    ):
        raise RuntimeError("LoRA trainable-parameter boundary is not language-model-only")

    messages = examples[0]["messages"]
    tokenized = tokenizer.apply_chat_template(
        messages,
        continue_final_message=True,
        tokenize=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
        return_dict=True,
    )
    batch = {
        key: value.to(model.device) for key, value in tokenized.items() if hasattr(value, "to")
    }
    labels = batch["input_ids"].clone()
    optimizer = torch.optim.AdamW((parameter for _, parameter in trainable), lr=2e-4)
    change_probe = next(
        ((name, parameter) for name, parameter in trainable if "lora_B" in name),
        None,
    )
    if change_probe is None:
        raise RuntimeError("LoRA B adapter tensor is missing")
    probe_name, probe_parameter = change_probe
    before = probe_parameter.detach().float().cpu().clone()
    model.train()
    optimizer.zero_grad(set_to_none=True)
    outputs = model(**batch, labels=labels)
    loss = outputs.loss
    if loss is None or not math.isfinite(loss.item()):
        raise RuntimeError("one-step compatibility loss is missing or non-finite")
    loss.backward()
    gradients = [parameter.grad for _, parameter in trainable if parameter.grad is not None]
    if not gradients or not all(torch.isfinite(gradient).all().item() for gradient in gradients):
        raise RuntimeError("one-step compatibility gradients are missing or non-finite")
    if not any(torch.count_nonzero(gradient).item() > 0 for gradient in gradients):
        raise RuntimeError("one-step compatibility gradients are all zero")
    optimizer.step()
    changed = not torch.equal(before, probe_parameter.detach().float().cpu())
    if not changed:
        raise RuntimeError(f"one-step optimizer did not change adapter tensor {probe_name}")

    output_dir.mkdir(parents=True, exist_ok=False)
    model.save_pretrained(output_dir, safe_serialization=True)
    required_outputs = {"adapter_config.json", "adapter_model.safetensors"}
    if not required_outputs.issubset({path.name for path in output_dir.iterdir()}):
        raise RuntimeError("adapter-only smoke output is incomplete")
    adapter_bytes = sum(path.stat().st_size for path in output_dir.iterdir() if path.is_file())
    return {
        "status": "gpu_step_passed",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "optimizer_steps": 1,
        "example_count": len(examples),
        "loss": loss.item(),
        "trainable_parameters": sum(parameter.numel() for _, parameter in trainable),
        "peak_cuda_bytes": torch.cuda.max_memory_allocated(),
        "adapter_bytes": adapter_bytes,
        "output_dir": str(output_dir),
        "gpu": torch.cuda.get_device_name(),
        "elapsed_seconds": time.monotonic() - started,
        "versions": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "peft": peft.__version__,
            "bitsandbytes": bitsandbytes.__version__,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--execute-gpu-step", action="store_true")
    args = parser.parse_args()

    examples = load_examples(args.fixture)
    metadata, config = fetch_model_metadata()
    summary = validate_preflight(examples, metadata, config)
    if args.execute_gpu_step:
        summary = run_gpu_step(examples, output_dir=args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
