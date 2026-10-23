const $ = (id) => document.getElementById(id);
const R = Math.random;
const rr = (a, b) => a + R() * (b - a);
const cl = (v, a, b) => Math.max(a, Math.min(b, v));
const css = (c) => '#' + c.toString(16).padStart(6, '0');
const LW = 2.2;
const NR = 75;
const NS = 82;

// --- Configurations & Locations ---
const DIFF = [
  { n: 'Easy', col: 0x59d97f, d: 'Relaxed pace, gentle curves, forgiving hits.', hp: 130, dmg: 0.6, v0: 12, vg: 0.12, vcap: 22, vmax: 34, gap: [28, 16, 0.08], nob: [1, 1, 1, 2], gc: 0.18, curve: 0.7 },
  { n: 'Medium', col: 0xffc733, d: 'The classic experience. Balanced speed and curves.', hp: 100, dmg: 1.0, v0: 14, vg: 0.20, vcap: 30, vmax: 42, gap: [24, 13, 0.12], nob: [1, 1, 2, 3], gc: 0.28, curve: 1.0 },
  { n: 'Hard', col: 0xff4d40, d: 'Fast, dense obstacles, sharp bends. Every hit hurts.', hp: 80, dmg: 1.4, v0: 17, vg: 0.28, vcap: 34, vmax: 48, gap: [21, 12, 0.15], nob: [2, 2, 3, 3], gc: 0.40, curve: 1.25 }
];

const LOC = [
  { n: 'Agrabah', tag: 'Desert highway', d: 'Golden domes, palms and warm dust.', kind: 'desert', sky: 0xf79954, top: 0x4d3385, gr: 0xdbb273, rd: 0x6b1a1f, ed: 0xf2bf26, dc: 0xf2e6cc, far: 0xc79457, sun: 0xffe08a, ac: 0xf2bf26, hs: 0xffe0b0, hg: 0x806040, hi: 0.95, sc: 0xffd9a0, si: 0.8, fg: 1.0, curve: 1.0, wx: 3 },
  { n: 'Neon City', tag: 'Cyber night', d: 'A rain-slick skyline that never sleeps.', kind: 'city', sky: 0x2a1040, top: 0x05050f, gr: 0x12121a, rd: 0x1c1c28, ed: 0x33e6ff, dc: 0xd36bff, far: 0x2a1d52, sun: 0xb9b2ff, ac: 0x59e6ff, hs: 0x7a5fb8, hg: 0x1a1428, hi: 0.9, sc: 0x9a7bff, si: 0.5, fg: 0.85, curve: 0.6, wx: 1 },
  { n: 'Frozen Peaks', tag: 'Snow and ice', d: 'A winding alpine pass under pale skies.', kind: 'snow', sky: 0xb8cde6, top: 0x6f8fc0, gr: 0xeef3ff, rd: 0x454d61, ed: 0x99d9ff, dc: 0xffffff, far: 0xaab9d4, sun: 0xffffff, ac: 0x99d9ff, hs: 0xdfeaff, hg: 0x8899aa, hi: 1.0, sc: 0xffffff, si: 0.7, fg: 0.9, curve: 1.3, wx: 2 },
  { n: 'Emerald Vale', tag: 'Misty forest', d: 'A twisty valley road through dense trees.', kind: 'forest', sky: 0x84b8a0, top: 0x3a7d95, gr: 0x336e33, rd: 0x5c4730, ed: 0x99e066, dc: 0xf5ecc0, far: 0x2e665a, sun: 0xe8f0b0, ac: 0x8ce673, hs: 0xcfeedd, hg: 0x405a30, hi: 0.95, sc: 0xfff2c0, si: 0.7, fg: 0.78, curve: 1.5, wx: 0 }
];

