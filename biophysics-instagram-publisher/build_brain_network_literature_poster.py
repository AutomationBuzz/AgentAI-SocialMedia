"""Build a source-grounded poster on recent Nature memory-network research."""

import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
STEM = "brain-network-memory-literature-review"
POSTER = ASSETS / (STEM + ".jpg")
CAPTION = ASSETS / (STEM + "-caption.txt")
SOURCES = ASSETS / (STEM + "-sources.md")
SUMMARY = ASSETS / (STEM + "-summary.json")
WIDTH, HEIGHT = 1080, 1350
PAPER = "#F7F6F0"
INK = "#202A2D"
MUTED = "#596866"
TEAL = "#08766C"
CORAL = "#C8523C"
GOLD = "#A96F12"
RULE = "#D7DED8"
PALE_TEAL = "#E3F1EB"
PALE_CORAL = "#F7E8E1"
PALE_GOLD = "#F5EEDB"


def font(size):
    return ImageFont.load_default(size=size)


def wrap(draw, content, use_font, max_width):
    lines = []
    for paragraph in content.split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = (current + " " + word).strip()
            if current and draw.textlength(candidate, font=use_font) > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return lines


def add_text(draw, content, box, size, color=INK, spacing=4, align="left"):
    left, top, right, bottom = box
    use_font = font(size)
    lines = wrap(draw, content, use_font, right - left)
    text = "\n".join(lines)
    bounds = draw.multiline_textbbox((left, top), text, font=use_font, spacing=spacing)
    if bounds[2] > right or bounds[3] > bottom:
        raise AssertionError((content, bounds, box))
    draw.multiline_text((left, top), text, font=use_font, fill=color, spacing=spacing, align=align)
    return bounds


def draw_network(draw):
    # Deliberately conceptual: distinguish recurring cell ensembles and synaptic change,
    # without presenting an invented anatomical image or measured connectivity map.
    draw.rounded_rectangle((64, 303, 1016, 682), radius=14, fill="#FCFCF8", outline=RULE, width=2)
    add_text(draw, "CONCEPTUAL CIRCUIT / NOT A BRAIN SCAN", (88, 321, 620, 347), 13, MUTED)

    edges = [
        ((202, 465), (372, 415)), ((202, 465), (382, 534)),
        ((372, 415), (516, 476)), ((382, 534), (516, 476)),
        ((516, 476), (690, 401)), ((516, 476), (697, 543)),
        ((690, 401), (862, 459)), ((697, 543), (862, 459)),
        ((372, 415), (697, 543)), ((382, 534), (690, 401)),
    ]
    for first, second in edges:
        draw.line((first, second), fill="#A9C0B4", width=4)

    # Overlapping engram ensembles, shown as overlapping outlines rather than storage boxes.
    draw.ellipse((294, 356, 554, 584), outline=TEAL, width=4)
    draw.ellipse((389, 371, 640, 604), outline=CORAL, width=4)
    draw.rounded_rectangle((337, 357, 487, 390), radius=9, fill=PALE_TEAL)
    add_text(draw, "MEMORY A", (349, 363, 475, 385), 13, TEAL)
    draw.rounded_rectangle((444, 585, 596, 618), radius=9, fill=PALE_CORAL)
    add_text(draw, "MEMORY B", (456, 591, 584, 614), 13, CORAL)

    neuron_nodes = [((202, 465), "CUE", 11), ((372, 415), "ENGRAM", 7),
                    ((382, 534), "ENGRAM", 7), ((516, 476), "CA1", 10),
                    ((690, 401), "ASTRO", 8), ((697, 543), "SYN", 10),
                    ((862, 459), "CTX", 10)]
    for (x, y), label, label_size in neuron_nodes:
        radius = 23 if label in ("CA1", "ASTROCYTE") else 19
        fill = PALE_GOLD if label == "ASTROCYTE" else (PALE_CORAL if label == "CA1" else "#FFFFFF")
        outline = GOLD if label == "ASTROCYTE" else (CORAL if label == "CA1" else TEAL)
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=fill, outline=outline, width=3)
        label_font = font(label_size)
        label_width = draw.textlength(label, font=label_font)
        if label_width > radius * 1.8:
            raise AssertionError((label, label_width, radius))
        draw.text((x-label_width/2, y-label_size/2), label, font=label_font, fill=INK)

    draw.ellipse((540, 489, 551, 500), fill=CORAL)
    draw.ellipse((678, 424, 687, 433), fill=GOLD)
    add_text(draw, "Partly shared ensembles can link experiences while synapses and branches preserve distinct details.",
             (95, 635, 985, 669), 15, MUTED)


