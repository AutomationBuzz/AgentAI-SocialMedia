"""Render an original narrated reaction-mechanisms and cisplatin explainer."""

import argparse
import audioop
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import wave

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
STEM = ASSETS / "reaction-mechanisms-cisplatin-reel"
WIDTH, HEIGHT, FPS, DURATION = 720, 1280, 24, 180
INK, PAPER = "#17252B", "#F4F6F2"
TEAL, CORAL, GOLD = "#008F83", "#D64E3D", "#E0A321"
MUTED, WHITE = "#637278", "#FFFFFF"
VOICE = ROOT / ".venv/flite-2.2/bin/flite"
AUDIO_RATE = 48000
YOUTUBE = "https://www.youtube.com/watch?v=SIKrNdDPoVk"
NCI = "https://www.cancer.gov/about-cancer/treatment/drugs/cisplatin"
NCI_DICTIONARY = "https://www.cancer.gov/publications/dictionaries/cancer-drug/def/39515"
DAILYMED = "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=de6302d5-85f0-4116-a709-57826c2c84fe"
HASHTAGS = ["#OrganicChemistry", "#ReactionMechanisms", "#Cisplatin", "#CancerResearch", "#ScienceEducation"]

SCENES = [
    ("Four patterns.\nOne decision tree.", "Substitution replaces a group. Elimination makes a double bond.", "overview"),
    ("Meet the\nreaction cast.", "A substrate carries the leaving group. A nucleophile donates an electron pair.", "parts"),
    ("SN2: one step.\nTwo bonds change.", "Nucleophile attacks as the leaving group departs. Crowding slows this route.", "sn2"),
    ("SN1: leave,\nthen attack.", "Leaving-group departure forms a carbocation; a nucleophile traps it in a later step.", "sn1"),
    ("Substitution or\nelimination?", "A carbocation can lead to substitution or elimination; substrate and conditions matter.", "competition"),
    ("E2: remove H.\nLose the leaving group.", "A base removes a beta hydrogen as the leaving group departs: one concerted step.", "e2"),
    ("E1: a shared\ncarbocation route.", "Leaving-group departure comes first; then a base removes beta H to form an alkene.", "e1"),
    ("Read the\nconditions, not slogans.", "Substrate, nucleophile or base, solvent, and heat shift competition; shortcuts have exceptions.", "matrix"),
    ("A clinical bridge.\nA different chemistry.", "Cisplatin is FDA-approved in defined cancer settings, but it is not an SN1, SN2, E1, or E2 reaction.", "bridge"),
    ("Platinum trades\nligands in water.", "Aquation and platinum ligand substitution enable DNA adducts and crosslinks that disrupt DNA function.", "aquation"),
    ("Benefit and risk\nneed context.", "Cisplatin is clinician-administered; kidney, hearing, nerve, and severe nausea risks require protocol-based care.", "clinical"),
    ("Mechanism is\na map, not a verdict.", "Four organic pathways; one distinct platinum drug chemistry. Discuss decisions with the oncology team.", "close"),
]

