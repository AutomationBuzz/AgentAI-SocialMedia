"""Build a sourced NHANES delayed-recall poster from public CDC XPT files."""

from io import BytesIO
import json
from pathlib import Path
import urllib.request

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import pyreadstat


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
STEM = "memory-nhanes-cerad-delayed-recall"
POSTER_PATH = ASSETS / (STEM + ".jpg")
CAPTION_PATH = ASSETS / (STEM + "-caption.txt")
SOURCES_PATH = ASSETS / (STEM + "-sources.md")
SUMMARY_PATH = ASSETS / (STEM + "-summary.json")
CFQ_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/CFQ_G.xpt"
DEMO_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2011/DataFiles/DEMO_G.xpt"
CFQ_DOC = "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/CFQ_G.htm"
DEMO_DOC = "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/DEMO_G.htm"
NHANES_ABOUT = "https://www.cdc.gov/nchs/nhanes/about/index.html"
NIMH_SLEEP = "https://www.nimh.nih.gov/news/science-updates/2025/how-the-brain-creates-new-memories-while-maintaining-old-ones"
NIMH_DOI = "https://doi.org/10.1038/s41586-024-08340-w"
NINDS = "https://www.ninds.nih.gov/health-information/public-education/brain-basics"
HASHTAGS = ["#MemoryResearch", "#Neuroscience", "#BrainHealth", "#ScienceCommunication", "#NHANES"]
WIDTH, HEIGHT = 1080, 1350
PAPER, INK, MUTED = "#F7F6F0", "#202A2D", "#5C6969"
TEAL, CORAL, GOLD = "#08766C", "#C8523C", "#A96F12"
RULE, PALE_TEAL, PALE_GOLD = "#D9DFD9", "#E3F1EB", "#F5EEDB"


def font(size):
    return ImageFont.load_default(size=size)


