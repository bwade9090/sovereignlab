"""CPU-only contract tests for the isolated QLoRA compatibility harness."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "experiments" / "qlora" / "ministral3_smoke.py"
SPEC = importlib.util.spec_from_file_location("ministral3_smoke", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


def _metadata(**updates: object) -> dict[str, object]:
    value: dict[str, object] = {
        "sha": smoke.MODEL_REVISION,
        "private": False,
        "gated": False,
        "cardData": {"license": "apache-2.0"},
        "siblings": [
            {"rfilename": "config.json"},
            {"rfilename": "model.safetensors.index.json"},
            {"rfilename": "tokenizer.json"},
        ],
    }
    value.update(updates)
    return value


def _config(**updates: object) -> dict[str, object]:
    value: dict[str, object] = {
        "architectures": [smoke.EXPECTED_ARCHITECTURE],
        "model_type": "mistral3",
        "text_config": {"hidden_size": 3072, "num_hidden_layers": 26},
        "vision_config": {"hidden_size": 1024, "num_hidden_layers": 24},
    }
    value.update(updates)
    return value


def test_committed_fixture_and_pinned_metadata_validate() -> None:
    examples = smoke.load_examples(smoke.DEFAULT_FIXTURE)
    summary = smoke.validate_preflight(examples, _metadata(), _config())

    assert len(examples) == 4
    assert summary["status"] == "preflight_passed"
    assert summary["weights_downloaded"] is False
    assert summary["external_cost_usd"] == 0.0


@pytest.mark.parametrize(
    ("metadata", "config", "message"),
    [
        (_metadata(sha="wrong"), _config(), "pinned commit"),
        (_metadata(private=True), _config(), "public and ungated"),
        (_metadata(gated="auto"), _config(), "public and ungated"),
        (_metadata(cardData={"license": "other"}), _config(), "license"),
        (_metadata(siblings=[]), _config(), "required files"),
        (_metadata(), _config(architectures=["Other"]), "architecture"),
        (_metadata(), _config(text_config={}), "dimensions"),
        (_metadata(), _config(vision_config={}), "dimensions"),
    ],
)
def test_preflight_rejects_checkpoint_contract_drift(
    metadata: dict[str, object],
    config: dict[str, object],
    message: str,
) -> None:
    examples = smoke.load_examples(smoke.DEFAULT_FIXTURE)
    with pytest.raises(ValueError, match=message):
        smoke.validate_preflight(examples, metadata, config)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("not-json\n", "invalid JSONL"),
        (json.dumps({"messages": []}), "at least two"),
        (
            json.dumps(
                {
                    "messages": [
                        {"role": "user", "content": "question"},
                        {"role": "invalid", "content": "answer"},
                    ]
                }
            ),
            "invalid message",
        ),
        (
            json.dumps(
                {
                    "messages": [
                        {"role": "system", "content": "instruction"},
                        {"role": "user", "content": "question"},
                    ]
                }
            ),
            "assistant target",
        ),
        ("\n", "no examples"),
    ],
)
def test_fixture_loader_fails_closed(tmp_path: Path, payload: str, message: str) -> None:
    path = tmp_path / "fixture.jsonl"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        smoke.load_examples(path)
