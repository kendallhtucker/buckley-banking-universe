/* ============================================================
   BANKING UNIVERSE · v4
   - Broadcast clock + HUD timecode
   - Web Audio drone toggle
   - Click-to-play → reveal finale
   - "BUCKLEY" easter egg → hyperspace
   - Replay button restarts to player state
   ============================================================ */

// -------- broadcast clock --------
function tickClock() {
  const el = document.getElementById('bb-clock');
  if (!el) return;
  const now = new Date();
  const h = String(now.getHours()).padStart(2, '0');
  const m = String(now.getMinutes()).padStart(2, '0');
  const s = String(now.getSeconds()).padStart(2, '0');
  el.textContent = `${h}:${m}:${s}`;
}
setInterval(tickClock, 1000);
tickClock();

// -------- HUD timecode (frozen but live frame counter for vibe) --------
let tcFrame = 0;
function tickTC() {
  const el = document.getElementById('hud-tc');
  if (!el) return;
  tcFrame = (tcFrame + 1) % 30;
  // show 00:00:00:FF, paused at zero seconds but frames ticking
  el.textContent = `00:00:00:${String(tcFrame).padStart(2, '0')}`;
}
setInterval(tickTC, 33); // ~30fps

// -------- web audio drone --------
let audioCtx = null;
let droneNodes = null;
let droneOn = false;

function startDrone() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (droneNodes) return;

  const master = audioCtx.createGain();
  master.gain.value = 0;
  master.gain.linearRampToValueAtTime(0.08, audioCtx.currentTime + 1.5);
  master.connect(audioCtx.destination);

  const filter = audioCtx.createBiquadFilter();
  filter.type = 'lowpass';
  filter.frequency.value = 380;
  filter.Q.value = 6;
  filter.connect(master);

  const lfo = audioCtx.createOscillator();
  const lfoGain = audioCtx.createGain();
  lfo.frequency.value = 0.08;
  lfoGain.gain.value = 60;
  lfo.connect(lfoGain).connect(filter.frequency);
  lfo.start();

  const o1 = audioCtx.createOscillator();
  o1.type = 'sawtooth';
  o1.frequency.value = 55;
  o1.connect(filter);
  o1.start();

  const o2 = audioCtx.createOscillator();
  o2.type = 'sawtooth';
  o2.frequency.value = 55.4;
  o2.connect(filter);
  o2.start();

  const bufSize = 2 * audioCtx.sampleRate;
  const noiseBuf = audioCtx.createBuffer(1, bufSize, audioCtx.sampleRate);
  const data = noiseBuf.getChannelData(0);
  for (let i = 0; i < bufSize; i++) data[i] = (Math.random() * 2 - 1) * 0.3;
  const noise = audioCtx.createBufferSource();
  noise.buffer = noiseBuf;
  noise.loop = true;
  const noiseFilter = audioCtx.createBiquadFilter();
  noiseFilter.type = 'highpass';
  noiseFilter.frequency.value = 2000;
  const noiseGain = audioCtx.createGain();
  noiseGain.gain.value = 0.04;
  noise.connect(noiseFilter).connect(noiseGain).connect(master);
  noise.start();

  droneNodes = { master, filter, lfo, o1, o2, noise };
}

function stopDrone() {
  if (!droneNodes) return;
  const { master } = droneNodes;
  master.gain.linearRampToValueAtTime(0, audioCtx.currentTime + 0.6);
  setTimeout(() => {
    try {
      droneNodes.lfo.stop();
      droneNodes.o1.stop();
      droneNodes.o2.stop();
      droneNodes.noise.stop();
    } catch (e) {}
    droneNodes = null;
  }, 700);
}

document.getElementById('sound-toggle').addEventListener('click', (e) => {
  const btn = e.currentTarget;
  droneOn = !droneOn;
  if (droneOn) {
    if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
    startDrone();
    btn.classList.add('on');
    btn.querySelector('.st-label').textContent = 'SOUND ON';
  } else {
    stopDrone();
    btn.classList.remove('on');
    btn.querySelector('.st-label').textContent = 'SOUND OFF';
  }
});

// -------- PLAY → FINALE --------
document.getElementById('play-btn').addEventListener('click', () => {
  document.body.classList.add('playing');
});

// -------- REPLAY → back to player --------
document.getElementById('replay').addEventListener('click', () => {
  document.body.classList.remove('playing');
});

// -------- BUCKLEY easter egg → hyperspace --------
let typedBuffer = '';
document.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  if (e.key.length === 1) {
    typedBuffer = (typedBuffer + e.key.toUpperCase()).slice(-8);
    if (typedBuffer.endsWith('BUCKLEY')) {
      triggerHyperspace();
      typedBuffer = '';
    }
  }
});

function triggerHyperspace() {
  document.body.classList.add('hyperspace');
  setTimeout(() => {
    document.body.classList.remove('hyperspace');
  }, 1500);
}
