// The still pictures shown while the 3D loads: the landing shot first, and a room's
// own still if a room is opened before the 3D is ready. They are drawn by the site's
// own renderer from the exact cameras the 3D uses (npm run stills, tools/stills.mjs),
// so when the 3D takes over underneath, nothing moves or changes colour.
//
// How the 3D camera fits the window (main.js, cameraFov):
//   - 4:5 or wider: a fixed 45° vertical field of view; a wider window sees more to the sides.
//   - narrower than 4:5 (a phone held upright): a fixed sideways view (PORTRAIT.tanH) and a
//     taller one, so a phone still sees the house and the rooms' close-ups across.
// The stills follow the same two rules, so each lines up exactly with the 3D:
//   - wide: rendered at MARGIN x the 45° view's height and 2.4:1, shown at MARGIN x the
//     window's height, centred. Windows from 4:5 to 1:1 get a square crop of it.
//   - tall: rendered at MARGIN x the sideways view and 0.42:1, shown at MARGIN x the
//     window's width, centred.
// The margin is what a drag can pan into.
//
// No three.js in here: this file has to work before three.js has arrived.

const tan = deg => Math.tan(deg / 2 * Math.PI / 180), deg = t => 2 * Math.atan(t) * 180 / Math.PI;
export const STILL = {
  fov: 45,                    // the 3D camera's vertical field of view, 4:5 and wider
  margin: 1.1,                // stills are rendered 10% bigger than the view (5% each side)
  aspect: 2.4,                // the wide still's shape
  portrait: {
    below: 0.8,               // narrower than 4:5 counts as upright
    tanH: 0.8 * tan(45),      // there, the sideways view is fixed: as wide as a 4:5 window's (36.6°)
    aspect: 0.42,             // the tall still's shape, enough for 21:9 phones
  },
};
STILL.renderFov = deg(STILL.margin * tan(STILL.fov));                                              // wide still, vertical
STILL.portrait.renderFov = deg(STILL.margin * STILL.portrait.tanH / STILL.portrait.aspect);      // tall still, vertical
// the 3D camera's vertical field of view for a window of this shape (width / height)
export const cameraFov = aspect => (aspect < STILL.portrait.below ? deg(STILL.portrait.tanH / aspect) : STILL.fov);

// The files, in assets/stills/. Widths in pixels; the browser picks one for the screen.
export const SIZES = {
  landing: {wide: [1280, 2048, 2880], square: [900, 1400], tall: [720, 1080]},
  room: {wide: [1440, 2400], square: [1000], tall: [720, 1080]},
};
export const stillFiles = id => {
  const s = id === "landing" ? SIZES.landing : SIZES.room;
  return {wide: s.wide.map(w => `${id}-${w}.webp`), square: s.square.map(w => `${id}-sq-${w}.webp`),
    tall: s.tall.map(w => `${id}-tall-${w}.webp`), sizes: s};
};
export const TALL = "(max-aspect-ratio: 4/5)", SQUARE = "(max-aspect-ratio: 1/1)";

// <picture> markup for a stop's still (id "landing" for the landing shot)
export function stillPicture(id, base = "assets/stills/") {
  const {sizes} = stillFiles(id);
  const set = (kind, list) => list.map(w => `${base}${id}${kind}-${w}.webp ${w}w`).join(", ");
  const m = STILL.margin * 100;
  return `<picture><source media="${TALL}" srcset="${set("-tall", sizes.tall)}" sizes="${m}vw">` +
    `<source media="${SQUARE}" srcset="${set("-sq", sizes.square)}" sizes="${m}vh">` +
    `<img srcset="${set("", sizes.wide)}" sizes="${(m * STILL.aspect).toFixed(0)}vh" src="${base}${id}-${sizes.wide[1] ?? sizes.wide[0]}.webp" alt="" draggable="false"></picture>`;
}

