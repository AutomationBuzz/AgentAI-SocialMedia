"""Draw a labeled, schematic heart anatomy poster using Pillow."""

import io
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "assets" / "heart-anatomy-detailed-glossy.jpg"
CAPTION_OUTPUT = ROOT / "assets" / "heart-anatomy-detailed-glossy-caption.txt"
WIDTH, HEIGHT = 1080, 1350
PAPER = "#F7F6F0"
INK = "#202A2D"
MUTED = "#5C6969"
TEAL = "#08766C"
BURGUNDY = "#842343"
RED = "#B9363C"
BLUE = "#176B9A"
PALE_RED = "#F7E6E1"
PALE_BLUE = "#E5EFF5"
RULE = "#D8DFDA"
HASHTAGS = "#HeartAnatomy #AnatomyAndPhysiology #CardiovascularSystem #BloodFlow #ScienceEducation"
OPENSTAX = "https://openstax.org/books/anatomy-and-physiology-2e/pages/19-introduction"


def cubic(p0, p1, p2, p3, steps=24):
    points = []
    for index in range(steps + 1):
        t = index / steps
        inverse = 1 - t
        x = inverse**3 * p0[0] + 3 * inverse**2 * t * p1[0] + 3 * inverse * t**2 * p2[0] + t**3 * p3[0]
        y = inverse**3 * p0[1] + 3 * inverse**2 * t * p1[1] + 3 * inverse * t**2 * p2[1] + t**3 * p3[1]
        points.append((x, y))
    return points


def font(size):
    return ImageFont.load_default(size=size)


def draw_arrow(draw, points, color, width=8):
    draw.line(points, fill=color, width=width, joint="curve")
    end, previous = points[-1], points[-2]
    angle = math.atan2(end[1] - previous[1], end[0] - previous[0])
    arrow_length = 18
    wings = [
        (end[0] - arrow_length * math.cos(angle - 0.55), end[1] - arrow_length * math.sin(angle - 0.55)),
        (end[0] - arrow_length * math.cos(angle + 0.55), end[1] - arrow_length * math.sin(angle + 0.55)),
    ]
    draw.polygon([end, *wings], fill=color)


def add_label(draw, text, x, y, width, color=INK, size=18, plate=None):
    use_font = font(size)
    bounds = draw.multiline_textbbox((x, y), text, font=use_font, spacing=3)
    assert 38 <= bounds[0] < bounds[2] <= WIDTH - 38, (text, bounds)
    assert 35 <= bounds[1] < bounds[3] <= HEIGHT - 30, (text, bounds)
    if bounds[2] - bounds[0] > width:
        raise AssertionError(("label too wide", text, bounds, width))
    if plate:
        draw.rounded_rectangle((bounds[0]-7, bounds[1]-4, bounds[2]+7, bounds[3]+4),
                               radius=7, fill=plate)
    draw.multiline_text((x, y), text, font=use_font, fill=color, spacing=3,
                        stroke_width=2, stroke_fill=PAPER)


def glossy_chamber(image, box, radius, top_color, bottom_color, outline):
    left, top, right, bottom = box
    width, height = right-left, bottom-top
    gradient = Image.new("RGB", (width, height), top_color)
    gradient_draw = ImageDraw.Draw(gradient)
    start = tuple(int(top_color[index:index+2], 16) for index in (1, 3, 5))
    finish = tuple(int(bottom_color[index:index+2], 16) for index in (1, 3, 5))
    for row in range(height):
        ratio = row / max(1, height-1)
        shade = tuple(round(start[channel]*(1-ratio)+finish[channel]*ratio) for channel in range(3))
        gradient_draw.line((0, row, width, row), fill=shade)
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width-1, height-1), radius=radius, fill=255)
    image.paste(gradient, (left, top), mask)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius=radius, outline=outline, width=4)
    sheen = Image.new("RGBA", image.size, (0, 0, 0, 0))
    sheen_draw = ImageDraw.Draw(sheen)
    sheen_draw.arc((left+18, top+10, right-18, top+height*.58), 195, 340,
                   fill=(255, 255, 255, 190), width=6)
    sheen_draw.line((left+25, top+20, right-35, top+20), fill=(255, 255, 255, 90), width=3)
    return Image.alpha_composite(image.convert("RGBA"), sheen).convert("RGB")


