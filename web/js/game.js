const $ = i => document.getElementById(i),
  R = Math.random,
  rr = (a, b) => a + R() * (b - a),
  cl = (v, a, b) => Math.max(a, Math.min(b, v)),
  css = c => '#' + c.toString(16).padStart(6, '0'),
  LW = 2.2,
  NR = 75,
  NS = 82;

// Platform detection
const isMobile = matchMedia('(pointer:coarse)').matches || /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) || navigator.maxTouchPoints > 0;

// ---------- data ----------
const DIFF = [
  { n: 'Easy', col: 0x59d97f, d: 'Relaxed pace, gentle curves, forgiving hits.', hp: 130, dmg: 0.6, v0: 12, vg: 0.12, vmax: 34, gap: [28, 16, 0.08], nob: [1, 1, 1, 2], gc: 0.18, curve: 0.7, ecd: 1.5, dt: 30, dm: 1, dp: 0.12, dcap: 0.25 },
  { n: 'Medium', col: 0xffc733, d: 'The classic experience. Balanced speed and curves.', hp: 100, dmg: 1, v0: 14, vg: 0.2, vmax: 42, gap: [24, 13, 0.12], nob: [1, 1, 2, 3], gc: 0.28, curve: 1, ecd: 1, dt: 12, dm: 3, dp: 0.2, dcap: 0.45 },
  { n: 'Hard', col: 0xff4d40, d: 'Fast, dense obstacles, sharp bends. Every hit hurts.', hp: 80, dmg: 1.4, v0: 17, vg: 0.28, vmax: 48, gap: [21, 12, 0.15], nob: [2, 2, 3, 3], gc: 0.4, curve: 1.25, ecd: 0.7, dt: 6, dm: 4, dp: 0.3, dcap: 0.6 }
];

const LOC = [
  { n: 'Agrabah', tag: 'Desert highway', d: 'Golden domes, palms and warm dust. Sandstorms roll in at times.', kind: 'desert', sky: 0xf79954, top: 0x4d3385, gr: 0xdbb273, rd: 0x6b1a1f, ed: 0xf2bf26, dc: 0xf2e6cc, far: 0xc79457, sun: 0xffe08a, ac: 0xf2bf26, hs: 0xffe0b0, hg: 0x806040, hi: 0.95, sc: 0xffd9a0, si: 0.8, fg: 1, curve: 1, wx: 3 },
  { n: 'Neon City', tag: 'Cyber night', d: 'A rain-slick skyline that never sleeps. Neon everywhere.', kind: 'city', sky: 0x2a1040, top: 0x05050f, gr: 0x12121a, rd: 0x1c1c28, ed: 0x33e6ff, dc: 0xd36bff, far: 0x2a1d52, sun: 0xb9b2ff, ac: 0x59e6ff, hs: 0x7a5fb8, hg: 0x1a1428, hi: 0.9, sc: 0x9a7bff, si: 0.5, fg: 0.85, curve: 0.6, wx: 1 },
  { n: 'Frozen Peaks', tag: 'Snow and ice', d: 'A winding alpine pass under pale skies. Snow falls, bends are tight.', kind: 'snow', sky: 0xb8cde6, top: 0x6f8fc0, gr: 0xeef3ff, rd: 0x454d61, ed: 0x99d9ff, dc: 0xffffff, far: 0xaab9d4, sun: 0xffffff, ac: 0x99d9ff, hs: 0xdfeaff, hg: 0x8899aa, hi: 1, sc: 0xffffff, si: 0.7, fg: 0.9, curve: 1.3, wx: 2 },
  { n: 'Emerald Vale', tag: 'Misty forest', d: 'A twisty valley road through dense trees and drifting mist.', kind: 'forest', sky: 0x84b8a0, top: 0x3a7d95, gr: 0x336e33, rd: 0x5c4730, ed: 0x99e066, dc: 0xf5ecc0, far: 0x2e665a, sun: 0xe8f0b0, ac: 0x8ce673, hs: 0xcfeedd, hg: 0x405a30, hi: 0.95, sc: 0xfff2c0, si: 0.7, fg: 0.78, curve: 1.5, wx: 0 }
];

const S = {
  st: 'menu', di: 1, li: 0, D: 0, t: 0, time: 0, speed: 7.5, target: 14, lane: 2,
  px: 0, py: 0, vy: 0, slide: 0, hp: 100, score: 0, coins: 0, kills: 0, chain: 0,
  inv: 0, cd: 0, roll: 0, cdir: 1, segs: [], cend: 40, rt: new Float32Array(NR + 1),
  k0: 0, obs: [], cns: [], gs: [], bl: [], next: 20, phase: 0, wx: 0, eb: [], dr: [],
  it: [], view: 0, tod: 3, clock: R() * 120, wmode: 0, wn: 0, wt: 30, wk: 1, envT: 0,
  shield: 0, rapid: 0, shake: 0, fire: 0, fuel: 100, heat: 0, mx: innerWidth / 2, my: innerHeight * 0.45, mouse: 0, aim: [0, 0, -1]
};

let hi = [0, 0, 0];
try { hi = JSON.parse(localStorage.getItem('dd3')) || hi; } catch (e) {}

const DF = () => DIFF[S.di],
  LC = () => LOC[S.li],
  mult = () => 1 + Math.min((S.chain / 5) | 0, 4);

let AC;
function sfx(f, ms) {
  try {
    AC = AC || new (window.AudioContext || window.webkitAudioContext)();
    if (AC.state === 'suspended') AC.resume();
    const o = AC.createOscillator(),
      g = AC.createGain(),
      t = AC.currentTime;
    o.type = 'square';
    o.frequency.value = f;
    g.gain.setValueAtTime(0.06, t);
    g.gain.exponentialRampToValueAtTime(0.001, t + ms / 1000);
    o.connect(g);
    g.connect(AC.destination);
    o.start();
    o.stop(t + ms / 1000);
  } catch (e) {}
}

// ---------- curved road ----------
function curv(d) {
  while (S.cend < d + 220) {
    const a = S.cend + rr(60, 190),
      l = rr(110, 240);
    S.cdir = R() < 0.65 ? -S.cdir : S.cdir;
    S.segs.push([a, l, S.cdir * rr(1.8e-3, 3.5e-3)]);
    S.cend = a + l;
  }
  const f = DF().curve * LC().curve;
  for (const [a, l, p] of S.segs) {
    if (d >= a && d < a + l) return p * f * Math.sin((Math.PI * (d - a)) / l) ** 2;
  }
  return 0;
}

function road() {
  let h = 0, x = 0;
  S.k0 = curv(S.D);
  S.rt[0] = 0;
  for (let i = 1; i <= NR; i++) {
    const k = curv(S.D + (i - 0.5) * 2),
      h2 = h + k * 2;
    x += (h + h2) * 0.5 * 2;
    h = h2;
    S.rt[i] = x;
  }
  S.segs = S.segs.filter(q => q[0] + q[1] > S.D - 40);
}

function off(z) {
  const d = -z;
  if (d <= 0) return 0.5 * S.k0 * d * d;
  const i = d / 2, n = Math.floor(i);
  if (n >= NR) return S.rt[NR];
  return S.rt[n] + (S.rt[n + 1] - S.rt[n]) * (i - n);
}

// ---------- three.js setup ----------
const ren = new THREE.WebGLRenderer({ canvas: $('c'), antialias: true, alpha: true }),
  scene = new THREE.Scene(),
  cam = new THREE.PerspectiveCamera(58, 1, 0.3, 260);

const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 0.9),
  sunL = new THREE.DirectionalLight(0xffffff, 0.8);
sunL.position.set(0.4, 1, 0.5);
scene.add(hemi, sunL);

const BG = new THREE.BoxGeometry(1, 1, 1),
  SG = new THREE.SphereGeometry(1, 14, 10),
  CG = new THREE.ConeGeometry(1, 1, 9),
  YG = new THREE.CylinderGeometry(1, 1, 1, 10),
  mc = {};

const mat = (c, e) => mc[c + '_' + (e || 0)] || (mc[c + '_' + (e || 0)] = new THREE.MeshLambertMaterial({ color: c, emissive: e || 0 }));

function mk(g, c, x, y, z, sx, sy, sz, p, e) {
  const m = new THREE.Mesh(g, mat(c, e));
  m.position.set(x, y, z);
  m.scale.set(sx, sy, sz);
  if (p) p.add(m);
  return m;
}

