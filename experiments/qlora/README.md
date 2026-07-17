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