def build_poster():
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 15), fill=TEAL)
    add_text(draw, "LITERATURE REVIEW  /  NATURE FAMILY  /  2024-2025", (64, 39, 1016, 65), 15, TEAL)
    add_text(draw, "Memory is a\nnetwork event", (64, 82, 1016, 216), 66, INK, spacing=0)
    add_text(draw, "Engrams, astrocytes + synaptic plasticity", (66, 224, 1010, 260), 25, MUTED)
    draw_network(draw)

    columns = [
        {
            "x": 64, "color": TEAL, "fill": PALE_TEAL, "number": "01",
            "title": "LINKED ENGRAMS",
            "body": "2024 REVIEW / Choucry et al. synthesize evidence that memories formed close in time may share some engram neurons. Overlap can link experiences while synaptic and dendritic organization may help retain distinct details."
        },
        {
            "x": 388, "color": CORAL, "fill": PALE_CORAL, "number": "02",
            "title": "ASTROCYTES PARTICIPATE",
            "body": "2025 MOUSE STUDY / Learning-activated hippocampal astrocyte ensembles were affiliated with engram neurons. Reactivating these ensembles stimulated recall; selective Nfia deletion suppressed recall. This is animal evidence, not a human result."
        },
        {
            "x": 712, "color": GOLD, "fill": PALE_GOLD, "number": "03",
            "title": "PLASTICITY, MAPPED",
            "body": "2025 MOUSE METHODS / DELTA mapped learning-related GluA2 turnover, strongest in hippocampal CA1. EPSILON mapped AMPAR exocytosis during mouse fear learning; it correlated with c-Fos. These tools reveal candidate plasticity, not a complete memory or human diagnosis."
        },
    ]
    card_top, card_bottom, card_width = 716, 1068, 304
    for item in columns:
        x = item["x"]
        draw.rounded_rectangle((x, card_top, x+card_width, card_bottom), radius=12,
                               fill="#FFFEFA", outline=RULE, width=2)
        draw.rounded_rectangle((x+15, card_top+15, x+60, card_top+48), radius=8, fill=item["fill"])
        add_text(draw, item["number"], (x+25, card_top+21, x+52, card_top+43), 17, item["color"])
        add_text(draw, item["title"], (x+15, card_top+61, x+card_width-14, card_top+103), 20, item["color"])
        add_text(draw, item["body"], (x+15, card_top+115, x+card_width-14, card_bottom-18), 17, INK, spacing=5)

    draw.rounded_rectangle((64, 1087, 1016, 1190), radius=12, fill="#243839")
    add_text(draw, "WHAT THIS LITERATURE SAYS", (84, 1103, 520, 1129), 15, "#A8D5C4")
    add_text(draw, "Memory depends on interacting ensembles and changing synapses, not one storage site.",
             (84, 1135, 990, 1168), 19, "#FFFFFF")
    add_text(draw, "LIMIT / Animal models and molecular tools illuminate mechanisms, but do not by themselves explain human subjective memory or identity.",
             (84, 1168, 990, 1187), 13, "#D6E3DE")

    draw.line((64, 1208, 1016, 1208), fill=TEAL, width=3)
    add_text(draw, "SELECTED RECENT LITERATURE", (64, 1222, 1016, 1244), 14, TEAL)
    add_text(draw, "Choucry et al. Nat Rev Neurosci (2024) doi:10.1038/s41583-024-00814-0  |  Williamson et al. Nature (2025) doi:10.1038/s41586-024-08170-w",
             (64, 1248, 1016, 1271), 11, MUTED)
    add_text(draw, "Mohar et al. Nat Neurosci (2025) doi:10.1038/s41593-025-01923-4  |  Kim et al. Nat Neurosci (2025) doi:10.1038/s41593-025-01922-5",
             (64, 1274, 1016, 1297), 11, MUTED)
    add_text(draw, "Conceptual illustration only / No measured connectivity or brain scan shown", (64, 1305, 1016, 1325), 12, MUTED)

    if POSTER.exists():
        raise FileExistsError("Refusing to overwrite: " + str(POSTER))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=96, subsampling=0, optimize=True)
    with Image.open(io.BytesIO(buffer.getvalue())) as decoded:
        assert decoded.size == (WIDTH, HEIGHT) and decoded.mode == "RGB"
        decoded.verify()
    POSTER.write_bytes(buffer.getvalue())
    return image


