# Ministral 3 QLoRA compatibility spike

This isolated spike answers one question only: can the pinned public BF16 checkpoint load in NF4,
attach language-model-only LoRA weights, produce a finite loss and gradients, complete exactly one
optimizer step, and save an adapter without writing base-model weights?

The BF16 checkpoint is used as the QLoRA source because the main instruct checkpoint is FP8. The
model revision and all direct Python dependencies are pinned. The fixture is synthetic and contains
no benchmark gold/test evidence.

## Free local preflight

From the project environment:

```bash
python experiments/qlora/ministral3_smoke.py
```

This downloads only public Hub metadata and `config.json`, checks the pinned commit, Apache-2.0
model-card license, public/ungated state, required files, architecture, text/vision dimensions, and
four fixture rows. It does not download weights or use a GPU.

## Paid GPU step

Use a fresh Linux CUDA instance with BF16 support and sufficient disk. Install into an isolated
environment; do not add these packages to the CPU application requirements:

```bash
python3.12 -m venv .venv-qlora
source .venv-qlora/bin/activate
python -m pip install -r experiments/qlora/requirements.txt
python experiments/qlora/ministral3_smoke.py
python experiments/qlora/ministral3_smoke.py \
  --execute-gpu-step \
  --output-dir artifacts/qlora/ministral3-3b-compatibility
```

Success requires exactly one optimizer step, finite nonzero adapter gradients, a changed adapter
tensor, no trainable vision/projector parameters, and adapter-only safetensors output. `artifacts/`
is ignored. Record provider, GPU, wall time, peak memory, output summary, and actual cost in
`docs/PROJECT_STATUS.md`; preserve a failure with its taxonomy instead of silently switching
models. Do not push model weights or adapters from the smoke run.

## Verified RunPod result (2026-07-18)

The paid path passed on RunPod Secure Cloud with an NVIDIA A40 (46,068 MiB), driver 580.159.04,
CUDA 13.0, and Python 3.12.3. The pinned environment reported `torch 2.13.0+cu130`, completed one
optimizer step in 23.439 seconds with loss `5.192200660705566`, trained 12,353,536 parameters, and
peaked at 4,210,338,304 CUDA bytes. The adapter-only directory was 49,474,005 bytes. It was verified
and then deleted with the Pod; it was never copied into the repository.

The full RunPod balance delta, including discarded provisioning paths and the successful run, was
finalized by the billing API at USD `0.23584524099715054`. No Pod or network volume remained
afterward. This proves compatibility only; it is not a route-quality or benchmark result.

Operational findings:

- `torch==2.13.0` installs the CUDA 13.0 wheel, so create the Pod with a minimum CUDA version of
  13.0 and verify a 580-series-or-compatible driver before downloading weights.
- Run `runpodctl doctor` before Pod creation so its dedicated SSH key is injected at boot.
- Use an official RunPod PyTorch template. The verified template was `runpod-torch-v280`.
- Put the repository and virtual environment on the container disk (for example `/root`), not the
  network-mounted `/workspace`; Python package installation on the latter was severely delayed.
- Set an automatic termination deadline at creation and still delete the Pod explicitly as soon as
  the result is captured.
