# Orbit Mobile Reel

The 20-second vertical demo records the existing music simulator at a 390 x 844 mobile viewport. It starts Neon Current, scrolls from the original robot artwork to the controls, pauses briefly at 8 seconds, resumes at 8.6 seconds, seeks at 11 seconds, lowers volume at 14 seconds, and restores it at 16 seconds. The live waveform is rendered by the app's real audio analyser.

The soundtrack is captured from the simulator's master Web Audio output, including the demonstrated pause, seek and volume adjustments. The app uses its existing OfflineAudioContext synthesizer; there is no substituted song. A 0.3-second ending fade is added during encoding. Capture-only instrumentation does not change the app files. No personal data, desktop chrome or account information is included.

The app is HTML/CSS/JavaScript with Web Audio, not Flutter. It supports three synthesized presets, playback navigation, repeat, mute, volume and stereo WAV export. Only Neon Current is demonstrated in this reel.

Reproduction: install Playwright in an isolated directory, set ORBIT_PLAYWRIGHT to that module path, serve the existing app at localhost:8874, and run `node capture_orbit_reel.cjs`. Then run `render_orbit_reel.py` with the configured project Python environment containing Pillow and imageio_ffmpeg. Temporary capture files live in .orbit-reel-capture and are not committed. The renderer locates a capture-only synchronization marker, crops it away and exports H.264/AAC, yuv420p, 720 x 1280 at 30 fps. Validation JSON and a five-frame contact sheet accompany the MP4.

The original renderer performs no Instagram operations or pushing.

## Instagram Audio Compatibility And Publication

On 2026-10-22, the integrated browser could not decode the original AAC audio even though full FFmpeg decoding confirmed nonzero samples. Instagram's editor consequently displayed "Video has no audio". `convert_orbit_audio.py` creates a separate MP3-in-MP4 variant using the same encoding pattern as the existing reaction-mechanisms variant. It copies the H.264 video without changes, preserves 720 x 1280 at 30 fps, encodes stereo MP3 at 48 kHz / 192 kb/s, and verifies full decode, nonzero audio and identical video elementary-stream hashes. Existing outputs are never overwritten.

The MP3 variant passed local AudioContext decoding and video playback. Instagram's editor displayed "Sound on" with nonzero decoded audio bytes. The approved caption was entered unchanged, composer identity was verified as wowscifi_lab, Original crop was selected, and Share was clicked once. Instagram confirmed "Your reel has been shared." The new post appeared on the profile at https://www.instagram.com/reel/DezM67wSQtp/.

The initial published Edit view showed an empty caption despite the composer text. The approved caption was restored through Edit info and saved. After reloading the permalink, the expanded published caption showed all three paragraphs and all five approved hashtags unchanged.

Instagram transcodes the published audio to stereo HE-AAC. The public server rendition fully decoded through FFmpeg to 20.033 seconds of nonzero audio at -18.88 dBFS RMS. This integrated browser still cannot play that rendition because its AAC decoder reports kUnsupportedConfig. This is a browser limitation, not evidence of silent server audio. Human listening was not performed. Technical evidence and the non-secret publication receipt are saved alongside the asset and under receipts/instagram-DezM67wSQtp.json. No credentials or temporary CDN URLs are retained.