def leader(draw, start, end, color=MUTED):
    draw.line((start, end), fill=color, width=2)
    radius = 4
    draw.ellipse((end[0]-radius, end[1]-radius, end[0]+radius, end[1]+radius), fill=color)


def build_poster():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite: " + str(OUTPUT))

    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, WIDTH, 14), fill=TEAL)
    add_label(draw, "ANATOMY / CIRCULATION", 54, 42, 500, TEAL, 18)
    add_label(draw, "A four-chamber\npump", 54, 82, 970, INK, 66)
    add_label(draw, "Follow the route of blood through the heart", 58, 222, 900, MUTED, 23)

    # Main cutaway: viewer's left is the heart's right side.
    # The outline is intentionally a simplified teaching silhouette.
    outline = []
    outline += cubic((540, 423), (476, 359), (359, 381), (336, 496))[:-1]
    outline += cubic((336, 496), (306, 650), (435, 796), (540, 891))[:-1]
    outline += cubic((540, 891), (645, 796), (774, 650), (744, 496))[:-1]
    outline += cubic((744, 496), (721, 381), (604, 359), (540, 423))
    draw.polygon(outline, fill="#FFFDF9", outline=BURGUNDY)
    draw.line(outline + [outline[0]], fill=BURGUNDY, width=6, joint="curve")

    # Chambers. The right-heart chambers are on the viewer's left.
    draw.rounded_rectangle((357, 472, 519, 609), radius=48, fill=PALE_BLUE, outline=BLUE, width=4)
    draw.rounded_rectangle((561, 472, 723, 609), radius=48, fill=PALE_RED, outline=RED, width=4)
    draw.rounded_rectangle((350, 635, 522, 822), radius=72, fill="#DCEAF2", outline=BLUE, width=4)
    draw.rounded_rectangle((558, 635, 730, 822), radius=70, fill="#F3DCD7", outline=RED, width=6)

    # Septum and valve markers.
    draw.line((540, 591, 540, 827), fill=BURGUNDY, width=9)
    for center, color in [((438, 621), BLUE), ((640, 621), RED),
                          ((488, 423), BLUE), ((595, 453), RED)]:
        x, y = center
        draw.ellipse((x-11, y-11, x+11, y+11), fill=PAPER, outline=color, width=4)

    # Large vessels, drawn behind their flow arrows.
    draw.line([(404, 467), (404, 384), (404, 322)], fill=BLUE, width=36)
    draw.line([(458, 817), (458, 893), (458, 944)], fill=BLUE, width=34)
    draw.line([(639, 477), (639, 425)], fill=RED, width=30)
    draw.line([(595, 640), (595, 564), (595, 453)], fill=RED, width=31)
    aorta = cubic((595, 452), (591, 330), (696, 310), (722, 366), 30)
    aorta += cubic((722, 366), (749, 411), (714, 454), (684, 470), 22)[1:]
    draw.line(aorta, fill=RED, width=39, joint="curve")
    draw.line([(684, 430), (684, 342)], fill=RED, width=25)
    draw.line([(710, 416), (754, 349)], fill=RED, width=22)
    draw.line([(684, 342), (754, 349)], fill=RED, width=20)

    # Pulmonary trunk and branches, in blue for oxygen-poor blood leaving the heart.
    pulmonary = cubic((428, 638), (429, 542), (462, 460), (488, 423), 28)
    draw.line(pulmonary, fill=BLUE, width=34, joint="curve")
    draw.line([(488, 423), (436, 360), (373, 348)], fill=BLUE, width=26, joint="curve")
    draw.line([(488, 423), (539, 355), (583, 340)], fill=BLUE, width=26, joint="curve")

    # Simplified anterior coronary arteries and branches on the heart surface.
    coronary_left = cubic((541, 628), (520, 672), (493, 706), (468, 756), 16)
    coronary_right = cubic((541, 628), (569, 675), (601, 713), (636, 773), 16)
    draw.line(coronary_left, fill="#8E3748", width=7, joint="curve")
    draw.line(coronary_right, fill="#8E3748", width=7, joint="curve")
    draw.line([(510, 681), (476, 685), (451, 711)], fill="#8E3748", width=5, joint="curve")
    draw.line([(589, 691), (623, 680), (656, 698)], fill="#8E3748", width=5, joint="curve")

    # Glossy chamber surfaces sit above vessel underlays for clear separation.
    image = glossy_chamber(image, (357, 472, 519, 609), 48, "#F9FFFF", "#C6E3F0", BLUE)
    image = glossy_chamber(image, (561, 472, 723, 609), 48, "#FFFBFA", "#F3C8C4", RED)
    image = glossy_chamber(image, (350, 635, 522, 822), 72, "#F4FBFF", "#AFCFE0", BLUE)
    image = glossy_chamber(image, (558, 635, 730, 822), 70, "#FFF8F5", "#E7B2AC", RED)
    draw = ImageDraw.Draw(image)

    # Flow arrows: blue = oxygen-poor; red = oxygen-rich.
    draw_arrow(draw, [(401, 395), (401, 465), (412, 529)], BLUE, 8)     # vena cava -> RA
    draw_arrow(draw, [(433, 585), (433, 637), (430, 704)], BLUE, 8)    # RA -> RV
    draw_arrow(draw, [(441, 718), (450, 635), (482, 512), (490, 431)], BLUE, 8)  # RV -> lungs
    draw_arrow(draw, [(380, 357), (437, 365)], BLUE, 7)
    draw_arrow(draw, [(566, 365), (526, 400), (503, 457)], RED, 7)     # lungs -> LA
    draw_arrow(draw, [(641, 440), (641, 502), (630, 555)], RED, 8)
    draw_arrow(draw, [(620, 594), (620, 643), (620, 726)], RED, 8)     # LA -> LV
    draw_arrow(draw, [(641, 735), (641, 645), (623, 540), (609, 459)], RED, 8)  # LV -> aorta
    draw_arrow(draw, [(696, 385), (713, 366), (729, 364)], RED, 7)

    # Labels and leader lines.
    add_label(draw, "SUPERIOR\nVENA CAVA", 43, 304, 190, BLUE, 15)
    leader(draw, (197, 337), (389, 354), BLUE)
    add_label(draw, "PULMONARY\nARTERIES", 48, 393, 190, BLUE, 15)
    leader(draw, (197, 425), (383, 365), BLUE)
    add_label(draw, "PULMONARY\nTRUNK", 47, 447, 190, BLUE, 15, plate="#F7FBFE")
    leader(draw, (194, 480), (472, 431), BLUE)
    add_label(draw, "RIGHT ATRIUM", 55, 508, 185, BLUE, 17)
    leader(draw, (200, 530), (357, 530), BLUE)
    add_label(draw, "TRICUSPID VALVE", 48, 617, 190, TEAL, 15, plate="#F0F8F5")
    leader(draw, (198, 644), (426, 622), TEAL)
    add_label(draw, "RIGHT VENTRICLE", 51, 734, 195, BLUE, 17)
    leader(draw, (205, 756), (351, 737), BLUE)
    add_label(draw, "INFERIOR\nVENA CAVA", 58, 895, 180, BLUE, 15)
    leader(draw, (197, 922), (456, 917), BLUE)
    add_label(draw, "CORONARY\nARTERIES", 49, 952, 190, BURGUNDY, 14, plate="#FFF8F6")
    leader(draw, (200, 978), (472, 711), BURGUNDY)

    add_label(draw, "AORTA", 827, 302, 190, RED, 18)
    leader(draw, (824, 327), (738, 360), RED)
    add_label(draw, "PULMONARY\nVEINS", 826, 398, 195, RED, 15)
    leader(draw, (824, 431), (644, 435), RED)
    add_label(draw, "PULMONARY VALVE", 817, 465, 205, BLUE, 14, plate="#F7FBFE")
    leader(draw, (818, 488), (503, 428), BLUE)
    add_label(draw, "LEFT ATRIUM", 831, 510, 190, RED, 17)
    leader(draw, (823, 532), (722, 532), RED)
    add_label(draw, "MITRAL VALVE", 833, 620, 180, TEAL, 15, plate="#F0F8F5")
    leader(draw, (825, 644), (653, 622), TEAL)
    add_label(draw, "LEFT VENTRICLE", 825, 734, 210, RED, 17)
    leader(draw, (820, 756), (729, 753), RED)
    add_label(draw, "AORTIC VALVE", 832, 816, 175, RED, 15, plate="#FFF7F5")
    leader(draw, (824, 840), (603, 460), RED)
    add_label(draw, "SEPTUM", 834, 865, 160, BURGUNDY, 16, plate="#FFF9F9")
    leader(draw, (824, 887), (544, 835), BURGUNDY)
    add_label(draw, "MYOCARDIUM\n(HEART MUSCLE)", 817, 914, 205, BURGUNDY, 13, plate="#FFF9F9")
    leader(draw, (816, 947), (711, 704), BURGUNDY)
    add_label(draw, "APEX / TIP", 833, 970, 160, INK, 14, plate="#FFFDF9")
    leader(draw, (822, 990), (550, 887), INK)

    # Chamber names inside the diagram.
    add_label(draw, "RIGHT\nATRIUM", 386, 515, 108, BLUE, 15, plate="#F5FCFF")
    add_label(draw, "LEFT\nATRIUM", 591, 515, 104, RED, 15, plate="#FFF7F5")
    add_label(draw, "RIGHT\nVENTRICLE", 378, 713, 116, BLUE, 15, plate="#F5FCFF")
    add_label(draw, "LEFT\nVENTRICLE", 585, 713, 118, RED, 15, plate="#FFF7F5")

    draw.rounded_rectangle((64, 1010, 1016, 1170), radius=14, fill="#FFFDF9", outline=RULE, width=2)
    add_label(draw, "BLOOD-FLOW ROUTE", 84, 1024, 260, TEAL, 16)
    add_label(draw, "Body -> vena cava -> right atrium -> tricuspid valve -> right ventricle", 84, 1052, 910, INK, 16)
    add_label(draw, "-> pulmonary valve -> pulmonary arteries -> lungs -> pulmonary veins", 84, 1080, 910, INK, 16)
    add_label(draw, "-> left atrium -> mitral valve -> left ventricle -> aortic valve -> aorta -> body", 84, 1108, 910, INK, 16)
    add_label(draw, "Blue = oxygen-poor / Red = oxygen-rich. Valves guide one-way flow; the septum divides sides.", 84, 1138, 910, MUTED, 13)

    draw.line((64, 1195, 1016, 1195), fill=TEAL, width=3)
    add_label(draw, "SCHEMATIC / SIMPLIFIED / NOT TO SCALE / NOT MEDICAL ADVICE", 64, 1207, 950, MUTED, 12)
    add_label(draw, "Source: OpenStax Anatomy & Physiology 2e, Ch. 19: Cardiovascular System", 64, 1232, 950, MUTED, 12)
    add_label(draw, "#HeartAnatomy  #AnatomyAndPhysiology  #CardiovascularSystem", 64, 1256, 950, TEAL, 12)
    add_label(draw, "#BloodFlow  #ScienceEducation", 64, 1278, 950, TEAL, 12)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=96, subsampling=0, optimize=True)
    payload = buffer.getvalue()
    with Image.open(io.BytesIO(payload)) as decoded:
        assert decoded.size == (WIDTH, HEIGHT) and decoded.mode == "RGB"
        decoded.verify()
    OUTPUT.parent.mkdir(exist_ok=True)
    with OUTPUT.open("xb") as handle:
        handle.write(payload)
    if CAPTION_OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite: " + str(CAPTION_OUTPUT))
    CAPTION_OUTPUT.write_text(
        "Explore the heart's four chambers, valves, great vessels, septum, myocardium, apex, and coronary arteries. "
        "This script-generated glossy diagram is simplified and not to scale. It is an educational illustration, not medical advice.\n\n"
        "Source: OpenStax Anatomy & Physiology 2e, Chapter 19: Cardiovascular System.\n"
        + OPENSTAX + "\n\n" + HASHTAGS + "\n",
        encoding="utf-8",
    )
    print("Created and validated:", OUTPUT.relative_to(ROOT))
    print("Resolution: %d x %d RGB JPEG; %d bytes" % (WIDTH, HEIGHT, len(payload)))


if __name__ == "__main__":
    build_poster()