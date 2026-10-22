from pathlib import Path
import argparse
import math

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1080, 1350
ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "assets" / "pancreatic-cancer-poster-draft.jpg"
CHARCOAL = "#182326"
WHITE = "#F7FAF8"
MUTED = "#BFCFCC"
TEAL = "#65D8C0"
CORAL = "#FF9987"
RULE = "#405654"


def build_poster(palette="original"):
    palettes = {
        "original": ("#182326", "#F7FAF8", "#BFCFCC", "#65D8C0", "#FF9987", "#405654", "#344B4A"),
        "burgundy-teal": ("#FFFFFF", "#291B25", "#505B62", "#006B64", "#842343", "#B7C9CD", "#F4E5EB"),
    }
    background, foreground, muted, teal, coral, rule, cell_fill = palettes[palette]
    WHITE, MUTED, TEAL, CORAL, RULE = foreground, muted, teal, coral, rule
    output_path = OUTPUT if palette == "original" else ROOT / "assets" / "pancreatic-cancer-poster-burgundy-teal.jpg"
    if output_path.exists():
        raise FileExistsError("Refusing to overwrite an existing poster: " + str(output_path))
    image = Image.new("RGB", (WIDTH, HEIGHT), background)
    drawing = ImageDraw.Draw(image)
    text_bounds = []

    def text(content, position, size, color, region, spacing=7):
        font = ImageFont.load_default(size=size)
        local_bounds = drawing.multiline_textbbox(
            (0, 0), content, font=font, spacing=spacing
        )
        origin = (position[0] - local_bounds[0], position[1] - local_bounds[1])
        bounds = drawing.multiline_textbbox(
            origin, content, font=font, spacing=spacing
        )
        assert region[0] <= bounds[0] and region[1] <= bounds[1], (content, bounds)
        assert bounds[2] <= region[2] and bounds[3] <= region[3], (content, bounds)
        assert 48 <= bounds[0] < bounds[2] <= WIDTH - 48, (content, bounds)
        assert 40 <= bounds[1] < bounds[3] <= HEIGHT - 30, (content, bounds)
        for previous in text_bounds:
            assert (
                bounds[2] <= previous[0]
                or bounds[0] >= previous[2]
                or bounds[3] <= previous[1]
                or bounds[1] >= previous[3]
            ), ("Text overlap", content, bounds, previous)
        text_bounds.append(bounds)
        drawing.multiline_text(
            origin, content, font=font, fill=color, spacing=spacing
        )

    def line(points, color=RULE, width=2):
        drawing.line(points, fill=color, width=width)

    text("ORIGINAL EDUCATIONAL POSTER", (64, 55), 23, TEAL, (64, 55, 850, 85))
    text("DRAFT", (919, 55), 23, CORAL, (919, 55, 1016, 85))
    line([(64, 100), (1016, 100)])
    text("Pancreatic cancer", (64, 140), 84, WHITE, (64, 140, 1016, 225))
    text("Progress needs evidence.", (64, 245), 42, TEAL, (64, 245, 1016, 295))

    cell_center = (255, 432)
    for radius, color, thickness in [(104, TEAL, 3), (92, RULE, 1), (77, RULE, 1)]:
        drawing.ellipse(
            (cell_center[0] - radius, cell_center[1] - radius,
             cell_center[0] + radius, cell_center[1] + radius),
            outline=color, width=thickness,
        )
    drawing.ellipse((220, 398, 288, 466), fill=cell_fill, outline=CORAL, width=3)
    drawing.ellipse((243, 420, 260, 437), fill=CORAL)
    for angle in range(0, 360, 45):
        radians = math.radians(angle)
        center = (255 + math.cos(radians) * 104, 432 + math.sin(radians) * 104)
        drawing.ellipse((center[0] - 5, center[1] - 5, center[0] + 5, center[1] + 5), fill=TEAL)
    for center in [(205, 386), (304, 405), (208, 467), (285, 492)]:
        drawing.ellipse((center[0] - 9, center[1] - 4, center[0] + 9, center[1] + 4), outline=TEAL, width=2)

    line([(389, 432), (530, 432)], TEAL)
    nodes = [(604, 432), (666, 358), (750, 381), (786, 469), (696, 510), (887, 399), (943, 481)]
    for first, second in [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 2), (2, 5), (5, 6), (3, 6)]:
        line([nodes[first], nodes[second]], RULE, 3)
    for index, center in enumerate(nodes):
        radius = 13 if index in (0, 2, 3) else 9
        drawing.ellipse((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), fill=CORAL if index in (2, 5) else TEAL)
    text("CONCEPTUAL CELL / MOLECULAR ILLUSTRATION - NOT PATIENT IMAGING", (64, 558), 19, MUTED, (64, 558, 1016, 585))

    def band(number, label, top, body, bottom):
        line([(64, top), (1016, top)])
        text(number, (64, top + 23), 26, CORAL, (64, top + 23, 120, top + 58))
        text(label, (143, top + 24), 24, TEAL, (143, top + 24, 1016, top + 57))
        text(body, (143, top + 65), 27, WHITE, (143, top + 65, 1016, bottom), spacing=8)

    band("01", "CARE IS PERSONAL", 607,
         "Care depends on cancer stage, overall health\nand patient preferences.", 735)
    band("02", "TREATMENT OPTIONS", 755,
         "Treatment may include surgery, chemotherapy\nor radiation. Biomarker testing may identify\ntargeted therapy or immunotherapy options\nfor selected patients.", 957)
    band("03", "RESEARCH, NOT A GUARANTEE", 978,
         "Clinical trials test new approaches in people.\nBenefit is not guaranteed.", 1110)

    drawing.rectangle((64, 1141, 70, 1220), fill=CORAL)
    text("ASK YOUR CARE TEAM", (91, 1141), 20, CORAL, (91, 1141, 1016, 1170))
    text("Which options and tests fit my situation?", (91, 1178), 29, WHITE, (91, 1178, 1016, 1220))
    line([(64, 1245), (1016, 1245)])
    text("Educational only. Not medical advice. Video transcript unavailable.",
         (64, 1263), 20, MUTED, (64, 1263, 1016, 1290))
    text("Sources: NCI | Pancreatic Cancer Treatment (PDQ); What Are Clinical Trials?",
         (64, 1300), 19, MUTED, (64, 1300, 1016, 1320))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("xb") as output_file:
        image.save(output_file, format="JPEG", quality=95, subsampling=0)
    with Image.open(output_path) as decoded:
        decoded.load()
        assert decoded.size == (WIDTH, HEIGHT), decoded.size
        assert decoded.mode == "RGB", decoded.mode
        assert decoded.format == "JPEG", decoded.format
    print("Created:", output_path.relative_to(ROOT))
    print("Validated: JPEG decode; 1080 x 1350; RGB;")
    print("Validated:", len(text_bounds), "text blocks within assigned bounds, margins, and no text overlap.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build an original educational poster without overwriting existing artwork.")
    parser.add_argument("--palette", choices=("original", "burgundy-teal"), default="original")
    build_poster(parser.parse_args().palette)