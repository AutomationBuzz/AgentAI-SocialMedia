"""Original narrated scientific animation; local rendering and validation only."""

import argparse
import audioop
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import wave

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat
import imageio_ffmpeg


ROOT = Path(__file__).resolve().parent
STEM = ROOT / "assets" / "ai-molecular-research-reel"
WIDTH, HEIGHT, FPS, DURATION = 720, 1280, 24, 180
INK, WHITE, CYAN, MAGENTA = "#111111", "#FFFFFF", "#00D9EB", "#EA268B"
PAPER = "https://www.nature.com/articles/s41586-024-07487-w"
VIDEO = "https://www.youtube.com/shorts/FoifEkBtxkE"
HASHTAGS = ["#AIinScience", "#AlphaFold", "#CancerResearch", "#DrugDiscovery", "#ScienceCommunication"]
VOICE = ROOT / ".venv/flite-2.2/bin/flite"
AUDIO_RATE = 48000
CAPTION = """An AI-predicted molecular structure is a hypothesis, not a cancer cure.

AlphaFold 3 predicts joint structures of molecular complexes, including proteins, DNA/RNA and small molecules. Its diffusion-based model can help researchers explore how molecules may fit together, but a plausible pose is not proof of binding, biological activity, safety or clinical benefit.

This original, narrated 3-minute explainer separates prediction from measurement: inspect model uncertainty, test interactions experimentally, study biological effects, and require clinical evidence for claims about treatments. Pause for the quiz: does a predicted fit prove a medicine works?

Independent educational explainer, not a summary of the linked Short. Video metadata was verified; no transcript was available. All animation is original schematic artwork, not an AlphaFold output or experimental structure.

Primary source: Abramson et al., Nature (2024), DOI: 10.1038/s41586-024-07487-w
https://www.nature.com/articles/s41586-024-07487-w

What experiment would you ask for next?

#AIinScience #AlphaFold #CancerResearch #DrugDiscovery #ScienceCommunication"""
SCENES = [
    ("A fit is not\na cure.", "AlphaFold 3 predicts molecular structures. It does not prove a treatment works.", "hook"),
    ("Meet the\nmolecular cast.", "Proteins, DNA/RNA, small molecules and ions can be modelled together.", "cast"),
    ("Shape matters.\nContext matters.", "A predicted arrangement suggests how molecular partners may meet.", "fit"),
    ("From noise\nto structure.", "A diffusion-based model refines noisy coordinates into a predicted complex.", "diffusion"),
    ("One model.\nMany partners.", "A unified framework predicts joint structures across molecular types.", "network"),
    ("A published\nexample.", "The paper models a bacterial regulatory protein with DNA and cGMP (Fig. 1a).", "dna"),
    ("PAUSE + PREDICT", "A predicted fit proves a medicine works. True or false?", "quiz"),
    ("Confidence is\nnot certainty.", "Models can get geometry wrong or invent plausible-looking structure.", "uncertainty"),
    ("Prediction\nmeets the lab.", "Measure binding and test biological activity. A structure alone is not enough.", "lab"),
    ("Cancer research:\na starting point.", "Predictions may guide hypotheses. Clinical benefit requires clinical evidence.", "clinical"),
    ("A structure is\nnot a movie.", "Molecules move. A single model does not capture their full dynamics.", "dynamics"),
    ("Predict. Test.\nQuestion again.", "What experiment would you ask for next? Share your reasoning.", "close"),
]
NARRATION = [
    "A fit is not a cure. Alpha Fold three predicts how molecules may be arranged together. That is a powerful scientific starting point, but it does not prove that a cancer treatment works. Let's separate the prediction from the evidence.",
    "Meet the molecular cast. Proteins do many jobs in cells. DNA and RNA carry biological information. Small molecules and ions can interact with them. Alpha Fold three predicts joint structures involving these different kinds of molecular partners.",
    "Shape matters, and context matters. The arrangement of molecular partners can suggest how they might interact. These moving shapes are original schematic diagrams, not actual model outputs. A plausible fit is a hypothesis to investigate, not a measured result.",
    "The primary paper describes a diffusion based architecture. In simplified terms, the model refines noisy molecular coordinates into a predicted complex. Our animation illustrates that idea only. It is not a recording of the model's internal computation.",
    "One framework can handle many kinds of partners. That broader scope is important because biology depends on interactions, not isolated proteins alone. The paper reports structural prediction benchmarks. Those benchmarks measure prediction performance, not patient outcomes or treatment success.",
    "Here is a published example. Figure one in the paper includes a bacterial regulatory protein with DNA and cyclic G M P. It illustrates the model's molecular scope. It is not a cancer therapy example, and this artwork does not reproduce its atomic coordinates.",
    "Pause and predict. Does a predicted molecular fit prove a medicine works? Think about what evidence is missing. The answer is false. A predicted fit does not establish biological activity, treatment safety, or clinical benefit. Those are separate scientific questions.",
    "Confidence is not certainty. The authors discuss limitations including incorrect geometry and plausible looking invented structure. Accuracy can depend on the target. Confidence estimates help researchers judge a prediction, but they cannot replace experimental checks or guarantee correctness.",
    "Now prediction meets the laboratory. Researchers can measure whether molecules bind and test what happens in biological systems. Results may support a hypothesis, challenge it, or suggest a new experiment. A structure alone does not establish how a molecule affects disease.",
    "For cancer research, structural predictions may help generate hypotheses about molecular interactions. That is different from demonstrating an effective treatment. Claims about a therapy's safety and clinical benefit require appropriate clinical evidence. This paper does not announce a cancer cure.",
    "A structure is not a movie. Real molecules move, and their environment matters. A single predicted arrangement does not capture every biological state or the full range of molecular motion. The movement shown here is illustrative, not a validated simulation.",
    "Predict, test, and question again. Alpha Fold three expands molecular structure prediction, while experiments determine what those predictions mean in practice. This is an independent topic explainer, not a verified transcript summary of the linked short. What experiment would you ask for next?",
]


