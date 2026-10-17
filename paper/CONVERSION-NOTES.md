# S9 — JEDM template conversion notes

**Date:** 2026-10-16
**Source:** `paper.tex` (article class, hand-rolled JEDM-spec formatting) — untouched, remains the content source of truth.
**Output:** `paper-jedm.tex` → `paper-jedm.pdf` (14 pages, clean build: 0 errors, 0 undefined references/citations).

## Template used

Official JEDM LaTeX package **`2024_08_02_jedm-latex.zip`**, downloaded from the
journal's Information for Authors page
(https://jedm.educationaldatamining.org/index.php/JEDM/information/authors).
Contains `jedm.cls` (copied into `paper/` as `jedm.cls`), `instructions.tex`,
`acmtrans.bst`, `ref.bib`, `example-fig.pdf`. No Word-template or elsarticle
fallback was needed — JEDM publishes a real official LaTeX class.

Usage follows the template's own `instructions.tex`: `\documentclass[notitlepage,12pt]{jedm}`.

## What the conversion changed (format only)

- Document class `article` → `jedm` (Times body, Helvetica title/headings,
  small-caps numbered sections, JEDM margins 2.75cm L/R × 2.25cm T/B, page
  numbers at bottom for review).
- Dropped hand-rolled formatting now owned by the class: `geometry`,
  `titlesec`/`\titleformat`, `caption`/`\captionsetup`. Kept `mathptmx`,
  `helvet`, `graphicx`, `booktabs`, `amsmath/amssymb`, `natbib [round]`,
  `hyperref [hidelinks]`, `microtype`.
- Keywords moved inside the `abstract` environment per the template
  (`{\parindent0pt \textbf{Keywords:} ...}`).
- Appendix sections now lettered A/B via the class's `\appendix` (were
  continuation-numbered); they are not `\ref`'d anywhere, so nothing breaks.
- **Paper size:** the class defaults to **letterpaper**, and the current
  official `instructions.tex` says "letter sized paper" (the older spec said
  A4). The conversion follows the current template default.

## Adaptations / fixes

- `jedm.cls` pre-allocates `\bibhang`, which collides with natbib's own
  allocation (`! LaTeX Error: Command \bibhang already defined`). Fixed with
  `\let\bibhang\relax` before loading natbib — the class's own bibliography
  environment is dead code once natbib takes over, so this is safe. The class
  file itself was not modified.
- Manual `thebibliography` with natbib author-year `\bibitem[...]{...}`
  entries kept verbatim; all 15 `\citep` + 6 `\citet` calls resolve (ACM
  author-year style, matching the template's ACM reference requirement).

## Verification (pdftotext vs original PDF)

- Title, abstract, keywords, all 8 numbered sections, appendix A/B, AI
  declaration (verbatim), Competing Interests, Data and Code Availability:
  present and intact.
- Spot-checked numbers: 297 of 300, 300 episodes, 24 preregistered tests,
  162 of 300, 5,000 sequences, 50 trajectories, M1 slope, 0.833,
  ASSISTments — all present in both.
- Citations render correctly, e.g. `(Xu et al., 2026)`; zero `[?]`, zero
  undefined references/citations in the log.
- 3 figures embedded; table caption on top per JEDM spec.
- Fonts embedded: Times body, Helvetica headings, Courier for `\texttt`.
- Page count 14 vs 13 for the old PDF (template title block + heading spacing;
  no JEDM review page limit is violated).
- Anonymized: empty author block, no author names in the PDF text.
