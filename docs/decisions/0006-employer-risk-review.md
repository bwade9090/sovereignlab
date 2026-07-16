# ADR 0006: employer-risk review for personal-capacity public activity

- Status: accepted — owner-authored answers recorded 2026-07-17
- Date: 2026-07-17
- Related: charter v2.2 §7 (week-1 gate) and §9; `docs/PROJECT_STATUS.md` "Owner decisions closed"

## Context

Charter v2.2 §7 requires a one-hour written employer-risk review of the project as
personal-capacity public activity, committed as a decision record, before the week-1 gate can
close. `docs/PROJECT_STATUS.md` scopes it to five topics: the public harvester, personal-capacity
disclaimers, automated release notes, Bank of Korea branding, and whether the workstation path in
earlier Git history needs remediation. The rule of authorship is explicit: an agent may provide
questions but may not author the review; completion requires the owner's text.

Accordingly, the agent supplied a structured question list on 2026-07-17 and the owner
(Hyungbae Cho, `bwade9090`) answered every question in their own words in the same session. The
Korean answers below are the owner's verbatim text and are the authoritative content of this
review. The agent's contribution is limited to the questions, the document structure, and the
English glosses in parentheses.

## Owner's review (verbatim answers, 2026-07-17)

### 1. Workplace rules

- 1-1 (Does the employer's outside-activity policy cover this unpaid personal public project?):
  "무보수 개인 공개 프로젝트 자유로움. 오히려 장려함" (unpaid personal public projects are
  unrestricted and in fact encouraged).
- 1-2 (Is prior reporting or approval required?): "신고 대상 아님" (not subject to reporting).
- 1-3 (Any use of employer equipment, network, or working hours?): "쓰지 않음" (none used).
- 1-4 (Overlap with job duties or risk of non-public work information entering the project?):
  "리스크 없음" (no risk).
- 1-5 (Any issue with the current employer seeing the repository used as an application
  portfolio?): "문제 없음" (no issue).

### 2. Personal-capacity disclaimer

- 2-1 (Where should the disclaimer appear?): "없어도 되지만 굳이 붙인다면 README" (not strictly
  necessary; if placed anywhere, the README).
- 2-2 (Language and exact wording?): "영어만. '이 프로젝트는 개인 자격으로 진행하며, 한국은행과
  무관합니다.'" (English only; the sentence renders as "This project is conducted in a personal
  capacity and is not affiliated with the Bank of Korea.").
- 2-3 (Name the employer or only state independence?): "'소속과 무관' 명시" (state independence
  from any affiliation).
- 2-4 (How to answer external inquiries about the project?): "업무상 비밀이 아니면 답변 가능"
  (may answer anything that is not a work-related secret).

### 3. Public harvester

- 3-1 (Could weekly automated capture read as institutional activity?): "오해 소지 전혀 없음"
  (no room for misunderstanding).
- 3-2 (Is the collection volume within the APIs' terms and ordinary courtesy?): "매우 일반적인
  활용 수준" (a very ordinary level of use).
- 3-3 (Can the harvester be stopped and its output removed if a provider ever asks?): "그럴 일
  자체가 없을 것 같지만 만약의 경우에는 중단 및 삭제는 언제든지 가능" (unlikely to arise; if it
  does, stopping and deleting are possible at any time).
- 3-4 (Are the automated commit account and email personal?): "개인 계정임" (personal account).

### 4. Automated release notes

- 4-1 (Could machine-written notes be mistaken for forecasts or market commentary?): "오해 소지
  전혀 없음" (no room for misunderstanding).
- 4-2 (How prominent must the "automated reconstruction" label be?): "너무 당연해서 없어도 됨"
  (so self-evident it could be omitted).
- 4-3 (How are wrong numbers corrected?): "발견 즉시 정정하고 정정한 사실을 투명하게 기록"
  (correct immediately and record the correction transparently).
- 4-4 (Is same-day posting around sensitive releases a risk?): "전혀 리스크 없음" (no risk at
  all).

### 5. Bank of Korea branding

- 5-1 (Could current wording read as BOK approval or cooperation?): "리스크 전혀 없음" (no risk
  at all).
- 5-2 (Any logo or official design element in use?): "없음" (none).
- 5-3 (Any "official/cooperation/partnership"-flavored wording?): "없음" (none).
- 5-4 (Is source attribution distinguishable from an implied relationship?): "출처 표기를 공식적
  관계로 오해할 여지 없음" (attribution cannot be mistaken for an official relationship).

### 6. Workstation path in earlier Git history

- 6-1 (What does the recorded path expose?): "리스크 없음" (no risk).
- 6-2 (Severity if it stays public?): "리스크 없음" (no risk).
- 6-3 (Rewrite history or leave it?): "안 고쳐도 됨" (no remediation needed).
- 6-4 (How to prevent recurrence?): "안전한 경로 및 계정으로만 작업" (work only with safe paths
  and accounts).

### 7. Resulting decisions

- 7-1 (Proceed / modify / stop): "진행" (proceed).
- 7-2 (Concrete follow-up): "README에 영어로 '이 프로젝트는 개인 자격으로 진행하며, 한국은행과
  무관합니다.'만 바로 추가하고 다음 단계 진행" (immediately add only the English disclaimer
  sentence to the README, then continue to the next work item).
