"use strict";
const $ = id => document.getElementById(id);
let state = null, profile = "", selected = null, csrf = "", toastTimer;
const activeStates = ["pending", "draft", "reviewed"];
function statusLabel(job) {
  return job.evidence_type === "legacy_record" && job.status === "done" ? "이전 완료 기록" : state.statuses[job.status];
}
function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function notify(message) {
  $("toast").textContent = message;
  $("toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { $("toast").hidden = true; }, 4500);
}
async function request(path, data) {
  const options = data ? {method: "POST", headers: {"Content-Type": "application/json", "X-Goni-Csrf": csrf}, body: JSON.stringify(data)} : {};
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "요청을 처리하지 못했습니다.");
  return result;
}
async function load() {
  state = await request("/api/workspace" + (profile ? "?profile=" + encodeURIComponent(profile) : ""));
  csrf = state.csrf;
  if (!profile && state.profiles.length) {
    profile = (state.profiles.find(p => state.jobs.some(j => j.profile === p.name)) || state.profiles[0]).name;
    return load();
  }
  renderProfiles();
  renderJobs();
  const current = state.profiles.find(p => p.name === profile);
  $("version").textContent = state.version;
  $("category").textContent = current ? current.category : "시작하기";
  $("workspace-title").textContent = current ? current.name + "의 소통 노트" : "계정을 나누고, 글을 읽고, 내 말로 소통하세요.";
  $("intro-description").textContent = current ? current.naver_id + " 계정으로 정리한 글과 초안을 살펴보세요." : "왼쪽에서 계정 구분을 추가하고 첫 글을 등록해 주세요.";
  $("new-target").disabled = !current;
  $("prompt-button").disabled = !current;
  const job = state.jobs.find(j => j.id === selected);
  showDetail(job || null);
}
function renderProfiles() {
  $("profiles").replaceChildren(...state.profiles.map(p => {
    const button = el("button", p.name, "profile" + (p.name === profile ? " active" : ""));
    button.append(el("span", p.naver_id + " / " + p.category));
    button.setAttribute("aria-pressed", String(p.name === profile));
    button.onclick = safe(async () => { profile = p.name; selected = null; await load(); });
    return button;
  }));
}
function renderJobs() {
  const filter = $("filter").value;
  const jobs = state.jobs.filter(j => !filter || (filter === "active" ? activeStates.includes(j.status) : j.status === filter));
  $("job-count").textContent = state.jobs.length;
  $("counts").replaceChildren(el("span", "준비·초안 " + (state.counts.pending + state.counts.draft)),
    el("span", "검토 " + state.counts.reviewed), el("span", "완료 기록 " + state.counts.done));
  if (!jobs.length) {
    $("jobs").replaceChildren(el("p", state.jobs.length ? "선택한 상태의 작업이 없습니다." : "아직 등록한 글이 없습니다. ‘글 추가’에서 주소와 본문 메모를 넣어 주세요.", "empty-list"));
    return;
  }
  $("jobs").replaceChildren(...jobs.map(j => {
    const button = el("button", undefined, "job" + (j.id === selected ? " active" : ""));
    button.setAttribute("aria-pressed", String(j.id === selected));
    const head = el("div", undefined, "job-head");
    head.append(el("span", "#" + j.id + "  " + state.actions[j.action]), el("span", statusLabel(j), "badge " + j.status));
    button.append(head, el("h3", j.title || j.url.replace("https://blog.naver.com/", "")),
      el("p", j.draft || j.excerpt || j.evidence || "본문 메모를 넣으면 초안을 준비할 수 있습니다."));
    button.onclick = () => { selected = j.id; renderJobs(); showDetail(j); };
    return button;
  }));
}
function showDetail(job) {
  $("detail").hidden = !job;
  $("detail-empty").hidden = Boolean(job);
  if (!job) { selected = null; return; }
  $("detail-action").textContent = "#" + job.id + " / " + state.actions[job.action];
  $("detail-status").textContent = statusLabel(job);
  $("detail-status").className = "badge " + job.status;
  $("detail-title").textContent = job.title || "제목을 입력해 주세요";
  $("detail-url").href = job.url;
  $("detail-url").textContent = job.url;
  $("source-title").value = job.title;
  $("source-excerpt").value = job.excerpt;
  $("draft-text").value = job.draft;
  $("draft-section").hidden = job.action === "like";
  $("like-review").hidden = job.action !== "like";
  $("evidence").value = job.evidence;
  $("result-status").value = ["done", "skipped", "uncertain"].includes(job.status) ? job.status : "done";
  $("evidence-type").textContent = job.evidence_type === "legacy_record" ? "이전 기록에서 가져옴" : job.evidence_type === "user_report" ? "사용자가 입력한 확인 기록" : "자동 게시 여부를 확인하는 기능은 없습니다.";
  $("reopen-area").hidden = activeStates.includes(job.status);
  $("reopen-reason").value = "";
  $("history").open = false;
  $("events").replaceChildren();
  const closed = !activeStates.includes(job.status);
  $("save-draft").disabled = closed;
  $("review").disabled = closed;
  $("review-like").disabled = closed;
  updateLength();
}
function updateLength() { $("draft-length").textContent = $("draft-text").value.length + " / 1500"; }
function safe(fn) {
  return async event => {
    if (event) event.preventDefault();
    try { await fn(event); } catch (error) { notify(error.message); }
  };
}
async function mutate(route, data, message) {
  await request(route, data);
  await load();
  notify(message);
}
async function copy(id) {
  const text = $(id).value;
  if (!text.trim()) throw new Error("복사할 내용이 없습니다.");
  try { await navigator.clipboard.writeText(text); notify("복사했습니다."); }
  catch { $(id).focus(); $(id).select(); notify("내용을 선택했습니다. Ctrl+C로 복사해 주세요."); }
}
$("new-profile").onclick = () => $("profile-dialog").showModal();
$("help").onclick = () => $("help-dialog").showModal();
document.querySelectorAll(".close-dialog").forEach(b => { b.onclick = () => b.closest("dialog").close(); });
$("new-target").onclick = () => { $("add-profile-label").textContent = profile + " 계정에 추가합니다."; $("target-dialog").showModal(); };
$("profile-form").onsubmit = safe(async event => {
  const data = Object.fromEntries(new FormData(event.target));
  await request("/api/profile", data);
  profile = data.name; selected = null;
  $("profile-dialog").close(); event.target.reset();
  await load(); notify("계정 구분을 저장했습니다.");
});
$("target-form").onsubmit = safe(async event => {
  const form = new FormData(event.target), data = Object.fromEntries(form);
  data.profile = profile; data.actions = form.getAll("action"); delete data.action;
  const result = await request("/api/add", data);
  selected = result.jobs[0].id; profile = result.profile;
  $("target-dialog").close(); event.target.reset();
  await load(); notify(result.added_jobs ? result.added_jobs + "개 작업을 추가했습니다." : "이미 등록된 작업입니다. 기존 기록을 보존했습니다.");
});
$("refresh").onclick = safe(load);
$("shutdown").onclick = safe(async () => {
  await request("/api/shutdown", {});
  document.querySelectorAll("button").forEach(button => { button.disabled = true; });
  notify("앱을 종료했습니다. 기록은 저장되어 있습니다. 다시 사용할 때 실행 명령으로 켜 주세요.");
});
$("filter").onchange = renderJobs;
$("draft-text").oninput = updateLength;
async function persistSource() {
  const job = state.jobs.find(j => j.id === selected);
  if ($("source-title").value !== job.title || $("source-excerpt").value !== job.excerpt) {
    await request("/api/source", {id: selected, title: $("source-title").value, excerpt: $("source-excerpt").value});
  }
}
$("save-source").onclick = safe(async () => {
  const unsavedDraft = $("draft-text").value;
  await mutate("/api/source", {id: selected, title: $("source-title").value, excerpt: $("source-excerpt").value}, "본문 메모를 저장했습니다. 진행 중인 작업은 다시 검토해 주세요.");
  $("draft-text").value = unsavedDraft; updateLength();
});
$("save-draft").onclick = safe(async () => {
  await persistSource();
  await mutate("/api/draft", {id: selected, text: $("draft-text").value}, "초안을 저장했습니다.");
});
$("review").onclick = safe(async () => {
  await persistSource();
  const job = state.jobs.find(j => j.id === selected);
  if ($("draft-text").value !== job.draft) {
    await request("/api/draft", {id: selected, text: $("draft-text").value});
  }
  await mutate("/api/review", {id: selected}, "검토 완료로 기록했습니다. 외부 등록은 하지 않았습니다.");
});
$("review-like").onclick = safe(async () => {
  await persistSource();
  await mutate("/api/review", {id: selected}, "검토 완료로 기록했습니다.");
});
$("record").onclick = safe(() => mutate("/api/record", {id: selected, status: $("result-status").value, evidence: $("evidence").value}, "직접 확인한 결과를 저장했습니다."));
$("reopen").onclick = safe(() => mutate("/api/reopen", {id: selected, reason: $("reopen-reason").value}, "작업을 다시 열었습니다. 이전 기록은 변경 기록에 남아 있습니다."));
$("copy-draft").onclick = safe(() => copy("draft-text"));
$("copy-prompt").onclick = safe(() => copy("prompt-text"));
$("prompt-button").onclick = safe(async () => {
  const data = await request("/api/prompt?profile=" + encodeURIComponent(profile) + "&count=5");
  $("prompt-text").value = data.prompt; $("prompt-dialog").showModal();
});
$("history").ontoggle = safe(async () => {
  if (!$("history").open || !selected) return;
  const events = await request("/api/events?id=" + selected);
  $("events").replaceChildren(...events.map(e => el("li", new Date(e.created_at).toLocaleString("ko-KR") + " · " + e.kind + "\n" + e.detail)));
});
safe(load)();
