# Bank of Korea November 2025 outlook manifest verification

- Status: verified; document manifests recorded as `allowed` under the ADR 0009 family ruling
- Date: 2026-11-02
- Scope: frozen document unit `bok-outlook-release-2025-11` for pairs `kv-core-doc-02` and
  `kv-core-both-02`
- Cost: USD 0; public landing pages and attachments only
- Payload policy: with owner approval, the PDFs were downloaded into the Git-ignored `data/raw/`
  for hashing and later page-anchor authoring; they are not added to the repository

## Locating the editions

On 2026-11-02 the official Korean list page
`https://www.bok.or.kr/portal/bbs/P0002359/list.do?menuNo=200066` displayed only an
"updating" placeholder, and the English list page
`https://www.bok.or.kr/eng/bbs/B0000358/list.do?menuNo=400413` exposed no entries without
JavaScript. Both editions were reached through the related-publication links on the already
verified May 2026 landing pages and then opened at their canonical `view.do` URLs.

## Korean publication

- Official landing page:
  `https://www.bok.or.kr/portal/bbs/P0002359/view.do?menuNo=200066&nttId=10094817`
- Landing-page title: `경제전망보고서(2025년 11월)`
- Publisher-displayed registration date: `2025-11-27`
- Attachment filename: `2025년 11월 경제전망보고서(Indigo Book)_F4.pdf`
- Stable official attachment URL:
  `https://www.bok.or.kr/fileSrc/portal/2d0d7d85a73244d1aca9059f02f47aa0/1/2a02451c23404621af8522b49636443a.pdf`
- Capture interval: `2026-11-02T11:51:56Z`–`2026-11-02T11:51:57Z`
- Response: official URL HTTP 302 to a short-lived signed `file-cdn.bok.or.kr` URL, then HTTP 200
  `application/pdf`
- Byte size: `17,435,251`
- SHA-256: `7f51f0333ac16da57150cb32e05e5aa7dc7530ba96f389b47b604e19a872eb1b`
- Cover: `경제전망`, `Indigo Book`, `2025년 11월`, ISSN `2288-7083`; 150 pages

## English publication

- Official landing page:
  `https://www.bok.or.kr/eng/bbs/B0000358/view.do?menuNo=400413&nttId=10096024`
- Landing-page title: `Korea Economic Outlook (November 2025)`
- Publisher-displayed registration date: `2026-01-22`
- Attachment filename: `Korea Economic Outlook(Nov. 2025)_F.pdf`
- Stable official attachment URL:
  `https://www.bok.or.kr/fileSrc/eng/337f8afe778640708bc06cae6386144d/1/24dfb68f6b6f452bb6299829fb19f962.pdf`
- Capture interval: `2026-11-02T11:51:57Z`–`2026-11-02T11:51:59Z`
- Response: official URL HTTP 302 to a short-lived signed `file-cdn.bok.or.kr` URL, then HTTP 200
  `application/pdf`
- Byte size: `7,033,792`
- SHA-256: `d997c6a1f5853b434449a0322119fe3e9e2a3df3704e909afdfa9504a1e8eb78`
- 62 pages; ISSN `2983-2373`

The English full translation is independently dated almost two months after the Korean
publication. Its manifest is not backdated to the Korean release label or publication date, so
English records over this edition need an `as_of` on or after 2026-01-22.

## Redistribution conclusion

Neither landing page displayed a publication-specific KOGL mark, open-license notice, or other
edition-specific licence when checked on 2026-11-02. The English page footer states Bank of Korea
copyright, exactly as recorded for the May 2026 edition in
`docs/discovery/04_bok_outlook_2026_05_manifest_log.md`.

A scan of both PDFs found no licence notice in the Korean report. The English translation's page 3
asks readers to request permission before commercial reproduction and to credit the source for
non-commercial use, and its last page carries the Bank of Korea copyright line. Both notices are
identical to those in the May 2026 English edition that ADR 0009 already covers, and they match its
attribution duty and the project's non-commercial profile. They are therefore not an
edition-specific change.

ADR 0009 lets later Economic Outlook editions reuse the family ruling while the publisher,
publication family, governing policy, intended use, attribution duties, and third-party
boundaries remain unchanged. All of these hold for this edition, so both manifests record
`allowed` with the same licence name and URL as the May 2026 manifests and no typed
`rights_decision`, subject to:

1. attribution to the Bank of Korea;
2. disclosure of modification, processing, or transformation; and
3. separate treatment of material carrying a third-party source or rights notice.

No KOGL type is inferred. The PDF bodies and extracted text remain uncommitted as a
repository-scope choice rather than a rights restriction.

## Reproduction boundary

A later integrity check may repeat a direct `curl -fL` capture from each stable official attachment
URL and compare its byte size and SHA-256 with the manifests. Signed CDN URLs are ephemeral and are
not persisted. Any content change at the stable URL must create a new manifest rather than rewrite
these records.
