"""Render an original educational illustration; no credentials or network needed."""

import io
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "assets" / "biophysics-ai-poster.jpg"
WIDTH, HEIGHT = 1080, 1350
BURGUNDY = "#842343"
TEAL = "#006B64"
GOLD = "#AF7900"
INK = "#241F24"
MUTED = "#53565A"
RULE = "#D9DDDC"


def overlaps(first, second):
    return (first[0] < second[2] and first[2] > second[0]
            and first[1] < second[3] and first[3] > second[1])


def build_poster():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite: " + str(OUTPUT))
    image = Image.new("RGB", (WIDTH, HEIGHT), "#FFFFFF")
    drawing = ImageDraw.Draw(image)
    text_boxes = []
    graphic_boxes = []

    def text(content, left, top, size, color=INK, right=1016, bottom=1310):
        font = ImageFont.load_default(size=size)
        local = drawing.multiline_textbbox((0, 0), content, font=font, spacing=9)
        origin = (left - local[0], top - local[1])
        bounds = drawing.multiline_textbbox(origin, content, font=font, spacing=9)
        assert 64 <= bounds[0] < bounds[2] <= right <= 1016, (content, bounds)
        assert 40 <= bounds[1] < bounds[3] <= bottom <= 1310, (content, bounds)
        for previous_content, previous_bounds in text_boxes:
            assert not overlaps(bounds, previous_bounds), (content, previous_content)
        for graphic_bounds in graphic_boxes:
            assert not overlaps(bounds, graphic_bounds), (content, graphic_bounds)
        text_boxes.append((content, bounds))
        drawing.multiline_text(origin, content, font=font, fill=color, spacing=9)

    def reserve(bounds):
        assert 64 <= bounds[0] < bounds[2] <= 1016
        assert 40 <= bounds[1] < bounds[3] <= 1310
        for content, text_bounds in text_boxes:
            assert not overlaps(bounds, text_bounds), (content, bounds)
        graphic_boxes.append(bounds)

    def line(points, color=RULE, width=2):
        drawing.line(points, fill=color, width=width, joint="curve")

    def arrow(points, color=TEAL):
        line(points, color, 4)
        end, previous = points[-1], points[-2]
        angle = math.atan2(end[1] - previous[1], end[0] - previous[0])
        wings = [(end[0] - 13 * math.cos(angle + offset),
                  end[1] - 13 * math.sin(angle + offset))
                 for offset in (-0.5, 0.5)]
        drawing.polygon([end, *wings], fill=color)

    text("BIOPHYSICS + AI", 64, 48, 24, TEAL)
    text("MODELS / DATA / EVIDENCE", 670, 51, 19, MUTED)
    line([(64, 96), (1016, 96)], BURGUNDY, 3)
    text("Predict. Measure.", 64, 128, 76, BURGUNDY, bottom=215)
    text("Refine.", 64, 218, 76, BURGUNDY, bottom=295)
    text("Physical models + machine learning + experiments", 64, 317, 30)

    text("01  PHYSICAL MODEL", 64, 387, 23, BURGUNDY, right=350)
    text("02  LEARNING", 418, 387, 23, TEAL, right=690)
    text("03  EXPERIMENT", 766, 387, 23, BURGUNDY)
    reserve((64, 435, 350, 645))
    reserve((418, 435, 690, 645))
    reserve((766, 435, 1016, 645))
    reserve((360, 510, 408, 535))
    reserve((704, 510, 752, 535))

    chain = []
    for index in range(75):
        phase = index / 74 * math.pi * 4.7
        chain.append((91 + index * 3.05 + 13 * math.sin(phase * 1.8),
                      533 + 63 * math.sin(phase) + 22 * math.cos(phase * 0.5)))
    for index in range(0, 56, 9):
        line([chain[index], chain[index + 17]], "#C9B2BC", 2)
    line(chain, "#E9D8DF", 17)
    line(chain, BURGUNDY, 6)
    for index, center in enumerate(chain[::3]):
        radius = 6 + (index % 3)
        drawing.ellipse((center[0] - radius, center[1] - radius,
                        center[0] + radius, center[1] + radius),
                       fill=GOLD if index % 6 == 0 else BURGUNDY,
                       outline="#FFFFFF", width=1)

    layers = [[(440, 475), (440, 535), (440, 595)],
              [(535, 455), (535, 505), (535, 555), (535, 605)],
              [(650, 490), (650, 570)]]
    for first_layer, second_layer in zip(layers, layers[1:]):
        for first_node in first_layer:
            for second_node in second_layer:
                line([first_node, second_node], "#B8CECA", 2)
    for layer_index, layer in enumerate(layers):
        for center in layer:
            drawing.ellipse((center[0] - 11, center[1] - 11,
                             center[0] + 11, center[1] + 11),
                            fill=GOLD if layer_index == 2 else TEAL)

    line([(794, 453), (794, 615), (1000, 615)], INK, 3)
    curve = [(804 + step * 2, 594 - 115 / (1 + math.exp(-(step - 43) / 10)))
             for step in range(93)]
    line(curve, TEAL, 4)
    for center, error in [((823, 587), 13), ((860, 573), 17),
                          ((896, 535), 15), ((935, 494), 12), ((975, 486), 14)]:
        line([(center[0], center[1] - error), (center[0], center[1] + error)], BURGUNDY, 2)
        for endpoint in (center[1] - error, center[1] + error):
            line([(center[0] - 5, endpoint), (center[0] + 5, endpoint)], BURGUNDY, 2)
        drawing.ellipse((center[0] - 5, center[1] - 5,
                         center[0] + 5, center[1] + 5), fill=BURGUNDY)
    arrow([(363, 522), (404, 522)], GOLD)
    arrow([(707, 522), (748, 522)], GOLD)
    text("Geometry + interactions", 64, 662, 22, MUTED, right=350)
    text("Patterns + predictions", 418, 662, 22, MUTED, right=700)
    text("Measurements + error", 766, 662, 22, MUTED)
    reserve((180, 703, 910, 735))
    arrow([(905, 705), (905, 731), (194, 731), (194, 705)])
    text("TEST ASSUMPTIONS / UPDATE THE MODEL", 291, 748, 21, TEAL)
    text("Conceptual chain, network and plot; no measured data shown.", 64, 791, 20, MUTED)

    line([(64, 835), (1016, 835)], BURGUNDY, 2)
    text("01", 64, 860, 28, BURGUNDY)
    text("Prediction is not a measurement.", 137, 858, 31, BURGUNDY)
    text("AlphaFold predicts protein structure and estimates confidence. [1]\nA structure prediction alone does not establish dynamics or function.",
         137, 905, 24, bottom=975)
    line([(64, 990), (1016, 990)])
    text("02", 64, 1014, 28, TEAL)
    text("Make uncertainty part of the test.", 137, 1012, 31, TEAL)
    text("Compare predictions with independent measurements and their error.\nTest out-of-distribution: new proteins or conditions beyond training.",
         137, 1059, 24, bottom=1130)
    text("Validation practice: confidence is not proof; physical constraints are not a guarantee.",
         64, 1150, 21, MUTED)

    line([(64, 1194), (1016, 1194)], BURGUNDY, 3)
    text("SOURCE / PRIMARY RESEARCH", 64, 1214, 19, TEAL)
    text("[1] Jumper et al. Nature 596, 583-589 (2021). AlphaFold.", 64, 1244, 22)
    text("doi:10.1038/s41586-021-03819-2", 64, 1280, 22, BURGUNDY)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=97, subsampling=0, optimize=True)
    payload = buffer.getvalue()
    assert len(payload) < 8 * 1024 * 1024
    with Image.open(io.BytesIO(payload)) as decoded:
        assert decoded.format == "JPEG" and decoded.mode == "RGB"
        assert decoded.size == (WIDTH, HEIGHT)
        decoded.verify()
    with Image.open(io.BytesIO(payload)) as decoded:
        decoded.load()
    OUTPUT.parent.mkdir(exist_ok=True)
    with OUTPUT.open("xb") as handle:
        handle.write(payload)
    print("PASS: %d text boxes within bounds; no text/text or text/graphic overlap."
          % len(text_boxes))
    print("PASS: JPEG decoded, RGB, 1080x1350, %d bytes (<8 MiB)." % len(payload))
    print(OUTPUT)


if __name__ == "__main__":
    build_poster()