const wt = (() => {
  const c = document.createElement('canvas');
  c.width = 8;
  c.height = 16;
  const x = c.getContext('2d');
  x.fillStyle = '#000';
  x.fillRect(0, 0, 8, 16);
  for (let i = 0; i < 8; i++) {
    for (let j = 0; j < 16; j++) {
      if (R() < 0.4) {
        x.fillStyle = ['#ffd27a', '#6fe3ff', '#ff6ad5'][(R() * 3) | 0];
        x.fillRect(i, j, 1, 1);
      }
    }
  }
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter;
  return t;
})();

const bt = (() => {
  const c = document.createElement('canvas');
  c.width = 1;
  c.height = 2;
  const x = c.getContext('2d');
  x.fillStyle = '#fff';
  x.fillRect(0, 0, 1, 1);
  x.fillStyle = '#d8d8d8';
  x.fillRect(0, 1, 1, 1);
  const t = new THREE.CanvasTexture(c);
  t.wrapT = THREE.RepeatWrapping;
  t.magFilter = t.minFilter = THREE.NearestFilter;
  return t;
})();

// ground + road ribbons
const B = c => new THREE.MeshBasicMaterial({ color: c }),
  gm = B(0),
  rm = new THREE.MeshBasicMaterial({ color: 0, map: bt }),
  em = B(0),
  dm = B(0),
  rib = [];

const gnd = new THREE.Mesh(new THREE.PlaneGeometry(500, 360), gm);
gnd.rotation.x = -Math.PI / 2;
gnd.position.set(0, -0.02, -100);
scene.add(gnd);

function ribbon(xl, xr, y, m) {
  const g = new THREE.BufferGeometry(),
    p = new Float32Array(NS * 6),
    u = new Float32Array(NS * 4),
    ix = [];
  for (let k = 0; k < NS; k++) {
    u[k * 4 + 1] = u[k * 4 + 3] = k / 4;
    u[k * 4 + 2] = 1;
    if (k < NS - 1) {
      const a = k * 2;
      ix.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
    }
  }
  g.setAttribute('position', new THREE.BufferAttribute(p, 3));
  g.setAttribute('uv', new THREE.BufferAttribute(u, 2));
  g.setIndex(ix);
  const o = new THREE.Mesh(g, m);
  o.frustumCulled = false;
  scene.add(o);
  rib.push({ p, xl, xr, y, g });
}

ribbon(-5.5, 5.5, 0, rm);
ribbon(-5.9, -5.5, 0.04, em);
ribbon(5.5, 5.9, 0.04, em);
const glm = new THREE.MeshBasicMaterial({ color: 0, transparent: true, opacity: 0.3, depthWrite: false, blending: THREE.AdditiveBlending });
ribbon(-7.4, -5.9, 0.03, glm);
ribbon(5.9, 7.4, 0.03, glm);

const dash = new THREE.InstancedMesh(BG, dm, 104),
  dum = new THREE.Object3D();
dash.frustumCulled = false;
scene.add(dash);

// characters
function figure(vest, pants, skin, hair, en) {
  const g = new THREE.Group(), L = [];
  for (const s of [-1, 1]) {
    const lg = new THREE.Group();
    lg.position.set(s * 0.2, 0.9, 0);
    mk(BG, pants, 0, -0.45, 0, 0.24, 0.9, 0.26, lg);
    g.add(lg);
    L.push(lg);
    const ar = new THREE.Group();
    ar.position.set(s * 0.5, 1.6, 0);
    mk(BG, skin, 0, -0.35, 0, 0.18, 0.75, 0.18, ar);
    g.add(ar);
    L.push(ar);
  }
  mk(BG, vest, 0, 1.3, 0, 0.75, 0.75, 0.38, g);
  mk(BG, 0xf2bf26, 0, 0.98, 0, 0.78, 0.14, 0.42, g);
  mk(SG, skin, 0, 1.9, 0, 0.27, 0.27, 0.27, g);
  mk(SG, hair, 0, 1.98, 0.04, 0.3, 0.22, 0.3, g);
  if (en) {
    mk(BG, 0xff2020, -0.1, 1.92, 0.26, 0.08, 0.06, 0.04, g, 0xff0000);
    mk(BG, 0xff2020, 0.1, 1.92, 0.26, 0.08, 0.06, 0.04, g, 0xff0000);
  }
  g.userData.L = L;
  scene.add(g);
  return g;
}

function swing(g, ph) {
  const s = Math.sin(ph) * 0.7,
    L = g.userData.L;
  L[0].rotation.x = -s;
  L[2].rotation.x = s;
  L[1].rotation.x = s;
  L[3].rotation.x = -s;
}

const pl = figure(0xbf1a26, 0xf2f2e6, 0xcc8c59, 0x141210),
  shd = new THREE.Mesh(new THREE.CircleGeometry(0.8, 16), new THREE.MeshBasicMaterial({ color: 0, transparent: true, opacity: 0.35 }));
shd.rotation.x = -Math.PI / 2;
scene.add(shd);

const shM = new THREE.Mesh(SG, new THREE.MeshBasicMaterial({ color: 0x4db3ff, transparent: true, opacity: 0.28 }));
scene.add(shM);

// ---------- location scenery ----------
const pine = (x, z, s, g) => {
  mk(YG, 0x4d331f, x, 0.6 * s, z, 0.2 * s, 1.2 * s, 0.2 * s, g);
  [[1.8, 2.4, 0.9, 0x1a5238], [1.4, 2.2, 2.3, 0x246142], [1, 2, 3.6, 0xdbebf5]].forEach(([r, h, y, c]) =>
    mk(CG, c, x, (y + h / 2) * s, z, r * s, h * s, r * s, g)
  );
};

const tree = (x, z, s, c, g) => {
  mk(YG, 0x593d24, x, 1.2 * s, z, 0.25 * s, 2.4 * s, 0.25 * s, g);
  mk(SG, c, x, 3.1 * s, z, 1.6 * s, 1.7 * s, 1.6 * s, g);
  mk(SG, c + 0x0a1a0a, x, 4.3 * s, z, 1.1 * s, 1.1 * s, 1.1 * s, g);
};

const SC = {
  desert(s, g) {
    const h = 3 + R() * 6,
      bx = s * (9 + ((R() * 4) | 0));
    mk(BG, [0xd9b380, 0xc7a470, 0xb5946a][(R() * 3) | 0], bx, h / 2, 0, 3, h, 3, g);
    if (R() < 0.5) mk(SG, 0xf2bf26, bx, h + 0.2, 0, 1.3, 1.2, 1.3, g);
    mk(BG, 0xffd966, bx - s * 1.52, h * 0.6, 0, 0.05, 0.8, 0.6, g, 0xffd966);
    mk(YG, 0x66401a, s * 6.9, 1.5, 3, 0.15, 3, 0.15, g);
    [[0.7, 0], [-0.7, 0], [0, 0.7], [0, -0.7]].forEach(([a, b]) => mk(SG, 0x1a8026, s * 6.9 + a, 3.1, 3 + b, 0.9, 0.22, 0.9, g));
    mk(SG, 0x1a7326, s * 6.9, 3.3, 3, 0.4, 0.4, 0.4, g);
  },
  city(s, g) {
    const h = 9 + R() * 24,
      w = 3 + R() * 2,
      nc = [0x33e6ff, 0xff40cc, 0xb366ff][(R() * 3) | 0];
    const m = new THREE.Mesh(BG, new THREE.MeshLambertMaterial({ color: 0x14141f, emissive: 0xffffff, emissiveMap: wt }));
    m.position.set(s * (10 + w / 2), h / 2, 0);
    m.scale.set(w, h, 4.5);
    g.add(m);
    mk(BG, nc, s * (10 + w / 2) - (s * w) / 2, h / 2, 2, 0.12, h, 0.12, g, nc);
    if (R() < 0.5) mk(BG, nc, s * (10 + w / 2), h + 0.7, 0, w * 0.7, 1.2, 0.3, g, nc);
    mk(YG, 0x222233, s * 5.9, 1.2, 0, 0.07, 2.4, 0.07, g);
    mk(SG, nc, s * 5.9, 2.5, 0, 0.22, 0.22, 0.22, g, nc);
  },
  snow(s, g) {
    pine(s * (8 + R() * 5), R() * 5, 0.9 + R() * 1.1, g);
    pine(s * (13 + R() * 6), 6 - R() * 4, 0.9 + R() * 1.1, g);
    mk(SG, 0xf5f8ff, s * (7.4 + R() * 2), 0.25, 3, 1.4, 0.35, 1, g);
  },
  forest(s, g) {
    const c = [0x1f7330, 0x2e8538, 0x1a6140, 0x4d8c26][(R() * 4) | 0];
    tree(s * (8 + R() * 5), 1, 0.9 + R() * 0.7, c, g);
    tree(s * (13 + R() * 6), 5, 1 + R() * 0.7, c, g);
    if (R() < 0.4) mk(SG, 0x737378, s * 7.2, 0.4, 4, 0.85, 0.5, 0.7, g);
  }
};

