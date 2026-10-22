from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def main():
    size = 1600
    image = Image.new("RGB", (size, size))
    pixels = image.load()
    for vertical in range(size):
        for horizontal in range(size):
            radius = min(1, ((horizontal - 800) ** 2 + (vertical - 700) ** 2) ** 0.5 / 1100)
            pixels[horizontal, vertical] = tuple(int(channel * (1 - radius) + edge * radius) for channel, edge in zip((24, 87, 88), (5, 15, 25)))
    draw = ImageDraw.Draw(image)
    draw.ellipse((165, 165, 1435, 1435), outline=(54, 123, 125), width=7)
    draw.arc((200, 200, 1400, 1400), 205, 315, fill=(103, 240, 216), width=16)
    draw.arc((200, 200, 1400, 1400), 25, 65, fill=(255, 125, 109), width=16)
    draw.rounded_rectangle((420, 1120, 1180, 1510), radius=190, fill=(80, 115, 131))
    draw.rounded_rectangle((480, 1150, 1120, 1490), radius=160, fill=(185, 209, 214))
    draw.rectangle((685, 1040, 915, 1220), fill=(67, 97, 113))
    draw.rounded_rectangle((710, 1060, 890, 1200), radius=40, fill=(139, 172, 183))
    draw.line((800, 420, 800, 300), fill=(186, 216, 220), width=28)
    draw.ellipse((755, 245, 845, 335), fill=(255, 123, 106))
    draw.rounded_rectangle((308, 635, 440, 900), radius=55, fill=(79, 118, 133))
    draw.rounded_rectangle((1160, 635, 1292, 900), radius=55, fill=(79, 118, 133))
    draw.rounded_rectangle((360, 405, 1240, 1115), radius=225, fill=(59, 91, 109))
    draw.rounded_rectangle((385, 420, 1215, 1080), radius=210, fill=(208, 228, 228))
    draw.rounded_rectangle((415, 445, 1185, 1025), radius=190, fill=(232, 243, 239))
    draw.rounded_rectangle((445, 560, 1155, 895), radius=135, fill=(18, 38, 53))
    draw.rounded_rectangle((465, 580, 1135, 875), radius=120, fill=(7, 22, 35))
    glow = Image.new("RGBA", image.size)
    light = ImageDraw.Draw(glow)
    for center in (620, 980):
        light.rounded_rectangle((center - 64, 658, center + 64, 790), radius=52, fill=(64, 255, 229, 220))
    image = Image.alpha_composite(image.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(32)))
    draw = ImageDraw.Draw(image)
    for center in (620, 980):
        draw.rounded_rectangle((center - 51, 668, center + 51, 778), radius=42, fill=(111, 255, 230))
        draw.ellipse((center - 28, 683, center - 6, 705), fill=(236, 255, 250))
    draw.arc((710, 737, 890, 835), 15, 165, fill=(107, 235, 217), width=12)
    for center in (485, 1115):
        draw.ellipse((center - 18, 944, center + 18, 980), fill=(90, 131, 145))
    draw.ellipse((755, 1275, 845, 1365), fill=(18, 77, 87))
    draw.ellipse((775, 1295, 825, 1345), fill=(110, 240, 215))
    output = Path(__file__).parent / "assets" / "wowscifi-lab-robot-avatar.png"
    image.convert("RGB").resize((1080, 1080), Image.Resampling.LANCZOS).save(output)
    with Image.open(output) as result:
        assert result.size == (1080, 1080)
        assert result.mode == "RGB"
    print(output)


if __name__ == "__main__":
    main()