def write_supporting_files():
    caption = """How does a memory live in a brain-wide network?

Recent Nature-family research points to interacting neuronal ensembles, astrocytes and changing synapses. A 2024 review describes how partly overlapping engrams may link memories formed close together while preserving differences. A 2025 mouse study found learning-associated hippocampal astrocyte ensembles closely affiliated with engram neurons; reactivating them stimulated recall. Two 2025 Nature Neuroscience studies add tools to map synaptic protein turnover and AMPA-receptor exocytosis during learning.

Important: the astrocyte and synaptic experiments are in mice. Tool papers map candidate plasticity; they do not directly measure human memory, diagnose people, or resolve consciousness. The network artwork is conceptual, not a brain scan or measured connectome.

Selected sources:
Choucry et al., Nature Reviews Neuroscience (2024): https://doi.org/10.1038/s41583-024-00814-0
Williamson et al., Nature (2025): https://doi.org/10.1038/s41586-024-08170-w
Mohar et al., Nature Neuroscience (2025): https://doi.org/10.1038/s41593-025-01923-4
Kim et al., Nature Neuroscience (2025): https://doi.org/10.1038/s41593-025-01922-5

#Neuroscience #MemoryResearch #BrainNetworks #Neurobiology #ScienceCommunication"""
    sources = """# Brain network and memory literature poster

## Review synthesis
Choucry A, Nomoto M, Inokuchi K. Engram mechanisms of memory linking and identity. *Nature Reviews Neuroscience*. 2024;25(6):375-392. DOI: https://doi.org/10.1038/s41583-024-00814-0. PubMed PMID 38664582. Review article. The abstract describes prospective linking of memories occurring close in time through partial engram overlap while maintaining identity, and retrospective linking through offline reactivation. This is a review of experimental and modelling work, not a new single cohort result.

## Recent primary study: astrocytes and recall
Williamson MR, et al. Learning-associated astrocyte ensembles regulate memory recall. *Nature*. 2025;637:478-486. DOI: https://doi.org/10.1038/s41586-024-08170-w. PMID 39506118; PMCID PMC11924044. The indexed abstract reports mouse experiments: learning-induced c-Fos in a subset of hippocampal astrocytes; those ensembles were affiliated with engram neurons; reactivation stimulated recall; selective Nfia deletion suppressed recall. Do not generalize directly to humans.

## Recent primary methods: synaptic plasticity
Mohar B, et al. DELTA: a method for brain-wide measurement of synaptic protein turnover reveals localized plasticity during learning. *Nature Neuroscience*. 2025;28(5):1089-1098. DOI: https://doi.org/10.1038/s41593-025-01923-4. PMID 40164741; PMCID PMC12081306. Abstract describes HaloTag knock-in mice and learning-associated GluA2 turnover, most marked in hippocampal CA1, with input-specific effects. This is a measurement method and mouse study, not direct evidence of human memory storage.

Kim D, et al. EPSILON: a method for pulse-chase labeling to probe synaptic AMPAR exocytosis during memory formation. *Nature Neuroscience*. 2025;28(5):1099-1107. DOI: https://doi.org/10.1038/s41593-025-01922-5. PMID 40164742. Abstract describes in-vivo pulse-chase mapping in mice undergoing contextual fear conditioning; AMPAR exocytosis in CA1 pyramidal neurons correlated with c-Fos expression. Correlation and a methods paper do not alone establish a complete causal theory of memory.

## Interpretation and artwork
The illustration is an original conceptual network only. No anatomical image, patient data, scan, or measured connectome is presented. The literature supports a distributed, interacting view of memory-related plasticity; it does not resolve how neural mechanisms produce subjective conscious experience. The mouse studies are explicitly identified as animal evidence.

## Hashtags
#Neuroscience #MemoryResearch #BrainNetworks #Neurobiology #ScienceCommunication
"""
    summary = {
        "poster": POSTER.name,
        "resolution": [WIDTH, HEIGHT],
        "theme": "Nature-family literature synthesis on memory networks",
        "review_count": 1,
        "primary_studies_count": 3,
        "animal_evidence_prominently_labeled": True,
        "measured_dataset_used": False,
        "artwork_is_conceptual": True,
        "hashtags": ["#Neuroscience", "#MemoryResearch", "#BrainNetworks", "#Neurobiology", "#ScienceCommunication"],
        "publication_performed": False,
    }
    for path in (CAPTION, SOURCES, SUMMARY):
        if path.exists():
            raise FileExistsError("Refusing to overwrite: " + str(path))
    CAPTION.write_text(caption + "\n", encoding="utf-8")
    SOURCES.write_text(sources, encoding="utf-8")
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def main():
    ASSETS.mkdir(exist_ok=True)
    build_poster()
    write_supporting_files()
    print("Created research poster:", POSTER.relative_to(ROOT))
    print("Sources:", SOURCES.relative_to(ROOT))
    print("Caption:", CAPTION.relative_to(ROOT))
    print("Summary:", SUMMARY.relative_to(ROOT))


if __name__ == "__main__":
    main()