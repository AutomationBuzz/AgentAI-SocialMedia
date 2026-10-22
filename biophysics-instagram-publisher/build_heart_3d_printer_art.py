"""Render an original glossy 3D-printer-and-heart concept illustration."""

import io
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "assets" / "heart-3d-printer-concept.jpg"
WIDTH, HEIGHT = 1080, 1350


def font(size):
    return ImageFont.load_default(size=size)


def gradient(size, first, second):
    image = Image.new("RGB", size, first)
    draw = ImageDraw.Draw(image)
    a = tuple(int(first[i:i+2], 16) for i in (1, 3, 5))
    b = tuple(int(second[i:i+2], 16) for i in (1, 3, 5))
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        color = tuple(round(a[c] * (1-t) + b[c] * t) for c in range(3))
        draw.line((0, y, size[0], y), fill=color)
    return image


def heart_points(cx, cy, sx, sy, count=720):
    points = []
    for index in range(count):
        t = 2 * math.pi * index / count
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
        points.append((cx + sx*x, cy - sy*y))
    return points


def bezier(p0, p1, p2, p3, count=32):
    result = []
    for i in range(count + 1):
        t = i / count
        u = 1 - t
        result.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                       u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return result


def arrow(draw, points, color, width=5):
    draw.line(points, fill=color, width=width, joint="curve")
    (x0, y0), (x1, y1) = points[-2], points[-1]
    angle = math.atan2(y1-y0, x1-x0)
    length = 16
    left = (x1-length*math.cos(angle-.55), y1-length*math.sin(angle-.55))
    right = (x1-length*math.cos(angle+.55), y1-length*math.sin(angle+.55))
    draw.polygon([(x1, y1), left, right], fill=color)


def label(draw, text, x, y, color, size=14):
    use_font = font(size)
    bounds = draw.multiline_textbbox((x, y), text, font=use_font, spacing=2)
    draw.rounded_rectangle((bounds[0]-7, bounds[1]-5, bounds[2]+7, bounds[3]+5),
                           radius=6, fill=(17, 34, 38, 220))
    draw.multiline_text((x, y), text, font=use_font, fill=color, spacing=2,
                        stroke_width=1, stroke_fill="#14272D")


def leader(draw, start, end, color, width=2):
    draw.line((start, end), fill=color, width=width)
    r = 4
    draw.ellipse((end[0]-r, end[1]-r, end[0]+r, end[1]+r), fill=color)


