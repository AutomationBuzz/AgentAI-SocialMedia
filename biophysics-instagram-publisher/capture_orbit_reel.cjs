const { chromium } = require(process.env.ORBIT_PLAYWRIGHT || 'playwright');
const fs = require('node:fs/promises');
const path = require('node:path');

async function main() {
  const destination = path.resolve(process.argv[2] || '.orbit-reel-capture');
  await fs.mkdir(destination, { recursive: true });
  const browser = await chromium.launch({ headless: true, args: ['--autoplay-policy=no-user-gesture-required'] });
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true, recordVideo: { dir: destination, size: { width: 390, height: 844 } } });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(() => {
    const NativeContext = window.AudioContext;
    window.AudioContext = class extends NativeContext {
      constructor(...args) {
        super(...args);
        window.reelContext = this;
      }
    };
  });
  await page.goto(process.env.ORBIT_URL || 'http://127.0.0.1:8874/music-simulator.html');
  await page.locator('.cover img').evaluate(image => image.decode());
  await page.evaluate(() => window.orbit.render(0));
  await page.evaluate(() => {
    const NativeContext = window.AudioContext;
    window.AudioContext = class extends NativeContext {
      constructor(...args) {
        super(...args);
        const processor = this.createScriptProcessor(4096, 2, 2);
        window.reelSamples = [[], []];
        processor.onaudioprocess = event => {
          if (!window.reelRecording) return;
          for (let channel = 0; channel < 2; channel++) window.reelSamples[channel].push(new Float32Array(event.inputBuffer.getChannelData(channel)));
        };
        processor.connect(this.destination);
        const nativeConnect = AudioNode.prototype.connect;
        const destination = this.destination;
        AudioNode.prototype.connect = function(target, ...args) {
          if (target === destination && this !== processor) nativeConnect.call(this, processor);
          return nativeConnect.call(this, target, ...args);
        };
      }
    };
  });
  await page.locator('#play').evaluate(button => button.click());
  await page.waitForFunction(() => window.orbit.inspect().position > 0.3);
  await page.locator('#play').evaluate(button => button.click());
  await page.locator('#restart').evaluate(button => button.click());
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.evaluate(() => {
    const marker = document.createElement('div');
    marker.style.cssText = 'position:fixed;top:0;left:0;width:12px;height:12px;background:#ff00ff;z-index:9999';
    document.body.append(marker);
    window.reelStart = performance.now();
    window.reelRecording = true;
  });
  const timeline = [];
  async function at(seconds, action) {
    await page.waitForFunction(target => performance.now() - window.reelStart >= target, seconds * 1000);
    await action();
    timeline.push(await page.evaluate(() => ({ time: (performance.now() - window.reelStart) / 1000, ...window.orbit.inspect() })));
  }
  await at(0, () => page.locator('#play').evaluate(button => button.click()));
  await at(2.5, () => page.evaluate(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })));
  await at(8, () => page.locator('#play').evaluate(button => button.click()));
  await at(8.6, () => page.locator('#play').evaluate(button => button.click()));
  await at(11, () => page.locator('#seek').evaluate(input => { input.value = '10'; input.dispatchEvent(new Event('input', { bubbles: true })); }));
  await at(14, () => page.locator('#volume').evaluate(input => { input.value = '0.4'; input.dispatchEvent(new Event('input', { bubbles: true })); }));
  await at(16, () => page.locator('#volume').evaluate(input => { input.value = '0.7'; input.dispatchEvent(new Event('input', { bubbles: true })); }));
  await at(20, () => page.evaluate(() => { window.reelRecording = false; }));
  const audioBase64 = await page.evaluate(() => {
    const length = window.reelSamples[0].reduce((total, chunk) => total + chunk.length, 0);
    const bytes = new ArrayBuffer(44 + length * 4);
    const view = new DataView(bytes);
    const text = (offset, value) => [...value].forEach((character, index) => view.setUint8(offset + index, character.charCodeAt(0)));
    text(0, 'RIFF'); view.setUint32(4, bytes.byteLength - 8, true); text(8, 'WAVE'); text(12, 'fmt ');
    view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 2, true);
    view.setUint32(24, window.reelContext.sampleRate, true); view.setUint32(28, window.reelContext.sampleRate * 4, true);
    view.setUint16(32, 4, true); view.setUint16(34, 16, true); text(36, 'data'); view.setUint32(40, length * 4, true);
    for (let channel = 0; channel < 2; channel++) {
      let sample = 0;
      for (const chunk of window.reelSamples[channel]) for (const value of chunk) {
        view.setInt16(44 + sample * 4 + channel * 2, Math.max(-1, Math.min(1, value)) * 32767, true); sample++;
      }
    }
    let binary = '';
    for (const byte of new Uint8Array(bytes)) binary += String.fromCharCode(byte);
    return btoa(binary);
  });
  await fs.writeFile(path.join(destination, 'audio.wav'), Buffer.from(audioBase64, 'base64'));
  const timing = await page.evaluate(() => ({ start: window.reelStart, origin: performance.timeOrigin }));
  await page.screenshot({ path: path.join(destination, 'mobile-playing.png') });
  const video = page.video();
  await context.close();
  await video.saveAs(path.join(destination, 'capture.webm'));
  await browser.close();
  await fs.writeFile(path.join(destination, 'capture.json'), JSON.stringify({ timeline, errors, timing, note: 'Raw capture includes browser setup; align using video content before rendering.' }, null, 2));
  console.log(JSON.stringify({ destination, timeline, errors }));
}

main().catch(error => { console.error(error); process.exitCode = 1; });