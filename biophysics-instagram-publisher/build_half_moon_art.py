"""Create an original, monochrome half-moon illustration with Pillow."""

import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "assets" / "half-moon-lunar-texture.jpg"
WIDTH, HEIGHT = 1080, 1350
SCALE = 2


def build_image():
    width, height = WIDTH * SCALE, HEIGHT * SCALE
    center_x, center_y = 540 * SCALE, 610 * SCALE
    radius = 365 * SCALE
    diameter = radius * 2
    left, top = center_x - radius, center_y - radius
    rng = random.Random(42)

    image = Image.new("RGB", (width, height), "#020305")
    sky = ImageDraw.Draw(image)
    for x, y, size, shade in [
        (143, 219, 2, 72), (862, 165, 2, 86), (913, 420, 1, 68),
        (194, 831, 1, 65), (855, 1029, 2, 67), (302, 1101, 1, 72),
        (733, 187, 1, 61), (114, 536, 1, 72), (955, 731, 1, 69),
    ]:
        px, py = x * SCALE, y * SCALE
        sky.ellipse((px-size, py-size, px+size, py+size), fill=(shade, shade, shade))

    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((left-40*SCALE, top-40*SCALE, left+diameter+40*SCALE,
                       top+diameter+40*SCALE), fill=(170, 180, 195, 22))
    glow = glow.filter(ImageFilter.GaussianBlur(42 * SCALE))
    image = Image.alpha_composite(image.convert("RGBA"), glow)

    gradient = Image.new("L", (diameter, diameter))
    gradient_draw = ImageDraw.Draw(gradient)
    for x in range(diameter):
        value = int(92 + 145 * x / max(1, diameter - 1))
        gradient_draw.line((x, 0, x, diameter), fill=value)
    fine_noise = Image.effect_noise((diameter, diameter), 105).filter(
        ImageFilter.GaussianBlur(0.7*SCALE))
    broad_noise = Image.effect_noise((diameter//9, diameter//9), 115).resize(
        (diameter, diameter), Image.Resampling.BICUBIC).filter(
            ImageFilter.GaussianBlur(3*SCALE))
    surface_luma = ImageChops.blend(gradient, broad_noise, 0.24)
    surface_luma = ImageChops.blend(surface_luma, fine_noise, 0.19)
    surface = Image.merge("RGB", (surface_luma, surface_luma, surface_luma))
    surface_draw = ImageDraw.Draw(surface, "RGBA")

    # Broad, low-contrast maria give the illuminated face tonal structure.
    for box, shade in [
        ((radius*1.10, radius*.28, radius*1.58, radius*.63), 96),
        ((radius*1.33, radius*.65, radius*1.86, radius*1.04), 82),
        ((radius*1.05, radius*1.18, radius*1.62, radius*1.57), 104),
        ((radius*1.47, radius*1.47, radius*1.88, radius*1.80), 91),
    ]:
        scaled_box = tuple(int(value) for value in box)
        surface_draw.ellipse(scaled_box, fill=(shade, shade, shade, 20))

    # Crater rims catch light from the right while their left walls stay dark.
    craters = [
        (radius*1.31, radius*.35, radius*.13),
        (radius*1.64, radius*.49, radius*.09),
        (radius*1.17, radius*.68, radius*.075),
        (radius*1.48, radius*.77, radius*.16),
        (radius*1.80, radius*.91, radius*.085),
        (radius*1.22, radius*1.02, radius*.12),
        (radius*1.69, radius*1.24, radius*.14),
        (radius*1.36, radius*1.48, radius*.075),
        (radius*1.78, radius*1.62, radius*.11),
        (radius*1.19, radius*1.72, radius*.10),
    ]
    for _ in range(34):
        crater_x = rng.uniform(radius*1.04, radius*1.88)
        crater_y = rng.uniform(radius*.10, radius*1.90)
        crater_r = rng.uniform(radius*.018, radius*.055)
        if (crater_x-radius)**2 + (crater_y-radius)**2 < (radius-crater_r)**2:
            craters.append((crater_x, crater_y, crater_r))

    for cx, cy, crater_radius in craters:
        x0, y0 = cx-crater_radius, cy-crater_radius
        x1, y1 = cx+crater_radius, cy+crater_radius
        surface_draw.ellipse((x0-5*SCALE, y0+7*SCALE, x1+2*SCALE, y1+8*SCALE),
                     fill=(28, 30, 32, 110))
        surface_draw.ellipse((x0, y0, x1, y1), fill=(48, 50, 53, 80))
        surface_draw.arc((x0, y0, x1, y1), 282, 78,
                 fill=(242, 243, 244, 145), width=max(2, int(SCALE*3)))
        surface_draw.arc((x0, y0, x1, y1), 100, 258,
                 fill=(24, 26, 28, 155), width=max(2, int(SCALE*4)))
        if crater_radius > 20*SCALE:
            surface_draw.ellipse((cx-crater_radius*.11, cy-crater_radius*.11,
                                  cx+crater_radius*.11, cy+crater_radius*.11),
                                 fill=(185, 187, 189, 72))

    # Clip to a subtly irregular terminator and the Moon's circular limb.
    circle_mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(circle_mask).ellipse((1, 1, diameter-2, diameter-2), fill=255)
    terminator_mask = Image.new("L", (diameter, diameter), 0)
    terminator_points = []
    for y in range(-20, diameter+21, 8):
        bend = 8*SCALE * math.sin((y / diameter) * math.pi * 2)
        terminator_points.append((int(radius + bend), y))
    terminator_points += [(diameter, diameter+20), (diameter, -20)]
    ImageDraw.Draw(terminator_mask).polygon(terminator_points, fill=255)
    light_mask = ImageChops.multiply(circle_mask, terminator_mask)
    image.paste(surface, (left, top), light_mask)

    # A fine bright edge along the lit limb separates it from the black sky.
    edge = Image.new("RGBA", image.size, (0, 0, 0, 0))
    edge_draw = ImageDraw.Draw(edge)
    arc_box = (left+1, top+1, left+diameter-1, top+diameter-1)
    edge_draw.arc(arc_box, 270, 90, fill=(235, 238, 242, 88), width=2*SCALE)
    image = Image.alpha_composite(image, edge)
    return image.convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def main():
    image = build_image()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("xb") as output_file:
        image.save(output_file, format="JPEG", quality=95, optimize=True)
    with Image.open(OUTPUT) as saved:
        saved.verify()
    print("Created and validated: {}".format(OUTPUT.relative_to(ROOT)))
    print("Resolution: {} x {} RGB JPEG; {} bytes".format(
        WIDTH, HEIGHT, OUTPUT.stat().st_size))


if __name__ == "__main__":
    main()