def main():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite: " + str(OUTPUT))

    base = gradient((WIDTH, HEIGHT), "#14272E", "#2B4142").convert("RGBA")
    # Soft pool of cool light behind the printer build volume.
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((270, 255, 835, 1080), fill=(60, 204, 188, 62))
    base = Image.alpha_composite(base, glow.filter(ImageFilter.GaussianBlur(105)))
    d = ImageDraw.Draw(base)

    # Studio floor perspective grid.
    for x in range(50, 1090, 55):
        d.line((x, 1095, 540+(x-540)*1.5, 1320), fill=(127, 165, 156, 35), width=1)
    for y in range(1110, 1320, 34):
        d.line((40, y, 1040, y), fill=(127, 165, 156, 30), width=1)

    d.text((65, 45), "FORM / FUNCTION", font=font(19), fill="#56D9CF")
    d.text((65, 82), "A heart, built\nlayer by layer", font=font(58), fill="#FFF5E9", spacing=2)
    d.text((70, 222), "An original 3D-printing concept illustration", font=font(18), fill="#C2D4CE")

    steel, steel_light = "#587174", "#B9CBC7"
    # Printer frame and rails.
    d.line((174, 340, 906, 340), fill=steel_light, width=19)
    d.line((203, 347, 203, 1060), fill=steel_light, width=19)
    d.line((877, 347, 877, 1060), fill=steel_light, width=19)
    d.line((170, 1057, 910, 1057), fill=steel_light, width=20)
    d.line((222, 371, 857, 371), fill=steel, width=6)
    d.line((213, 421, 293, 367), fill=steel, width=8)
    d.line((867, 421, 787, 367), fill=steel, width=8)
    d.line((205, 1015, 278, 1052), fill=steel, width=8)
    d.line((875, 1015, 802, 1052), fill=steel, width=8)
    for x, y in [(203, 340), (877, 340), (203, 1057), (877, 1057)]:
        d.ellipse((x-13, y-13, x+13, y+13), fill="#42D6CA", outline="#F4FFF5", width=2)

    # Build plate with beveled edges and a reflected highlight.
    d.rounded_rectangle((271, 1035, 810, 1072), radius=10, fill="#657D7D", outline="#E0EEE7", width=2)
    d.line((294, 1043, 789, 1043), fill="#E5F1EA", width=3)
    d.rounded_rectangle((314, 1071, 768, 1090), radius=7, fill="#3D5458")

    # Print-head carriage, nozzle, and filament strand.
    d.rounded_rectangle((421, 344, 660, 407), radius=13, fill="#6D8585", outline="#EAF6EF", width=3)
    d.rounded_rectangle((493, 389, 590, 470), radius=12, fill="#B5C6C0", outline="#F5FFF7", width=3)
    d.rounded_rectangle((516, 414, 567, 474), radius=8, fill="#51696A", outline="#4ED9CF", width=3)
    d.polygon([(520, 467), (563, 467), (551, 499), (533, 499)], fill="#FFC46E", outline="#FFF2D9")
    d.line((542, 497, 542, 615), fill="#FFCF80", width=5)
    d.ellipse((536, 605, 548, 617), fill="#FF7468")
    for x in (441, 640):
        d.ellipse((x-7, 360, x+7, 374), fill="#49D7CE", outline="white", width=2)

    # Heart silhouette, shaded like a glossy printed object.
    cx, cy, sx, sy = 543, 805, 14.2, 13.8
    silhouette = heart_points(cx, cy, sx, sy)
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    ImageDraw.Draw(mask).polygon(silhouette, fill=255)
    body = gradient((WIDTH, HEIGHT), "#FFB8A0", "#C74355").convert("RGBA")
    alpha = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    alpha.paste(body, (0, 0), mask)
    base = Image.alpha_composite(base, alpha)
    d = ImageDraw.Draw(base)
    d.line(silhouette+[silhouette[0]], fill="#FFE0CC", width=5, joint="curve")

    # Glossy print layers clipped to the heart surface.
    layers = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layers)
    for y in range(630, 1035, 7):
        phase = (y-630)/47
        left = 337+16*math.sin(phase)
        right = 748+16*math.sin(phase+.5)
        alpha_line = 118 if y % 28 == 0 else 55
        ld.arc((left, y-20, right, y+25), 190, 350, fill=(255, 244, 224, alpha_line), width=2)
    layers.putalpha(ImageChops.multiply(layers.getchannel("A"), mask))
    base = Image.alpha_composite(base, layers)

    # Specular highlight on the upper left curve.
    shine = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shine)
    sd.ellipse((378, 636, 535, 835), fill=(255, 252, 239, 78))
    shine.putalpha(ImageChops.multiply(shine.getchannel("A"), mask))
    base = Image.alpha_composite(base, shine.filter(ImageFilter.GaussianBlur(13)))
    d = ImageDraw.Draw(base)

    # Subtle anatomical grooves and coronary surface branching.
    d.arc((405, 637, 661, 876), 190, 285, fill="#FFE6CF", width=9)
    d.arc((444, 671, 701, 925), 245, 316, fill="#912B45", width=8)
    d.arc((383, 685, 578, 935), 225, 292, fill="#912B45", width=7)
    arterial = [(545, 690), (520, 738), (500, 792), (468, 843), (446, 897)]
    d.line(arterial, fill="#8D253B", width=9, joint="curve")
    d.line([(516, 751), (474, 748), (441, 773)], fill="#8D253B", width=6, joint="curve")
    d.line([(497, 797), (535, 818), (554, 862)], fill="#8D253B", width=6, joint="curve")
    d.line([(573, 724), (617, 761), (650, 812)], fill="#8D253B", width=8, joint="curve")
    d.line([(609, 763), (654, 750), (689, 765)], fill="#8D253B", width=5, joint="curve")

    # Base cast shadow gives the printed object depth above the plate.
    shadow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse((356, 1002, 736, 1058), fill=(5, 12, 14, 105))
    base = Image.alpha_composite(base, shadow.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(base)

    # Minimal, readable labels around the focal object.
    annotations = [
        ("PRINT HEAD", (454, 291), (545, 411), "#57DDD1"),
        ("LAYERED HEART", (74, 570), (373, 693), "#FF8A7B"),
        ("CORONARY BRANCHES", (70, 860), (477, 797), "#FFD080"),
        ("BUILD PLATE", (802, 1010), (780, 1053), "#65DED5"),
        ("PRINTER GANTRY", (738, 430), (858, 467), "#D4E1DC"),
    ]
    for text, pos, target, color in annotations:
        x, y = pos
        d.line((x+4, y+24, target[0], target[1]), fill=color, width=2)
        d.ellipse((target[0]-4, target[1]-4, target[0]+4, target[1]+4), fill=color)
        d.text(pos, text, font=font(13), fill=color, stroke_width=2, stroke_fill="#16292E")

    d.rounded_rectangle((67, 1173, 1013, 1261), radius=13, fill=(9, 23, 27, 210), outline=(109, 149, 143, 170), width=2)
    d.text((90, 1190), "CONCEPT / ANATOMICAL FORM MEETS ADDITIVE MANUFACTURING", font=font(15), fill="#FFF7EC")
    d.text((90, 1221), "Original digital art / no patient scan / not a print demonstration", font=font(13), fill="#C6D8D1")
    d.text((68, 1293), "A HEART, BUILT LAYER BY LAYER", font=font(14), fill="#52D9CF")

    flattened = Image.new("RGB", base.size, "#14272E")
    flattened.paste(base, mask=base.getchannel("A"))
    buffer = io.BytesIO()
    flattened.save(buffer, format="JPEG", quality=96, subsampling=0, optimize=True)
    payload = buffer.getvalue()
    with Image.open(io.BytesIO(payload)) as decoded:
        assert decoded.size == (WIDTH, HEIGHT) and decoded.mode == "RGB"
        decoded.verify()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("xb") as handle:
        handle.write(payload)
    print("Created and validated:", OUTPUT.relative_to(ROOT))
    print("Resolution: %d x %d RGB JPEG; %d bytes" % (WIDTH, HEIGHT, len(payload)))


if __name__ == "__main__":
    main()
