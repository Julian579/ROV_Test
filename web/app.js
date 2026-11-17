const $ = (id) => document.getElementById(id);
let state = null;
let prevLeft = null;
let audio = null;
let toastTimer = null;

async function post(url, body) {
  try {
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
  } catch (e) { /* server unreachable: the next poll shows it */ }
}

function clock(sec) {
  const s = Math.ceil(sec);
  return String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");
}

function deg(v) { return (v < 0 ? "−" : "+") + Math.abs(v).toFixed(1) + "°"; }

function unlockAudio() {          // browsers only allow sound after a click
  try { audio = audio || new AudioContext(); audio.resume(); } catch (e) {}
}

function beep() {
  if (!audio) return;
  const osc = audio.createOscillator(), gain = audio.createGain();
  osc.frequency.value = 880; gain.gain.value = 0.2;
  osc.connect(gain); gain.connect(audio.destination);
  osc.start(); osc.stop(audio.currentTime + 1.0);
}

function toast(msg, isErr) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.toggle("err", !!isErr);
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 3000);
}

/* ---------- timer ---------- */
function renderTimer(t) {
  const finished = t.remaining <= 0;
  const started = t.remaining < t.total;

  $("time").textContent = clock(t.remaining);
  $("bar-fill").style.width = (100 * t.remaining / t.total) + "%";
  $("clock").classList.toggle("warn", t.remaining <= 120 && t.remaining > 30);
  $("clock").classList.toggle("last", t.remaining <= 30);
  $("status").textContent = finished ? "Time’s up" : t.running ? "Running" : started ? "Paused" : "Ready";

  $("btn-start").textContent = t.running ? "Pause" : (started && !finished) ? "Resume" : "Start";
  $("btn-start").disabled = finished;
  $("btn-reset").disabled = t.running;           // no accidental reset mid-run

  if (prevLeft !== null && prevLeft > 0 && finished) beep();
  prevLeft = t.remaining;
}

/* ---------- connection icons ---------- */
const ICON_ROV =
  '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="9" width="18" height="7" rx="3"/>' +
  '<path d="M9 9V6h4v3M21 12.5h2M1 12.5h2M8 19h8"/></svg>';
const ICON_CAM =
  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 8h4l2-3h6l2 3h4v11H3z"/>' +
  '<circle cx="12" cy="13" r="3.5"/></svg>';

function setConn(el, ok) {
  el.classList.toggle("ok", ok);
  el.querySelector(".st").textContent = ok ? "OK" : "Off";
}

function renderConn(s) {
  const box = $("conn");
  const items = [{ label: "ROV", icon: ICON_ROV, ok: s.link }]
    .concat(s.cameras.map((c, i) => ({ label: "Cam " + (i + 1), icon: ICON_CAM, ok: c.live,
                                       title: c.name })));
  if (box.children.length !== items.length) {
    box.innerHTML = "";
    items.forEach((it) => {
      const li = document.createElement("li");
      li.innerHTML = it.icon + '<span class="lbl"></span><span class="st"></span>';
      li.querySelector(".lbl").textContent = it.label;
      if (it.title) li.title = it.title;
      box.appendChild(li);
    });
  }
  items.forEach((it, i) => setConn(box.children[i], it.ok));
}

/* ---------- cameras / layout ---------- */
function renderCameras(s) {
  const box = $("cams");
  if (box.children.length !== s.cameras.length) {
    box.innerHTML = "";
    s.cameras.forEach((c, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.addEventListener("click", () => post("/api/camera", { index: i }));
      box.appendChild(b);
    });
  }
  s.cameras.forEach((c, i) => {
    box.children[i].textContent = c.name + (c.live ? "" : " (no signal)");
    box.children[i].setAttribute("aria-pressed", !s.dual && i === s.camera);
    box.children[i].disabled = s.dual;           // both are shown anyway
  });

  $("btn-single").setAttribute("aria-pressed", !s.dual);
  $("btn-dual").setAttribute("aria-pressed", s.dual);
  $("caption").textContent = s.dual
    ? s.cameras.map((c) => c.name).join("  |  ")
    : s.cameras[s.camera].name + " camera";
}

function renderFilter(on) {
  $("filter").setAttribute("aria-checked", on);
  $("filter-state").textContent = on ? "ON" : "OFF";
}

function render(s) {
  state = s;
  renderTimer(s.timer);
  renderConn(s);
  renderCameras(s);
  renderFilter(s.filter);

  $("roll").textContent = deg(s.roll);
  $("pitch").textContent = deg(s.pitch);
  $("yaw").textContent = deg(s.yaw);
  // If the horizon tilts the wrong way on the real ROV, flip the sign of roll or pitch here.
  const shift = Math.max(-40, Math.min(40, s.pitch * 1.2));
  $("hz").setAttribute("transform", `rotate(${-s.roll}) translate(0 ${shift})`);

  $("link").textContent = s.link ? "ROV link ok" : "ROV link lost";
  $("link").classList.toggle("bad", !s.link);
}

async function poll() {
  try {
    const r = await fetch("/api/state", { cache: "no-store" });
    render(await r.json());
  } catch (e) {
    $("link").textContent = "Lost contact with the topside program";
    $("link").classList.add("bad");
  }
}

/* ---------- actions ---------- */
async function setDual(dual) {
  await post("/api/view", { dual });
  poll();
}

async function toggleFilter() {
  const on = !(state && state.filter);
  renderFilter(on);                              // instant feedback
  await post("/api/filter", { on });
  poll();
}

async function saveFrame() {
  try {
    const r = await fetch("/api/snapshot", { cache: "no-store" });
    if (!r.ok) {
      let msg = "Could not save frame";
      try { msg = (await r.json()).error || msg; } catch (e) {}
      toast(msg, true);
      return;
    }
    const name = r.headers.get("X-Filename") || "rov_frame.jpg";
    const url = URL.createObjectURL(await r.blob());
    const a = document.createElement("a");
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    toast("Saved " + name);
  } catch (e) {
    toast("Server unreachable", true);
  }
}

$("btn-start").addEventListener("click", () => {
  unlockAudio();
  post(state && state.timer.running ? "/api/timer/pause" : "/api/timer/start");
});
$("btn-reset").addEventListener("click", () => post("/api/timer/reset"));
$("btn-single").addEventListener("click", () => setDual(false));
$("btn-dual").addEventListener("click", () => setDual(true));
$("filter").addEventListener("click", toggleFilter);
$("btn-snap").addEventListener("click", saveFrame);

document.addEventListener("keydown", (e) => {
  if (!state || e.target.tagName === "INPUT" || e.ctrlKey || e.metaKey || e.altKey) return;
  const k = e.key.toLowerCase();
  if (k === "c" && !state.dual) post("/api/camera", { index: (state.camera + 1) % state.cameras.length });
  if (k === "v") setDual(!state.dual);
  if (k === "f") toggleFilter();
  if (k === "s") saveFrame();
});

setInterval(poll, 250);
poll();