def output(suffix):
    return Path(str(STEM) + suffix)


def exclusive_text(path, content):
    with path.open("x", encoding="utf-8") as handle:
        handle.write(content)


def overlaps(first, second):
    return first[0] < second[2] and first[2] > second[0] and first[1] < second[3] and first[3] > second[1]


def base_frame(scene_index, reveal=False):
    title, explanation, mode = SCENES[scene_index]
    image = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    drawing = ImageDraw.Draw(image)
    boxes = []
    graphic_box = (60, 390, 600, 700)

    def label(content, top, size, max_width=540):
        font = ImageFont.load_default(size=size)
        lines = []
        for paragraph in content.split("\n"):
            line = ""
            for word in paragraph.split():
                candidate = (line + " " + word).strip()
                if drawing.textlength(candidate, font=font) > max_width and line:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        text = "\n".join(lines)
        bounds = drawing.multiline_textbbox((60, top), text, font=font, spacing=9)
        assert 60 <= bounds[0] < bounds[2] <= 600 and 160 <= bounds[1] < bounds[3] <= 1000, (content, bounds)
        assert not overlaps(bounds, graphic_box), (content, bounds)
        assert all(not overlaps(bounds, previous) for previous in boxes), (content, boxes)
        boxes.append(bounds)
        drawing.multiline_text((60, top), text, fill=INK, font=font, spacing=9)

    label("MOLECULAR / 03:00", 160, 21)
    label(title, 218, 48)
    label("SCHEMATIC / NOT MODEL OUTPUT", 706, 16)
    if mode == "quiz" and reveal:
        explanation = "FALSE. Predicted fit is not proof of activity, safety or clinical benefit."
    label(explanation, 754, 30)
    label("SOURCE: NATURE / 2024 / ALPHAFOLD 3", 950, 15)
    label("%02d / 12    |    NARRATED EXPLAINER" % (scene_index + 1), 980, 15)
    drawing.rectangle((60, 195, 600, 199), fill=INK)
    return image


BASES = {}