let sceneG = [],
  bd = new THREE.Group(),
  wp,
  wpos = new Float32Array(1200);
scene.add(bd);

wp = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({ size: 0.14, transparent: true, opacity: 0.8 }));
wp.frustumCulled = false;
scene.add(wp);

const FN = 700,
  fp = [],
  fpos = new Float32Array(FN * 3),
  fcol = new Float32Array(FN * 3),
  fgeo = new THREE.BufferGeometry();
fgeo.setAttribute('position', new THREE.BufferAttribute(fpos, 3));
fgeo.setAttribute('color', new THREE.BufferAttribute(fcol, 3));

const fpt = new THREE.Points(
  fgeo,
  new THREE.PointsMaterial({ size: 0.8, vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, fog: false })
);
fpt.frustumCulled = false;
scene.add(fpt);

const fLight = new THREE.PointLight(0xff8a30, 0, 14);
scene.add(fLight);
const ray = new THREE.Raycaster(),
  hm = new THREE.Vector2();

const rx = (x, z) => x + off(z),
  hand = () => (S.view == 1 ? [S.px + 0.35, S.py + (S.slide > 0 ? 0.6 : 1.45), -0.5] : [S.px + 0.5, S.py + (S.slide > 0 ? 0.6 : 1.25), -0.4]);

function burst(x, y, z, n) {
  for (let i = 0; i < n && fp.length < FN; i++)
    fp.push({ x, y, z, vx: rr(-4, 4), vy: rr(1, 6), vz: rr(-4, 4), l: 0.5, L: 0.5 });
}

// 3D Raycasting Aimer
function aim() {
  const [hx, hy] = hand();
  hm.set((S.mx / innerWidth) * 2 - 1, 1 - (S.my / innerHeight) * 2);
  cam.updateMatrixWorld();
  ray.setFromCamera(hm, cam);
  const r = ray.ray;
  let T = null;
  if (r.direction.y < -1e-3) {
    const t = (hy - r.origin.y) / r.direction.y;
    if (t > 0) T = r.origin.clone().addScaledVector(r.direction, t);
  }
  if (!T && r.direction.z < -1e-3) {
    T = r.origin.clone().addScaledVector(r.direction, (-25 - r.origin.z) / r.direction.z);
  }
  if (!T) return [0, 0, -1];
  const h = hand();
  let v = [T.x - h[0], T.y - h[1], T.z - h[2]];
  if (Math.hypot(...v) < 1.5) v = [r.direction.x, r.direction.y, r.direction.z];
  const yaw = cl(Math.atan2(v[0], -v[2]) * 1.2, -1.48, 1.48),
    pit = cl(Math.atan2(v[1], Math.hypot(v[0], v[2])), -0.8, 1.05);
  return [Math.sin(yaw) * Math.cos(pit), Math.sin(pit), -Math.cos(yaw) * Math.cos(pit)];
}

// Tuned Flame Hitbox
function cone(x, y, z) {
  const [hx, hy, hz] = hand(),
    d = S.aim || [0, 0, -1],
    vx = x - hx,
    vy = y - hy,
    vz = z - hz,
    al = vx * d[0] + vy * d[1] + vz * d[2];
  if (al < 0.6 || al > 15.5) return false;
  const r = 0.9 + al * 0.11;
  return (vx * vx + vy * vy + vz * vz - al * al) < (r * r);
}

function mkDrone() {
  const g = new THREE.Group(), r = new THREE.Group();
  mk(SG, 0x383d4d, 0, 0, 0, 0.5, 0.3, 0.5, g);
  mk(SG, 0xff1a1a, 0, 0, 0.4, 0.14, 0.14, 0.14, g, 0xff0000);
  mk(BG, 0x262629, 0, -0.3, 0, 0.3, 0.12, 0.5, g);
  r.position.y = 0.4;
  mk(BG, 0xbfbfc7, 0, 0, 0, 1.5, 0.04, 0.12, r);
  mk(BG, 0xbfbfc7, 0, 0, 0, 0.12, 0.04, 1.5, r);
  g.add(r);
  g.userData.r = r;
  scene.add(g);
  return g;
}

const ebG = new THREE.SphereGeometry(1, 10, 8),
  ebM = new THREE.MeshBasicMaterial({ color: 0xff1010, fog: false });

function eBullet(o, s) {
  o.m = new THREE.Mesh(ebG, ebM);
  o.m.scale.setScalar(s);
  scene.add(o.m);
  S.eb.push(o);
}

const PAL = [
    { sky: 0x8cc7f2, top: 0x2a66d9, li: 1, sun: 0xfff2c0, sy: 60, n: 0 },
    { sky: 0xf79954, top: 0x4d3385, li: 0.85, sun: 0xffd070, sy: 30, n: 0 },
    { sky: 0x080a21, top: 0x01010a, li: 0.35, sun: 0xdfe6ff, sy: 50, n: 1 }
  ],
  WT = [
    [5, 1, 0, 3],
    [2, 5, 1, 0],
    [2, 0, 6, 0],
    [3, 5, 0, 0]
  ],
  TN = ['Day', 'Dusk', 'Night', 'Auto cycle'],
  WNN = ['Clear', 'Rain', 'Snow', 'Sandstorm'],
  WMN = ['Auto'].concat(WNN);

const hc = document.createElement('canvas');
hc.width = hc.height = 128;
const hx = hc.getContext('2d'),
  hgr = hx.createRadialGradient(64, 64, 0, 64, 64, 64);
hgr.addColorStop(0, 'rgba(255, 255, 255, 0.55)');
hgr.addColorStop(1, 'rgba(255, 255, 255, 0)');
hx.fillStyle = hgr;
hx.fillRect(0, 0, 128, 128);

const halo = new THREE.Sprite(
  new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(hc), blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, fog: false })
);
halo.scale.set(130, 130, 1);

let sunM, bmat;
const stars = new THREE.Points(
  (() => {
    const g = new THREE.BufferGeometry(),
      p = [];
    for (let i = 0; i < 190; i++) p.push(rr(-230, 230), rr(20, 190), -245);
    g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
    return g;
  })(),
  new THREE.PointsMaterial({ color: 0xffffff, size: 2, sizeAttenuation: false, transparent: true, opacity: 0, fog: false, depthWrite: false })
);
scene.add(stars);

function pickWx(ex) {
  const w = WT[S.li],
    c = [0, 1, 2, 3].filter(i => i != ex && w[i] > 0);
  let r = R() * c.reduce((a, i) => a + w[i], 0);
  for (const i of c) {
    r -= w[i];
    if (r <= 0) return i;
  }
  return c[0] || 0;
}

function wxSet() {
  wp.material.color.set([0, 0xaec8ff, 0xffffff, 0xd9b36b][S.wx]);
  wp.visible = !!S.wx;
  for (let i = 0; i < 1200; i += 3) {
    wpos[i] = rr(-16, 16);
    wpos[i + 1] = rr(0, 14);
    wpos[i + 2] = rr(-45, 8);
  }
}

function wxTick(dt) {
  if (S.wmode == 0) {
    S.wt -= dt;
    if (S.wt <= 0) {
      S.wt = rr(25, 50);
      S.wn = pickWx(S.wn);
    }
  } else S.wn = S.wmode - 1;
  if (S.wx != S.wn) {
    S.wk -= dt / 1.5;
    if (S.wk <= 0 || S.wx == 0) {
      S.wx = S.wn;
      S.wk = 0;
      wxSet();
    }
  } else S.wk = Math.min(1, S.wk + dt / 3);
}

