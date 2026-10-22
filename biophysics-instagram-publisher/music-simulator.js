'use strict';

(() => {
  const duration = 20;
  const beat = 60 / 96;
  const presets = [
    { title: 'Neon Current', key: 'A MINOR', roots: [45, 41, 48, 43], melody: [69, 72, 76, 79, 76, 72, 67, 72], type: 'sawtooth', cutoff: 2100 },
    { title: 'Glass Satellite', key: 'D MINOR', roots: [50, 46, 53, 48], melody: [86, 81, 77, 84, 81, 77, 74, 81], type: 'sine', cutoff: 6500 },
    { title: 'After Hours', key: 'C MINOR', roots: [36, 44, 39, 46], melody: [67, 70, 74, 79, 74, 70, 65, 62], type: 'triangle', cutoff: 1400 }
  ];
  const element = (id) => document.getElementById(id);
  const cache = new Map();
  let context, analyser, output, source;
  let selected = 0, offset = 0, startedAt = 0, playing = false, repeating = false, muted = false, loading = false;
  let previousVolume = 0.7;
  let peak = 0;
  const frequency = (note) => 440 * 2 ** ((note - 69) / 12);

  async function synthesize(index) {
    if (cache.has(index)) return cache.get(index);
    const rendering = (async () => {
      const preset = presets[index];
      const offline = new OfflineAudioContext(2, duration * 44100, 44100);
      const compressor = offline.createDynamicsCompressor();
      compressor.threshold.value = -16;
      compressor.ratio.value = 4;
      const master = offline.createGain();
      master.gain.value = 0.72;
      compressor.connect(master).connect(offline.destination);
      const delay = offline.createDelay(1);
      const echo = offline.createGain();
      delay.delayTime.value = beat * 0.75;
      echo.gain.value = 0.24;
      delay.connect(echo).connect(delay);
      echo.connect(compressor);
      const noise = offline.createBuffer(1, 44100, 44100);
      const noiseData = noise.getChannelData(0);
      let seed = 1701 + index;
      for (let sample = 0; sample < noiseData.length; sample++) {
        seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
        noiseData[sample] = seed / 2147483648 - 1;
      }

      function tone(note, time, length, level, type, pan = 0, echoSend = false) {
        const oscillator = offline.createOscillator();
        const envelope = offline.createGain();
        const filter = offline.createBiquadFilter();
        const stereo = offline.createStereoPanner();
        oscillator.type = type;
        oscillator.frequency.value = frequency(note);
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(preset.cutoff, time);
        filter.frequency.exponentialRampToValueAtTime(450, time + length);
        stereo.pan.value = pan;
        envelope.gain.setValueAtTime(0, time);
        envelope.gain.linearRampToValueAtTime(level, time + 0.012);
        envelope.gain.exponentialRampToValueAtTime(0.0001, time + length);
        oscillator.connect(filter).connect(envelope).connect(stereo).connect(compressor);
        if (echoSend) stereo.connect(delay);
        oscillator.start(time);
        oscillator.stop(time + length + 0.01);
      }

      function percussion(time, snare) {
        const noiseSource = offline.createBufferSource();
        const filter = offline.createBiquadFilter();
        const envelope = offline.createGain();
        noiseSource.buffer = noise;
        filter.type = 'highpass';
        filter.frequency.value = snare ? 1300 : 7500;
        envelope.gain.setValueAtTime(snare ? 0.19 : 0.055, time);
        envelope.gain.exponentialRampToValueAtTime(0.0001, time + (snare ? 0.16 : 0.045));
        noiseSource.connect(filter).connect(envelope).connect(compressor);
        noiseSource.start(time);
        noiseSource.stop(time + 0.18);
      }

      for (let step = 0; step < 64; step++) {
        const time = step * beat / 2;
        const root = preset.roots[Math.floor(step / 16)];
        if (step % 2 === 0) {
          const kick = offline.createOscillator();
          const envelope = offline.createGain();
          kick.frequency.setValueAtTime(135, time);
          kick.frequency.exponentialRampToValueAtTime(43, time + 0.14);
          envelope.gain.setValueAtTime(0.65, time);
          envelope.gain.exponentialRampToValueAtTime(0.0001, time + 0.26);
          kick.connect(envelope).connect(compressor);
          kick.start(time);
          kick.stop(time + 0.27);
        }
        if (step % 4 === 2) percussion(time, true);
        percussion(time + 0.02, false);
        if (step % 2 === (index === 2 ? 1 : 0)) tone(root, time + 0.025, 0.23, 0.23, 'triangle');
        const note = preset.melody[(step + Math.floor(step / 16) * 2) % 8];
        if (index !== 2 || step % 3 !== 0) tone(note, time, index === 1 ? 0.6 : 0.24, 0.095, preset.type, step % 2 ? -0.35 : 0.35, true);
        if (step % 16 === 0) {
          for (const interval of [12, 15, 19]) tone(root + interval, time, 4.2, 0.05, 'sine', interval === 12 ? -0.6 : 0.6, true);
        }
      }
      const buffer = await offline.startRendering();
      for (let channel = 0; channel < buffer.numberOfChannels; channel++) {
        const samples = buffer.getChannelData(channel);
        for (let sample = 0; sample < samples.length; sample++) {
          const fadeIn = Math.min(1, sample / 220);
          const fadeOut = Math.min(1, (samples.length - 1 - sample) / 8820);
          samples[sample] = Math.tanh(samples[sample]) * fadeIn * fadeOut;
        }
      }
      return buffer;
    })();
    cache.set(index, rendering);
    try { return await rendering; } catch (error) { cache.delete(index); throw error; }
  }

  function initialize() {
    if (context) return;
    context = new AudioContext();
    analyser = context.createAnalyser();
    analyser.fftSize = 2048;
    output = context.createGain();
    output.gain.value = muted ? 0 : Number(element('volume').value);
    analyser.connect(output).connect(context.destination);
    context.addEventListener('statechange', () => {
      if (context.state !== 'running' && playing) pause();
    });
  }

  function position() {
    if (!playing) return offset;
    const current = offset + context.currentTime - startedAt;
    return repeating ? current % duration : Math.min(duration, current);
  }

  function stopSource() {
    if (!source) return;
    source.onended = null;
    source.stop();
    source.disconnect();
    source = null;
  }

  function updateButton() {
    element('play').textContent = playing ? '\u23f8' : '\u25b6';
    element('play').setAttribute('aria-label', playing ? 'Pause' : 'Play');
    element('play').title = playing ? 'Pause' : 'Play';
    element('status').textContent = playing ? 'Playing' : offset > 0 && offset < duration ? 'Paused' : 'Ready';
  }

  async function play() {
    if (loading) return;
    loading = true;
    element('play').disabled = true;
    element('status').textContent = 'Rendering';
    try {
      initialize();
      await context.resume();
      const buffer = await synthesize(selected);
      if (offset >= duration) offset = 0;
      source = context.createBufferSource();
      source.buffer = buffer;
      source.loop = repeating;
      source.connect(analyser);
      startedAt = context.currentTime;
      playing = true;
      source.onended = () => {
        playing = false;
        offset = duration;
        source.disconnect();
        source = null;
        updateButton();
      };
      source.start(0, offset);
      updateButton();
    } catch (error) {
      element('status').textContent = 'Audio unavailable. Tap play to retry.';
      console.error(error);
    } finally {
      loading = false;
      element('play').disabled = false;
    }
  }

  function pause() {
    offset = position();
    playing = false;
    stopSource();
    updateButton();
  }

  async function seek(time) {
    if (loading) return;
    const wasPlaying = playing;
    pause();
    offset = Math.max(0, Math.min(duration, time));
    updateButton();
    if (wasPlaying) await play();
  }

  async function select(index) {
    if (loading) return;
    const wasPlaying = playing;
    pause();
    selected = (index + presets.length) % presets.length;
    offset = 0;
    element('track-title').textContent = presets[selected].title;
    element('key').textContent = presets[selected].key;
    document.querySelectorAll('.preset').forEach((button, presetIndex) => button.setAttribute('aria-pressed', String(presetIndex === selected)));
    updateButton();
    if (wasPlaying) await play();
  }

  element('play').addEventListener('click', () => playing ? pause() : play());
  element('seek').addEventListener('input', (event) => seek(Number(event.target.value)));
  element('previous').addEventListener('click', () => select(selected - 1));
  element('next').addEventListener('click', () => select(selected + 1));
  element('restart').addEventListener('click', () => seek(0));
  document.querySelectorAll('.preset').forEach((button) => button.addEventListener('click', () => select(Number(button.dataset.preset))));
  element('presets').addEventListener('keydown', (event) => {
    if (!['ArrowDown', 'ArrowUp'].includes(event.key)) return;
    event.preventDefault();
    select(selected + (event.key === 'ArrowDown' ? 1 : -1));
    document.querySelector(`[data-preset="${selected}"]`).focus();
  });
  let wheelAt = 0;
  element('presets').addEventListener('wheel', (event) => {
    if (Math.abs(event.deltaY) < 8) return;
    event.preventDefault();
    if (performance.now() - wheelAt < 350) return;
    wheelAt = performance.now();
    select(selected + Math.sign(event.deltaY));
  }, { passive: false });
  let touchY;
  element('presets').addEventListener('touchstart', (event) => { touchY = event.changedTouches[0].clientY; }, { passive: true });
  element('presets').addEventListener('touchend', (event) => {
    const distance = touchY - event.changedTouches[0].clientY;
    if (Math.abs(distance) > 35) select(selected + Math.sign(distance));
  }, { passive: true });
  element('repeat').addEventListener('click', () => {
    const current = position();
    repeating = !repeating;
    if (playing) { offset = current; startedAt = context.currentTime; }
    if (source) source.loop = repeating;
    element('repeat').setAttribute('aria-pressed', String(repeating));
  });

  function setVolume() {
    const volume = Number(element('volume').value);
    if (output) output.gain.setTargetAtTime(muted ? 0 : volume, context.currentTime, 0.015);
    element('volume-value').textContent = `${Math.round((muted ? 0 : volume) * 100)}%`;
    element('mute').setAttribute('aria-pressed', String(muted));
    element('mute').setAttribute('aria-label', muted ? 'Unmute' : 'Mute');
    element('mute').title = muted ? 'Unmute' : 'Mute';
  }
  element('volume').addEventListener('input', () => { muted = false; setVolume(); });
  element('mute').addEventListener('click', () => { muted = !muted; setVolume(); });

  function wav(buffer) {
    const bytes = new ArrayBuffer(44 + buffer.length * 4);
    const view = new DataView(bytes);
    const text = (at, value) => { for (let index = 0; index < value.length; index++) view.setUint8(at + index, value.charCodeAt(index)); };
    text(0, 'RIFF'); view.setUint32(4, bytes.byteLength - 8, true); text(8, 'WAVE');
    text(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
    view.setUint16(22, 2, true); view.setUint32(24, buffer.sampleRate, true);
    view.setUint32(28, buffer.sampleRate * 4, true); view.setUint16(32, 4, true); view.setUint16(34, 16, true);
    text(36, 'data'); view.setUint32(40, buffer.length * 4, true);
    for (let sample = 0; sample < buffer.length; sample++) {
      for (let channel = 0; channel < 2; channel++) {
        const value = Math.max(-1, Math.min(1, buffer.getChannelData(channel)[sample]));
        view.setInt16(44 + sample * 4 + channel * 2, value * (value < 0 ? 32768 : 32767), true);
      }
    }
    return new Blob([bytes], { type: 'audio/wav' });
  }
  element('download').addEventListener('click', async () => {
    const index = selected;
    element('download').disabled = true;
    try {
      const buffer = await synthesize(index);
      const url = URL.createObjectURL(wav(buffer));
      const link = document.createElement('a');
      link.href = url;
      link.download = `orbit-${presets[index].title.toLowerCase().replaceAll(' ', '-')}-96bpm.wav`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 30000);
    } catch (error) { element('status').textContent = 'Export failed. Try again.'; console.error(error); }
    finally { element('download').disabled = false; }
  });

  const canvas = element('wave');
  const drawing = canvas.getContext('2d');
  const signal = new Float32Array(2048);
  function frame() {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const scale = devicePixelRatio || 1;
    if (canvas.width !== Math.round(width * scale) || canvas.height !== Math.round(height * scale)) {
      canvas.width = Math.round(width * scale);
      canvas.height = Math.round(height * scale);
    }
    drawing.setTransform(scale, 0, 0, scale, 0, 0);
    drawing.clearRect(0, 0, width, height);
    signal.fill(0);
    if (playing && analyser) analyser.getFloatTimeDomainData(signal);
    peak = signal.reduce((maximum, value) => Math.max(maximum, Math.abs(value)), 0);
    drawing.lineWidth = 1.5;
    drawing.strokeStyle = playing ? '#d4f76e' : '#536358';
    drawing.beginPath();
    for (let sample = 0; sample < signal.length; sample++) {
      const horizontal = sample / (signal.length - 1) * width;
      const vertical = height / 2 + signal[sample] * height * 0.45;
      if (sample === 0) drawing.moveTo(horizontal, vertical); else drawing.lineTo(horizontal, vertical);
    }
    drawing.stroke();
    const current = position();
    if (document.activeElement !== element('seek')) element('seek').value = current;
    element('seek').setAttribute('aria-valuetext', `${current.toFixed(1)} seconds of 20`);
    element('elapsed').textContent = `0:${String(Math.floor(current)).padStart(2, '0')}`;
    requestAnimationFrame(frame);
  }
  frame();
  element('download').disabled = false;
  window.orbit = Object.freeze({
    inspect: () => ({ playing, selected, position: position(), repeating, muted, volume: output?.gain.value ?? 0.7, contextState: context?.state ?? 'uninitialized', analyserPeak: peak }),
    render: synthesize,
    exportWav: async (index) => wav(await synthesize(index))
  });
})();