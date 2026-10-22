"""Render an interactive, fun-facts anatomy and physiology word cheat sheet."""

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
WIDTH, HEIGHT = 1654, 2339
MARGIN = 76
PAPER, INK, MUTED = "#FAF9F6", "#202A2D", "#586568"
TEAL, BURGUNDY, GOLD = "#006B64", "#842343", "#AF7900"
PALE_TEAL, PALE_ROSE, PALE_GOLD = "#E8F2EF", "#F5E9ED", "#F7F0DC"
RULE = "#D6DFDC"

PREFIXES = [
    ("a-, an-", "without; not", "apnea: no breathing"),
    ("brady-", "slow", "bradycardia: slow heart rate"),
    ("tachy-", "fast; rapid", "tachycardia: fast heart rate"),
    ("hyper-", "high; excessive", "hypertension: high blood pressure"),
    ("hypo-", "low; below normal", "hypoglycemia: low blood glucose"),
    ("poly-", "many; much", "polyuria: excessive urine output"),
    ("oligo-", "few; scanty", "oliguria: low urine output"),
    ("peri-", "around", "pericardium: around the heart"),
    ("endo-", "within", "endoscopy: look inside the body"),
    ("epi-", "upon; above", "epidermis: outer skin layer"),
    ("intra-", "within", "intravenous: within a vein"),
    ("inter-", "between", "intercostal: between the ribs"),
    ("sub-", "under; below", "subcutaneous: under the skin"),
    ("dys-", "difficult; abnormal", "dysphagia: difficulty swallowing"),
    ("hemi-", "half; one side", "hemiplegia: paralysis on one side"),
    ("bi-", "two; both", "bilateral: relating to both sides"),
    ("uni-", "one; single", "unilateral: relating to one side"),
]

SUFFIXES = [
    ("-itis", "inflammation", "gastritis: stomach inflammation"),
    ("-algia", "pain", "neuralgia: nerve pain"),
    ("-ectomy", "surgical removal", "appendectomy: appendix removal"),
    ("-otomy", "surgical incision", "tracheotomy: incision into trachea"),
    ("-ostomy", "create an opening", "colostomy: opening into colon"),
    ("-ology", "study of", "cardiology: study of the heart"),
    ("-ologist", "specialist", "cardiologist: heart specialist"),
    ("-pathy", "disease; disorder", "neuropathy: nerve disorder"),
    ("-megaly", "enlargement", "cardiomegaly: enlarged heart"),
    ("-emia", "blood condition", "anemia: blood condition"),
    ("-uria", "urine; urination condition", "hematuria: blood in urine"),
    ("-pnea", "breathing", "dyspnea: difficult breathing"),
    ("-scopy", "visual examination", "colonoscopy: visual colon exam"),
    ("-gram", "record; image", "electrocardiogram: heart tracing"),
    ("-graphy", "recording process", "angiography: vessel imaging"),
    ("-lysis", "breakdown; separation", "hemolysis: red-cell breakdown"),
    ("-rrhea", "flow; discharge", "diarrhea: frequent loose stools"),
    ("-rrhage", "excessive flow; bleeding", "hemorrhage: heavy bleeding"),
    ("-oma", "tumor; mass", "lymphoma: lymph-cell cancer"),
    ("-osis", "condition; often abnormal", "cyanosis: bluish discoloration"),
]

ROOTS = [
    ("cardi/o", "heart", "cardiology"), ("neur/o", "nerve", "neurology"),
    ("cerebr/o", "brain", "cerebral"), ("encephal/o", "brain", "encephalitis"),
    ("oste/o", "bone", "osteoporosis"), ("arthr/o", "joint", "arthritis"),
    ("my/o", "muscle", "myopathy"), ("derm/dermat/o", "skin", "dermatology"),
    ("hemat/o, hem/o", "blood", "hematology; hemorrhage"), ("gastr/o", "stomach", "gastritis"),
    ("enter/o", "intestine", "enteritis"), ("hepat/o", "liver", "hepatitis"),
    ("nephr/o", "kidney", "nephrology"), ("cyst/o", "bladder; sac", "cystitis"),
    ("pulmon/o", "lung", "pulmonary"), ("pneumon/o", "lung", "pneumonia"),
    ("angi/o", "vessel", "angiography"), ("cyt/o", "cell", "cytology"),
    ("hist/o", "tissue", "histology"),
]