function envUpd() {
  const L = LC();
  let A, B, f = 0;
  if (S.tod < 3) A = B = PAL[S.tod];
  else {
    const ph = (S.clock % 120) / 30,
      i = ph | 0;
    f = ph - i;
    f = f * f * (3 - 2 * f);
    A = PAL[[0, 1, 2, 1][i]];
    B = PAL[[0, 1, 2, 1][(i + 1) % 4]];
  }
  const nb = L.kind == 'city' ? 0.85 : 0,
    L2 = (a, b) => a + (b - a) * f,
    col = k => new THREE.Color(A[k]).lerp(new THREE.Color(B[k]), f).lerp(new THREE.Color(PAL[2][k]), nb),
    n = Math.max(nb, L2(A.n, B.n)),
    w = S.wx ? S.wk : 0,
    grey = new THREE.Color([0, 0x737880, 0xccd4e0, 0xc79e66][S.wx]).multiplyScalar(0.25 + 0.75 * (1 - n)),
    sky = col('sky').lerp(new THREE.Color(L.sky), 0.35).lerp(grey, 0.65 * w),
    top = col('top').lerp(new THREE.Color(L.top), 0.35).lerp(sky, 0.7 * w),
    li = L2(A.li, B.li) * (1 - nb) + PAL[2].li * nb,
    br = 0.25 + 0.75 * (1 - n),
    fz = 1 - w * (1 - [1, 0.7, 0.75, 0.4][S.wx]);

  scene.fog.color.copy(sky);
  scene.fog.near = 25 * L.fg * fz;
  scene.fog.far = 105 * L.fg * fz;
  document.body.style.background = 'linear-gradient(#' + top.getHexString() + ',#' + sky.getHexString() + ' 55%)';
  hemi.intensity = L.hi * li;
  sunL.intensity = L.si * li * (1 - 0.4 * w);
  gm.color.setHex(L.gr).multiplyScalar(br);
  rm.color.setHex(L.rd).multiplyScalar(br);
  bmat.color.setHex(L.far).multiplyScalar(br).lerp(sky, 0.42);
  sunM.material.color.copy(col('sun').lerp(sky, 0.75 * w));
  sunM.position.y = L2(A.sy, B.sy) + 10;
  sunM.scale.setScalar(14 - 5 * n);
  stars.material.opacity = n * (1 - 0.85 * w);
  wp.material.opacity = 0.8 * w;
  halo.position.set(sunM.position.x, sunM.position.y, -188);
  halo.material.color.copy(sunM.material.color);
  halo.material.opacity = 1 - 0.85 * w;
}

function applyLoc() {
  const L = LC();
  scene.fog = new THREE.Fog(L.sky, 25 * L.fg, 105 * L.fg);
  document.body.style.background = `linear-gradient(${css(L.top)},${css(L.sky)} 55%)`;
  hemi.color.set(L.hs);
  hemi.groundColor.set(L.hg);
  hemi.intensity = L.hi;
  sunL.color.set(L.sc);
  sunL.intensity = L.si;
  gm.color.set(L.gr);
  rm.color.set(L.rd);
  em.color.set(L.ed);
  glm.color.set(L.ed);
  dm.color.set(L.dc);
  S.wx = S.wn = S.wmode ? S.wmode - 1 : pickWx(-1);
  S.wk = 1;
  S.wt = rr(25, 50);
  wxSet();

  for (let i = 0; i < 1200; i += 3) {
    wpos[i] = rr(-16, 16);
    wpos[i + 1] = rr(0, 14);
    wpos[i + 2] = rr(-45, 8);
  }
  wp.geometry.setAttribute('position', new THREE.BufferAttribute(wpos, 3));
  sceneG.forEach(g => scene.remove(g));
  sceneG = [];

  for (let i = 0; i < 14; i++) {
    for (const s of [-1, 1]) {
      const g = new THREE.Group();
      SC[L.kind](s, g);
      if (i % 2 == 0 && L.kind != 'city') {
        const lc = [0xffe666, 0, 0xb3d9ff, 0xffd980][S.li];
        mk(BG, 0x332619, s * 5.9, 1.2, 0, 0.1, 2.4, 0.1, g);
        mk(SG, lc, s * 5.9, 2.5, 0, 0.22, 0.22, 0.22, g, lc);
      }
      g.position.z = 10 - i * 12;
      scene.add(g);
      sceneG.push(g);
    }
  }

  while (bd.children.length) bd.remove(bd.children[0]);
  const fc = new THREE.Color(L.far).lerp(new THREE.Color(L.sky), 0.42),
    bm = (bmat = new THREE.MeshBasicMaterial({ color: fc, fog: false }));

  for (let i = 0; i < 30; i++) {
    const x = -290 + i * 20 + rr(-7, 7),
      a = R(),
      b = R();
    let m;
    if (L.kind == 'city') {
      m = new THREE.Mesh(BG, bm);
      const h = 25 + b * 60;
      m.scale.set(8 + a * 10, h, 9);
      m.position.set(x, h / 2, -165);
    } else if (L.kind == 'snow') {
      m = new THREE.Mesh(CG, bm);
      const h = 44 + b * 34;
      m.scale.set(28 + a * 20, h, 28 + a * 20);
      m.position.set(x, h / 2, -165);
    } else if (L.kind == 'desert' && i % 5 == 0) {
      m = new THREE.Mesh(CG, bm);
      m.scale.set(26, 28 + b * 12, 26);
      m.position.set(x, 14, -165);
    } else {
      m = new THREE.Mesh(SG, bm);
      m.scale.set(30 + a * 22, L.kind == 'forest' ? 14 + b * 10 : 10, 18);
      m.position.set(x, -1, -165);
    }
    bd.add(m);
  }

  sunM = new THREE.Mesh(SG, new THREE.MeshBasicMaterial({ color: L.sun, fog: false }));
  sunM.scale.set(14, 14, 14);
  sunM.position.set(-38, 60, -190);
  bd.add(sunM);
  bd.add(halo);
  document.documentElement.style.setProperty('--a', css(L.ac));
  envUpd();
}

// ---------- gameplay ----------
function mkObs(k, lane, z) {
  const g = new THREE.Group();
  if (k == 'barrier') {
    mk(BG, 0xf28019, 0, 0.45, 0, 1.9, 0.9, 0.5, g);
    mk(BG, 0xffffff, 0, 0.45, 0, 1.95, 0.2, 0.55, g);
  } else if (k == 'beam') {
    mk(BG, 0x40261a, -0.95, 1.15, 0, 0.2, 2.3, 0.3, g);
    mk(BG, 0x40261a, 0.95, 1.15, 0, 0.2, 2.3, 0.3, g);
    mk(BG, 0xb3331a, 0, 1.65, 0, 2.1, 1.1, 0.5, g);
    mk(BG, 0xf2bf26, 0, 1.65, 0, 2.15, 0.2, 0.55, g);
  } else {
    mk(BG, 0x8c5c2e, 0, 0.9, 0, 1.7, 1.8, 1.2, g);
    mk(BG, 0x4d2e14, 0, 0.9, 0, 1.75, 0.2, 1.25, g);
  }
  scene.add(g);
  return { k, x: (lane - 2) * LW, z, g };
}

const itC = [0x4db3ff, 0xff8019, 0x33e64d],
  torG = new THREE.TorusGeometry(0.6, 0.05, 8, 20);

function mkItem(k, x, z) {
  const g = new THREE.Group();
  mk(SG, itC[k], 0, 0, 0, 0.35, 0.35, 0.35, g, itC[k]);
  mk(torG, 0xffffff, 0, 0, 0, 1, 1, 1, g, 0x888888).rotation.x = 1.2;
  scene.add(g);
  return { k, x, z, g };
}

const coinG = new THREE.CylinderGeometry(0.35, 0.35, 0.08, 16);

function spawn() {
  const d = DF(),
    z = -100,
    ln = [0, 1, 2, 3, 4].sort(() => R() - 0.5),
    n = d.nob[(R() * 4) | 0];

  for (let i = 0; i < n; i++) S.obs.push(mkObs(['barrier', 'beam', 'crate'][(R() * 3) | 0], ln[i], z));

  const fr = ln.slice(3),
    cx = (fr[(R() * fr.length) | 0] - 2) * LW,
    cn = 3 + ((R() * 4) | 0);

  for (let i = 0; i < cn; i++) {
    const g = new THREE.Group();
    mk(coinG, 0xf2bf26, 0, 0, 0, 1, 1, 1, g, 0x6a4a00).rotation.x = Math.PI / 2;
    scene.add(g);
    S.cns.push({ x: cx, z: z - i * 2.2, g });
  }

  if (R() < d.gc && S.gs.length < 3)
    S.gs.push({ x: (ln[n + ((R() * (5 - n)) | 0)] - 2) * LW, z: z - 6, cd: rr(0.5, 1.5), g: figure(0x1f1f26, 0x0d0d12, 0x806659, 0, 1) });

  if (S.time > d.dt && S.dr.length < d.dm && R() < Math.min(d.dcap, d.dp + S.time * 0.003))
    S.dr.push({ x: (ln[n + ((R() * (5 - n)) | 0)] - 2) * LW, y: 3.2, z: z - 12, cd: rr(0.8, 1.6), ph: rr(0, 6.28), rot: 0, g: mkDrone() });

  if (R() < [0.2, 0.12, 0.08][S.di]) S.it.push(mkItem((R() * 3) | 0, (ln[n + ((R() * (5 - n)) | 0)] - 2) * LW, z - 10));
}