// --- State Management ---
const S = {
  st: 'menu', di: 1, li: 0, D: 0, t: 0, time: 0,
  speed: 5, target: 14, lane: 2, px: 0, py: 0, vy: 0, slide: 0,
  hp: 100, score: 0, coins: 0, kills: 0, chain: 0, inv: 0, cd: 0,
  roll: 0, cdir: 1, segs: [], cend: 40, rt: new Float32Array(NR + 1),
  k0: 0, obs: [], cns: [], gs: [], bl: [], next: 20, phase: 0, wx: 0
};

let hi = [0, 0, 0];
try { hi = JSON.parse(localStorage.getItem('dd3')) || hi; } catch (e) {}

const DF = () => DIFF[S.di];
const LC = () => LOC[S.li];
const mult = () => 1 + Math.min((S.chain / 5) | 0, 4);

// --- Curved Track Geometry ---
function curv(d) {
  while (S.cend < d + 220) {
    const a = S.cend + rr(60, 190);
    const l = rr(110, 240);
    S.cdir = R() < 0.65 ? -S.cdir : S.cdir;
    S.segs.push([a, l, S.cdir * rr(1.8e-3, 3.5e-3)]);
    S.cend = a + l;
  }
  const f = DF().curve * LC().curve;
  for (const [a, l, p] of S.segs) {
    if (d >= a && d < a + l) return p * f * Math.sin(Math.PI * (d - a) / l) ** 2;
  }
  return 0;
}

function road() {
  let h = 0, x = 0;
  S.k0 = curv(S.D);
  S.rt[0] = 0;
  for (let i = 1; i <= NR; i++) {
    const k = curv(S.D + (i - 0.5) * 2);
    const h2 = h + k * 2;
    x += (h + h2) * 0.5 * 2;
    h = h2;
    S.rt[i] = x;
  }
  S.segs = S.segs.filter((q) => q[0] + q[1] > S.D - 40);
}

function off(z) {
  const d = -z;
  if (d <= 0) return 0.5 * S.k0 * d * d;
  const i = d / 2;
  const n = Math.floor(i);
  if (n >= NR) return S.rt[NR];
  return S.rt[n] + (S.rt[n + 1] - S.rt[n]) * (i - n);
}

// --- Three.js Initialization ---
const ren = new THREE.WebGLRenderer({ canvas: $('c'), antialias: true, alpha: true });
const scene = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(58, 1, 0.3, 260);

const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 0.9);
const sunL = new THREE.DirectionalLight(0xffffff, 0.8);
sunL.position.set(0.4, 1, 0.5);
scene.add(hemi, sunL);

const BG = new THREE.BoxGeometry(1, 1, 1);
const SG = new THREE.SphereGeometry(1, 14, 10);
const CG = new THREE.ConeGeometry(1, 1, 9);
const YG = new THREE.CylinderGeometry(1, 1, 1, 10);
const mc = {};

const mat = (c, e) => mc[c + '_' + (e || 0)] || (mc[c + '_' + (e || 0)] = new THREE.MeshLambertMaterial({ color: c, emissive: e || 0 }));
function mk(g, c, x, y, z, sx, sy, sz, p, e) {
  const m = new THREE.Mesh(g, mat(c, e));
  m.position.set(x, y, z);
  m.scale.set(sx, sy, sz);
  if (p) p.add(m);
  return m;
}

// Procedural Canvas Textures
const wt = (() => {
  const c = document.createElement('canvas');
  c.width = 8; c.height = 16;
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
  c.width = 1; c.height = 2;
  const x = c.getContext('2d');
  x.fillStyle = '#fff'; x.fillRect(0, 0, 1, 1);
  x.fillStyle = '#d8d8d8'; x.fillRect(0, 1, 1, 1);
  const t = new THREE.CanvasTexture(c);
  t.wrapT = THREE.RepeatWrapping;
  t.magFilter = t.minFilter = THREE.NearestFilter;
  return t;
})();

// Road & Ground Meshes
const B = (c) => new THREE.MeshBasicMaterial({ color: c });
const gm = B(0), rm = new THREE.MeshBasicMaterial({ color: 0, map: bt }), em = B(0), dm = B(0), rib = [];
const gnd = new THREE.Mesh(new THREE.PlaneGeometry(500, 360), gm);
gnd.rotation.x = -Math.PI / 2;
gnd.position.set(0, -0.02, -100);
scene.add(gnd);