SYSTEMS = [
    ("HEART + VESSELS", [
        ("Tachycardia", "fast heart rate"), ("Bradycardia", "slow heart rate"),
        ("Cardiomegaly", "enlarged heart"), ("Pericarditis", "inflammation around heart"),
    ], TEAL, PALE_TEAL),
    ("BREATHING", [
        ("Apnea", "cessation of breathing"), ("Dyspnea", "difficult breathing"),
        ("Tachypnea", "rapid breathing"), ("Hypoxia", "low oxygen in body tissues"),
    ], BURGUNDY, PALE_ROSE),
    ("DIGESTION", [
        ("Gastritis", "stomach inflammation"), ("Hepatomegaly", "enlarged liver"),
        ("Gastrectomy", "surgical stomach removal"), ("Dysphagia", "difficulty swallowing"),
    ], BURGUNDY, PALE_ROSE),
    ("URINARY", [
        ("Hematuria", "blood in urine"), ("Polyuria", "excessive urine output"),
        ("Oliguria", "low urine output"), ("Nephritis", "kidney inflammation"),
    ], TEAL, PALE_TEAL),
]


def f(size):
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


def header(draw, page, title, subtitle):
    draw.text((MARGIN, 54), "BODY WORDS / ANATOMY + PHYSIOLOGY", font=f(23), fill=TEAL)
    draw.text((WIDTH - 190, 56), "PAGE %s / 2" % page, font=f(21), fill=MUTED)
    draw.text((MARGIN, 107), title, font=f(61), fill=BURGUNDY)
    draw.text((MARGIN, 190), subtitle, font=f(26), fill=MUTED)
    draw.line((MARGIN, 244, WIDTH - MARGIN, 244), fill=BURGUNDY, width=4)


def table(draw, x, y, width, title, rows, accent, row_height):
    draw.rounded_rectangle((x, y, x + width, y + 60), radius=12, fill=accent)
    draw.text((x + 18, y + 12), title, font=f(26), fill="#FFFFFF")
    y += 72
    widths = (114, 222, width - 336)
    for index, label in enumerate(("PART", "MEANING", "SPOT IT")):
        draw.text((x + sum(widths[:index]) + 8, y), label, font=f(17), fill=MUTED)
    y += 30
    body_font = f(21)
    for i, row in enumerate(rows):
        draw.rounded_rectangle((x, y, x + width, y + row_height - 4), radius=7,
                               fill="#FFFFFF" if i % 2 == 0 else PAPER)
        left = x
        for j, value in enumerate(row):
            cell_width = widths[j]
            lines = wrap(draw, value, body_font, cell_width - 16)
            line_height = 25
            assert len(lines) * line_height <= row_height - 8, (title, value, lines)
            top = y + (row_height - len(lines) * line_height) // 2
            draw.multiline_text((left + 8, top), "\n".join(lines), font=body_font,
                                fill=accent if j == 0 else (INK if j == 1 else MUTED), spacing=1)
            left += cell_width
        y += row_height
    return y


