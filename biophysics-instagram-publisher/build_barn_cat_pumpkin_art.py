"""Create an original painterly farm-cat-and-pumpkins illustration with Pillow."""

import io
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "assets" / "barn-cats-pumpkins-original.jpg"
WIDTH, HEIGHT = 1080, 1350


def font(size):
    return ImageFont.load_default(size=size)


def rgb(value):
    return tuple(int(value[index:index + 2], 16) for index in (1, 3, 5))


def gradient(size, top, bottom):
    image = Image.new("RGB", size, top)
    draw = ImageDraw.Draw(image)
    a, b = rgb(top), rgb(bottom)
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        color = tuple(round(a[k] * (1-t) + b[k] * t) for k in range(3))
        draw.line((0, y, size[0], y), fill=color)
    return image


def cubic(p0, p1, p2, p3, count=36):
    points = []
    for index in range(count + 1):
        t = index / count
        u = 1 - t
        points.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                       u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return points


def ellipse_gradient(image, box, top, bottom, outline=None, width=1):
    left, upper, right, lower = map(int, box)
    w, h = max(1, right-left), max(1, lower-upper)
    fill = gradient((w, h), top, bottom)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, w-1, h-1), fill=255)
    image.paste(fill, (left, upper), mask)
    if outline:
        ImageDraw.Draw(image).ellipse(box, outline=outline, width=width)


def draw_pumpkin(draw, cx, cy, rx, ry, colors, stem=True):
    # Side lobes first, then the center lobe to create a ribbed, rounded pumpkin.
    dark, mid, light = colors
    for offset, factor in [(-.58, .71), (.58, .71), (-.30, .88), (.30, .88)]:
        x = cx + offset * rx
        ellipse_gradient(draw._image, (x-rx*factor*.55, cy-ry*.86, x+rx*factor*.55, cy+ry*.84), dark, mid, outline="#684323", width=2)
    ellipse_gradient(draw._image, (cx-rx*.44, cy-ry, cx+rx*.44, cy+ry*.89), light, mid, outline="#704526", width=2)
    # Rib highlights follow the curved shell.
    for side in (-1, 1):
        x = cx + side * rx * .29
        draw.arc((x-rx*.18, cy-ry*.79, x+rx*.21, cy+ry*.72),
                 80 if side < 0 else 100, 275 if side < 0 else 260, fill="#FFD58A", width=3)
    draw.arc((cx-rx*.85, cy-ry*.35, cx+rx*.85, cy+ry*.48), 15, 165, fill="#F3B965", width=2)
    if stem:
        draw.polygon([(cx-7, cy-ry+2), (cx-3, cy-ry-17), (cx+6, cy-ry-23),
                      (cx+10, cy-ry-9), (cx+5, cy-ry+3)], fill="#50633A", outline="#35452D")


def draw_barrel(draw):
    # Barrel body with bowed sides, staves, and two dark iron hoops.
    body = [(365, 312), (714, 312), (691, 617), (389, 617)]
    draw.polygon(body, fill="#8C542E", outline="#3E281B")
    for index in range(9):
        x = 382 + index * 36
        draw.line(cubic((x, 325), (x-10, 412), (x+10, 523), (x+2, 608), 20),
                  fill="#583A27", width=3)
    draw.rounded_rectangle((355, 354, 722, 394), radius=12, fill="#42352E", outline="#241E1A", width=3)
    draw.rounded_rectangle((366, 529, 707, 569), radius=11, fill="#3C302A", outline="#241E1A", width=3)
    draw.line((365, 361, 714, 361), fill="#B69770", width=4)
    draw.line((375, 536, 699, 536), fill="#9D8265", width=3)
    draw.ellipse((365, 289, 714, 341), fill="#9C6337", outline="#38271D", width=4)
    draw.ellipse((379, 298, 700, 331), fill="#6F482E", outline="#BD8A56", width=3)