// The still layer on the page: swaps stills, pans on drag, fades away when the 3D is ready.
export class Still {
  constructor(el, {onDrag = () => {}} = {}) {
    this.el = el;
    this.id = "landing";
    this.x = 0; this.y = 0;            // pan, in CSS pixels
    this.sx = 0; this.sy = 0;          // how far the view is slid away from a phone's panel (main.js, shiftView)
    this.on = true;
    // tiny blurred copies of every still (npm run stills writes them), shown while a room's still loads
    this.thumbs = {};
    fetch("assets/stills/thumbs.json").then(r => r.ok ? r.json() : {}).then(t => { this.thumbs = t; }, () => {});
    let drag = null;
    el.addEventListener("pointerdown", e => { drag = {x: e.clientX, y: e.clientY, px: this.x, py: this.y}; el.setPointerCapture(e.pointerId); el.classList.add("dragging"); });
    el.addEventListener("pointermove", e => {
      if (!drag) return;
      // half the pointer's movement, held inside the margin, a little elastic at its edge
      this.panTo(drag.px + (e.clientX - drag.x) * 0.5, drag.py + (e.clientY - drag.y) * 0.5);
      onDrag();
    });
    const end = () => { drag = null; el.classList.remove("dragging"); };
    el.addEventListener("pointerup", end); el.addEventListener("pointercancel", end);
  }
  img() { return this.el.querySelector("picture:last-child img"); }
  // how far the picture on show can move each way before its edge comes into view
  room() {
    const vw = this.el.clientWidth, vh = this.el.clientHeight, img = this.img();
    const r = img && img.naturalWidth ? img.getBoundingClientRect() : {width: vw * STILL.margin, height: vh * STILL.margin};
    return {x: Math.max(0, (r.width - vw) / 2), y: Math.max(0, (r.height - vh) / 2)};
  }
  panTo(x, y) {
    const r = this.room(), soft = (v, m) => Math.sign(v) * (Math.abs(v) <= m ? Math.abs(v) : m + (1 - Math.exp(-(Math.abs(v) - m) / 40)) * 12);
    this.x = soft(x, r.x); this.y = soft(y, r.y);
    this.place();
  }
  shiftTo(x, y) { if (x !== this.sx || y !== this.sy) { this.sx = x; this.sy = y; this.place(); } }
  place() {
    const x = this.x - this.sx, y = this.y - this.sy;
    for (const img of this.el.querySelectorAll("img")) img.style.transform = x || y ? `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))` : "";
  }
  // show a stop's still ("landing" for the landing shot), cross-fading from the one on show
  show(id) {
    if (id === this.id) return;
    this.id = id;
    this.panTo(0, 0);
    const holder = document.createElement("div");
    const thumb = this.thumbs[id] && this.thumbs[id][matchMedia(TALL).matches ? "tall" : "wide"];
    if (thumb) {
      // its tiny copy first, blurred, at once (the still itself may wait behind the 3D's downloads)
      holder.innerHTML = `<picture class="thumb"><img src="${thumb}" alt="" draggable="false"></picture>`;
      this.el.appendChild(holder.firstElementChild);
      this.place();
    }
    holder.innerHTML = stillPicture(id);
    const pic = holder.firstElementChild, img = pic.querySelector("img");
    pic.classList.add("in");
    this.el.appendChild(pic);
    this.place();
    const reveal = () => {
      requestAnimationFrame(() => pic.classList.remove("in"));
      // drop the ones underneath once this one has faded in
      setTimeout(() => { for (const old of [...this.el.querySelectorAll("picture")]) if (old !== pic && old.nextElementSibling) old.remove(); }, 600);
    };
    if (img.complete && img.naturalWidth) reveal(); else { img.onload = reveal; img.onerror = reveal; }
  }
  // ease the pan back to the middle (the 3D isn't panned), then fade the still away
  async fadeOut() {
    if (!this.on) return;
    if (this.x || this.y) {
      const x0 = this.x, y0 = this.y, t0 = performance.now();
      await new Promise(done => {
        const step = t => { const k = Math.min(1, (t - t0) / 350), e = 1 - (1 - k) ** 3; this.panTo(x0 * (1 - e), y0 * (1 - e)); k < 1 ? requestAnimationFrame(step) : done(); };
        requestAnimationFrame(step);
      });
    }
    this.on = false;
    this.el.classList.add("gone");
    await new Promise(r => setTimeout(r, 900));
    this.el.hidden = true;
  }
}