function hurt(n) {
  if (S.inv > 0) return;
  S.inv = 1;
  S.shake = 0.5;
  if (S.shield) {
    S.shield = 0;
    sfx(500, 80);
    burst(S.px, 1, 0, 16);
    return;
  }
  sfx(180, 140);
  burst(S.px, 1, 0, 12);
  S.hp -= Math.max(1, Math.round(n * DF().dmg));
  S.chain = 0;
  $('fl').style.opacity = 0.4;
  if (S.hp <= 0) {
    S.st = 'over';
    S.fire = 0;
    const i = S.di;
    if (S.score > hi[i]) {
      hi[i] = S.score | 0;
      try {
        localStorage.setItem('dd3', JSON.stringify(hi));
      } catch (e) {}
    }
    showOver();
  }
}

function shoot() {
  if (S.st != 'play' || S.cd > 0) return;
  const [hx, hy, hz] = hand(),
    a = S.aim || [0, 0, -1],
    m = new THREE.Mesh(SG, new THREE.MeshBasicMaterial({ color: 0xffee55 }));
  m.scale.setScalar(0.22);
  scene.add(m);
  S.bl.push({ x: hx, y: hy, z: hz, vx: a[0] * 55, vy: a[1] * 55, vz: a[2] * 55, m });
  S.cd = S.rapid > 0 ? 0.1 : 0.28;
  sfx(720, 45);
}

function clr() {
  for (const a of [S.obs, S.cns, S.gs, S.bl, S.dr, S.eb, S.it]) {
    for (const e of a) scene.remove(e.g || e.m);
  }
  S.obs = [];
  S.cns = [];
  S.gs = [];
  S.bl = [];
  S.dr = [];
  S.eb = [];
  S.it = [];
  fp.length = 0;
  fLight.intensity = 0;
}

function start() {
  const d = DF();
  clr();
  const startSpd = Math.max(7.5, d.v0);
  Object.assign(S, {
    st: 'play', time: 0, speed: startSpd, target: startSpd, lane: 2, px: 0, py: 0, vy: 0,
    slide: 0, hp: d.hp, score: 0, coins: 0, kills: 0, chain: 0, inv: 0, cd: 0,
    next: S.D + 20, fire: 0, fuel: 100, heat: 0, shield: 0, rapid: 0, shake: 0
  });
  $('ov').style.display = 'none';
  $('hud').style.display = 'block';
  if (isMobile) $('bv').style.display = 'flex';
}

function avoid(e, dt, dz) {
  for (const o of S.obs) {
    if (!o.dead && Math.abs(o.z - e.z) < dz && Math.abs(o.x - e.x) < 1.9) {
      const k = e.x >= o.x ? 1 : -1;
      let nx = cl(e.x + k * 5 * dt, -4.4, 4.4);
      if (nx == e.x) nx = cl(e.x - k * 5 * dt, -4.4, 4.4);
      e.x = nx;
    }
  }
}

function upd(dt) {
  S.t += dt;
  S.clock += dt;
  wxTick(dt);
  S.envT -= dt;
  if (S.envT <= 0) {
    S.envT = 0.1;
    envUpd();
  }
  const d = DF();
  $('fl').style.opacity = Math.max(0, $('fl').style.opacity - dt * 1.5);

  if (S.st == 'menu') {
    S.D += 5 * dt;
    S.phase += 4 * dt;
    S.speed = 5;
  } else if (S.st == 'play') {
    S.time += dt;

    // Lowest speed starts at 30 km/h (7.5 raw) and climbs smoothly over time towards top speed (d.vmax)
    const baseMin = 7.5; // 7.5 * 4 = 30 km/h
    const vmin = Math.min(baseMin + S.time * d.vg, d.vmax);

    // Strict clamp: target can never fall below the dynamic climbing minimum floor (vmin)
    S.target = cl(S.target, vmin, d.vmax);

    // Smooth transition towards target speed
    S.speed += (S.target - S.speed) * Math.min(1, 3 * dt);

    // Strict speed floor: game speed will never run under vmin
    if (S.speed < vmin) {
      S.speed = vmin;
    }

    const sp = S.speed;
    S.D += sp * dt;
    S.score += (sp * dt * 0.2 * sp) / 14;
    S.phase += sp * dt * 0.7;
    S.px += ((S.lane - 2) * LW - S.px) * Math.min(1, 12 * dt);

    if (S.py > 0 || S.vy > 0) {
      S.vy -= 24 * dt;
      S.py = Math.max(0, S.py + S.vy * dt);
      if (!S.py) S.vy = 0;
    }

    S.slide = Math.max(0, S.slide - dt);
    S.inv = Math.max(0, S.inv - dt);
    S.cd -= dt;
    S.rapid = Math.max(0, S.rapid - dt);
    S.shake = Math.max(0, S.shake - dt * 1.5);

    if (S.D >= S.next) {
      spawn();
      S.next = S.D + Math.max(d.gap[1], d.gap[0] - S.time * d.gap[2]);
    }

    const top = S.py + (S.slide > 0 ? 0.9 : 1.9);

    for (const o of S.obs) {
      o.z += sp * dt;
      if (!o.dead && Math.abs(o.z) < 1 && Math.abs(o.x - S.px) < 1 && ((o.k == 'barrier' && S.py < 0.9) || (o.k == 'crate' && S.py < 1.8) || (o.k == 'beam' && top > 1.1 && S.py < 2.2))) {
        o.dead = 1;
        hurt(20);
      }
      if (o.z > 6) o.dead = 1;
    }

    for (const c of S.cns) {
      c.z += sp * dt;
      if (Math.abs(c.z) < 1 && Math.abs(c.x - S.px) < 1 && S.py < 2.2) {
        c.dead = 1;
        S.coins++;
        S.chain++;
        S.score += 10 * mult();
        sfx(1300, 30);
        burst(c.x, 1, c.z, 4);
      }
      if (c.z > 6) c.dead = 1;
    }

    for (const it of S.it) {
      it.z += sp * dt;
      if (!it.dead && Math.abs(it.z) < 1.2 && Math.abs(it.x - S.px) < 1.2) {
        it.dead = 1;
        if (it.k == 0) S.shield = 1;
        else if (it.k == 1) S.rapid = 8;
        else S.hp = Math.min(d.hp, S.hp + [40, 30, 25][S.di]);
        sfx(900, 90);
        burst(it.x, 1, it.z, 14);
      }
      if (it.z > 6) it.dead = 1;
    }

    for (const g of S.gs) {
      g.z += sp * 0.55 * dt;
      if (g.z > -30) {
        const nx = g.x + cl(S.px - g.x, -1, 1) * 1.6 * dt;
        if (!S.obs.some(o => !o.dead && Math.abs(o.z - g.z) < 3 && Math.abs(o.x - nx) < 1.9)) g.x = nx;
      }
      avoid(g, dt, 3);
      g.cd -= dt;
      if (g.z > -60 && g.z < -8 && g.cd <= 0) {
        eBullet({ k: 'g', x: g.x, z: g.z + 1 }, 0.28);
        g.cd = rr(1.3, 2.2) * d.ecd;
      }
      if (Math.abs(g.z) < 1.2 && Math.abs(g.x - S.px) < 1.2) {
        g.dead = 1;
        hurt(30);
      }
      if (g.z > 6) g.dead = 1;
    }

    S.aim = aim();
    const hd = hand(),
      kill = (e, pts, x, y) => {
        e.dead = 1;
        S.kills++;
        S.chain++;
        S.score += pts * mult();
        burst(x, y, e.z, 16);
        sfx(pts > 60 ? 450 : 700, pts > 60 ? 80 : 60);
      };

    if (S.heat && S.fuel > 25) S.heat = 0;

    if (S.fire && !S.heat) {
      S.fuel -= 36 * dt;
      if (S.fuel <= 0) {
        S.fuel = 0;
        S.heat = 1;
      }
      for (let i = 0; i < 7 && fp.length < FN; i++) {
        const L = rr(0.45, 0.65),
          v = rr(22, 27),
          a = S.aim;
        fp.push({ x: hd[0], y: hd[1], z: hd[2], vx: a[0] * v + rr(-1.5, 1.5), vy: a[1] * v + rr(-1.0, 1.0), vz: a[2] * v + rr(-1.5, 1.5), l: L, L });
      }

      for (const o of S.obs) {
        const X = rx(o.x, o.z),
          cy = { crate: 0.9, barrier: 0.45, beam: 1.5 }[o.k];
        if (!o.dead && cone(X, cy, o.z)) {
          o.burn = (o.burn || 0) + dt * 2.2;
          burst(X, 0.8, o.z, 2);
          if (o.burn > { crate: 0.25, barrier: 0.35, beam: 0.45 }[o.k]) {
            o.dead = 1;
            S.score += 15 * mult();
            burst(X, 1, o.z, 18);
            sfx(380, 70);
          }
        }
      }

      for (const g of S.gs) {
        const X = rx(g.x, g.z);
        if (!g.dead && cone(X, 1.1, g.z)) {
          g.burn = (g.burn || 0) + dt * 2.4;
          burst(X, 1.2, g.z, 2);
          if (g.burn > 0.3) kill(g, 50, X, 1.2);
        }
      }

      for (const r of S.dr) {
        const X = rx(r.x, r.z);
        if (!r.dead && cone(X, r.y, r.z)) {
          r.burn = (r.burn || 0) + dt * 2.4;
          burst(X, r.y, r.z, 2);
          if (r.burn > 0.28) kill(r, 75, X, r.y);
        }
      }
    } else {
      S.fuel = Math.min(100, S.fuel + 15 * dt);
    }

    fLight.intensity = S.fire && !S.heat ? 2.5 : 0;
    fLight.position.set(hd[0], hd[1] + 0.3, hd[2] - 1);

    for (const b of S.bl) {
      for (let q = 0; q < 3 && !b.dead; q++) {
        b.x += (b.vx * dt) / 3;
        b.y += (b.vy * dt) / 3;
        b.z += (b.vz * dt) / 3;
        for (const o of S.obs) {
          if (o.k == 'crate' && !o.dead && (rx(o.x, o.z) - b.x) ** 2 + (0.9 - b.y) ** 2 + (o.z - b.z) ** 2 < 1.4) {
            o.dead = b.dead = 1;
            S.score += 20 * mult();
            burst(rx(o.x, o.z), 1, o.z, 16);
          }
        }
        for (const g of S.gs) {
          if (!g.dead && (rx(g.x, g.z) - b.x) ** 2 + (1.1 - b.y) ** 2 + (g.z - b.z) ** 2 < 1.2) {
            b.dead = 1;
            kill(g, 50, rx(g.x, g.z), 1.2);
          }
        }
        for (const r of S.dr) {
          if (!r.dead && (rx(r.x, r.z) - b.x) ** 2 + (r.y - b.y) ** 2 + (r.z - b.z) ** 2 < 1.3) {
            b.dead = 1;
            kill(r, 75, rx(r.x, r.z), r.y);
          }
        }
      }
      if (b.z < -110 || b.y < 0 || b.y > 40 || Math.abs(b.x) > 60) b.dead = 1;
    }

    for (const r of S.dr) {
      r.z += sp * 0.5 * dt;
      r.x += cl(S.px - r.x, -1, 1) * 2.2 * dt;
      if (r.y < 2.8) avoid(r, dt, 3);
      r.rot += 15 * dt;
      r.cd -= dt;
      r.y = r.z > -22 ? r.y + (1.45 - r.y) * Math.min(1, 1.2 * dt) : 3.2 + 0.25 * Math.sin(S.t * 3 + r.ph);
      if (r.z > -55 && r.z < -10 && r.cd <= 0) {
        const X = rx(r.x, r.z),
          tx = S.px - X,
          ty = S.py + 0.9 - r.y,
          tz = -r.z,
          n = Math.hypot(tx, ty, tz) || 1;
        eBullet({ k: 'd', x: X, y: r.y, z: r.z, vx: (tx / n) * 26, vy: (ty / n) * 26, vz: (tz / n) * 26 }, 0.32);
        r.cd = rr(1.4, 2.2) * d.ecd;
      }
      if (!r.dead && Math.abs(r.z) < 1.2 && Math.abs(r.x - S.px) < 1.1 && r.y > S.py - 0.3 && r.y < top + 0.3) {
        r.dead = 1;
        burst(S.px, r.y, 0, 16);
        hurt(25);
      }
      if (r.z > 6) r.dead = 1;
    }

    for (const b of S.eb) {
      if (b.k == 'd') {
        b.x += b.vx * dt;
        b.y += b.vy * dt;
        b.z += b.vz * dt;
        const cy = S.py + (S.slide > 0 ? 0.45 : 0.95);
        if ((b.x - S.px) ** 2 + (b.y - cy) ** 2 + b.z ** 2 < 0.8) {
          b.dead = 1;
          hurt(12);
        }
        if (b.z > 8 || b.y < 0) b.dead = 1;
      } else {
        b.z += (sp + 22) * dt;
        if (Math.abs(b.z) < 0.8 && Math.abs(b.x - S.px) < 0.8 && top > 0.95 && S.py < 1.45) {
          b.dead = 1;
          hurt(15);
        }
        if (b.z > 8) b.dead = 1;
      }
    }

    for (const k of ['obs', 'cns', 'gs', 'bl', 'dr', 'eb', 'it']) {
      S[k] = S[k].filter(e => {
        if (e.dead) scene.remove(e.g || e.m);
        return !e.dead;
      });
    }
  }

  road();
  S.roll += (cl(curv(S.D + 25) * 18, -0.08, 0.08) - S.roll) * Math.min(1, 4 * dt);
  draw(dt);
}