def draw_wagon_wheel(draw):
    cx, cy, radius = 99, 785, 264
    draw.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline="#2E2924", width=22)
    draw.ellipse((cx-radius+19, cy-radius+19, cx+radius-19, cy+radius-19), outline="#916942", width=7)
    for index in range(14):
        angle = 2 * math.pi * index / 14
        end = (cx + math.cos(angle)*(radius-22), cy + math.sin(angle)*(radius-22))
        draw.line((cx, cy, end[0], end[1]), fill="#795839", width=10)
        draw.line((cx+2, cy+2, end[0], end[1]), fill="#B58A5C", width=3)
    draw.ellipse((cx-33, cy-33, cx+33, cy+33), fill="#62452F", outline="#C09A69", width=6)
    draw.ellipse((cx-12, cy-12, cx+12, cy+12), fill="#332820")


def draw_cat(image):
    draw = ImageDraw.Draw(image)
    # Ground shadow and seated body.
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse((363, 1122, 790, 1197), fill=(20, 15, 12, 130))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
    draw = ImageDraw.Draw(image)
    body = [(439, 842), (476, 779), (533, 756), (606, 782), (654, 869),
            (674, 1067), (624, 1151), (465, 1151), (420, 1095)]
    draw.polygon(body, fill="#17191A", outline="#090B0C")
    # Chest bib and front paws.
    chest = cubic((494, 802), (524, 819), (540, 836), (559, 876), 16)
    chest += cubic((559, 876), (581, 839), (597, 824), (616, 811), 14)[1:]
    chest += [(621, 1028), (584, 1071), (510, 1073), (480, 1036)]
    draw.polygon(chest, fill="#F1EEE7")
    draw.rounded_rectangle((452, 1086, 537, 1166), radius=28, fill="#F4F0E9", outline="#BEB9AE", width=2)
    draw.rounded_rectangle((573, 1087, 658, 1165), radius=28, fill="#F4F0E9", outline="#BEB9AE", width=2)
    draw.line((465, 1145, 523, 1145), fill="#C5BEB3", width=2)
    draw.line((586, 1145, 644, 1145), fill="#C5BEB3", width=2)
    # Tail curls around the cat's right side.
    tail = cubic((640, 1050), (755, 1117), (767, 1018), (708, 1003), 28)
    tail += cubic((708, 1003), (664, 993), (681, 1062), (726, 1053), 20)[1:]
    draw.line(tail, fill="#141617", width=32, joint="curve")

    # Head, triangular ears, and white facial mask.
    draw.polygon([(446, 774), (438, 696), (493, 733), (588, 728), (643, 686), (634, 784)],
                 fill="#111415", outline="#050607")
    draw.ellipse((446, 710, 639, 858), fill="#17191A", outline="#080A0B", width=3)
    draw.polygon([(475, 747), (520, 763), (540, 817), (513, 844), (480, 817)], fill="#F1EEE7")
    draw.polygon([(548, 817), (569, 763), (613, 747), (611, 817), (579, 845)], fill="#F1EEE7")
    draw.ellipse((498, 780, 511, 796), fill="#B8C878")
    draw.ellipse((574, 780, 587, 796), fill="#B8C878")
    draw.ellipse((502, 783, 507, 794), fill="#111415")
    draw.ellipse((578, 783, 583, 794), fill="#111415")
    draw.polygon([(531, 817), (553, 817), (542, 829)], fill="#D8878C")
    draw.line((542, 828, 542, 840), fill="#6C514D", width=2)
    draw.arc((522, 831, 544, 850), 5, 95, fill="#6C514D", width=2)
    draw.arc((542, 831, 565, 850), 85, 175, fill="#6C514D", width=2)
    for y in (818, 830, 842):
        draw.line((520, y, 453, y-7), fill="#F6F2EA", width=2)
        draw.line((563, y, 630, y-7), fill="#F6F2EA", width=2)
    # Ear interiors and forehead blaze.
    draw.polygon([(455, 718), (449, 705), (482, 730)], fill="#B77875")
    draw.polygon([(610, 727), (635, 698), (629, 739)], fill="#B77875")
    draw.polygon([(535, 726), (547, 730), (548, 779), (540, 795), (533, 779)], fill="#EEEAE2")
    # Soft gloss highlights.
    draw.arc((457, 720, 623, 846), 195, 315, fill="#777A77", width=3)
    return image


