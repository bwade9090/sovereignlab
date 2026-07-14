# Mistral Applied AI Engineer: role-gap analysis and project directions

- Status: discovery draft for review
- Date: 2026-07-14
- Scope: project selection only; no implementation decision has been made
- Evidence reviewed: applicant profile, Seoul Applied AI Engineer posting, role-specific application questions, and current official Mistral documentation

## 1. Decision to make

Select one portfolio project that does more than demonstrate a generic LLM application. It should close the most visible gaps against Mistral's Applied AI Engineer role, exploit Hyungbae Cho's unusual strengths in high-stakes economic systems, and produce reusable public evidence for later Applied AI, Forward Deployed Engineer, and AI Solutions roles.

## 2. What the role is actually hiring for

The posting is not primarily for a model researcher or a conventional data scientist. It describes a hybrid role with four identities:

1. **Applied LLM engineer:** prompting, evaluation, fine-tuning, advanced RAG, agents, PyTorch, and production integration.
2. **Forward-deployed builder:** independently turn a customer's ambiguous, high-impact use case into a working production system.
3. **Technical customer partner:** communicate with executives, data scientists, and software engineers from pre-sales through post-implementation.
4. **Product/research feedback channel:** externalize research in production, diagnose product gaps, and contribute improvements back to product, science, or open source.

The portfolio therefore needs to resemble a credible customer pilot with acceptance criteria and operational evidence, not merely a notebook or chat interface.

## 3. Evidence matrix

Scores below measure how clearly the supplied profile currently proves each requirement, not Hyungbae's underlying potential.

| Role signal | Current evidence | Evidence strength | Project implication |
|---|---|---:|---|
| English and Korean | Fluent English; native Korean; international collaboration | 5/5 | Make the artifact and benchmark genuinely bilingual, not merely translated UI text. |
| Master's/PhD in AI or data science | Incoming OMSA; bachelor's degree; strong publications and advanced professional training | 2/5 | This is the largest structural screening risk and cannot be erased by a project. Compensate with unusually rigorous public technical evidence. Do not imply the master's is completed. |
| 2+ years as technical IC on AI products | Transformer NSI, PRISM-Now, Samsung engineering, RateGauge | 5/5 | Lead with this; the new project should connect the history into a current LLM narrative. |
| Fine-tuning LLMs | Transformer training is present, but no explicit modern LLM fine-tuning artifact | 1/5 | Must include a real LoRA/QLoRA experiment, ablations, held-out evaluation, adapter artifact, and failure analysis. |
| Advanced RAG / agentic use cases / vector DB | No explicit production-shaped evidence in the supplied profile | 1/5 | Must be central to the system and evaluated beyond answer-quality screenshots. |
| Deep ML and LLM understanding | PyTorch, Transformers, econometrics, time series, peer-reviewed work | 4/5 | Demonstrate correct separation of what belongs in weights, retrieval, tools, and deterministic code. |
| Deploying LLM/NLP applications | Daily NSI production pipeline; RateGauge FastAPI/Docker/CI | 4.5/5 | Preserve the production rigor and add an interactive end-user path. |
| APIs plus back-end and front-end | APIs, dashboards, web administration, Power BI, Azure ML | 4/5 | One coherent LLM product should visibly join API, back end, UI, and observability. |
| Python and PyTorch | Strong direct evidence | 5/5 | Use typed, tested Python and expose the training/inference path rather than hiding it behind a framework. |
| Customer/FDE/solutions behavior | Tier 2/3 support, training, vendor PoC, stakeholder coordination, international partners | 3.5/5 | Reframe this strength through customer discovery, SLOs, trade-off decisions, pilot report, and deployment runbook. |
| LLM open-source contribution | Strong personal open-source projects, but no clear upstream LLM contribution | 2/5 | Include one small, genuine upstream contribution discovered during implementation; do not manufacture a cosmetic PR. |
| Evaluation and high-stakes reliability | RateGauge, NSI monitoring, reproducible forecasting pipelines | 5/5 | This is the differentiator to compound, while avoiding a simple repeat of RateGauge. |

