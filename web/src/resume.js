// The resume, drawn from web/resume.json. The same markup is used twice: in the
// resume view inside the site ("Skip to resume", the door under the stairs) and on
// resume.html, the page `npm run resume:pdf` prints to make the Download PDF.

export const RESUME_JSON = "resume.json";
export const RESUME_PDF = "assets/resume.pdf";

const esc = s => String(s).replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));

export async function loadResume() {
  const r = await fetch(RESUME_JSON, {cache: "no-cache"});
  if (!r.ok) throw new Error(`${RESUME_JSON}: ${r.status}`);
  return r.json();
}

const link = c => `<a href="${esc(c.url)}"${c.url.startsWith("http") ? ' target="_blank" rel="noopener"' : ""}>${esc(c.label)}</a>`;

// One entry: a title and its date on one line, a subtitle and its place on the next
// (or, for a project, its links), then the bullet points.
function entry(title, dates, sub, place, points, links) {
  let h = `<article class="rv-entry"><div class="rv-line"><h4>${title}</h4><span class="rv-date">${esc(dates || "")}</span></div>`;
  if (links?.length) h += `<div class="rv-line rv-links">${links.map(link).join('<span class="rv-dot">·</span>')}</div>`;
  else if (sub || place) h += `<div class="rv-line rv-sub"><span>${sub ? esc(sub) : ""}</span><span>${place ? esc(place) : ""}</span></div>`;
  if (points?.length) h += `<ul>${points.map(p => `<li>${esc(p)}</li>`).join("")}</ul>`;
  return h + "</article>";
}

const section = (name, body) => `<section class="rv-sec"><h3>${name}</h3><div>${body}</div></section>`;

// `actions` is extra markup for the header's right side (the site's buttons).
export function resumeHTML(d, actions = "") {
  const contact = [`<span>${esc(d.location)}</span>`, ...(d.contact || []).map(link)]
    .join('<span class="rv-dot">·</span>');
  let h = `<header class="rv-head"><div><h1>${esc(d.name)}</h1><p class="rv-contact">${contact}</p></div>${actions}</header>`;
  if (d.education?.length) h += section("Education", d.education.map(e => entry(esc(e.school), e.dates, e.degree, e.place, e.points)).join(""));
  if (d.experience?.length) h += section("Experience", d.experience.map(e => entry(esc(e.org), e.dates, e.role, e.place, e.points)).join(""));
  if (d.projects?.length) h += section("Projects", d.projects.map(p => entry(`${esc(p.name)}${p.stack ? ` <span class="rv-stack">${esc(p.stack)}</span>` : ""}`, p.dates, "", "", p.points, p.links)).join(""));
  if (d.skills?.length) h += section("Skills", `<dl class="rv-skills">${d.skills.map(s => `<dt>${esc(s.label)}</dt><dd>${esc(s.items)}</dd>`).join("")}</dl>`);
  return h;
}