def draw_white_cat(image):
    draw = ImageDraw.Draw(image)
    # A smaller companion sits to the right of the tuxedo cat in the foreground.
    draw.ellipse((654, 1098, 867, 1160), fill=(18, 13, 10, 135))
    # Curled tail behind the body.
    tail = cubic((767, 1030), (860, 1082), (871, 1004), (820, 996), 24)
    tail += cubic((820, 996), (778, 991), (790, 1050), (834, 1041), 18)[1:]
    draw.line(tail, fill="#F3F0E9", width=28, joint="curve")
    draw.line(tail, fill="#C7C2B9", width=3, joint="curve")
    # Seated body, chest bib, and paws.
    draw.ellipse((680, 905, 811, 1149), fill="#F4F1EA", outline="#C8C3B9", width=3)
    draw.polygon([(710, 922), (752, 939), (771, 1003), (746, 1036),
                  (712, 1011), (696, 958)], fill="#FFFFFF")
    draw.rounded_rectangle((681, 1092, 746, 1164), radius=22, fill="#F8F6F0", outline="#BEB9AF", width=2)
    draw.rounded_rectangle((754, 1092, 819, 1164), radius=22, fill="#F8F6F0", outline="#BEB9AF", width=2)
    # Ears and head.
    draw.polygon([(683, 867), (674, 789), (730, 824), (785, 817), (838, 779), (830, 873)],
                 fill="#F5F2EB", outline="#BEB9AF")
    draw.ellipse((680, 814, 834, 935), fill="#F7F4ED", outline="#BEB9AF", width=3)
    draw.polygon([(691, 817), (682, 799), (713, 823)], fill="#D99A9B")
    draw.polygon([(805, 821), (832, 791), (825, 833)], fill="#D99A9B")
    # Soft gray forehead patch, eyes, muzzle and whiskers make the white face readable.
    draw.polygon([(747, 820), (758, 822), (759, 860), (752, 873), (745, 858)], fill="#D8D3C9")
    draw.ellipse((711, 854, 722, 869), fill="#9DAE70")
    draw.ellipse((785, 854, 796, 869), fill="#9DAE70")
    draw.ellipse((714, 857, 718, 867), fill="#202021")
    draw.ellipse((788, 857, 792, 867), fill="#202021")
    draw.polygon([(746, 886), (766, 886), (756, 896)], fill="#D8898D")
    draw.line((756, 895, 756, 905), fill="#77706A", width=2)
    draw.arc((739, 899, 757, 913), 0, 100, fill="#77706A", width=2)
    draw.arc((756, 899, 775, 913), 80, 180, fill="#77706A", width=2)
    for y in (887, 898, 909):
        draw.line((738, y, 690, y-5), fill="#9C968E", width=2)
        draw.line((775, y, 823, y-5), fill="#9C968E", width=2)
    draw.arc((691, 824, 822, 923), 195, 315, fill="#FFFFFF", width=3)
    return image