## 4. Central diagnosis

The profile already proves research-to-production engineering, high-stakes evaluation, and stakeholder communication. The missing proof is a **single contemporary system showing fine-tuning + advanced RAG + agentic tool use + customer-shaped deployment**.

The best strategy is not to abandon the economic/public-sector identity and build a generic SaaS assistant. It is to use that domain credibility as the setting for a technically modern, Mistral-native deployment problem that few applicants can execute convincingly.

## 5. Project selection criteria

Any selected project should satisfy all of the following:

1. **Direct gap closure:** fine-tuning, RAG, tools/agents, vector retrieval, front/back integration, and deployment are observable in one coherent product.
2. **A measurable reason for each technique:** LoRA must solve a failure that prompting or retrieval alone does not; RAG must supply changing facts; tools must perform deterministic data operations.
3. **High-stakes differentiation:** use public financial/economic evidence where provenance, time, revisions, and abstention matter.
4. **Mistral-native but portable:** deeply exercise Mistral models and interfaces while preserving provider and deployment abstractions.
5. **Bilingual difficulty:** Korean/English retrieval and answers should be evaluated as separate capability slices.
6. **FDE realism:** begin from a customer problem and acceptance tests; end with an implementation guide, pilot results, operational runbook, and executive demo.
7. **Public reproducibility:** use public data only, version datasets and prompts, pin dependencies, test offline where possible, and report cost/latency/hardware.
8. **Ablations over spectacle:** compare meaningful system variants instead of adding unnecessary multi-agent choreography.
9. **Controlled scope:** deliver a narrow end-to-end vertical slice first, then earn each extension with evaluation results.

## 6. Candidate projects

### Candidate A — SovereignLab: an eval-driven sovereign AI deployment lab

**One-line pitch:** Build and evaluate a bilingual, locally deployable Mistral system that produces citation-grounded economic policy briefs from public documents and official time-series APIs, then quantify when LoRA, temporal RAG, and tool use each add value.

**Representative customer scenario:** A Korean financial or public institution needs analysts to ask a question in Korean or English and receive an auditable brief based only on information available as of a chosen date. Sensitive deployments must support local open-weight inference, while a cloud mode should remain available for comparison.

**Narrow vertical slice:**

`question -> evidence plan -> temporally filtered document retrieval and/or SDMX tool -> cited brief -> verification trace`

The distinguishing technical choice is to fine-tune a small open-weight Mistral model for **evidence routing and structured tool behavior**, rather than trying to memorize changing economic facts. Facts remain in versioned retrieval and deterministic APIs.

**Ablation ladder:**

1. Closed-book base model.
2. Hybrid temporal RAG.
3. Hybrid temporal RAG plus official-data tools.
4. The same system with a LoRA-tuned evidence router/tool planner.

**Core metrics:** routing/tool-call accuracy, citation entailment and completeness, numerical provenance, temporal or `as-of` correctness, bilingual retrieval recall, calibrated abstention, latency, cost, and local VRAM.

**Public artifacts:** a small bilingual benchmark; LoRA adapter and training recipe; RAG/agent service; API and UI; evaluation report; threat model; local/cloud deployment guide; customer-style pilot brief.

**Why it stands out:** It maps almost line-for-line to Mistral's finance/public-sector, open-weight deployment, evaluation, fine-tuning, RAG, agent, and customer-integration narrative. It also turns Hyungbae's central-bank background into a moat.

**Main risk:** Scope can expand quickly. The benchmark and one complete vertical slice must precede OCR breadth, multiple institutions, elaborate UI, or multi-agent extensions.

### Candidate B — Bilingual RAG Reliability Lab

**One-line pitch:** Publish a Korean/English benchmark and adversarial test harness for temporal leakage, citation errors, numerical inconsistency, prompt injection, and false-premise compliance in high-stakes RAG systems.

**Strengths:** Highest probability of a rigorous, publishable result; naturally extends Hyungbae's evaluation expertise; useful as an open-source library across providers.

**Weaknesses:** It risks reading as "RateGauge for RAG" and provides weaker evidence of full customer deployment, front-end integration, and fine-tuning unless expanded.

