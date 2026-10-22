# Memory recall data poster: sources and method

Accessed 2026-10-21. Reproduce with `build_memory_data_poster.py` and the pinned `requirements-memory-poster.txt`.

## Primary measured data
- CDC/NCHS, NHANES 2011-2012 Cognitive Functioning (CFQ_G) codebook: https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/CFQ_G.htm
- Public CFQ_G XPT: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/CFQ_G.xpt
- CDC/NCHS, NHANES 2011-2012 Demographics (DEMO_G) codebook: https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/DEMO_G.htm
- Public DEMO_G XPT: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/DEMO_G.xpt
- NHANES overview and public-data explanation: https://www.cdc.gov/nchs/nhanes/about/index.html

## Variables and calculation
- `CFDCSR`: data-file label “CERAD: Score Delayed Recall”; observed scores in the included records range 0-10.
- `CFDCCS == 1`: included completed CERAD tests; records with other status codes were excluded.
- `RIDAGEYR`: observed included age range 60-80.
- `WTMEC2YR`: MEC exam weight used for weighted descriptive score-band proportions.
- `SDMVSTRA` and `SDMVPSU`: retained design fields; no confidence interval is presented on the graphic.
- Join CFQ_G and DEMO_G on `SEQN`, then retain completed status, nonmissing score, and nonmissing weight. Completed n=1,451.
- Bands are 0-2, 3-4, 5-6, 7-8, 9-10. The 0-2 highlight is an arbitrary visual group only, not a validated impairment threshold, clinical cutoff, or diagnosis.
- Weighted shares: 0-2 9.59%; 3-4 17.57%; 5-6 30.91%; 7-8 30.21%; 9-10 11.73%. Unweighted n appears beneath bars.
- This is a single 2011-2012 survey-cycle descriptive estimate among completed tests, not a current prevalence or individual prognosis. No CI shown.

## Neuroscience context (separate from the plotted dataset)
- Chang H, et al. Sleep microstructure organizes memory replay. Nature. 2025;637:1161-1169. doi:10.1038/s41586-024-08340-w. https://doi.org/10.1038/s41586-024-08340-w
- NIMH research highlight (2025) explicitly summarizes the relevant sleep/replay findings in mice: https://www.nimh.nih.gov/news/science-updates/2025/how-the-brain-creates-new-memories-while-maintaining-old-ones
- NINDS Brain Basics: https://www.ninds.nih.gov/health-information/public-education/brain-basics

The chart uses real NHANES observations. The sleep study is a separate animal-research finding and is not the source of the plotted values. No person-level data are retained in the project outputs.