def page_one():
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    d = ImageDraw.Draw(image)
    header(d, 1, "Decode the body", "Tiny word parts. Big clues about what is happening inside you.")

    d.rounded_rectangle((MARGIN, 270, WIDTH - MARGIN, 432), radius=18, fill=PALE_GOLD)
    d.text((MARGIN + 22, 288), "QUICK GUESS / What might bradycardia mean?", font=f(24), fill=GOLD)
    d.text((MARGIN + 22, 330), "brady-  SLOW     +     cardi  HEART     +     -ia  CONDITION", font=f(27), fill=INK)
    d.text((MARGIN + 22, 382), "REVEAL / A condition of an abnormally slow heart rate.", font=f(24), fill=BURGUNDY)

    gap = 30
    col_width = (WIDTH - 2 * MARGIN - gap) // 2
    x1, x2, y = MARGIN, MARGIN + col_width + gap, 458
    end_prefix = table(d, x1, y, col_width, "PREFIXES / front-of-word clues", PREFIXES, TEAL, 65)
    end_suffix = table(d, x2, y, col_width, "SUFFIXES / end-of-word clues", SUFFIXES, BURGUNDY, 67)

    fact_y = max(end_prefix, end_suffix) + 16
    d.rounded_rectangle((MARGIN, fact_y, WIDTH - MARGIN, fact_y + 238), radius=16, fill=PALE_TEAL)
    d.text((MARGIN + 22, fact_y + 17), "DID YOU SPOT IT?", font=f(23), fill=TEAL)
    d.text((MARGIN + 22, fact_y + 57), "-ectomy = remove   /   -otomy = cut into   /   -ostomy = make an opening",
           font=f(24), fill=INK)
    d.text((MARGIN + 22, fact_y + 102), "FUN FACT / Not every medical word has all three parts.", font=f(24), fill=BURGUNDY)
    d.text((MARGIN + 22, fact_y + 148), "MINI CHALLENGE / Which ending means a surgical incision?", font=f(24), fill=INK)
    d.text((MARGIN + 22, fact_y + 190), "ANSWER / -otomy. An ostomy creates an opening; an -ectomy removes.",
           font=f(21), fill=MUTED)
    assert fact_y + 238 < HEIGHT - 90, fact_y
    d.text((MARGIN, HEIGHT - 62), "Study aid. Word-part meanings are clues; use the full term and context.",
           font=f(19), fill=MUTED)
    return image


def root_table(draw, x, y, width, roots):
    draw.rounded_rectangle((x, y, x + width, y + 50), radius=9, fill=TEAL)
    draw.text((x + 12, y + 10), "ROOT", font=f(17), fill="#FFFFFF")
    draw.text((x + 225, y + 10), "BODY PART", font=f(17), fill="#FFFFFF")
    draw.text((x + 405, y + 10), "EXAMPLE", font=f(17), fill="#FFFFFF")
    y += 58
    for i, (root, meaning, example) in enumerate(roots):
        d_fill = "#FFFFFF" if i % 2 == 0 else PAPER
        draw.rounded_rectangle((x, y, x + width, y + 48), radius=6, fill=d_fill)
        draw.text((x + 12, y + 10), root, font=f(20), fill=BURGUNDY)
        draw.text((x + 225, y + 10), meaning, font=f(20), fill=INK)
        draw.text((x + 405, y + 10), example, font=f(19), fill=MUTED)
        y += 52
    return y


def system_card(draw, x, y, width, height, title, entries, accent, fill_color):
    draw.rounded_rectangle((x, y, x + width, y + height), radius=15, fill=fill_color)
    draw.text((x + 18, y + 16), title, font=f(25), fill=accent)
    top = y + 60
    for term, definition in entries:
        draw.text((x + 20, top), term, font=f(21), fill=INK)
        lines = wrap(draw, definition, f(19), width - 275)
        draw.multiline_text((x + 265, top), "\n".join(lines), font=f(19), fill=MUTED, spacing=1)
        top += 53 if len(lines) == 1 else 72
    assert top <= y + height - 8, (title, top)


