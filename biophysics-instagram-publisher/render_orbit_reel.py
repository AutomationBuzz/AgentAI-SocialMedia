"""Render and validate the actual Orbit mobile browser recording."""

import array
import json
import math
from pathlib import Path
import subprocess

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageStat


ROOT = Path(__file__).resolve().parent
CAPTURE = ROOT / '.orbit-reel-capture'
STEM = ROOT / 'assets' / 'orbit-music-simulator-reel'
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FPS = 30


def render():
    frames = imageio_ffmpeg.read_frames(str(CAPTURE / 'capture.webm'), pix_fmt='rgb24', output_params=['-vf', 'fps=30'])
    metadata = next(frames)
    width, height = metadata['size']
    start_frame = None
    first_frame = None
    for frame_index, frame_bytes in enumerate(frames):
        candidate = Image.frombytes('RGB', (width, height), frame_bytes)
        red, green, blue = candidate.getpixel((5, 5))
        if red > 170 and green < 80 and blue > 170:
            start_frame = frame_index
            first_frame = candidate
            break
    assert first_frame is not None, 'Missing synchronization marker'
    command = [FFMPEG, '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '720x1280', '-r', str(FPS), '-i', '-', '-i', str(CAPTURE / 'audio.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-af', 'apad,afade=t=out:st=19.7:d=0.3', '-t', '20', '-movflags', '+faststart', str(STEM) + '.mp4']
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    title_font = ImageFont.load_default(size=34)
    caption_font = ImageFont.load_default(size=29)
    label_font = ImageFont.load_default(size=17)
    sample_frames = []
    for frame_index in range(600):
        if frame_index == 0:
            screen = first_frame
        else:
            screen = Image.frombytes('RGB', (width, height), next(frames))
        screen = screen.crop((12, 0, width, height)).resize((484, 1080), Image.Resampling.LANCZOS)
        image = Image.new('RGB', (720, 1280), '#101713')
        image.paste(screen, (118, 96))
        drawing = ImageDraw.Draw(image)
        drawing.text((40, 26), 'orbit. / MOBILE SESSION', font=title_font, fill='#d4f76e')
        elapsed = frame_index / FPS
        caption = 'Original electronic audio' if elapsed < 5 else 'Waveform follows the sound' if elapsed < 10 else 'Play / pause / seek / volume'
        bounds = drawing.textbbox((0, 0), caption, font=caption_font)
        assert bounds[2] < 660
        drawing.text(((720 - bounds[2]) / 2, 1190), caption, font=caption_font, fill='#f2f5ee')
        drawing.text((40, 1240), 'HTML / CSS / JS + WEB AUDIO', font=label_font, fill='#a4b2a8')
        process.stdin.write(image.tobytes())
        if frame_index in (30, 180, 246, 450, 570):
            sample_frames.append(image.copy())
    process.stdin.close()
    errors = process.stderr.read().decode()
    assert process.wait() == 0, errors[-3000:]
    frames.close()
    contact = Image.new('RGB', (720 * len(sample_frames), 1280))
    for index, image in enumerate(sample_frames):
        contact.paste(image, (index * 720, 0))
    contact.resize((1440, 512)).save(str(STEM) + '-contact-sheet.jpg')
    video = str(STEM) + '.mp4'
    probe = subprocess.run([FFMPEG, '-i', video, '-f', 'null', '-'], capture_output=True, text=True)
    assert probe.returncode == 0, probe.stderr
    assert 'h264' in probe.stderr and 'aac' in probe.stderr and 'yuv420p' in probe.stderr and '720x1280' in probe.stderr
    decoded = imageio_ffmpeg.read_frames(video, pix_fmt='rgb24')
    result_metadata = next(decoded)
    frame_count = 0
    frame_means = []
    for frame_bytes in decoded:
        if frame_count % 150 == 0:
            image = Image.frombytes('RGB', (720, 1280), frame_bytes)
            frame_means.append(ImageStat.Stat(image).mean)
        frame_count += 1
    assert frame_count == 600, frame_count
    assert abs(result_metadata['duration'] - 20) < 0.1
    pcm = subprocess.run([FFMPEG, '-i', video, '-vn', '-f', 's16le', '-ac', '2', '-ar', '44100', '-'], capture_output=True, check=True).stdout
    samples = array.array('h', pcm)
    rms = math.sqrt(sum(value * value for value in samples) / len(samples)) / 32768
    peak = max(abs(value) for value in samples) / 32768
    assert rms > 0.001 and 0 < peak < 1, (rms, peak)
    capture = json.loads((CAPTURE / 'capture.json').read_text())
    assert not capture['errors']
    report = {'duration_seconds': result_metadata['duration'], 'frames': frame_count, 'fps': FPS, 'resolution': [720, 1280], 'video_codec': 'h264', 'pixel_format': 'yuv420p', 'audio_codec': 'aac', 'audio_rms': rms, 'audio_rms_dbfs': 20 * math.log10(rms), 'audio_peak': peak, 'sampled_frame_rgb_means': frame_means, 'source_video_start_seconds': start_frame / FPS, 'capture_timeline': capture['timeline'], 'browser_errors': capture['errors'], 'source': 'Actual mobile browser UI and captured Web Audio master output; no replacement soundtrack.', 'published': False}
    Path(str(STEM) + '-validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    render()