def frame_at(frame_index):
    elapsed = frame_index / FPS
    scene_index = min(11, int(elapsed // 15))
    local = elapsed - scene_index * 15
    mode = SCENES[scene_index][2]
    reveal = mode == "quiz" and local >= 8
    key = (scene_index, reveal)
    if key not in BASES:
        BASES[key] = base_frame(*key)
    image = BASES[key].copy()
    drawing = ImageDraw.Draw(image)
    phase = local * 0.8

    def node(center, radius, color):
        horizontal, vertical = center
        drawing.ellipse((horizontal-radius, vertical-radius, horizontal+radius, vertical+radius), fill=color, outline=INK, width=2)

    def chain(center_x=280, center_y=540, amplitude=72, noise=0):
        points = []
        for atom_index in range(31):
            angle = atom_index * 0.43
            horizontal = center_x + (atom_index-15)*9 + 17*math.sin(angle+phase)
            vertical = center_y + amplitude*math.sin(angle+phase*0.6) + noise*math.sin(atom_index*2.1+phase)
            points.append((horizontal, vertical))
        drawing.line(points, fill=INK, width=5)
        for atom_index, point in enumerate(points):
            node(point, 7, CYAN if atom_index % 3 else MAGENTA)
        return points

    if mode == "network":
        layers = [[(115+layer*140, 440+row*72) for row in range(3)] for layer in range(4)]
        for layer_index in range(3):
            for first in layers[layer_index]:
                for second in layers[layer_index+1]:
                    drawing.line((first, second), fill="#B4BDC0", width=2)
                    travel = (local*0.25+first[1]/400) % 1
                    node((first[0]+(second[0]-first[0])*travel, first[1]+(second[1]-first[1])*travel), 4, MAGENTA)
        for layer in layers:
            for point in layer:
                node(point, 13, CYAN)
    elif mode in ("dna", "cast"):
        for step in range(23):
            vertical = 415 + step*11
            offset = 46*math.sin(step*0.48+phase)
            drawing.line((420-offset, vertical, 420+offset, vertical), fill=INK, width=2)
            node((420-offset, vertical), 5, CYAN)
            node((420+offset, vertical), 5, MAGENTA)
        chain(220, 540, 58)
        node((510+12*math.sin(phase), 540), 17, MAGENTA)
    elif mode in ("lab", "clinical", "close"):
        positions = [(145, 530), (330, 530), (515, 530)]
        for position_index, point in enumerate(positions):
            if position_index < 2:
                drawing.line((point[0]+35, 530, point[0]+145, 530), fill=INK, width=4)
            drawing.ellipse((point[0]-32, 498, point[0]+32, 562), fill=CYAN if position_index != 1 else MAGENTA, outline=INK, width=3)
        words = ["MODEL", "TEST", "EVIDENCE"]
        for position_index, point in enumerate(positions):
            font = ImageFont.load_default(size=18)
            drawing.text((point[0]-drawing.textlength(words[position_index], font=font)/2, 600), words[position_index], fill=INK, font=font)
        travel = (local / 5) % 1
        node((145+370*travel, 462+9*math.sin(phase)), 8, MAGENTA)
    elif mode == "quiz":
        chain(330, 520, 58)
        answer = "FALSE" if reveal else "TRUE OR FALSE?"
        font = ImageFont.load_default(size=36)
        drawing.text((330-drawing.textlength(answer,font=font)/2, 620), answer, fill=INK, font=font)
    else:
        noise = max(0, 1-local/12)*40 if mode == "diffusion" else 0
        chain(310, 535, 68, noise)
        orbit = 18 if mode != "fit" else 90*max(0,1-local/10)
        center = (460+orbit*math.cos(phase), 540+orbit*math.sin(phase))
        ligand = [(center[0]+27*math.cos(angle*math.pi/3+phase*0.2),center[1]+27*math.sin(angle*math.pi/3+phase*0.2)) for angle in range(6)]
        drawing.line(ligand+[ligand[0]], fill=INK, width=4)
        for point in ligand:
            node(point, 8, MAGENTA)
        if mode in ("uncertainty", "dynamics"):
            for offset in range(5):
                drawing.arc((120+offset*4,430+offset*3,540-offset*4,650-offset*3), int(phase*15)+offset*30, int(phase*15)+offset*30+95, fill="#7B8386", width=2)
    drawing.rectangle((60, 1015, 600, 1020), fill="#DCE1E2")
    drawing.rectangle((60, 1015, 60+540*elapsed/DURATION, 1020), fill=INK)
    return image


def synthesize(directory, scene_count=12):
    encoder = imageio_ffmpeg.get_ffmpeg_exe()
    combined = bytearray()
    evidence = []
    for scene_index in range(scene_count):
        narration = NARRATION[scene_index]
        parts = [(narration, 0.4, 14.0)]
        if scene_index == 6:
            question, answer = narration.split("The answer is false. ")
            parts = [(question, 0.4, 6.5), ("The answer is false. " + answer, 8.0, 6.5)]
        scene_audio = bytearray(AUDIO_RATE * 15 * 2)
        for part_index, (text, start, target_duration) in enumerate(parts):
            raw_path = directory / ("scene-%02d-%d.wav" % (scene_index + 1, part_index))
            subprocess.run([str(VOICE), "-voice", "slt", "-t", text, "-o", str(raw_path)], check=True, capture_output=True)
            with wave.open(str(raw_path), "rb") as handle:
                original_duration = handle.getnframes() / handle.getframerate()
            tempo = original_duration / target_duration
            assert 0.5 <= tempo <= 2.0, (scene_index, tempo)
            processed = subprocess.run([encoder, "-v", "error", "-i", str(raw_path), "-af", "atempo=%.8f" % tempo, "-ar", str(AUDIO_RATE), "-ac", "1", "-f", "s16le", "pipe:1"], capture_output=True, check=True).stdout
            peak = audioop.max(processed, 2)
            assert peak > 0
            processed = audioop.mul(processed, 2, 24000 / peak)
            assert len(processed) <= int((target_duration + 0.15) * AUDIO_RATE) * 2
            offset = round(start * AUDIO_RATE) * 2
            assert offset + len(processed) <= len(scene_audio)
            scene_audio[offset:offset + len(processed)] = processed
            evidence.append({"scene": scene_index + 1, "start_seconds": scene_index * 15 + start, "speech_seconds": len(processed) / (2 * AUDIO_RATE), "original_seconds": original_duration, "tempo": tempo, "text": text})
        combined.extend(scene_audio)
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
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=errors)
        try:
            for frame_index in range(count):
                process.stdin.write(frame_at(frame_index).tobytes())
                if frame_index % (FPS*15) == 0:
                    print("Rendered %d / %d frames" % (frame_index, count), flush=True)
            process.stdin.close()
            return_code = process.wait()
        except BaseException:
            process.kill()
            process.wait()
            raise
        errors.seek(0)
        assert return_code == 0, errors.read().decode()


def validate(path, full=True):
    encoder = imageio_ffmpeg.get_ffmpeg_exe()
    samples = [int((scene*15+offset)*FPS) for scene in range(12 if full else 1) for offset in (4,7.5,11)] if full else [0,12,24]
    expression = "+".join("eq(n,%d)" % number for number in samples)
    command = [encoder, "-hide_banner", "-xerror", "-i", str(path), "-an", "-vf", "showinfo,select='"+expression+"',scale=240:426", "-vsync", "0", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]
    result = subprocess.run(command, capture_output=True, check=True)
    log = result.stderr.decode()
    timings = re.findall(r"n:\s*(\d+)\s+pts:\s*\d+\s+pts_time:([\d.]+)", log)
    expected = FPS*DURATION if full else 48
    assert len(timings) == expected, (len(timings),expected)
    assert all(int(number)==index and abs(float(timestamp)-index/FPS)<0.002 for index,(number,timestamp) in enumerate(timings))
    assert "Video: h264" in log and "yuv420p" in log and "720x1280" in log and "24 fps" in log
    frame_bytes = 240*426*3
    assert len(result.stdout) == frame_bytes*len(samples)
    images = [Image.frombytes("RGB",(240,426),result.stdout[offset:offset+frame_bytes]) for offset in range(0,len(result.stdout),frame_bytes)]
    motion = []
    for scene in range(12 if full else 1):
        first, midpoint, last = images[scene*3:scene*3+3]
        crop = (20,130,200,233)
        difference = sum(ImageStat.Stat(ImageChops.difference(first.crop(crop),last.crop(crop))).mean)/3
        assert difference > 0.2, (scene,difference)
        assert sum(ImageStat.Stat(midpoint).stddev) > 15
        motion.append(round(difference,3))
    if full:
        sheet = Image.new("RGB",(720,1704),WHITE)
        for scene in range(12):
            sheet.paste(images[scene*3+1],((scene%3)*240,(scene//3)*426))
        with output("-contact-sheet.jpg").open("xb") as handle:
            sheet.save(handle,format="JPEG",quality=95)
    assert "Audio: aac" in log and "48000 Hz" in log
    audio = subprocess.run([encoder, "-hide_banner", "-xerror", "-i", str(path), "-vn", "-ac", "1", "-ar", str(AUDIO_RATE), "-f", "s16le", "pipe:1"], capture_output=True, check=True).stdout
    audio_duration = len(audio) / (2 * AUDIO_RATE)
    assert abs(audio_duration - expected / FPS) <= 1 / FPS
    peak = audioop.max(audio, 2)
    assert 0 < peak < 32767, peak
    rms = audioop.rms(audio, 2)
    assert rms > 300, rms
    scene_levels = []
    for scene_index in range(12 if full else 1):
        segment = audio[scene_index * 15 * AUDIO_RATE * 2:(scene_index + 1) * 15 * AUDIO_RATE * 2]
        level = audioop.rms(segment, 2)
        assert level > 300, (scene_index, level)
        scene_levels.append(round(20 * math.log10(level / 32768), 2))
    silent_run = longest_silence = 0
    window_bytes = AUDIO_RATE // 10 * 2
    for offset in range(0, len(audio), window_bytes):
        level = audioop.rms(audio[offset:offset + window_bytes], 2)
        silent_run = silent_run + 1 if level < 104 else 0
        longest_silence = max(longest_silence, silent_run)
    assert longest_silence / 10 < 2.0, longest_silence / 10
    return {"full_decode_passed":True,"decoded_frames":len(timings),"duration_seconds":expected/FPS,"width":WIDTH,"height":HEIGHT,"codec":"h264","pixel_format":"yuv420p","fps":FPS,"constant_frame_timestamps_passed":True,"audio_streams":1,"audio_codec":"aac","audio_rate":AUDIO_RATE,"decoded_audio_duration_seconds":audio_duration,"audio_rms_dbfs":round(20*math.log10(rms/32768),2),"audio_peak_dbfs":round(20*math.log10(peak/32768),2),"audio_clipped_samples":0,"longest_silence_below_minus_50_db_seconds":longest_silence/10,"audio_scene_rms_dbfs":scene_levels,"motion_mean_absolute_difference_per_scene":motion,"nonblank_all_scenes":True,"text_bounds_nonoverlap_assertions":True,"contrast_black_on_white_ratio":18.88,"contact_sheet_visual_review":"pending operator review","playback_review":"Full software video/audio decode checked; human real-time listening not performed.","probe_method":"FFmpeg input stream probe and full frame/sample decode; ffprobe executable unavailable."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    arguments = parser.parse_args()
    for scene_index in range(12):
        base_frame(scene_index)
    base_frame(6,True)
    assert len(CAPTION) < 2200 and re.findall(r"#\w+",CAPTION) == HASHTAGS
    assert VOICE.is_file(), "Local licensed Flite 2.2 voice is required; no silent fallback."
    if arguments.smoke:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory)/"smoke.mp4"
            narration, timing = synthesize(Path(directory), 1)
            render(path,48,narration)
            print(json.dumps(validate(path,False),indent=2))
        return
    suffixes = [".mp4","-cover.jpg","-caption.txt","-storyboard.md","-sources.md","-validation.json","-contact-sheet.jpg","-narration","-voice-license.txt"]
    for suffix in suffixes:
        if output(suffix).exists():
            raise FileExistsError("Refusing to overwrite: " + str(output(suffix)))
    output("-narration").mkdir()
    narration, timing = synthesize(output("-narration"))
    render(output(".mp4"),FPS*DURATION,narration)
    evidence = validate(output(".mp4"))
    evidence.update({"caption_characters":len(CAPTION),"hashtags":HASHTAGS,"caption_validation_passed":True,"encoder":imageio_ffmpeg.get_ffmpeg_exe(),"silent":False,"source_date":"2026-10-21","voice":"Flite 2.2 bundled cmu_us_slt","voice_rights_basis":"Upstream COPYING and bundled cmu_us_slt source grant unrestricted use/distribution including publish/sell, subject to notices and no endorsement. No Apple voice, voice cloning, music or third-party footage.","voice_source":"https://github.com/festvox/flite/tree/v2.2/lang/cmu_us_slt","flite_archive_sha256":hashlib.sha256((ROOT/".venv/flite-v2.2.tar.gz").read_bytes()).hexdigest(),"narration_timing":timing,"mp4_sha256":hashlib.sha256(output(".mp4").read_bytes()).hexdigest()})
    with output("-cover.jpg").open("xb") as handle:
        frame_at(96).save(handle,format="JPEG",quality=95)
    exclusive_text(output("-caption.txt"),CAPTION+"\n")
    storyboard = "# AlphaFold 3: prediction is not proof\n\n180 seconds; 12 x 15 seconds; original narrated schematic animation.\nPalette: white, black, cyan, magenta. All scientific graphics are conceptual, not model outputs.\nVoice: Flite 2.2 bundled SLT, locally synthesized; no music. Narration starts 0.4 seconds into each scene and is tempo-fitted without pitch shifting. Quiz answer starts at 98 seconds, matching the reveal.\n\n"
    for scene_index,(title,explanation,mode) in enumerate(SCENES):
        storyboard += "## %03d-%03d seconds\n%s\n\n%s\n\nMotion: %s; continuous molecular or evidence-flow motion.\n\n" % (scene_index*15,(scene_index+1)*15,title.replace("\n"," "),explanation,mode)
        storyboard += "Narration: " + NARRATION[scene_index] + "\n\n"
    storyboard += "Quiz: question at 90 seconds; FALSE reveal at 98 seconds. No music, borrowed footage or thumbnails.\n"
    exclusive_text(output("-storyboard.md"),storyboard)
    sources = """# Sources and evidence scope

Accessed 2026-10-21.

## Primary paper
Abramson et al. Accurate structure prediction of biomolecular interactions with AlphaFold 3. Nature 630, 493-500 (2024). Published 8 May 2024. DOI: 10.1038/s41586-024-07487-w
https://www.nature.com/articles/s41586-024-07487-w
Direct HTTPS fetch returned 200 and readable full article text.

## Claim mapping
- Scenes 1-3, 5: abstract: joint structures of proteins, nucleic acids, small molecules, ions and modified residues. A predicted arrangement is a structural hypothesis, not measured efficacy.
- Scene 4: abstract and diffusion module description: updated diffusion-based architecture; noisy-coordinate refinement is a simplified conceptual explanation, not a technical implementation diagram.
- Scene 6: Figure 1a: bacterial CRP/FNR family regulatory protein bound to DNA and cGMP, PDB 7PZB. Artwork is original and not copied from the paper or PDB coordinates.
- Scenes 7-8: Model limitations section: stereochemistry, hallucinations, dynamics and target-dependent accuracy; plausible structure is not certainty. No numerical performance claims used.
- Scenes 9-10: educational inference, not a clinical result of the paper: structural prediction alone cannot establish binding, biological activity, treatment safety or benefit. Experiments are needed; claims of clinical benefit require clinical evidence. No specific medicine or cancer outcome is asserted.
- Scene 11: Model limitations: dynamics; a single structure does not capture full molecular motion.
- Scene 12: viewer question, not a scientific outcome claim.

## Video metadata only
https://www.youtube.com/shorts/FoifEkBtxkE
Public YouTube oEmbed returned 200: title "Google DeepMind's AI Cancer Breakthrough"; author "ZAUEY (Claire Zau)". Transcript unavailable; footage not viewed or downloaded. This is an independent AlphaFold 3 explainer, NOT a verified summary of the Short. Metadata does not prove the Short discusses AlphaFold 3.

## Inaccessible source
https://deepmind.google/discover/blog/alphafold-3-predicts-the-structure-and-interactions-of-all-of-lifes-molecules/
Direct fetch returned 404; not used as evidence. Nature paper is the primary factual source.

## Limitations and rights
Narrated animation: local Flite 2.2 bundled SLT voice; no music or third-party media. Upstream COPYING and the bundled voice source contain CMU's permissive unrestricted-use/distribution license; the notices are retained in the local source and accompanying voice-license file. No endorsement or voice cloning claimed. Molecular graphics are illustrative, not accurate atomic geometries, actual model predictions, or experimental structures. No cure, approval, endorsement or demonstrated clinical benefit claimed. All generated media remains local; no publication action performed.
"""
    exclusive_text(output("-sources.md"),sources)
    voice_source = (ROOT/".venv/flite-2.2/lang/cmu_us_slt/cmu_us_slt.c").read_text()
    exclusive_text(output("-voice-license.txt"),(ROOT/".venv/flite-2.2/COPYING").read_text()+"\n\nBundled SLT voice notice:\n"+voice_source.split('#include')[0])
    exclusive_text(output("-validation.json"),json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2),flush=True)


if __name__ == "__main__":
    main()