### Candidate C — Feedback-to-LoRA AgentOps Factory

**One-line pitch:** Build a vendor-neutral system that clusters production agent failures, converts approved traces into training/evaluation data, trains LoRA adapters, and promotes them only when regression and safety gates pass.

**Strengths:** Very close to the production feedback loop, observability, registry, and governance problems emphasized by modern enterprise AI platforms; broadly reusable beyond finance.

**Weaknesses:** Harder to create credible failure data without real users; weaker personal-domain moat; infrastructure scope may overwhelm the actual model and customer story.

## 7. Provisional comparison

Scale: 1 (weak) to 5 (strong). Feasibility is higher when delivery risk is lower.

| Criterion | A: SovereignLab | B: Reliability Lab | C: AgentOps Factory |
|---|---:|---:|---:|
| Direct match to explicit role gaps | 5 | 4 | 5 |
| Distinctiveness | 5 | 4 | 4 |
| Leverages existing credibility | 5 | 5 | 3 |
| Visible product/FDE evidence | 5 | 3 | 4 |
| Reusable after this application | 5 | 5 | 5 |
| Feasibility of a strong first release | 3 | 4 | 3 |
| Risk of duplicating RateGauge | 2 (low) | 4 (high) | 1 (very low) |

## 8. Recommendation

Proceed with **Candidate A, SovereignLab**, but treat Candidates B and C as optional modules rather than separate projects:

- Candidate B becomes SovereignLab's evaluation package and public benchmark.
- A thin part of Candidate C becomes its trace-to-evaluation feedback loop only after the vertical slice works.

This produces one memorable CV story instead of three disconnected repositories.

The first implementation milestone should be deliberately small: define one customer workflow, approximately 30–50 manually reviewed benchmark questions, two document sources, one official time-series tool, and the four-system ablation contract. No model training should begin until the baseline dataset and acceptance metrics are frozen.

## 9. What not to build

- A generic "chat with PDFs" interface.
- A system whose only evaluation is an LLM judge score.
- A multi-agent diagram with no ablation proving that multiple agents help.
- Fine-tuning that attempts to store current facts in weights.
- A project that uses confidential Bank of Korea data or implies institutional endorsement.
- A demo that only works through paid APIs and cannot be tested offline.

## 10. Current official Mistral alignment

The recommendation reflects the official product surface reviewed on 2026-07-14:

- [Mistral model deployment](https://docs.mistral.ai/models/deployment) documents both managed and local deployment of open-weight models.
- [Agents and tools](https://docs.mistral.ai/studio-api/agents/agent-tools) includes built-in tools, document libraries, function calling, and managed MCP connectors.
- [Document AI](https://docs.mistral.ai/studio-api/document-processing/overview) provides OCR and structured document extraction suitable for a later ingestion extension.
- [Mistral embeddings](https://docs.mistral.ai/studio-api/knowledge-rag/embeddings) supports text/code retrieval and managed libraries.
- [Mistral's open-source fine-tuning repository](https://github.com/mistralai/mistral-finetune) provides a LoRA-oriented reference implementation.
- [Mistral AI Studio](https://mistral.ai/news/ai-studio/) emphasizes evaluation, observability, governance, reproducibility, and hybrid/self-hosted operation.

These are design inputs, not fixed dependencies. Exact model, fine-tuning stack, vector store, and deployment target remain open until local hardware, time, and budget constraints are confirmed.

## 11. Decisions recorded after review

- Project direction approved: SovereignLab.
- Delivery target: four weeks at approximately 20 hours per week.
- Local training GPU: none; use CPU-compatible development and short-lived rented compute for QLoRA.
- Initial API/compute budget: approximately USD 100, expandable only after review.
- Repository: public GitHub under `bwade9090`.
- Proposed initial workflow for final review: Korean macroeconomic surveillance, which preserves the domain advantage without repeating RateGauge's policy-rate extraction task.

The detailed scope, evaluation contract, milestones, fallbacks, and definition of done are maintained in `docs/project/01_project_charter.md`.