def main():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite: " + str(OUTPUT))
    image = gradient((WIDTH, HEIGHT), "#281C18", "#4B3021").convert("RGBA")
    d = ImageDraw.Draw(image)

    # Warm light spilling through a barn opening, with dark timber walls.
    d.rectangle((0, 0, WIDTH, 1180), fill="#30231D")
    d.rectangle((134, 114, 944, 1090), fill="#6C472D")
    d.rectangle((183, 153, 899, 1058), fill="#211B18")
    d.rectangle((211, 179, 871, 1016), fill="#4C3325")
    for x in [154, 192, 225, 852, 891, 928]:
        d.rectangle((x, 104, x+20, 1093), fill="#714D34")
        d.line((x+5, 126, x+5, 1083), fill="#9A704B", width=2)
    # Timber grain and old crossbeam.
    for index in range(16):
        y = 188 + index*53
        d.line((227, y, 859, y+((index%3)-1)*4), fill="#5C3D2A", width=2)
    d.rectangle((136, 136, 945, 188), fill="#39271D", outline="#986B43", width=3)
    d.line((147, 146, 933, 146), fill="#A17850", width=4)

    # Wooden barrel behind the cat with distinct curved staves and iron hoops.
    draw_barrel(d)
    # Large wagon wheel, cropped by the left frame edge.
    draw_wagon_wheel(d)

    # Floor boards and threshold.
    d.rectangle((0, 1084, WIDTH, 1190), fill="#533826")
    for y in [1101, 1135, 1171]:
        d.line((0, y, WIDTH, y+4), fill="#9B7048", width=3)
    d.line((0, 1084, WIDTH, 1084), fill="#C2945D", width=8)
    for x in [95, 295, 780, 980]:
        d.ellipse((x, 1115, x+5, 1120), fill="#D1AA73")

    # Pumpkins arranged around the entrance, behind the cat.
    draw_pumpkin(d, 374, 1036, 119, 100, ("#775B20", "#C7A342", "#E5C76C"))
    draw_pumpkin(d, 517, 1045, 112, 91, ("#946027", "#E48C2C", "#F8B44B"))
    draw_pumpkin(d, 740, 1039, 116, 104, ("#9D4F19", "#E87821", "#FFA53B"))
    draw_pumpkin(d, 316, 1005, 71, 68, ("#77733E", "#B7AE61", "#D7D087"))

    # Pumpkin on top of the barrel.
    draw_pumpkin(d, 539, 341, 122, 93, ("#9A4B1F", "#D6752C", "#F1A74E"))

    # The white companion is placed first so the tuxedo cat remains the focal subject.
    image = draw_white_cat(image)
    # Cat silhouette sits in the foreground as the focal subject.
    image = draw_cat(image)
    d = ImageDraw.Draw(image)

    # Subtle edge lighting around the entrance and foreground produce.
    d.line((210, 194, 210, 1049), fill="#BB8B5A", width=4)
    d.line((868, 194, 868, 1049), fill="#8B6140", width=3)
    d.ellipse((419, 1113, 704, 1168), fill="#201A17")
    d.ellipse((434, 1119, 687, 1156), fill="#2A211B")
    # Re-draw bright paws over the grounding shadow.
    d.rounded_rectangle((452, 1086, 537, 1166), radius=28, fill="#F4F0E9", outline="#BEB9AE", width=2)
    d.rounded_rectangle((573, 1087, 658, 1165), radius=28, fill="#F4F0E9", outline="#BEB9AE", width=2)

    # Light photographic grain and slight vignette for a finished illustration feel.
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ov = ImageDraw.Draw(overlay)
    ov.rectangle((0, 0, WIDTH, HEIGHT), outline=(16, 11, 8, 95), width=72)
    image = Image.alpha_composite(image, overlay)
    flattened = Image.new("RGB", image.size, "#281C18")
    flattened.paste(image, mask=image.getchannel("A"))

    # Small original-art signature panel, not copied text from the source post.
    d = ImageDraw.Draw(flattened)
    d.rounded_rectangle((44, 45, 445, 113), radius=10, fill="#201B18", outline="#A47A51", width=2)
    d.text((62, 56), "BARN DOOR WATCH", font=font(20), fill="#F7E9D2")
    d.text((62, 84), "An original farm-scene illustration", font=font(13), fill="#D2B58E")

    buffer = io.BytesIO()
    flattened.save(buffer, format="JPEG", quality=95, subsampling=0, optimize=True)
    payload = buffer.getvalue()
    with Image.open(io.BytesIO(payload)) as decoded:
        assert decoded.size == (WIDTH, HEIGHT) and decoded.mode == "RGB"
        decoded.verify()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("xb") as output:
        output.write(payload)
    print("Created and validated:", OUTPUT.relative_to(ROOT))
    print("Resolution: %d x %d RGB JPEG; %d bytes" % (WIDTH, HEIGHT, len(payload)))


if __name__ == "__main__":
    main()