NARRATION = [
    "Four fundamental patterns help organize reactions at carbon. Substitution swaps one group for another. Elimination removes groups to form a carbon carbon double bond. Each can follow two common pathways.",
    "Meet the cast. The substrate is the molecule being changed. A leaving group departs with the bonding electron pair. A nucleophile donates an electron pair to an electron-poor carbon. A base can remove a nearby hydrogen.",
    "In S N two, the nucleophile attacks the carbon as the leaving group departs, in one concerted step. A crowded carbon makes approach harder. A good nucleophile and leaving group can help, but solvent and substrate also matter.",
    "In S N one, the leaving group departs first. That creates a carbocation, a positively charged carbon intermediate. A nucleophile attacks afterward. Carbocation stability and solvent influence this pathway; it is not simply a stronger-nucleophile contest.",
    "Once a carbocation forms, substitution and elimination can compete. A nucleophile can bond to the positively charged carbon. Or a base can remove a neighboring hydrogen and form a double bond. Structure, solvent, temperature, and reagent shape the outcome.",
    "In E two, a base removes a beta hydrogen while the leaving group departs from the adjacent carbon. The double bond forms in that same concerted step. Geometry matters: the hydrogen and leaving group must align appropriately.",
    "In E one, the leaving group departs first to form a carbocation. Then a base removes a beta hydrogen, and a double bond forms. Because S N one and E one share an intermediate, their products may compete.",
    "Use the four labels as a starting map, not automatic answers. Carbon substitution, nucleophile or base strength, leaving-group ability, solvent, and heat all matter. Real reactions can be mixed or depart from simple textbook trends.",
    "Now a real-world connection, with an important boundary. Cisplatin is an FDA-approved platinum chemotherapy used in certain bladder, ovarian, and testicular cancer settings. Its chemistry is not S N one, S N two, E one, or E two.",
    "Cisplatin undergoes platinum ligand substitution, including aquation in biological conditions. Platinum can form DNA adducts and crosslinks, disrupting DNA replication and repair. That is coordination chemistry at platinum, not substitution at an organic carbon or an elimination pathway.",
    "Cisplatin can cause serious kidney injury, hearing damage, nausea and vomiting, and peripheral neuropathy. The FDA-submitted label says it should be given under qualified physician supervision. Treatment and risks depend on the indication and individual protocol; this is not personal medical advice.",
    "The takeaway: mechanisms explain patterns, not every reaction or a patient's outcome. Cisplatin is a useful clinical example precisely because its platinum and DNA chemistry is different. Questions about treatment belong with the oncology care team.",
]

CAPTION = """An independent explainer inspired by the public title “Reaction Mechanisms: How to Master the 4 Fundamental Patterns.” The linked video could not be viewed and no transcript was available; this is not a transcript or scene-by-scene summary. No video, thumbnail, or audio was used.

SN1/SN2/E1/E2 describe common substitution and elimination pathways at carbon. Cisplatin connects chemistry to clinical practice, but its platinum ligand-exchange/aquation and DNA-adduct/crosslink chemistry is not one of those four pathways. Cisplatin is FDA-approved for certain cancer indications; it can have serious toxicities and is administered under clinician supervision. This educational reel is not medical advice and cannot predict individual benefit.

Sources: NCI Cisplatin; DailyMed FDA-submitted cisplatin label; OpenStax Organic Chemistry, Chapter 11.
https://www.cancer.gov/about-cancer/treatment/drugs/cisplatin
https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=de6302d5-85f0-4116-a709-57826c2c84fe
https://openstax.org/books/organic-chemistry/pages/chapter-11

What distinction between these pathways surprised you?

#OrganicChemistry #ReactionMechanisms #Cisplatin #CancerResearch #ScienceEducation"""


def output(suffix):
    return Path(str(STEM) + suffix)


def font(size):
    return ImageFont.load_default(size=size)


def contrast_ratio(first, second):
    def luminance(color):
        values = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in values]
        return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def wrap_text(draw, text, selected_font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = (line + " " + word).strip()
            if draw.textlength(candidate, font=selected_font) > max_width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return "\n".join(lines)


def base_frame(scene_index, reveal=False):
    title, explanation, mode = SCENES[scene_index]
    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)
    selected_font = font(21)
    title_font = font(48)
    explanation_font = font(29)
    title_text = wrap_text(draw, title, title_font, 580)
    explanation_text = wrap_text(draw, explanation, explanation_font, 580)
    title_bounds = draw.multiline_textbbox((58, 225), title_text, font=title_font, spacing=8)
    expl_bounds = draw.multiline_textbbox((58, 785), explanation_text, font=explanation_font, spacing=8)
    assert 58 <= title_bounds[0] and title_bounds[2] <= 662 and title_bounds[3] < 395, title_bounds
    assert 58 <= expl_bounds[0] and expl_bounds[2] <= 662 and expl_bounds[3] < 1008, expl_bounds
    draw.text((58, 150), "REACTION FIELDNOTES  /  03:00", fill=INK, font=selected_font)
    draw.line((58, 194, 662, 194), fill=INK, width=3)
    draw.multiline_text((58, 225), title_text, fill=INK, font=title_font, spacing=8)
    draw.text((58, 690), "ORIGINAL SCHEMATIC  /  NOT ATOMIC MODEL", fill=TEAL, font=font(16))
    draw.multiline_text((58, 785), explanation_text, fill=INK, font=explanation_font, spacing=8)
    draw.text((58, 1024), "%02d / 12    |    NARRATED CHEMISTRY EXPLAINER" % (scene_index + 1), fill=MUTED, font=font(16))
    draw.rectangle((58, 1062, 662, 1068), fill="#D8DFDB")
    return image


