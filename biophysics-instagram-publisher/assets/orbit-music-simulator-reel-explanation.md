# Orbit Mobile Reel

The 20-second vertical demo records the existing music simulator at a 390 x 844 mobile viewport. It starts Neon Current, scrolls from the original robot artwork to the controls, pauses briefly at 8 seconds, resumes at 8.6 seconds, seeks at 11 seconds, lowers volume at 14 seconds, and restores it at 16 seconds. The live waveform is rendered by the app's real audio analyser.

The soundtrack is captured from the simulator's master Web Audio output, including the demonstrated pause, seek and volume adjustments. The app uses its existing OfflineAudioContext synthesizer; there is no substituted song. A 0.3-second ending fade is added during encoding. Capture-only instrumentation does not change the app files. No personal data, desktop chrome or account information is included.

The app is HTML/CSS/JavaScript with Web Audio, not Flutter. It supports three synthesized presets, playback navigation, repeat, mute, volume and stereo WAV export. Only Neon Current is demonstrated in this reel.

Reproduction: install Playwright in an isolated directory, set ORBIT_PLAYWRIGHT to that module path, serve the existing app at localhost:8874, and run `node capture_orbit_reel.cjs`. Then run `render_orbit_reel.py` with the configured project Python environment containing Pillow and imageio_ffmpeg. Temporary capture files live in .orbit-reel-capture and are not committed. The renderer locates a capture-only synchronization marker, crops it away and exports H.264/AAC, yuv420p, 720 x 1280 at 30 fps. Validation JSON and a five-frame contact sheet accompany the MP4.

No Instagram operations, publishing or pushing are performed.