def page_two():
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    d = ImageDraw.Draw(image)
    header(d, 2, "Clues in context", "Body roots + quick physiology facts. Can you decode them before reading the reveal?")
    d.text((MARGIN, 278), "ROOTS / THE BODY-PART CLUES", font=f(25), fill=BURGUNDY)
    gap = 34
    col_width = (WIDTH - 2 * MARGIN - gap) // 2
    split = (len(ROOTS) + 1) // 2
    left_end = root_table(d, MARGIN, 318, col_width, ROOTS[:split])
    right_end = root_table(d, MARGIN + col_width + gap, 318, col_width, ROOTS[split:])
    cards_y = max(left_end, right_end) + 18
    d.text((MARGIN, cards_y), "PHYSIOLOGY / FOUR FAST FACT CHECKS", font=f(25), fill=BURGUNDY)
    y = cards_y + 45
    card_gap = 22
    card_width = (WIDTH - 2 * MARGIN - card_gap) // 2
    card_height = 314
    system_card(d, MARGIN, y, card_width, card_height, *SYSTEMS[0])
    system_card(d, MARGIN + card_width + card_gap, y, card_width, card_height, *SYSTEMS[1])
    y2 = y + card_height + 18
    system_card(d, MARGIN, y2, card_width, card_height, *SYSTEMS[2])
    system_card(d, MARGIN + card_width + card_gap, y2, card_width, card_height, *SYSTEMS[3])
    fact_y = y2 + card_height + 18
    d.rounded_rectangle((MARGIN, fact_y, WIDTH - MARGIN, fact_y + 182), radius=15, fill=PALE_GOLD)
    d.text((MARGIN + 18, fact_y + 15), "LIGHTNING ROUND / Say the meaning, then peek", font=f(23), fill=GOLD)
    d.text((MARGIN + 18, fact_y + 55), "1. hypo- + -emia  =  low + blood condition  => hypoglycemia: low blood glucose",
           font=f(20), fill=INK)
    d.text((MARGIN + 18, fact_y + 96), "2. peri- + cardi + -itis  =  around + heart + inflammation  => pericarditis",
           font=f(20), fill=INK)
    d.text((MARGIN + 18, fact_y + 137), "FUN FACT / cardi/o + -ology becomes cardiology: the combining o drops before a vowel.",
           font=f(19), fill=BURGUNDY)
    assert fact_y + 182 < HEIGHT - 88, (fact_y, y, y2)
    d.text((MARGIN, HEIGHT - 62), "Educational reference only; terms can depend on clinical context.",
           font=f(19), fill=MUTED)
    return image


def save_jpeg(image, path):
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=95, subsampling=0, optimize=True)
    with Image.open(io.BytesIO(buffer.getvalue())) as decoded:
        assert decoded.size == image.size and decoded.mode == "RGB"
        if path.name.endswith("page-1.jpg") or path.name.endswith("page-2.jpg"):
            assert decoded.size == (WIDTH, HEIGHT)
        decoded.verify()
    with path.open("xb") as handle:
        handle.write(buffer.getvalue())


def main():
    outputs = [
        ASSETS / "anatomy-physiology-fun-facts-cheatsheet.pdf",
        ASSETS / "anatomy-physiology-fun-facts-page-1.jpg",
        ASSETS / "anatomy-physiology-fun-facts-page-2.jpg",
        ASSETS / "anatomy-physiology-fun-facts-preview.jpg",
    ]
    for path in outputs:
        if path.exists():
            raise FileExistsError("Refusing to overwrite: " + str(path))
    ASSETS.mkdir(exist_ok=True)
    pages = [page_one(), page_two()]
    save_jpeg(pages[0], outputs[1])
    save_jpeg(pages[1], outputs[2])
    pages[0].save(outputs[0], "PDF", resolution=200, save_all=True, append_images=pages[1:])
    preview = Image.new("RGB", (WIDTH // 2, HEIGHT), PAPER)
    preview.paste(pages[0].resize((WIDTH // 2, HEIGHT // 2), Image.Resampling.LANCZOS), (0, 0))
    preview.paste(pages[1].resize((WIDTH // 2, HEIGHT // 2), Image.Resampling.LANCZOS), (0, HEIGHT // 2))
    save_jpeg(preview, outputs[3])
    print(
        "Created fun-facts cheat sheet: %d prefixes, %d suffixes, %d roots, %d system examples."
        % (len(PREFIXES), len(SUFFIXES), len(ROOTS), sum(len(rows) for _, rows, _, _ in SYSTEMS))
    )
    for path in outputs:
        print(path.relative_to(ROOT), path.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
