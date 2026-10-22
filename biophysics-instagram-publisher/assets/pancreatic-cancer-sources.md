# Pancreatic Cancer Poster: Sources and Draft Status

Original educational artwork, not a video summary. Prepared 2026-10-21.

## Topic Prompt

- Video: https://www.youtube.com/watch?v=d7NqRRbISBs
- Supplied verified YouTube oEmbed metadata: "Breakthrough treatment for pancreatic cancer", author NBC News.
- Transcript unavailable. The title is context only, not evidence of a specific therapy, efficacy, or cure. No specific video treatment is described or inferred.
- No borrowed thumbnail, logo, patient imaging, or implied NBC News endorsement.

## Factual Basis

The commissioning context supplied the following verified facts from NCI pages fetched upstream. This local build did not independently retrieve or reverify the pages.

| Poster statement | Source |
| --- | --- |
| Care depends on cancer stage, overall health and patient preferences. | NCI, Pancreatic Cancer Treatment (PDQ), patient version |
| Treatment may include surgery, chemotherapy or radiation. | NCI, Pancreatic Cancer Treatment (PDQ), patient version |
| Biomarker testing may identify targeted therapy or immunotherapy options for selected patients. | NCI, Pancreatic Cancer Treatment (PDQ), patient version |
| Clinical trials test new approaches in people; benefit is not guaranteed. | NCI, What Are Clinical Trials? |

- https://www.cancer.gov/types/pancreatic/patient/pancreatic-treatment-pdq
- https://www.cancer.gov/about-cancer/treatment/clinical-trials/what-are-trials

The care-team question is original editorial wording, not a quotation. The illustration is original and conceptual, not an anatomical diagram or patient imaging. The poster makes no new-drug, efficacy, or cure claim and is educational, not medical advice.

## Build and Checks

Run `.venv/bin/python build_poster.py` from the project directory. The generator writes only `assets/pancreatic-cancer-poster-draft.jpg` and refuses to overwrite an existing file. It uses Pillow's bundled scalable font without external font access.

The generator asserts that every text block fits its assigned region, respects page margins, and does not overlap another text block. It decodes the completed JPEG and asserts JPEG format, 1080 x 1350 dimensions, and RGB color mode. Visual inspection is a separate check, not a substitute for these assertions.

No publishing or uploading is part of this build.