function ribbon(xl, xr, y, m) {
  const g = new THREE.BufferGeometry();
  const p = new Float32Array(NS * 6);
  const u = new Float32Array(NS * 4);
  const ix = [];
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

const dash = new THREE.InstancedMesh(BG, dm, 104);
const dum = new THREE.Object3D();
dash.frustumCulled = false;
scene.add(dash);

// Character Mesh & Skeletal Swing
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
  const s = Math.sin(ph) * 0.7;
  const L = g.userData.L;
  L[0].rotation.x = -s;
  L[2].rotation.x = s;
  L[1].rotation.x = s;
  L[3].rotation.x = -s;
}

const pl = figure(0xbf1a26, 0xf2f2e6, 0xcc8c59, 0x141210);
const shd = new THREE.Mesh(new THREE.CircleGeometry(0.8, 16), new THREE.MeshBasicMaterial({ color: 0, transparent: true, opacity: 0.35 }));
shd.rotation.x = -Math.PI / 2;
scene.add(shd);

// Scenery Helpers
const pine = (x, z, s, g) => {
  mk(YG, 0x4d331f, x, 0.6 * s, z, 0.2 * s, 1.2 * s, 0.2 * s, g);
  [[1.8, 2.4, 0.9, 0x1a5238], [1.4, 2.2, 2.3, 0x246142], [1.0, 2.0, 3.6, 0xdbebf5]].forEach(([r, h, y, c]) =>
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
    const h = 3 + R() * 6;
    mk(BG, 0xd9b380, s * 10, h / 2, 0, 3, h, 3, g);
    if (R() < 0.5) mk(SG, 0xf2bf26, s * 10, h + 0.2, 0, 1.3, 1.2, 1.3, g);
    mk(YG, 0x66401a, s * 6.9, 1.5, 3, 0.15, 3, 0.15, g);
    mk(SG, 0x1a8026, s * 6.9, 3.1, 3, 1.3, 0.3, 1.3, g);
  },
  city(s, g) {
    const h = 9 + R() * 24, w = 3 + R() * 2;
    const nc = [0x33e6ff, 0xff40cc, 0xb366ff][(R() * 3) | 0];
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

let sceneG = [];
const bd = new THREE.Group();
const wpos = new Float32Array(1200);
scene.add(bd);

const wp = new THREE.Points(new THREE.BufferGeometry(), new THREE.PointsMaterial({ size: 0.14, transparent: true, opacity: 0.8 }));
wp.frustumCulled = false;
scene.add(wp);

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
  dm.color.set(L.dc);

  S.wx = L.wx === 3 ? (R() < 0.4 ? 3 : 0) : L.wx;
  wp.material.color.set([0, 0xaec8ff, 0xffffff, 0xd9b36b][S.wx]);
  wp.visible = !!S.wx;

  for (let i = 0; i < 1200; i += 3) {
    wpos[i] = rr(-16, 16);
    wpos[i + 1] = rr(0, 14);
    wpos[i + 2] = rr(-45, 8);
  }
  wp.geometry.setAttribute('position', new THREE.BufferAttribute(wpos, 3));

  sceneG.forEach((g) => scene.remove(g));
  sceneG = [];
  for (let i = 0; i < 14; i++) {
    for (const s of [-1, 1]) {
      const g = new THREE.Group();
      SC[L.kind](s, g);
      g.position.z = 10 - i * 12;
      scene.add(g);
      sceneG.push(g);
    }
  }

  while (bd.children.length) bd.remove(bd.children[0]);
  const fc = new THREE.Color(L.far).lerp(new THREE.Color(L.sky), 0.42);
  const bm = new THREE.MeshBasicMaterial({ color: fc, fog: false });
  for (let i = 0; i < 30; i++) {
    const x = -290 + i * 20 + rr(-7, 7);
    const a = R(), b = R();
    let m;
    if (L.kind === 'city') {
      m = new THREE.Mesh(BG, bm);
      const h = 25 + b * 60;
      m.scale.set(8 + a * 10, h, 9);
      m.position.set(x, h / 2, -165);
    } else if (L.kind === 'snow') {
      m = new THREE.Mesh(CG, bm);
      const h = 44 + b * 34;
      m.scale.set(28 + a * 20, h, 28 + a * 20);
      m.position.set(x, h / 2, -165);
    } else if (L.kind === 'desert' && i % 5 === 0) {
      m = new THREE.Mesh(CG, bm);
      m.scale.set(26, 28 + b * 12, 26);
      m.position.set(x, 14, -165);
    } else {
      m = new THREE.Mesh(SG, bm);
      m.scale.set(30 + a * 22, L.kind === 'forest' ? 14 + b * 10 : 10, 18);
      m.position.set(x, -1, -165);
    }
    bd.add(m);
  }
  const sn = new THREE.Mesh(SG, new THREE.MeshBasicMaterial({ color: L.sun, fog: false }));
  sn.scale.set(14, 14, 14);
  sn.position.set(-38, 60, -190);
  bd.add(sn);
  document.documentElement.style.setProperty('--a', css(L.ac));
}

// --- Gameplay Mechanics & Spawning ---
function mkObs(k, lane, z) {
  const g = new THREE.Group();
  if (k === 'barrier') {
    mk(BG, 0xf28019, 0, 0.45, 0, 1.9, 0.9, 0.5, g);
    mk(BG, 0xffffff, 0, 0.45, 0, 1.95, 0.2, 0.55, g);
  } else if (k === 'beam') {
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

const coinG = new THREE.CylinderGeometry(0.35, 0.35, 0.08, 16);
function spawn() {
  const d = DF(), z = -100;
  const ln = [0, 1, 2, 3, 4].sort(() => R() - 0.5);
  const n = d.nob[(R() * 4) | 0];

  for (let i = 0; i < n; i++) {
    S.obs.push(mkObs(['barrier', 'beam', 'crate'][(R() * 3) | 0], ln[i], z));
  }
  const fr = ln.slice(3);
  const cx = (fr[(R() * fr.length) | 0] - 2) * LW;
  const cn = 3 + ((R() * 4) | 0);
  for (let i = 0; i < cn; i++) {
    const g = new THREE.Group();
    mk(coinG, 0xf2bf26, 0, 0, 0, 1, 1, 1, g, 0x6a4a00).rotation.x = Math.PI / 2;
    scene.add(g);
    S.cns.push({ x: cx, z: z - i * 2.2, g });
  }
  if (R() < d.gc && S.gs.length < 3) {
    S.gs.push({ x: ((R() * 5) | 0) - 2, z: z - 6, g: figure(0x1f1f26, 0x0d0d12, 0x806659, 0, 1) });
    S.gs[S.gs.length - 1].x *= LW;
  }
}

function hurt(n) {
  if (S.inv > 0) return;
  S.inv = 1;
  S.hp -= Math.max(1, Math.round(n * DF().dmg));
  S.chain = 0;
  $('fl').style.opacity = '0.4';
  if (S.hp <= 0) {
    S.st = 'over';
    const i = S.di;
    if (S.score > hi[i]) {
      hi[i] = S.score | 0;
      try { localStorage.setItem('dd3', JSON.stringify(hi)); } catch (e) {}
    }
    showOver();
  }
}

function shoot() {
  if (S.st !== 'play' || S.cd > 0) return;
  const m = new THREE.Mesh(SG, new THREE.MeshBasicMaterial({ color: 0xffee55 }));
  m.scale.set(0.2, 0.2, 0.2);
  scene.add(m);
  S.bl.push({ x: S.px, z: -0.5, y: 1.25 + S.py, m });
  S.cd = 0.28;
}

function clr() {
  for (const a of [S.obs, S.cns, S.gs, S.bl]) {
    for (const e of a) scene.remove(e.g || e.m);
  }
  S.obs = [];
  S.cns = [];
  S.gs = [];
  S.bl = [];
}

function start() {
  const d = DF();
  clr();
  Object.assign(S, {
    st: 'play', time: 0, speed: d.v0, target: d.v0,
    lane: 2, px: 0, py: 0, vy: 0, slide: 0,
    hp: d.hp, score: 0, coins: 0, kills: 0, chain: 0,
    inv: 0, cd: 0, next: S.D + 20
  });
  $('ov').style.display = 'none';
  $('hud').style.display = 'block';
}

function upd(dt) {
  S.t += dt;
  const d = DF();
  $('fl').style.opacity = Math.max(0, parseFloat($('fl').style.opacity || 0) - dt * 1.5);

  if (S.st === 'menu') {
    S.D += 5 * dt;
    S.phase += 4 * dt;
    S.speed = 5;
  } else if (S.st === 'play') {
    S.time += dt;
    const vmin = Math.min(d.v0 - 2 + S.time * d.vg, d.vcap);
    S.target = cl(S.target, vmin, d.vmax);
    S.speed += (S.target - S.speed) * Math.min(1, 3 * dt);
    const sp = S.speed;

    S.D += sp * dt;
    S.score += sp * dt * 0.2 * (sp / 14);
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

    if (S.D >= S.next) {
      spawn();
      S.next = S.D + Math.max(d.gap[1], d.gap[0] - S.time * d.gap[2]);
    }

    const top = S.py + (S.slide > 0 ? 0.9 : 1.9);
    for (const o of S.obs) {
      o.z += sp * dt;
      if (!o.dead && Math.abs(o.z) < 1 && Math.abs(o.x - S.px) < 1 &&
          ((o.k === 'barrier' && S.py < 0.9) || (o.k === 'crate' && S.py < 1.8) || (o.k === 'beam' && top > 1.1 && S.py < 2.2))) {
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
      }
      if (c.z > 6) c.dead = 1;
    }

    for (const g of S.gs) {
      g.z += sp * 0.55 * dt;
      if (g.z > -30) g.x += cl(S.px - g.x, -1, 1) * 1.6 * dt;
      if (Math.abs(g.z) < 1.2 && Math.abs(g.x - S.px) < 1.2) {
        g.dead = 1;
        hurt(30);
      }
      if (g.z > 6) g.dead = 1;
    }

    for (const b of S.bl) {
      b.z -= 55 * dt;
      if (b.z < -110) b.dead = 1;
      for (const o of S.obs) {
        if (o.k === 'crate' && !o.dead && Math.abs(o.x - b.x) < 1.1 && Math.abs(o.z - b.z) < 1.2) {
          o.dead = b.dead = 1;
          S.score += 20 * mult();
        }
      }
      for (const g of S.gs) {
        if (!g.dead && Math.abs(g.x - b.x) < 1.1 && Math.abs(g.z - b.z) < 1.4) {
          g.dead = b.dead = 1;
          S.kills++;
          S.chain++;
          S.score += 50 * mult();
        }
      }
    }

    for (const k of ['obs', 'cns', 'gs', 'bl']) {
      S[k] = S[k].filter((e) => {
        if (e.dead) scene.remove(e.g || e.m);
        return !e.dead;
      });
    }
  }

  road();
  S.roll += (cl(curv(S.D + 25) * 18, -0.08, 0.08) - S.roll) * Math.min(1, 4 * dt);
  draw(dt);
}

function draw(dt) {
  const sp = S.speed, t = S.t;
  for (const r of rib) {
    for (let k = 0; k < NS; k++) {
      const z = 8 - 2 * k, o = off(z), i = k * 6;
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
    const z = 6 - j * 6 + (S.D % 6), o = off(z);
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

  pl.position.set(S.px, S.py + (S.slide > 0 ? 0.35 : 0), 0);
  pl.rotation.x = S.slide > 0 ? -1.2 : 0;
  swing(pl, S.phase);
  pl.visible = !(S.st === 'play' && S.inv > 0 && (((t * 20) | 0) % 2));

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
  for (const b of S.bl) b.m.position.set(b.x + off(b.z), b.y, b.z);

  if (S.wx) {
    const a = wp.geometry.attributes.position.array;
    for (let i = 0; i < a.length; i += 3) {
      if (S.wx === 1) a[i + 1] -= 24 * dt;
      else if (S.wx === 2) {
        a[i + 1] -= 2.2 * dt;
        a[i] += Math.sin(t * 1.5 + a[i + 2]) * 0.6 * dt;
      } else a[i] += 16 * dt;
      a[i + 2] += sp * 0.5 * dt;
      if (a[i + 1] < 0) a[i + 1] = 14;
      if (a[i + 2] > 8) a[i + 2] = -45;
      if (a[i] > 16) a[i] = -16;
    }
    wp.geometry.attributes.position.needsUpdate = true;
  }

  cam.fov = 58 + Math.max(0, sp - 14) * 0.3;
  cam.updateProjectionMatrix();
  cam.position.set(S.px * 0.6, 4.3, 7.5);
  cam.up.set(Math.sin(S.roll), Math.cos(S.roll), 0);
  cam.lookAt(S.px * 0.4 + off(-14) * 0.45, 1.4, -12);

  if (S.st !== 'menu') {
    const d = DF();
    $('hf').style.width = (Math.max(0, S.hp) / d.hp) * 100 + '%';
    $('hf').style.background = S.hp / d.hp > 0.35 ? '#4ade80' : '#f05545';
    $('ht').textContent = Math.max(0, S.hp) + ' / ' + d.hp;
    $('sv').textContent = S.score | 0;
    $('cn').innerHTML = 'Coins ' + S.coins + (mult() > 1 ? '<br><span style="color:#ff9a2e">COMBO x' + mult() + '</span>' : '') + '<small>' + d.n.toUpperCase() + ' | ' + LC().n.toUpperCase() + '</small>';
    $('st').textContent = ((sp * 4) | 0) + ' km/h';
    const k = curv(S.D + 35);
    $('cv').textContent = Math.abs(k) > 7e-4 ? (k > 0 ? 'CURVE RIGHT >>>' : '<<< CURVE LEFT') : '';
  }
  ren.render(scene, cam);
}

// --- Menus & Overlay UI ---
function menu() {
  S.st = 'menu';
  clr();
  $('hud').style.display = 'none';
  $('ov').style.display = 'flex';
  $('bx').innerHTML = `
    <h1>DICTATOR'S DASH</h1>
    <small>3D WEB EDITION | ENDLESS RUNNER</small>
    <h4>SELECT DIFFICULTY</h4>
    <div class="row">
      ${DIFF.map((d, i) => `<button class="b ${i === S.di ? 'sel' : ''}" style="--a:${css(d.col)}" onclick="pickD(${i})">${d.n}<small>Best ${hi[i]}</small></button>`).join('')}
    </div>
    <p style="color:${css(DF().col)}">${DF().d}</p>
    <h4>SELECT LOCATION</h4>
    <div class="row">
      ${LOC.map((l, i) => `<button class="b card ${i === S.li ? 'sel' : ''}" style="--a:${css(l.ac)}" onclick="pickL(${i})"><i style="background:linear-gradient(${css(l.top)},${css(l.sky)} 60%,${css(l.gr)} 60%)"></i>${l.n}<small>${l.tag}</small></button>`).join('')}
    </div>
    <p style="color:${css(LC().ac)}">${LC().d}</p>
    <button class="b go" onclick="start()">START RUN</button>
    <small>Arrows or A/D lanes | W/Space jump | S slide | F or click: shoot | P pause | B menu | touch: swipe, tap to shoot</small>
  `;
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
  $('bx').style.setProperty('--a', '#ff4d40');
  $('bx').innerHTML = `
    <h1 style="color:#ff5040">GAME OVER</h1>
    <p>Score ${S.score | 0} &nbsp; Coins ${S.coins} &nbsp; Guards downed ${S.kills}</p>
    <p style="color:#f2bf26">Best (${DF().n}): ${hi[S.di]}</p>
    <div class="row">
      <button class="b go" onclick="start()">RESTART [R]</button>
      <button class="b go" style="border-color:#ffc733;background:#4a3a10" onclick="menu()">MENU [B]</button>
    </div>
  `;
}

function pause() {
  if (S.st === 'play') {
    S.st = 'paused';
    $('ov').style.display = 'flex';
    $('bx').innerHTML = '<h1>PAUSED</h1><div class="row"><button class="b go" onclick="pause()">RESUME [P]</button><button class="b go" onclick="menu()">MENU [B]</button></div>';
  } else if (S.st === 'paused') {
    S.st = 'play';
    $('ov').style.display = 'none';
  }
}

// --- Keyboard & Touch Listeners ---
const go = (f) => { if (S.st === 'play') f(); };

addEventListener('keydown', (e) => {
  const k = e.key.toLowerCase();
  if ([' ', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(k)) e.preventDefault();
  if (S.st === 'menu') {
    if (k === 'enter' || k === ' ') start();
    else if ('123'.includes(k) && k.length === 1) pickD(+k - 1);
    else if (k === 'arrowleft' || k === 'a') pickL(S.li - 1);
    else if (k === 'arrowright' || k === 'd') pickL(S.li + 1);
    else if (k === 'arrowup') pickD(S.di - 1);
    else if (k === 'arrowdown') pickD(S.di + 1);
    return;
  }
  if (k === 'p') pause();
  else if (k === 'b' || k === 'escape') menu();
  else if (k === 'r') start();
  else if (k === 'a' || k === 'arrowleft') go(() => S.lane = Math.max(0, S.lane - 1));
  else if (k === 'd' || k === 'arrowright') go(() => S.lane = Math.min(4, S.lane + 1));
  else if (k === 'w' || k === ' ' || k === 'arrowup') go(() => { if (S.py <= 0.01) { S.vy = 9; S.slide = 0; } });
  else if (k === 's' || k === 'arrowdown') go(() => { if (S.py > 0.05) S.vy = -14; else S.slide = 0.7; });
  else if (k === 'f') shoot();
  else if (k === 'q') go(() => S.target -= 3);
  else if (k === 'e') go(() => S.target += 3);
});

let tx = 0, ty = 0;
$('c').addEventListener('pointerdown', (e) => { tx = e.clientX; ty = e.clientY; });
$('c').addEventListener('pointercancel', () => { tx = 0; ty = 0; });
$('c').addEventListener('pointerup', (e) => {
  if (S.st !== 'play') return;
  const dx = e.clientX - tx, dy = e.clientY - ty;
  if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) {
    S.lane = cl(S.lane + (dx > 0 ? 1 : -1), 0, 4);
  } else if (dy < -40) {
    if (S.py <= 0.01) { S.vy = 9; S.slide = 0; }
  } else if (dy > 40) {
    if (S.py > 0.05) S.vy = -14; else S.slide = 0.7;
  } else {
    shoot();
  }
});

document.addEventListener('visibilitychange', () => {
  if (document.hidden && S.st === 'play') pause();
});

function rs() {
  ren.setPixelRatio(Math.min(devicePixelRatio, 2));
  ren.setSize(innerWidth, innerHeight, false);
  cam.aspect = innerWidth / innerHeight;
  cam.updateProjectionMatrix();
}

addEventListener('resize', rs);
rs();
applyLoc();
menu();

// --- 60/120 Hz Dynamic Animation Loop ---
let last = performance.now();
(function loop(n) {
  requestAnimationFrame(loop);
  const dt = Math.min((n - last) / 1000, 0.05); // Supports higher display refresh rates smoothly
  last = n;
  if (S.st !== 'paused' && S.st !== 'over') upd(dt);
  else if (S.st === 'over') { road(); draw(0); }
  else ren.render(scene, cam);
})(last);