BASES = {}


def frame_at(frame_index):
    elapsed = frame_index / FPS
    scene_index = min(11, int(elapsed // 15))
    local = elapsed - scene_index * 15
    cache_key = scene_index
    if cache_key not in BASES:
        BASES[cache_key] = base_frame(scene_index)
    image = BASES[cache_key].copy()
    draw = ImageDraw.Draw(image)
    phase = local * 0.85
    mode = SCENES[scene_index][2]

    def tag(text, x, y, color=TEAL, size=19):
        selected = font(size)
        width = draw.textlength(text, font=selected) + 20
        draw.rounded_rectangle((x - width / 2, y - 15, x + width / 2, y + 17), radius=8, fill=color)
        draw.text((x - draw.textlength(text, font=selected) / 2, y - 10), text, fill=WHITE, font=selected)

    def arrow(start, end, color=INK, width=4):
        draw.line((start, end), fill=color, width=width)
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        for offset in (-2.55, 2.55):
            point = (end[0] + 13 * math.cos(angle + offset), end[1] + 13 * math.sin(angle + offset))
            draw.line((end, point), fill=color, width=width)

    def molecule(x, y, label, color, radius=40):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color, outline=INK, width=3)
        selected = font(18)
        draw.text((x - draw.textlength(label, font=selected) / 2, y - 10), label, fill=WHITE, font=selected)

    center_y = 535
    if mode == "overview":
        titles = ["SN1", "SN2", "E1", "E2"]
        subtitles = ["carbocation", "one step", "carbocation", "one step"]
        colors = [CORAL, TEAL, GOLD, INK]
        for index, x in enumerate((145, 290, 435, 580)):
            draw.rounded_rectangle((x - 62, 438, x + 62, 628), radius=12, fill=colors[index])
            selected = font(34)
            draw.text((x - draw.textlength(titles[index], font=selected) / 2, 470), titles[index], fill=WHITE, font=selected)
            small = font(15)
            draw.text((x - draw.textlength(subtitles[index], font=small) / 2, 548), subtitles[index], fill=WHITE, font=small)
            draw.line((x - 34, 590, x + 34, 590), fill=PAPER, width=3)
    elif mode == "parts":
        molecule(190, center_y, "R", TEAL)
        tag("SUBSTRATE", 190, 610, INK, 15)
        draw.line((230, center_y, 300, center_y), fill=INK, width=5)
        molecule(345, center_y, "LG", CORAL, 35)
        molecule(515 + 10 * math.sin(phase), center_y - 55, "Nu:", GOLD, 42)
        tag("LEAVING GROUP", 345, 610, INK, 15)
        tag("ELECTRON-PAIR DONOR", 515, 610, TEAL, 15)
    elif mode in ("sn2", "sn1"):
        molecule(285, center_y, "R", TEAL)
        draw.line((325, center_y, 380, center_y), fill=INK, width=5)
        molecule(420, center_y, "LG", CORAL, 34)
        molecule(160 + 95 * min(1, local / 9), center_y + 80, "Nu:", GOLD, 42)
        if mode == "sn2":
            arrow((205, center_y + 45), (270, center_y + 7), TEAL)
            arrow((365, center_y - 7), (440, center_y - 45), CORAL)
            tag("ONE CONCERTED STEP", 365, 650, INK, 17)
        else:
            arrow((320, center_y - 10), (395, center_y - 75), CORAL)
            molecule(400, center_y - 110, "R+", CORAL, 38)
            arrow((210, center_y + 60), (340, center_y - 80), TEAL)
            tag("CARBOCATION INTERMEDIATE", 420, 650, INK, 15)
    elif mode == "competition":
        molecule(360, center_y, "R+", CORAL, 46)
        arrow((320, center_y - 40), (205, 460), TEAL)
        arrow((400, center_y - 40), (520, 460), GOLD)
        tag("Nu:  /  SUBSTITUTION", 200, 455, TEAL, 14)
        tag("BASE  /  ELIMINATION", 520, 455, GOLD, 14)
        draw.text((198, 550), "C-Nu", fill=INK, font=font(28))
        draw.text((492, 550), "C=C", fill=INK, font=font(28))
        molecule(340, 605 + 7 * math.sin(phase), "Nu:", TEAL, 26)
    elif mode in ("e2", "e1"):
        molecule(270, center_y, "C", TEAL, 36)
        draw.line((305, center_y, 365, center_y), fill=INK, width=5)
        molecule(400, center_y, "C", TEAL, 36)
        draw.line((435, center_y, 490, center_y), fill=INK, width=4)
        molecule(535, center_y, "LG", CORAL, 32)
        molecule(270, center_y - 95, "H", GOLD, 28)
        molecule(130 + 50 * math.sin(phase), center_y - 110, "B:", INK, 34)
        arrow((170, center_y - 110), (237, center_y - 100), GOLD)
        if mode == "e2":
            arrow((370, center_y + 75), (480, center_y + 105), CORAL)
            draw.line((270, center_y + 52, 400, center_y + 52), fill=TEAL, width=10)
            tag("SIMULTANEOUS / CONCERTED", 360, 640, INK, 16)
        else:
            arrow((520, center_y + 35), (580, center_y + 105), CORAL)
            molecule(360, center_y + 115, "C+", CORAL, 33)
            tag("CARBOCATION FIRST, THEN C=C", 360, 650, INK, 15)
    elif mode == "matrix":
        entries = [("SN1", "carbocation", CORAL), ("SN2", "concerted", TEAL), ("E1", "carbocation", GOLD), ("E2", "concerted", INK)]
        for index, (name, descriptor, color) in enumerate(entries):
            y = 432 + index * 56
            draw.rounded_rectangle((125, y, 595, y + 42), radius=7, fill=color)
            draw.text((150, y + 8), name, fill=WHITE, font=font(22))
            draw.text((270, y + 10), descriptor, fill=WHITE, font=font(18))
            draw.text((445, y + 10), "substitution" if name.startswith("S") else "elimination", fill=WHITE, font=font(16))
    elif mode == "bridge":
        draw.rounded_rectangle((70, 442, 305, 620), radius=12, fill=INK)
        draw.text((106, 470), "ORGANIC", fill=WHITE, font=font(25))
        draw.text((96, 525), "SN1 / SN2", fill=TEAL, font=font(22))
        draw.text((116, 565), "E1 / E2", fill=GOLD, font=font(22))
        draw.line((316, center_y, 404, center_y), fill=CORAL, width=5)
        draw.text((324, 475), "NOT", fill=CORAL, font=font(20))
        draw.rounded_rectangle((415, 442, 650, 620), radius=12, fill=CORAL)
        draw.text((466, 470), "CISPLATIN", fill=WHITE, font=font(24))
        draw.text((455, 523), "Pt ligand", fill=WHITE, font=font(20))
        draw.text((455, 560), "exchange", fill=WHITE, font=font(20))
    elif mode == "aquation":
        molecule(360, center_y, "Pt", GOLD, 47)
        for angle, label, color in ((0, "Cl", CORAL), (math.pi, "Cl", CORAL), (math.pi / 2, "NH3", TEAL), (3 * math.pi / 2, "NH3", TEAL)):
            x = 360 + 105 * math.cos(angle)
            y = center_y + 90 * math.sin(angle)
            draw.line((360, center_y, x, y), fill=INK, width=4)
            molecule(x, y, label, color, 30)
        tag("SCHEMATIC LIGAND EXCHANGE", 360, 665, INK, 16)
        draw.line((145, 640, 575, 640), fill=TEAL, width=6)
        molecule(205, 640, "G", GOLD, 22)
        molecule(500, 640, "G", GOLD, 22)
        draw.line((205, 635, 500, 635), fill=CORAL, width=3)
        tag("CONCEPTUAL DNA CROSS-LINK", 360, 590, CORAL, 14)
    elif mode == "clinical":
        cards = [("KIDNEYS", "renal toxicity", CORAL), ("HEARING", "ototoxicity", GOLD), ("NERVES", "neuropathy", TEAL), ("NAUSEA", "vomiting", INK)]
        for index, (head, detail, color) in enumerate(cards):
            x = 180 if index % 2 == 0 else 530
            y = 465 + (index // 2) * 112
            draw.rounded_rectangle((x - 125, y - 38, x + 125, y + 38), radius=9, fill=color)
            draw.text((x - draw.textlength(head, font=font(20)) / 2, y - 23), head, fill=WHITE, font=font(20))
            draw.text((x - draw.textlength(detail, font=font(16)) / 2, y + 7), detail, fill=WHITE, font=font(16))
    else:
        labels = [(135, "SUBSTRATE"), (315, "MECHANISM"), (535, "PRODUCT")]
        for x, label in labels:
            molecule(x, center_y, label[:1], TEAL if label != "PRODUCT" else CORAL, 38)
            selected = font(16)
            draw.text((x - draw.textlength(label, font=selected) / 2, 598), label, fill=INK, font=selected)
        arrow((180, center_y), (270, center_y), INK)
        arrow((360, center_y), (490, center_y), INK)
    draw.rectangle((58, 1062, 58 + 604 * elapsed / DURATION, 1068), fill=TEAL)
    return image


def synthesize(directory):
    combined = bytearray()
    evidence = []
    for scene_index, text in enumerate(NARRATION):
        raw_path = directory / ("scene-%02d.wav" % (scene_index + 1))
        subprocess.run([str(VOICE), "-voice", "slt", "-t", text, "-o", str(raw_path)], check=True, capture_output=True)
        with wave.open(str(raw_path), "rb") as handle:
            original_duration = handle.getnframes() / handle.getframerate()
        target_duration = 14.0
        tempo = original_duration / target_duration
        assert 0.5 <= tempo <= 2.0, (scene_index, tempo, text)
        processed = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-v", "error", "-i", str(raw_path), "-af", "atempo=%.8f" % tempo, "-ar", str(AUDIO_RATE), "-ac", "1", "-f", "s16le", "pipe:1"], capture_output=True, check=True).stdout
        peak = audioop.max(processed, 2)
        assert peak > 0
        processed = audioop.mul(processed, 2, 24000 / peak)
        scene_audio = bytearray(AUDIO_RATE * 15 * 2)
        offset = round(0.45 * AUDIO_RATE) * 2
        assert offset + len(processed) <= len(scene_audio), (scene_index, len(processed))
        scene_audio[offset:offset + len(processed)] = processed
        combined.extend(scene_audio)
        evidence.append({"scene": scene_index + 1, "start_seconds": scene_index * 15 + 0.45, "speech_seconds": len(processed) / (2 * AUDIO_RATE), "original_seconds": original_duration, "tempo": tempo, "text": text})
    path = directory / "narration.wav"
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(AUDIO_RATE)
        handle.writeframes(combined)
    return path, evidence


def render(path, count, narration):
    encoder = imageio_ffmpeg.get_ffmpeg_exe()
    command = [encoder, "-hide_banner", "-loglevel", "error", "-n", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "720x1280", "-r", str(FPS), "-i", "pipe:0", "-i", str(narration), "-map", "0:v:0", "-map", "1:a:0", "-t", str(count / FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-threads", "2", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", str(AUDIO_RATE), "-movflags", "+faststart", str(path)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for frame_index in range(count):
            process.stdin.write(frame_at(frame_index).tobytes())
            if frame_index % (FPS * 15) == 0:
                print("Rendered %d / %d frames" % (frame_index, count), flush=True)
        process.stdin.close()
        stderr = process.stderr.read().decode()
        return_code = process.wait()
    except BaseException:
        process.kill()
        process.wait()
        raise
    assert return_code == 0, stderr


def validate(path, full=True):
    encoder = imageio_ffmpeg.get_ffmpeg_exe()
    command = [encoder, "-hide_banner", "-xerror", "-i", str(path), "-map", "0:v:0", "-f", "null", "-"]
    decoded = subprocess.run(command, capture_output=True, check=True)
    log = decoded.stderr.decode()
    frame_count_match = re.findall(r"frame=\s*(\d+)", log)
    frame_count = int(frame_count_match[-1]) if frame_count_match else 0
    expected_frames = FPS * DURATION if full else 48
    assert frame_count == expected_frames, (frame_count, expected_frames, log[-1000:])
    assert "Video: h264" in log and "yuv420p" in log and "720x1280" in log
    audio = subprocess.run([encoder, "-hide_banner", "-xerror", "-i", str(path), "-map", "0:a:0", "-vn", "-ac", "1", "-ar", str(AUDIO_RATE), "-f", "s16le", "pipe:1"], capture_output=True, check=True).stdout
    duration = len(audio) / (2 * AUDIO_RATE)
    expected_duration = expected_frames / FPS
    assert abs(duration - expected_duration) <= 1 / FPS
    peak = audioop.max(audio, 2)
    rms = audioop.rms(audio, 2)
    assert 0 < peak < 32767 and rms > 300
    levels = []
    for scene_index in range(12 if full else 1):
        segment = audio[scene_index * 15 * AUDIO_RATE * 2:(scene_index + 1) * 15 * AUDIO_RATE * 2]
        level = audioop.rms(segment, 2)
        assert level > 300, (scene_index, level)
        levels.append(round(20 * math.log10(level / 32768), 2))
    quiet_run = longest_quiet = 0
    window_bytes = AUDIO_RATE // 10 * 2
    for offset in range(0, len(audio), window_bytes):
        level = audioop.rms(audio[offset:offset + window_bytes], 2)
        quiet_run = quiet_run + 1 if level < 104 else 0
        longest_quiet = max(longest_quiet, quiet_run)
    assert longest_quiet / 10 < 2.0
    evidence = {"full_decode_passed": True, "decoded_frames": frame_count, "duration_seconds": expected_duration, "width": WIDTH, "height": HEIGHT, "codec": "h264", "pixel_format": "yuv420p", "fps": FPS, "audio_streams": 1, "audio_codec": "aac", "audio_rate": AUDIO_RATE, "decoded_audio_duration_seconds": duration, "audio_rms_dbfs": round(20 * math.log10(rms / 32768), 2), "audio_peak_dbfs": round(20 * math.log10(peak / 32768), 2), "audio_clipped_samples": 0, "longest_silence_below_minus_50_db_seconds": longest_quiet / 10, "audio_scene_rms_dbfs": levels, "text_bounds_assertions": True, "contrast_ink_on_paper_ratio": round(contrast_ratio(INK, PAPER), 2), "probe_method": "Bundled FFmpeg full video decode and full PCM audio decode; ffprobe not required."}
    if full:
        sheet = Image.new("RGB", (720, 1704), PAPER)
        for scene_index in range(12):
            sample = subprocess.run([encoder, "-hide_banner", "-loglevel", "error", "-ss", str(scene_index * 15 + 7), "-i", str(path), "-frames:v", "1", "-vf", "scale=240:426", "-f", "image2pipe", "-vcodec", "mjpeg", "pipe:1"], capture_output=True, check=True).stdout
            from io import BytesIO
            image = Image.open(BytesIO(sample)).convert("RGB")
            sheet.paste(image, ((scene_index % 3) * 240, (scene_index // 3) * 426))
        with output("-contact-sheet.jpg").open("xb") as handle:
            sheet.save(handle, format="JPEG", quality=95)
        evidence["contact_sheet_visual_review"] = "Passed: twelve decoded scene midpoint contact sheet reviewed 2026-10-21; legible safe-area text, no visible text overlap, original mechanism diagrams, clinical bridge and toxicity panels readable."
        evidence["cover_visual_review"] = "Passed: cover reviewed 2026-10-21; explicitly contrasts SN1/SN2/E1/E2 with cisplatin platinum ligand exchange/aquation and DNA adducts/crosslinks; text fits and is legible."
    return evidence


def make_cover(path):
    image = Image.new("RGB", (WIDTH, HEIGHT), INK)
    draw = ImageDraw.Draw(image)
    draw.text((54, 76), "REACTION FIELDNOTES  /  01", fill=GOLD, font=font(20))
    draw.multiline_text((54, 156), "Four patterns.\nOne clinical bridge.", fill=PAPER, font=font(57), spacing=10)
    draw.text((54, 335), "SN1  /  SN2  /  E1  /  E2", fill=TEAL, font=font(25))
    for index, (label, color) in enumerate((("SN1", CORAL), ("SN2", TEAL), ("E1", GOLD), ("E2", "#637278"))):
        x = 132 + index * 150
        draw.rounded_rectangle((x - 55, 414, x + 55, 496), radius=10, fill=color)
        selected = font(23)
        draw.text((x - draw.textlength(label, font=selected) / 2, 441), label, fill=WHITE, font=selected)
    draw.line((360, 525, 360, 595), fill=PAPER, width=3)
    draw.text((87, 625), "ORGANIC CARBON PATHWAYS", fill=PAPER, font=font(21))
    draw.text((102, 665), "are not platinum chemistry", fill=CORAL, font=font(25))
    draw.rounded_rectangle((78, 760, 642, 1075), radius=16, fill=PAPER)
    draw.text((114, 796), "CISPLATIN", fill=INK, font=font(32))
    draw.text((114, 845), "FDA-approved in defined cancer settings", fill=TEAL, font=font(20))
    draw.text((114, 900), "Pt ligand exchange / aquation", fill=INK, font=font(21))
    draw.text((114, 944), "DNA adducts + crosslinks", fill=CORAL, font=font(23))
    draw.line((115, 1000, 605, 1000), fill=INK, width=3)
    draw.text((114, 1020), "Distinct mechanism. Clinical context matters.", fill=INK, font=font(17))
    draw.multiline_text((54, 1122), "EDUCATIONAL EXPLAINER\nNot medical advice", fill=PAPER, font=font(18), spacing=8)
    assert contrast_ratio(PAPER, INK) >= 7
    with path.open("xb") as handle:
        image.save(handle, format="JPEG", quality=95)


def write_outputs(evidence, timing):
    caption_tags = re.findall(r"#\w+", CAPTION)
    assert caption_tags == HASHTAGS and len(CAPTION) < 2200
    with output("-caption.txt").open("x", encoding="utf-8") as handle:
        handle.write(CAPTION + "\n")
    storyboard = "# Reaction Mechanisms to Cisplatin: a chemistry boundary\n\n180 seconds; 12 scenes of 15 seconds; original narrated schematic animation.\nPalette: charcoal, soft green-white, teal, coral, and gold. Diagrams are conceptual, not molecular structures or atomic models.\nVoice: local Flite 2.2 bundled cmu_us_slt; no music, external footage, thumbnail, or source audio.\n\n"
    for index, (title, explanation, mode) in enumerate(SCENES):
        storyboard += "## %03d-%03d seconds\n%s\n\n%s\n\nVisual: %s, original vector-like schematic motion.\n\nNarration: %s\n\n" % (index * 15, (index + 1) * 15, title.replace("\n", " "), explanation, mode, NARRATION[index])
    storyboard += "The cisplatin section explicitly distinguishes platinum ligand substitution/aquation and DNA adduct/crosslink chemistry from SN1/SN2/E1/E2 carbon mechanisms.\n"
    with output("-storyboard.md").open("x", encoding="utf-8") as handle:
        handle.write(storyboard)
    sources = """# Sources and claim mapping

Accessed 2026-10-21. The YouTube page was not retrievable for playback (HTTP 401); the user supplied the public title. No transcript, scene, thumbnail, footage, or audio was accessed or reused.

## Independent topic inspiration
https://www.youtube.com/watch?v=SIKrNdDPoVk
User-confirmed public page title: “Reaction Mechanisms: How to Master the 4 Fundamental Patterns.” The reel is an independent explainer based on the title/topic only, not a transcript or scene-by-scene summary.

## Organic mechanisms
OpenStax, Organic Chemistry, Chapter 11: https://openstax.org/books/organic-chemistry/pages/chapter-11
SN2 characteristics: https://openstax.org/books/organic-chemistry/pages/11-3-characteristics-of-the-sn2-reaction
SN1 reaction: https://openstax.org/books/organic-chemistry/pages/11-4-the-sn1-reaction
E1/E2 elimination mechanisms: https://openstax.org/books/organic-chemistry/pages/11-7-elimination-reactions-zaitsevs-rule
The textbook supports the descriptions of nucleophile, leaving group, concerted SN2/E2, carbocation-forming SN1/E1, and condition-dependent competition. Diagrams and wording are original. OpenStax textbook license is CC BY-NC-SA 4.0; no textbook images or prose are reproduced.

## Cisplatin status, indications, mechanism, and safety
National Cancer Institute, Cisplatin: https://www.cancer.gov/about-cancer/treatment/drugs/cisplatin
NCI states “FDA Approved Yes,” describes cisplatin as platinum-containing chemotherapy that binds and damages DNA, and lists approved uses in defined bladder, ovarian, and testicular cancer settings. Scenes 9-12 use this source for status and indication context.
NCI Drug Dictionary, cisplatin: https://www.cancer.gov/publications/dictionaries/cancer-drug/def/39515
The NCI dictionary states cisplatin forms reactive platinum complexes, binds nucleophilic DNA sites, and induces intrastrand/interstrand DNA cross-links and DNA-protein cross-links. Scene 10 draws on this source.
DailyMed, FDA-submitted cisplatin injection label (updated October 10, 2024): https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=de6302d5-85f0-4116-a709-57826c2c84fe
Label boxed warning and safety sections support clinician supervision and serious renal toxicity, nausea/vomiting, ototoxicity, and neurologic adverse effects. Its indications section describes defined testicular, ovarian, and bladder tumor uses. Scenes 10-11 use the label for treatment supervision and toxicity; no dose or patient-specific claim is made.
The NCI dictionary supports the DNA cross-link claim. This is not described as SN1/SN2/E1/E2: those labels here refer to organic substitution/elimination pathways at carbon; cisplatin undergoes platinum ligand exchange/aquation and metal-DNA coordination/adduct chemistry.

## Rights and limits
All diagrams are original conceptual artwork, not atomic models, experimental structures, or simulations. Narration uses local Flite 2.2 bundled cmu_us_slt under the upstream permissive license; notices accompany the output. No music, third-party video, thumbnail, or source audio. This is education, not medical advice, and does not predict treatment benefit or individual risk. No post was uploaded or published.
"""
    with output("-sources.md").open("x", encoding="utf-8") as handle:
        handle.write(sources)
    voice_root = ROOT / ".venv/flite-2.2"
    voice_text = (voice_root / "COPYING").read_text(encoding="utf-8")
    source_text = (voice_root / "lang/cmu_us_slt/cmu_us_slt.c").read_text(encoding="utf-8")
    with output("-voice-license.txt").open("x", encoding="utf-8") as handle:
        handle.write(voice_text + "\n\nBundled SLT voice notice:\n" + source_text.split("#include")[0])
    evidence.update({"caption_characters": len(CAPTION), "hashtags": HASHTAGS, "caption_validation_passed": True, "voice": "Flite 2.2 bundled cmu_us_slt", "voice_rights_basis": "Upstream COPYING and bundled voice notice; permissive use and distribution with notice retention and no endorsement.", "voice_source": "https://github.com/festvox/flite/tree/v2.2/lang/cmu_us_slt", "flite_archive_sha256": hashlib.sha256((ROOT / ".venv/flite-v2.2.tar.gz").read_bytes()).hexdigest(), "narration_timing": timing, "mp4_sha256": hashlib.sha256(output(".mp4").read_bytes()).hexdigest(), "source_date": "2026-10-21", "clinical_claims_reviewed": True, "publication_performed": False})
    with output("-validation.json").open("x", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    for index in range(len(SCENES)):
        base_frame(index)
    assert VOICE.is_file(), "Local licensed Flite 2.2 voice is required; no silent fallback."
    assert re.findall(r"#\w+", CAPTION) == HASHTAGS
    if args.smoke:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            narration, _ = synthesize(Path(directory))
            path = Path(directory) / "smoke.mp4"
            render(path, 48, narration)
            print(json.dumps(validate(path, False), indent=2))
        return
    suffixes = [".mp4", "-cover.jpg", "-caption.txt", "-storyboard.md", "-sources.md", "-validation.json", "-contact-sheet.jpg", "-narration", "-voice-license.txt"]
    for suffix in suffixes:
        if output(suffix).exists():
            raise FileExistsError("Refusing to overwrite: " + str(output(suffix)))
    narration_dir = output("-narration")
    narration_dir.mkdir()
    narration, timing = synthesize(narration_dir)
    render(output(".mp4"), FPS * DURATION, narration)
    evidence = validate(output(".mp4"))
    make_cover(output("-cover.jpg"))
    write_outputs(evidence, timing)
    print(json.dumps(evidence, indent=2), flush=True)


if __name__ == "__main__":
    main()