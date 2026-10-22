# Biophysics + AI: Evidence and Claim Mapping

## Verified Primary Source

Jumper, J. et al. Highly accurate protein structure prediction with AlphaFold.
Nature 596, 583-589 (2021). DOI: 10.1038/s41586-021-03819-2.

- Canonical: https://www.nature.com/articles/s41586-021-03819-2
- Full text actually fetched: https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8371605/fullTextXML
- Bibliographic verification: https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/s41586-021-03819-2&format=json
- Accessed 2026-10-21. Nature redirected to an identity/cookie page; Europe PMC supplied the full article. No article figures were reused.

## Claim Mapping

| Artwork or caption statement | Evidence and limits |
| --- | --- |
| Physical models describe interactions and geometry; ML can incorporate physical and biological constraints. | Introduction, paragraphs 3-4; The AlphaFold network, paragraphs 7-8; Discussion, paragraph 24. AlphaFold is an example of physical/geometric inductive bias, not a claim that all ML is physics-informed or that it simulates folding dynamics. |
| AlphaFold predicts structure and estimates confidence. | Abstract; paragraph 6 and Figure 2c-d; paragraph 17. pLDDT estimates local structural accuracy; it is not a measurement of function or a complete uncertainty description. No numerical accuracy claim is made in the poster. |
| Predictions were tested against experimental structures, including blind CASP14. | Paragraphs 4-6; Figure 1; Methods, Test set of recent PDB sequences. CASP14 targets were not publicly disclosed to participating methods. Results do not establish universal accuracy on arbitrary proteins or conditions. |
| A structure prediction is not an experimental measurement, and alone does not establish dynamics or function. | Scope distinction: paragraph 8 describes coordinate prediction; paragraph 25 describes the likely PDB-like structure. The abstract says structure can facilitate mechanistic understanding, not prove function. This educational caution is not presented as a measured result of this paper. |
| Compare with independent measurements and experimental error; evaluate uncertainty and out-of-distribution performance. | Author-recommended validation practice, motivated by the paper's blind evaluation, confidence assessment and limitations (MSA depth and cross-chain contacts, paragraphs 22 and Figure 5). New proteins/conditions are examples of possible distribution shift, not a claim that every new protein is out-of-distribution or that CASP14 establishes arbitrary OOD robustness. |
| AI complements experiments; use feedback to refine models. | Educational synthesis, supported by dependence on experimental PDB data and Discussion, paragraph 26, describing experimental uses. The feedback diagram is a general research workflow, not the AlphaFold architecture or its internal recycling procedure. |

## Illustration and Editorial Scope

Original Pillow-drawn chain/contact model, learning network and prediction/measurement plot. The smooth line represents a conceptual prediction; dots and error bars symbolize measurements and their uncertainty. All coordinates are invented for illustration, with no empirical values or axes implying quantitative results. The on-art disclaimer states that no measured data are shown. No unavailable video was used.

White background; burgundy #842343, teal #006B64, gold #AF7900; dark ink #241F24. Gold is used for visual marks, not small body text. Final output is an RGB 1080x1350 JPEG. The standalone generator refuses to overwrite an existing image and checks text bounds, pairwise text collisions, text/illustration separation, JPEG decoding and the 8 MiB size ceiling.

The suggested review https://www.nature.com/articles/s42254-021-00314-5 could not yet be read through the fetch tool (cookie/access response). It is not used to substantiate claims or cited in the artwork/caption. The verified primary study above is sufficient for the conservative example used here.