def fetch_xpt(url, filename):
    request = urllib.request.Request(url, headers={"User-Agent": "MemoryLab-Educational-Poster/1.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = response.read()
    if len(payload) < 1000 or payload.lstrip().startswith(b"<!DOCTYPE"):
        raise RuntimeError("CDC did not return the expected XPT dataset: " + url)
    filename.write_bytes(payload)
    return payload


def load_data():
    import tempfile

    with tempfile.TemporaryDirectory(prefix="nhanes-memory-") as temp_dir:
        temp = Path(temp_dir)
        cfq_path, demo_path = temp / "CFQ_G.xpt", temp / "DEMO_G.xpt"
        fetch_xpt(CFQ_URL, cfq_path)
        fetch_xpt(DEMO_URL, demo_path)
        cognitive, metadata = pyreadstat.read_xport(str(cfq_path))
        demographics, _ = pyreadstat.read_xport(str(demo_path))
    expected_label = "CERAD: Score Delayed Recall"
    if metadata.column_names_to_labels.get("CFDCSR") != expected_label:
        raise RuntimeError("Unexpected NHANES CFDCSR label; refusing to chart unverified data.")
    if "CFDCCS" not in cognitive or "WTMEC2YR" not in demographics:
        raise RuntimeError("Required completion status or MEC examination weight is missing.")
    joined = cognitive[["SEQN", "CFDCSR", "CFDCCS"]].merge(
        demographics[["SEQN", "RIDAGEYR", "WTMEC2YR", "SDMVSTRA", "SDMVPSU"]],
        on="SEQN", how="inner", validate="one_to_one",
    )
    completed = joined.loc[
        (joined["CFDCCS"] == 1)
        & joined["CFDCSR"].notna()
        & joined["WTMEC2YR"].notna()
    ].copy()
    if len(completed) < 1000:
        raise RuntimeError("Unexpected completed-test sample size; inspect the CDC release.")
    if completed["CFDCSR"].min() != 0 or completed["CFDCSR"].max() != 10:
        raise RuntimeError("Unexpected delayed-recall score range; refusing to chart.")
    if completed["RIDAGEYR"].min() < 60:
        raise RuntimeError("Unexpected minimum age; inspect the cognitive component eligibility.")
    bins = [-0.5, 2, 4, 6, 8, 10]
    labels = ["0-2", "3-4", "5-6", "7-8", "9-10"]
    completed["score_band"] = pd.cut(completed["CFDCSR"], bins=bins, labels=labels)
    grouped = completed.groupby("score_band", observed=False).agg(
        unweighted_n=("CFDCSR", "size"), weight_sum=("WTMEC2YR", "sum")
    )
    grouped["weighted_percent"] = 100 * grouped["weight_sum"] / grouped["weight_sum"].sum()
    bands = [
        {
            "band": str(label),
            "unweighted_n": int(grouped.loc[label, "unweighted_n"]),
            "weighted_percent": round(float(grouped.loc[label, "weighted_percent"]), 2),
        }
        for label in labels
    ]
    low = completed["CFDCSR"] <= 2
    summary = {
        "dataset": "NHANES 2011-2012 public release",
        "component": "CFQ_G",
        "measure_variable": "CFDCSR",
        "measure_label": expected_label,
        "completion_variable": "CFDCCS",
        "included_completion_code": 1,
        "weight_variable": "WTMEC2YR",
        "design_variables": ["SDMVSTRA", "SDMVPSU"],
        "valid_completed_n": int(len(completed)),
        "age_min": int(completed["RIDAGEYR"].min()),
        "age_max": int(completed["RIDAGEYR"].max()),
        "score_min": int(completed["CFDCSR"].min()),
        "score_max": int(completed["CFDCSR"].max()),
        "visual_low_band": "0-2 (illustrative visualization band only; not a clinical threshold)",
        "visual_low_band_unweighted_n": int(low.sum()),
        "visual_low_band_unweighted_percent": round(float(low.mean() * 100), 2),
        "visual_low_band_weighted_percent": round(
            float(completed.loc[low, "WTMEC2YR"].sum() / completed["WTMEC2YR"].sum() * 100), 2
        ),
        "weighted_score_bands": bands,
        "uncertainty_interval_reported": False,
        "population_prevalence_claim": False,
        "raw_microdata_stored_in_project": False,
        "hashtags": HASHTAGS,
    }
    return completed, summary


def draw_poster(summary):
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)

    def text(value, xy, size, color=INK):
        draw.text(xy, value, font=font(size), fill=color)

    draw.rectangle((0, 0, WIDTH, 17), fill=TEAL)
    text("MEMORY / DATA NOTES  01", (62, 47), 20, TEAL)
    text("A real recall score\nfrom a public survey", (62, 91), 57, INK)
    text("NHANES 2011-2012  /  CERAD DELAYED WORD RECALL", (62, 229), 18, MUTED)

    draw.rounded_rectangle((62, 279, WIDTH - 62, 372), radius=12, fill=PALE_TEAL)
    text("9.59%", (83, 294), 42, TEAL)
    text("WEIGHTED SHARE IN THE 0-2 / 10 SCORE BAND", (258, 300), 18, INK)
    text("175 of 1,451 completed tests scored 0-2 (12.06% unweighted).", (258, 332), 16, MUTED)

    text("HOW SCORES WERE DISTRIBUTED", (64, 408), 20, CORAL)
    text("Survey-weighted share of completed delayed-recall scores", (64, 435), 15, MUTED)
    chart_left, chart_top, chart_width, chart_height = 92, 503, 900, 378
    y_bottom = chart_top + chart_height
    max_value = 35
    draw.line((chart_left, chart_top, chart_left, y_bottom), fill=INK, width=2)
    draw.line((chart_left, y_bottom, chart_left + chart_width, y_bottom), fill=INK, width=2)
    for tick in range(0, max_value + 1, 5):
        y = y_bottom - tick / max_value * chart_height
        draw.line((chart_left, y, chart_left + chart_width, y), fill=RULE, width=1)
        text(str(tick), (54, y - 10), 13, MUTED)
    text("WEIGHTED PERCENT", (64, 478), 12, MUTED)
    band_width, gap = 116, 48
    plot_width = len(summary["weighted_score_bands"]) * band_width + 4 * gap
    start_x = chart_left + (chart_width - plot_width) // 2
    for index, item in enumerate(summary["weighted_score_bands"]):
        x = start_x + index * (band_width + gap)
        height = item["weighted_percent"] / max_value * chart_height
        color = CORAL if item["band"] == "0-2" else TEAL
        top = y_bottom - height
        draw.rounded_rectangle((x, top, x + band_width, y_bottom - 2), radius=7, fill=color)
        value_text = "%.2f%%" % item["weighted_percent"]
        tw = draw.textlength(value_text, font=font(16))
        text(value_text, (x + (band_width - tw) / 2, top - 26), 16, INK)
        band_text = item["band"]
        bw = draw.textlength(band_text, font=font(16))
        text(band_text, (x + (band_width - bw) / 2, y_bottom + 11), 16, INK)
        n_text = "n=%d" % item["unweighted_n"]
        nw = draw.textlength(n_text, font=font(12))
        text(n_text, (x + (band_width - nw) / 2, y_bottom + 34), 12, MUTED)
    text("Score band (out of 10) / unweighted n shown below each bar", (chart_left, 925), 13, MUTED)

    draw.line((62, 968, WIDTH - 62, 968), fill=RULE, width=2)
    text("WHAT THIS NEGATIVE-CASE VIEW DOES - AND DOES NOT - SAY", (62, 992), 17, CORAL)
    text("The highlighted 0-2 band is a visual grouping, not a clinical cutoff, diagnosis, or impairment label.", (62, 1023), 16, INK)
    text("This is one older survey cycle, not current prevalence. Scores describe a word-recall task, not a person's whole memory.", (62, 1051), 15, MUTED)
    text("Sample: ages 60-80; completed CERAD delayed-recall tests only; n=1,451. Weighted with NHANES MEC exam weights.", (62, 1078), 15, MUTED)

    draw.rounded_rectangle((62, 1120, WIDTH - 62, 1207), radius=10, fill=PALE_GOLD)
    text("RESEARCH CONNECTION / not the plotted dataset", (80, 1135), 14, GOLD)
    text("A 2025 mouse study linked sleep substates with replay of new vs. old memories.", (80, 1161), 15, INK)
    text("Animal result: it does not establish the same mechanism in humans.", (80, 1182), 13, MUTED)

    draw.line((62, 1232, WIDTH - 62, 1232), fill=TEAL, width=2)
    text("SOURCES  /  CDC NHANES CFQ_G + DEMO_G (2011-2012); Chang et al., Nature 637 (2025), doi:10.1038/s41586-024-08340-w", (62, 1250), 11, MUTED)
    text("Educational data visualization. Weighted descriptive estimates; no confidence interval shown.", (62, 1273), 12, MUTED)
    text("#MemoryResearch  #Neuroscience  #BrainHealth  #ScienceCommunication  #NHANES", (62, 1303), 12, TEAL)

    for path in (POSTER_PATH,):
        if path.exists():
            raise FileExistsError("Refusing to overwrite: " + str(path))
    ASSETS.mkdir(exist_ok=True)
    image.save(POSTER_PATH, format="JPEG", quality=96, subsampling=0, optimize=True)
    with Image.open(POSTER_PATH) as decoded:
        decoded.load()
        assert decoded.size == (WIDTH, HEIGHT) and decoded.mode == "RGB"
    return image


def main():
    for path in (CAPTION_PATH, SOURCES_PATH, SUMMARY_PATH):
        if path.exists():
            raise FileExistsError("Refusing to overwrite: " + str(path))
    _, summary = load_data()
    draw_poster(summary)
    caption = (
        "What does a low score on one memory task actually tell us? In CDC NHANES 2011-2012, "
        "1,451 completed CERAD delayed word-recall tests (ages 60-80) had scores from 0 to 10. "
        "Using the NHANES MEC examination weights, 9.59% fell in the 0-2 score band; 175 people "
        "were in that band (12.06% of this tested sample, unweighted).\n\n"
        "Important: 0-2 is a visualization band chosen for this graphic, NOT a clinical cutoff or "
        "diagnosis. This one older survey cycle is not current prevalence; a single word-recall task "
        "does not define a person's memory or health. The bars show weighted descriptive shares; "
        "no confidence interval is displayed.\n\n"
        "The sleep research connection is separate: Chang et al. studied mice, not people. Animal "
        "findings help generate questions but do not prove the same mechanism in humans.\n\n"
        "Data and codebooks: CDC NHANES CFQ_G (https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/CFQ_G.htm), "
        "DEMO_G (https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/DEMO_G.htm), "
        "public XPT files CFQ_G.xpt and DEMO_G.xpt. NHANES overview: " + NHANES_ABOUT + "\n"
        "Sleep study: Chang et al. (2025), Nature 637, 1161-1169, " + NIMH_DOI + "\n"
        "Brain background: NINDS Brain Basics, " + NINDS + "\n\n"
        "#MemoryResearch #Neuroscience #BrainHealth #ScienceCommunication #NHANES"
    )
    CAPTION_PATH.write_text(caption + "\n", encoding="utf-8")
    source_text = """# Memory recall data poster: sources and method

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
"""
    SOURCES_PATH.write_text(source_text, encoding="utf-8")
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("Created:", POSTER_PATH.relative_to(ROOT))
    print("Valid completed records:", summary["valid_completed_n"])
    print("Weighted 0-2 visualization band:", summary["visual_low_band_weighted_percent"], "%")
    print("Hashtags:", " ".join(HASHTAGS))


if __name__ == "__main__":
    main()