- 7-3 (When to revisit): "내가 명시적으로 요청할 때" (only when the owner explicitly requests).

## Decision

1. The project proceeds unchanged as personal-capacity public activity. The owner's employer
   permits and encourages it; no reporting duty applies; no employer resources are used.
2. The README gains the English disclaimer "This project is conducted in a personal capacity and
   is not affiliated with the Bank of Korea." as the single mandated disclaimer location. This is
   the owner-approved implementation of charter §9's personal-capacity disclaimer for the current
   milestone.
3. The workstation path in earlier Git history is accepted as-is: no history rewrite. This closes
   the remediation question flagged in `docs/PROJECT_STATUS.md` and preserves the append-only
   commit-history guarantee intact. Future work uses safe paths and personal accounts only.
4. Automated release notes correct errors immediately and record corrections transparently.
5. This review records the owner's risk judgments; it does not amend the charter. In particular,
   charter §9's requirement that auto-generated notes carry the "automated reconstruction of
   official releases" label remains in force (the owner's answer 4-2 assesses employer risk as
   nil; it does not remove the labeling rule), and the standing non-endorsement rules in
   `AGENTS.md` are unchanged.

## Alternatives considered

- **Employer-named disclaimer on every artifact:** rejected by the owner as unnecessary; a single
  English README sentence stating independence suffices (answers 2-1–2-3).
- **Rewriting Git history to remove the workstation path:** rejected by the owner (answers
  6-1–6-3). This was the last inexpensive moment to rewrite — no data snapshots exist yet — so
  declining now is a deliberate, recorded choice, and it keeps public commit history verifiable.
- **Agent-drafted review prose:** prohibited by the status document's authorship rule; only the
  owner's verbatim answers carry decision weight here.

## Consequences

- The sole remaining owner-authored week-1 artifact is complete. The week-1 gate now depends only
  on the implementation items (contract `2.0.0` with the typed manifest-rights link, the
  fail-closed resolver, harvester wiring, number-normalization specification, and the QLoRA
  path).
- Raw ECOS/KOSIS capture remains blocked solely by the typed `SourceManifest`-to-rights-decision
  link implementation (ADR 0005 / charter v2.2), no longer by any pending owner review.
- The README disclaimer is added in the same change that commits this record.

## Revisit triggers

- The owner explicitly requests a re-review (owner answer 7-3).
- The owner's employment situation or the employer's outside-activity policy changes.
- A statistics provider objects to the harvester, or any external party plausibly reads project
  output as institutional activity — either event reopens sections 3–5 immediately.
