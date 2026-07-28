# Bank of Korea May 2026 outlook manifest verification

- Status: verified; metadata-only document manifests committed
- Date: 2026-07-28
- Scope: frozen document unit `bok-outlook-release-2026-05` for pair `kv-core-doc-01`
- Cost: USD 0; public landing pages and attachments only
- Payload policy: PDFs were captured under `/tmp` for hashing and were not added to the repository

## Korean publication

- Official landing page:
  `https://www.bok.or.kr/portal/bbs/P0002359/view.do?menuNo=200066&nttId=10098209`
- Landing-page title: `경제전망보고서(2026년 5월)`
- Publisher-displayed registration date: `2026-05-28`
- Attachment filename: `2026년 5월 경제전망보고서(Indigo Book)_F4.pdf`
- Stable official attachment URL:
  `https://www.bok.or.kr/fileSrc/portal/411de844aef442e7ad07896b7bbe2eef/1/4e0f66601a6a4f95ac4164f9286de537.pdf`
- Capture interval: `2026-07-28T13:49:39Z`–`2026-07-28T13:49:40Z`
- Response: official URL HTTP 302 to a short-lived signed `file-cdn.bok.or.kr` URL, then HTTP 200
  `application/pdf`
- Byte size: `10,711,393`
- SHA-256: `71f78145d30190ea6bb7e2eb3bdb919c1ae4730973d1f63bed641ec12660fd97`

## English publication

- Official landing page:
  `https://www.bok.or.kr/eng/bbs/B0000358/view.do?menuNo=400413&nttId=11062493`
- Landing-page title: `Korea Economic Outlook (May 2026)`
- Publisher-displayed registration date: `2026-06-30`
- Attachment filename: `Korea Economic Outlook(May. 2026)_FF.pdf`
- Stable official attachment URL:
  `https://www.bok.or.kr/fileSrc/eng/e27abe95005c4990835da2375bcfbbd5/1/e818948f3fac4222871a192ba109ea90.pdf`
- Capture interval: `2026-07-28T13:49:40Z`–`2026-07-28T13:49:41Z`
- Response: official URL HTTP 302 to a short-lived signed `file-cdn.bok.or.kr` URL, then HTTP 200
  `application/pdf`
- Byte size: `3,711,417`
- SHA-256: `c30dd8fae88ba62db18b38484985aad457f658a22a899de58918d7581465986d`

The English full translation is independently dated one month after the Korean publication. Its
manifest is not backdated to the Korean release label or publication date.

## Redistribution conclusion

Neither landing page displayed a publication-specific KOGL mark, open-license notice, or other
affirmative raw-document redistribution grant when checked on 2026-07-28. The English page footer
states Bank of Korea copyright.

The official Bank of Korea copyright policy at
`https://www.bok.or.kr/portal/main/contents.do?menuNo=200228` states that:

1. Bank of Korea owns homepage information unless a separate copyright mark or source applies;
2. information outside the published public-data list may be used through direct or deep links; and
3. use by another method requires prior agreement and approval, with Bank of Korea attribution and
   disclosure of modification or processing.

No publication-specific evidence established that either PDF is in the freely reusable
public-data list. The fail-closed result is therefore `metadata_only`: commit the strict manifests,
official links, byte sizes, and checksums, but not the PDF bodies or extracted text. The temporary
capture directory is deleted after validation.

## Reproduction boundary

A later integrity check may repeat a direct `curl -fL` capture from each stable official attachment
URL and compare its byte size and SHA-256 with the manifests. Signed CDN URLs are ephemeral and are
not persisted. Any content change at the stable URL must create a new manifest rather than rewrite
these records.