const slc = $('sl'),
  sx = slc.getContext('2d');

function slines(sp) {
  sx.clearRect(0, 0, slc.width, slc.height);
  if (S.st != 'play' || sp < 22) return;
  const w = slc.width,
    h = slc.height,
    k = Math.min(1, (sp - 22) / 20);
  sx.lineWidth = 1.5;
  for (let i = 0; i < 10 + 20 * k; i++) {
    const an = R() * 6.283,
      c = Math.cos(an),
      n = Math.sin(an),
      r0 = rr(0.38, 0.55),
      r1 = rr(0.6, 0.9),
      x0 = w / 2 + c * w * r0,
      y0 = h / 2 + n * h * r0,
      x1 = w / 2 + c * w * r1,
      y1 = h / 2 + n * h * r1,
      g = sx.createLinearGradient(x0, y0, x1, y1);
    g.addColorStop(0, 'rgba(255,255,255,0)');
    g.addColorStop(1, 'rgba(255,255,255,' + 0.22 * k + ')');
    sx.strokeStyle = g;
    sx.beginPath();
    sx.moveTo(x0, y0);
    sx.lineTo(x1, y1);
    sx.stroke();
  }
}

function draw(dt) {
  const sp = S.speed,
    t = S.t;
  for (const r of rib) {
    for (let k = 0; k < NS; k++) {
      const z = 8 - 2 * k,
        o = off(z),
        i = k * 6;
      r.p[i] = o + r.xl;
      r.p[i + 1] = r.y;
      r.p[i + 2] = z;
      r.p[i + 3] = o + r.xr;
      r.p[i + 4] = r.y;
      r.p[i + 5] = z;
    }
    r.g.attributes.position.needsUpdate = true;
  }
  bt.offset.y = S.D / 8;
  let n = 0;
  for (let j = 0; j < 26; j++) {
    const z = 6 - j * 6 + (S.D % 6),
      o = off(z);
    for (const lx of [-3.3, -1.1, 1.1, 3.3]) {
      dum.position.set(o + lx, 0.03, z);
      dum.scale.set(0.12, 0.02, 2.5);
      dum.updateMatrix();
      dash.setMatrixAt(n++, dum.matrix);
    }
  }
  dash.instanceMatrix.needsUpdate = true;

  for (const g of sceneG) {
    g.position.z += sp * dt;
    if (g.position.z > 24) g.position.z -= 168;
    g.position.x = off(g.position.z);
  }

  pl.position.set(S.px, S.py + (S.slide > 0 ? 0.35 : 0) + (S.py == 0 && S.st != 'over' ? Math.abs(Math.sin(S.phase)) * 0.07 : 0), 0);
  pl.rotation.x = S.slide > 0 ? -1.2 : 0;
  pl.rotation.z = cl((S.px - (S.lane - 2) * LW) * 0.12, -0.3, 0.3);
  shM.visible = !!S.shield && S.view != 1;
  shd.visible = S.view != 1;
  shM.position.set(S.px, S.py + 1, 0);
  shM.scale.setScalar(1.4 + 0.05 * Math.sin(t * 6));
  swing(pl, S.phase);
  pl.visible = S.view != 1 && !(S.st == 'play' && S.inv > 0 && ((t * 20) | 0) % 2);
  shd.position.set(S.px, 0.05, 0);
  shd.scale.setScalar(1 / (1 + S.py * 0.3));

  for (const o of S.obs) o.g.position.set(o.x + off(o.z), 0, o.z);
  for (const c of S.cns) {
    c.g.position.set(c.x + off(c.z), 1 + 0.15 * Math.sin(t * 4 + c.z), c.z);
    c.g.rotation.y = t * 3;
  }
  for (const g of S.gs) {
    g.g.position.set(g.x + off(g.z), 0, g.z);
    swing(g.g, t * 8);
  }
  for (const it of S.it) {
    it.g.position.set(it.x + off(it.z), 1.1 + 0.2 * Math.sin(t * 3), it.z);
    it.g.rotation.y = t * 2;
  }
  for (const b of S.bl) b.m.position.set(b.x, b.y, b.z);
  for (const r of S.dr) {
    r.g.position.set(rx(r.x, r.z), r.y, r.z);
    r.g.userData.r.rotation.y = r.rot;
  }
  for (const b of S.eb) b.m.position.set(b.k == 'd' ? b.x : rx(b.x, b.z), b.k == 'd' ? b.y : 1.2, b.z);

  for (let i = fp.length - 1; i >= 0; i--) {
    const p = fp[i];
    p.l -= dt;
    if (p.l <= 0) {
      fp.splice(i, 1);
      continue;
    }
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.z += p.vz * dt;
  }

  fp.forEach((p, n) => {
    const k = p.l / p.L,
      i = n * 3;
    fpos[i] = p.x;
    fpos[i + 1] = p.y;
    fpos[i + 2] = p.z;
    fcol[i] = k;
    fcol[i + 1] = 0.25 + 0.55 * k * k;
    fcol[i + 2] = 0.05 * k;
  });
  fgeo.setDrawRange(0, fp.length);
  fgeo.attributes.position.needsUpdate = fgeo.attributes.color.needsUpdate = true;

  const isPlaying = S.st == 'play';
  $('mb').style.display = isMobile && isPlaying ? 'grid' : 'none';
  $('bv').style.display = isMobile && isPlaying ? 'flex' : 'none';
  rt.style.display = isPlaying && (S.mouse || isMobile) ? 'block' : 'none';
  document.body.classList.toggle('pl', !isMobile && isPlaying && !!S.mouse);

  if (S.wx) {
    const a = wp.geometry.attributes.position.array;
    for (let i = 0; i < a.length; i += 3) {
      if (S.wx == 1) {
        a[i + 1] -= 24 * dt;
      } else if (S.wx == 2) {
        a[i + 1] -= 2.2 * dt;
        a[i] += Math.sin(t * 1.5 + a[i + 2]) * 0.6 * dt;
      } else {
        a[i] += 16 * dt;
      }
      a[i + 2] += sp * 0.5 * dt;
      if (a[i + 1] < 0) a[i + 1] = 14;
      if (a[i + 2] > 8) a[i + 2] = -45;
      if (a[i] > 16) a[i] = -16;
    }
    wp.geometry.attributes.position.needsUpdate = true;
  }

  const V = S.view,
    sk = S.st == 'play' ? S.shake * 0.8 : 0,
    ey = S.py + (S.slide > 0 ? 0.9 : 1.75);
  cam.fov = [58, 92, 50][V] + Math.max(0, sp - 14) * 0.3;
  cam.updateProjectionMatrix();

  const E = [
      [S.px * 0.6, 4.3, 7.5],
      [S.px, ey, -0.2],
      [S.px * 0.4, 15, 9]
    ][V],
    C = [
      [S.px * 0.4 + off(-14) * 0.45, 1.4, -12],
      [S.px + off(-20) * 0.5, ey - 0.15, -20],
      [S.px * 0.4 + off(-9) * 0.3, 0, -9]
    ][V];

  cam.position.set(E[0] + rr(-sk, sk), E[1] + rr(-sk, sk) * 0.5, E[2]);
  cam.up.set(Math.sin(S.roll), Math.cos(S.roll), 0);
  cam.lookAt(C[0], C[1], C[2]);

  if (S.st != 'menu') {
    const d = DF(),
      h = cl(S.hp / d.hp, 0, 1),
      fr = cl(sp / d.vmax, 0, 1),
      baseMin = 7.5,
      vmin = Math.min(baseMin + S.time * d.vg, d.vmax);

    $('hf').style.width = Math.max(0, h) * 100 + '%';
    $('hf').style.background = 'rgb(' + ((242 - 165 * h) | 0) + ',' + ((64 + 166 * h) | 0) + ',' + ((51 + 80 * h) | 0) + ')';
    $('ht').textContent = 'HP  ' + Math.max(0, S.hp) + ' / ' + d.hp;
    $('ff').style.width = S.fuel + '%';
    $('ff').style.background = S.heat ? '#f04030' : '#ff9a20';

    $('ft').textContent = S.heat ? 'OVERHEATED' : (isMobile ? 'FLAME' : 'FLAME [G]');
    $('ft').style.color = S.heat ? '#ff5a40' : '#ffcc66';

    $('sv').textContent = S.score | 0;
    $('cn').innerHTML =
      '<i class=coin></i><b>' +
      S.coins +
      '</b><span>Best ' +
      hi[S.di] +
      '</span><small style="color:' +
      css(d.col) +
      '">' +
      d.n.toUpperCase() +
      ' &nbsp;|&nbsp; ' +
      LC().n.toUpperCase() +
      '</small>';
    $('cb').innerHTML = mult() > 1 ? 'COMBO x' + mult() + '<div><i style="width:' + (mult() >= 5 ? 100 : (S.chain % 5) * 20) + '%"></i></div>' : '';
    $('pu').innerHTML = (S.shield ? '<span class=pill style="background:#1a5290">SHIELD</span>' : '') + (S.rapid > 0 ? '<span class=pill style="background:#8c470d">RAPID FIRE ' + (S.rapid | 0) + 's</span>' : '');
    $('sfill').style.width = fr * 100 + '%';
    $('sfill').style.background = 'hsl(' + (195 - 180 * fr) + ',85%,58%)';
    $('smin').style.left = (vmin / d.vmax) * 100 + '%';
    $('st').textContent = ((sp * 4) | 0) + ' km/h';

    $('shint').style.display = isMobile ? 'none' : 'inline';

    const k = curv(S.D + 35);
    $('cv').innerHTML = Math.abs(k) > 7e-4 ? (k > 0 ? '<b>&#9654;&#9654;&#9654;</b> CURVE RIGHT' : 'CURVE LEFT <b>&#9664;&#9664;&#9664;</b>') : '';
  }

  if (!isMobile) {
    $('sbr').textContent =
      '[N] Time: ' + TN[S.tod] + '    [M] Weather: ' + WMN[S.wmode] + (S.wmode ? '' : ' (' + WNN[S.wx] + ')') + '    [V] View: ' + ['Chase', 'First-person', 'Overhead'][S.view] + '    [B] Menu';
  }
  slines(sp);
  ren.render(scene, cam);
}

