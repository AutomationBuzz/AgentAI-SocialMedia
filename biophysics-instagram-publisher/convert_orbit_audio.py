"""Create a browser-compatible MP3-in-MP4 alternative without changing video."""

import array
import hashlib
import json
import math
from pathlib import Path
import subprocess

import imageio_ffmpeg


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'assets' / 'orbit-music-simulator-reel.mp4'
OUTPUT = ROOT / 'assets' / 'orbit-music-simulator-reel-mp3.mp4'
REPORT = OUTPUT.with_suffix('.validation.json')
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def video_digest(path):
    result = subprocess.run(
        [FFMPEG, '-v', 'error', '-i', str(path), '-map', '0:v:0',
         '-c:v', 'copy', '-f', 'h264', '-'], capture_output=True, check=True)
    return hashlib.sha256(result.stdout).hexdigest()


def convert():
    if OUTPUT.exists() or REPORT.exists():
        raise FileExistsError('Refusing to overwrite conversion outputs')
    subprocess.run(
        [FFMPEG, '-n', '-i', str(SOURCE), '-map', '0:v:0', '-map', '0:a:0',
         '-c:v', 'copy', '-c:a', 'libmp3lame', '-b:a', '192k', '-ar', '48000',
         '-ac', '2', '-movflags', '+faststart', str(OUTPUT)], check=True)
    decode = subprocess.run(
        [FFMPEG, '-i', str(OUTPUT), '-f', 'null', '-'],
        capture_output=True, text=True, check=True)
    for expected in ('h264', 'yuv420p', '720x1280', '30 fps', 'Audio: mp3'):
        assert expected in decode.stderr, expected
    pcm = subprocess.run(
        [FFMPEG, '-v', 'error', '-i', str(OUTPUT), '-vn', '-f', 's16le',
         '-ac', '2', '-ar', '48000', '-'], capture_output=True, check=True).stdout
    samples = array.array('h', pcm)
    rms = math.sqrt(sum(value * value for value in samples) / len(samples)) / 32768
    peak = max(abs(value) for value in samples) / 32768
    duration = len(samples) / (48000 * 2)
    assert rms > 0.001 and 0 < peak < 1, (rms, peak)
    assert abs(duration - 20) < 0.1, duration
    unchanged = video_digest(SOURCE) == video_digest(OUTPUT)
    assert unchanged, 'Video elementary stream changed'
    report = {
        'asset': OUTPUT.name, 'sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        'video_codec': 'h264', 'pixel_format': 'yuv420p',
        'resolution': [720, 1280], 'fps': 30, 'video_stream_unchanged': unchanged,
        'audio_codec': 'mp3', 'audio_rate': 48000, 'audio_channels': 2,
        'audio_duration_seconds': duration, 'audio_rms_dbfs': 20 * math.log10(rms),
        'audio_peak': peak, 'full_decode_passed': True,
        'browser_decode': 'Not yet checked', 'published': False,
    }
    REPORT.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    convert()