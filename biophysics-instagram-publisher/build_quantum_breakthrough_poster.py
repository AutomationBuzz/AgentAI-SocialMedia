"""Render a source-grounded Instagram graphic for the October 2026 quantum result."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "assets" / "quantum-error-correction-oct-2026.jpg"
CAPTION = ROOT / "assets" / "quantum-error-correction-oct-2026-caption.txt"
W, H = 1080, 1350
BG = (16, 22, 19)
PAPER = (241, 239, 229)
LIME = (207, 239, 117)
CORAL = (255, 126, 105)
BLUE = (139, 196, 214)
MUTED = (164, 174, 162)


def font(size, bold=False, serif=False):
    candidates = []
    if serif:
        candidates.extend([
            "/System/Library/Fonts/Supplemental/Georgia Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Georgia.ttf",
            "/Library/Fonts/Georgia Bold.ttf" if bold else "/Library/Fonts/Georgia.ttf",
        ])
    else:
        candidates.extend([
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        ])
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def text(draw, xy, value, size, fill, bold=False, serif=False, anchor=None):
    draw.text(xy, value, font=font(size, bold=bold, serif=serif), fill=fill, anchor=anchor)


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def make_art():
    image = Image.new("RGB", (W, H), BG)
    pixels = image.load()
    for y in range(H):
        blend = y / H
        for x in range(W):
            glow = max(0.0, 1.0 - (((x - 830) / 590) ** 2 + ((y - 290) / 570) ** 2) ** 0.5)
            pixels[x, y] = tuple(
                min(255, int(BG[c] * (1 - blend * .13) + (18, 32, 26)[c] * blend + (0, 10, 8)[c] * glow))
                for c in range(3)
            )

    draw = ImageDraw.Draw(image)
    text(draw, (72, 52), "QUANTUM / FIELD NOTE 08", 22, LIME, bold=True)
    text(draw, (1008, 56), "19 OCT 2026", 18, MUTED, bold=True, anchor="ra")
    draw.line((72, 99, 1008, 99), fill=(65, 77, 66), width=2)

    text(draw, (72, 130), "ERROR CORRECTION MILESTONE", 18, BLUE, bold=True)
    text(draw, (66, 164), "FIVE IN", 111, PAPER, serif=True)
    text(draw, (66, 269), "A MILLION.", 111, LIME, serif=True)
    text(draw, (75, 397), "Quantinuum reports 99.9995% logical fidelity", 27, PAPER)
    text(draw, (75, 435), "on its Helios trapped-ion system using a color code.", 24, PAPER)

    # Glowing logical-state motif, with orbital paths and error sparks.
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((594, 482, 1006, 894), fill=(207, 239, 117, 28))
    image = Image.alpha_composite(image.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(52))).convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.ellipse((666, 515, 946, 795), outline=(105, 135, 72), width=2)
    draw.ellipse((696, 545, 916, 765), outline=(74, 111, 116), width=2)
    draw.ellipse((630, 570, 980, 740), outline=(99, 78, 73), width=2)
    draw.arc((682, 531, 930, 779), 198, 328, fill=BLUE, width=3)
    draw.arc((652, 552, 956, 758), 15, 156, fill=CORAL, width=3)
    draw.ellipse((722, 571, 890, 739), fill=(117, 146, 66), outline=LIME, width=3)
    draw.ellipse((741, 587, 861, 707), fill=(207, 239, 117))
    text(draw, (801, 648), "|L>", 48, BG, serif=True, anchor="mm")
    for x, y, r, color in [(682, 540, 8, CORAL), (941, 630, 6, BLUE), (703, 769, 5, CORAL), (908, 526, 4, PAPER)]:
        draw.ellipse((x-r, y-r, x+r, y+r), fill=color)
    text(draw, (801, 826), "LOGICAL STATE · CONCEPTUAL ART", 15, MUTED, bold=True, anchor="mm")

    # The main reported metrics.
    draw.line((72, 916, 1008, 916), fill=(65, 77, 66), width=2)
    text(draw, (76, 945), "REPORTED LOGICAL FIDELITY", 17, MUTED, bold=True)
    text(draw, (73, 978), "99.9995%", 64, LIME, serif=True)
    rounded(draw, (674, 965, 1004, 1077), 8, (31, 40, 33), outline=(79, 95, 76), width=2)
    text(draw, (700, 983), "10× LOWER ERROR RATE", 17, BLUE, bold=True)
    text(draw, (700, 1016), "than its September result", 20, PAPER)

    # Scope note and careful qualification.
    rounded(draw, (72, 1105, 1008, 1216), 8, (30, 35, 30), outline=(79, 89, 74), width=2)
    draw.rectangle((72, 1105, 80, 1216), fill=CORAL)
    text(draw, (101, 1122), "WHAT THIS DOES — AND DOESN'T — SHOW", 16, CORAL, bold=True)
    text(draw, (101, 1151), "An experimental milestone, not a finished fault-tolerant computer.", 20, PAPER)
    text(draw, (101, 1180), "Scaling and commercial performance remain to be demonstrated.", 19, MUTED)

    draw.line((72, 1243, 1008, 1243), fill=(65, 77, 66), width=2)
    text(draw, (74, 1261), "SOURCE  Quantinuum · company announcement · 19 Oct 2026", 16, PAPER, bold=True)
    text(draw, (74, 1288), "quantinuum.com/press-releases · See caption for direct source + context", 15, MUTED)

    return image


def main():
    image = make_art()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, format="JPEG", quality=94, optimize=True)
    with Image.open(OUTPUT) as check:
        if check.size != (W, H) or check.mode != "RGB":
            raise RuntimeError("Rendered poster has unexpected image dimensions or mode")
        check.verify()

    caption = (
        "Five errors per million operations, in a reported test. Quantinuum says its Helios system "
        "reached 99.9995% logical fidelity using a color code. A promising experimental milestone "
        "for quantum error correction, not proof that large-scale fault-tolerant computing is already here. "
        "Scaling and commercial performance remain to be demonstrated.\n\n"
        "Source: Quantinuum, October 19, 2026: "
        "https://www.quantinuum.com/press-releases/quantinuum-breaks-error-correction-world-record-by-10x-validating-its-leading-path-to-fault-tolerant-quantum-computing-by-2029\n\n"
        "#QuantumComputing #QuantumErrorCorrection #QuantumPhysics #ScienceNews #Physics"
    )
    CAPTION.write_text(caption + "\n", encoding="utf-8")
    print("Created: {} ({}x{}, {} bytes)".format(OUTPUT, W, H, OUTPUT.stat().st_size))
    print("Caption/source/hashtags: {}".format(CAPTION))


if __name__ == "__main__":
    main()