// ---------- menus ----------
function menu() {
  S.st = 'menu';
  clr();
  $('hud').style.display = 'none';
  $('bv').style.display = 'none';
  $('ov').style.display = 'flex';

  const directionsText = isMobile
    ? `Swipe Left/Right: Switch Lanes | Swipe Up: Jump | Swipe Down: Slide<br>Tap / Drag: Aim & Shoot | Hold FLAME: Flamethrower | &#9650; / &#9660;: Speed<br>Eye Icon (Top Left): Viewpoint | Volume Buttons: Cycle Time & Weather`
    : `Arrows or A/D: Switch Lanes | Space / W: Jump | S: Slide<br>Mouse Aim + Left Click: Shoot | Hold G or Right-Click: Flamethrower | Q / E: Speed<br>V: Viewpoint | P: Pause | B: Menu | N: Time Cycle | M: Weather Cycle`;

  $('bx').innerHTML = `<h1>DICTATOR'S DASH</h1><small>3D WEB EDITION | ENDLESS RUNNER</small><h4>SELECT DIFFICULTY</h4><div class=row>${DIFF.map(
    (d, i) => `<button class="b ${i == S.di ? 'sel' : ''}" style="--a:${css(d.col)}" onclick="pickD(${i})">${d.n}<small>Best ${hi[i]}</small></button>`
  ).join('')}</div>
  <p style="color:${css(DF().col)}">${DF().d}</p><h4>SELECT LOCATION</h4><div class=row>${LOC.map(
    (l, i) =>
      `<button class="b card ${i == S.li ? 'sel' : ''}" style="--a:${css(l.ac)}" onclick="pickL(${i})"><i style="background:linear-gradient(${css(l.top)},${css(l.sky)} 60%,${css(l.gr)} 60%)"></i>${l.n}<small>${l.tag}</small></button>`
  ).join('')}</div>
  <p style="color:${css(LC().ac)}">${LC().d}</p><button class="b go" onclick="start()">START RUN</button>
  <small style="margin-top:12px;color:#a0aabf">${directionsText}</small>`;
  $('bx').style.setProperty('--a', css(LC().ac));
}

function pickD(i) {
  S.di = cl(i, 0, 2);
  menu();
}

function pickL(i) {
  S.li = (i + LOC.length) % LOC.length;
  applyLoc();
  menu();
}

function showOver() {
  $('ov').style.display = 'flex';
  $('bv').style.display = 'none';
  $('bx').style.setProperty('--a', '#ff4d40');
  const restartBtn = isMobile ? 'RESTART' : 'RESTART [R]';
  const menuBtn = isMobile ? 'MENU' : 'MENU [B]';
  $('bx').innerHTML = `<h1 style="color:#ff5040">GAME OVER</h1><p>Score ${S.score | 0} &nbsp; Coins ${S.coins} &nbsp; Guards downed ${S.kills}</p><p style="color:#f2bf26">Best (${DF().n}): ${hi[S.di]}</p><div class=row><button class="b go" onclick="start()">${restartBtn}</button><button class="b go" style="border-color:#ffc733;background:#4a3a10" onclick="menu()">${menuBtn}</button></div>`;
}

function toast(m) {
  const t = $('tv');
  t.textContent = m;
  t.style.opacity = 1;
  clearTimeout(tvT);
  tvT = setTimeout(() => (t.style.opacity = 0), 1400);
}

function cycTime() {
  S.tod = (S.tod + 1) % 4;
  toast('TIME: ' + TN[S.tod].toUpperCase());
  envUpd();
}

function cycWx() {
  S.wmode = (S.wmode + 1) % 5;
  if (S.wmode) S.wn = S.wmode - 1;
  else {
    S.wn = pickWx(S.wx);
    S.wt = rr(25, 50);
  }
  toast('WEATHER: ' + WMN[S.wmode].toUpperCase() + (S.wmode ? '' : ' (' + WNN[S.wx] + ')'));
}

let tvT;
function cview() {
  S.view = (S.view + 1) % 3;
  const t = $('tv');
  t.textContent = 'VIEW: ' + ['CHASE', 'FIRST-PERSON', 'OVERHEAD'][S.view];
  t.style.opacity = 1;
  clearTimeout(tvT);
  tvT = setTimeout(() => (t.style.opacity = 0), 1200);
}

function pause() {
  if (S.st == 'play') {
    S.st = 'paused';
    $('ov').style.display = 'flex';
    $('bv').style.display = 'none';
    const resumeBtn = isMobile ? 'RESUME' : 'RESUME [P]';
    const menuBtn = isMobile ? 'MENU' : 'MENU [B]';
    $('bx').innerHTML = `<h1>PAUSED</h1><div class=row><button class="b go" onclick="pause()">${resumeBtn}</button><button class="b go" onclick="menu()">${menuBtn}</button></div>`;
  } else if (S.st == 'paused') {
    S.st = 'play';
    $('ov').style.display = 'none';
    if (isMobile) $('bv').style.display = 'flex';
  }
}

// ---------- input handling ----------
const go = f => {
  if (S.st == 'play') f();
};

addEventListener('keydown', e => {
  const k = e.key.toLowerCase();
  if (k === 'v') {
    cview();
    return;
  }
  if (k === 'm' || k === 'audiovolumeup' || k === 'volumeup') {
    e.preventDefault();
    cycWx();
    return;
  }
  if (k === 'n' || k === 'audiovolumedown' || k === 'volumedown') {
    e.preventDefault();
    cycTime();
    return;
  }
  if ([' ', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(k)) e.preventDefault();
  if (S.st == 'menu') {
    if (k == 'enter' || k == ' ') start();
    else if ('123'.includes(k) && k.length == 1) pickD(+k - 1);
    else if (k == 'arrowleft' || k == 'a') pickL(S.li - 1);
    else if (k == 'arrowright' || k == 'd') pickL(S.li + 1);
    else if (k == 'arrowup') pickD(S.di - 1);
    else if (k == 'arrowdown') pickD(S.di + 1);
    return;
  }
  if (k == 'p') pause();
  else if (k == 'b' || k == 'escape') menu();
  else if (k == 'r') start();
  else if (k == 'a' || k == 'arrowleft') go(() => (S.lane = Math.max(0, S.lane - 1)));
  else if (k == 'd' || k == 'arrowright') go(() => (S.lane = Math.min(4, S.lane + 1)));
  else if (k == 'w' || k == ' ' || k == 'arrowup')
    go(() => {
      if (S.py <= 0.01) {
        S.vy = 9;
        S.slide = 0;
      }
    });
  else if (k == 's' || k == 'arrowdown')
    go(() => {
      if (S.py > 0.05) S.vy = -14;
      else S.slide = 0.7;
    });
  else if (k == 'f') shoot();
  else if (k == 'g') S.fire = 1;
  else if (k == 'q') go(() => (S.target -= 3));
  else if (k == 'e') go(() => (S.target += 3));
});

addEventListener('keyup', e => {
  if (e.key.toLowerCase() == 'g') S.fire = 0;
});

addEventListener('contextmenu', e => e.preventDefault());

let tx = 0, ty = 0;
const rt = $('rt');

function updateAimerPosition(clientX, clientY) {
  S.mouse = 1;
  S.mx = clientX;
  S.my = clientY;
  rt.style.left = S.mx + 'px';
  rt.style.top = S.my + 'px';
  S.aim = aim();
}

// Mouse aiming on PC
addEventListener('pointermove', e => {
  if (e.pointerType == 'mouse') {
    updateAimerPosition(e.clientX, e.clientY);
  }
});

// Canvas pointer down
$('c').addEventListener('pointerdown', e => {
  tx = e.clientX;
  ty = e.clientY;
  updateAimerPosition(e.clientX, e.clientY);
  if (e.pointerType == 'mouse' && S.st == 'play') {
    if (e.button == 2) S.fire = 1;
    else shoot();
  }
});

// Touch drag aiming while moving on screen
$('c').addEventListener('pointermove', e => {
  if (e.pointerType != 'mouse' && S.st == 'play') {
    updateAimerPosition(e.clientX, e.clientY);
  }
});

// Pointer up (Gestures on mobile & Aimed Shooting)
addEventListener('pointerup', e => {
  if (e.button == 2) S.fire = 0;
  if (e.pointerType == 'mouse' || S.st != 'play' || (e.target.closest && e.target.closest('#mb, #bv'))) return;
  const dx = e.clientX - tx,
    dy = e.clientY - ty;
  if (Math.abs(dx) > 35 && Math.abs(dx) > Math.abs(dy)) {
    S.lane = cl(S.lane + (dx > 0 ? 1 : -1), 0, 4);
  } else if (dy < -35) {
    if (S.py <= 0.01) {
      S.vy = 9;
      S.slide = 0;
    }
  } else if (dy > 35) {
    if (S.py > 0.05) S.vy = -14;
    else S.slide = 0.7;
  } else {
    updateAimerPosition(e.clientX, e.clientY);
    shoot();
  }
});

// Mobile Flame Button
(f => {
  const b = $('bf');
  b.addEventListener('pointerdown', e => {
    e.preventDefault();
    e.stopPropagation();
    f(1);
  });
  ['pointerup', 'pointercancel', 'pointerleave'].forEach(n =>
    b.addEventListener(n, () => f(0))
  );
})(v => (S.fire = v && S.st == 'play' ? 1 : 0));

// Mobile Slower & Faster Arrow Buttons
$('be').addEventListener('pointerdown', e => {
  e.preventDefault();
  go(() => (S.target += 3));
});
$('bq').addEventListener('pointerdown', e => {
  e.preventDefault();
  go(() => (S.target -= 3));
});

// Dedicated Top-Left Eye Button for View Toggling
$('bv').addEventListener('pointerdown', e => {
  e.preventDefault();
  e.stopPropagation();
  cview();
});

document.addEventListener('visibilitychange', () => {
  if (document.hidden && S.st == 'play') pause();
});

function rs() {
  ren.setPixelRatio(Math.min(devicePixelRatio, 2));
  ren.setSize(innerWidth, innerHeight, false);
  slc.width = innerWidth;
  slc.height = innerHeight;
  cam.aspect = innerWidth / innerHeight;
  cam.updateProjectionMatrix();
}

addEventListener('resize', rs);
rs();
applyLoc();
menu();

// Main game loop
let last = performance.now();
(function loop(n) {
  requestAnimationFrame(loop);
  const dt = Math.min((n - last) / 1000, 0.033);
  last = n;
  if (S.st != 'paused' && S.st != 'over') upd(dt);
  else if (S.st == 'over') {
    road();
    draw(0);
  } else ren.render(scene, cam);
})(last);