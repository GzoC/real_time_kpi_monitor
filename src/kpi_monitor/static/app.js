"use strict";
const $ = (id) => document.getElementById(id);
const num = (n, digits = 0) => new Intl.NumberFormat("es-CL", {maximumFractionDigits: digits, minimumFractionDigits: digits}).format(n);
const time = (date) => new Intl.DateTimeFormat("es-CL", {hour:"2-digit", minute:"2-digit", timeZone:"UTC", hourCycle:"h23"}).format(new Date(date));
const day = (date) => new Intl.DateTimeFormat("es-CL", {day:"2-digit", month:"short", year:"numeric", timeZone:"UTC"}).format(new Date(date));
const pct = (n) => n === null ? "Sin datos" : `${num(n * 100, 1)} %`;
const minutes = (s) => `${num(s / 60, 1)} min`;
let selected = "", current = null, controller = null, demo = false, actionBusy = false, refreshing = false;
let shiftSignature = "";
let generation = 0;

async function request(url, options = {}, signal) {
  let response;
  try { response = await fetch(url, {...options, signal}); }
  catch (error) { if (error.name === "AbortError" || error.name === "TimeoutError") throw error; throw new Error("No hay respuesta de la API local."); }
  if (!response.ok) throw new Error(`El servicio respondió HTTP ${response.status}.`);
  return response.json();
}
function setText(id, text) { $(id).textContent = text; }
function metric(id, value) {
  $(id).replaceChildren(document.createTextNode(value === null ? "—" : num(value * 100, 1)));
  if (value !== null) { const unit = document.createElement("small"); unit.textContent = "%"; $(id).append(unit); }
  const meter = $(`${id}-meter`);
  if (meter) meter.style.width = `${value === null ? 0 : Math.min(100, value * 100)}%`;
}
function setError(error) {
  $("error").hidden = false;
  setText("error-detail", `${error.message} ${current ? "Las cifras visibles corresponden a la última consulta correcta." : "Comprueba que la aplicación siga ejecutándose."}`);
  setText("connection", "Sin actualización"); $("connection").classList.add("offline");
  setText("updated", "Actualización interrumpida");
}
function chart(points) {
  const width = Math.max(620, points.length * 65), height = 180, left = 38, top = 9, plotHeight = 132, bottom = 141;
  const step = (width - left - 10) / points.length;
  let shapes = `<title>OEE por período de diez minutos</title><desc>${points.map(p => `${time(p.start)}: ${p.status === "planned_break" ? "descanso" : pct(p.oee)}`).join(". ")}</desc>`;
  for (const level of [0, .5, 1]) {
    const y = bottom - level * plotHeight;
    shapes += `<line x1="${left}" x2="${width}" y1="${y}" y2="${y}" stroke="#e6ece4" stroke-dasharray="3 4"/><text x="0" y="${y+3}" fill="#6e7b70" font-size="9">${level*100}%</text>`;
  }
  points.forEach((p,i) => {
    const x = left + step*i + step*.22, w = step*.56;
    const label = p.status === "planned_break" ? "Pausa" : p.oee === null ? "—" : `${num(p.oee*100, 0)}%`;
    const color = p.status === "planned_break" ? "#e4e9e3" : p.oee === null ? "#e8b86b" : "#78a879";
    const h = p.oee === null ? 6 : Math.max(2, p.oee * plotHeight);
    shapes += `<rect x="${x}" y="${bottom-h}" width="${w}" height="${h}" rx="3" fill="${color}"/><text x="${x+w/2}" y="${Math.max(top+8,bottom-h-7)}" text-anchor="middle" fill="#49614b" font-size="9">${label}</text><text x="${x+w/2}" y="${height-10}" text-anchor="middle" fill="#6e7b70" font-size="9">${time(p.start)}</text>`;
  });
  $("chart").innerHTML = `<svg viewBox="0 0 ${width} ${height}" style="min-width:${points.length > 8 ? width : 0}px" role="img" xmlns="http://www.w3.org/2000/svg">${shapes}</svg>`;
}
function render(data) {
  current = data;
  const {shift:s, report:r, metadata:m} = data;
  $("dashboard").hidden = false; $("empty").hidden = true; $("export").disabled = false;
  setText("source", s.source === "synthetic" ? "Demostración · datos sintéticos" : "Datos externos");
  setText("period", `${day(s.start)} · ${time(s.start)}–${time(s.end)} UTC`);
  setText("machine", s.machine_id);
  ["oee", "availability", "performance", "quality"].forEach(key => metric(key, r[key]));
  const states = {valid:"Cálculo con cobertura completa", insufficient_data:"Desconocido · cobertura incompleta", invalid_configuration:"Revisar ciclo ideal y conteos", no_production:"Sin piezas producidas"};
  setText("oee-status", states[r.status]);
  setText("availability-detail", `${minutes(r.running_seconds)} en marcha de ${minutes(r.planned_seconds)}`);
  setText("performance-detail", `Ciclo ideal: ${num(s.ideal_cycle_seconds, 1)} s / pieza`);
  setText("quality-detail", `${num(r.good_count)} buenas de ${num(r.total_count)} observadas`);
  setText("coverage-title", `Cobertura de datos: ${pct(r.coverage)}`);
  setText("coverage-description", r.coverage < 1 ? `${minutes(r.missing_seconds)} sin cobertura válida. No se imputan piezas ni OEE.` : "Todos los intervalos planificados están cubiertos. Las pausas están excluidas.");
  $("coverage-dot").style.background = r.coverage < 1 ? "#b77d29" : "#196349";
  setText("latest", m.last_event_end ? `${day(m.last_event_end)} · ${time(m.last_event_end)} UTC` : "Sin intervalos recibidos");
  const age = m.event_age_seconds === null ? "Sin señal" : `${num(Math.max(0,m.event_age_seconds)/60,1)} min desde el último intervalo`;
  setText("freshness", s.source === "synthetic" ? "Histórico simulado · no es señal de una planta" : m.clock_ahead ? "Advertencia: evento fechado en el futuro" : m.stale ? `Señal atrasada · ${age}` : m.phase === "finished" ? `Turno finalizado · ${age}` : age);
  ["planned", "running", "stopped", "missing"].forEach(key => setText(key, minutes(r[`${key}_seconds`])));
  setText("good", num(r.good_count)); setText("rejects", num(r.total_count-r.good_count)); setText("total", num(r.total_count));
  chart(data.series);
  const active = data.alerts.filter(a => a.active);
  setText("alert-count", String(active.length));
  $("alerts").replaceChildren();
  if (!active.length) { const p = document.createElement("p"); p.className = "ok-message"; p.textContent = "Sin alertas activas para este turno."; $("alerts").append(p); }
  active.forEach(a => {
    const row = document.createElement("div"); row.className = `alert ${a.severity}`;
    const severity = document.createElement("span"); severity.className = "severity"; severity.textContent = a.severity === "critical" ? "CRÍTICA" : "ATENCIÓN";
    const description = document.createElement("p"); description.textContent = a.message;
    const action = document.createElement(a.acknowledged ? "span" : "button");
    action.className = a.acknowledged ? "ack" : "button"; action.textContent = a.acknowledged ? "✓ Reconocida" : "Reconocer";
    if (!a.acknowledged) { action.setAttribute("aria-label", `Reconocer alerta: ${a.message}`); action.addEventListener("click", async () => { action.disabled = true; try { await request(`/api/alerts/${a.id}/acknowledge`, {method:"POST"}, AbortSignal.timeout(8000)); await refresh(); } catch(error) { action.disabled=false; setError(error); } }); }
    row.append(severity, description, action); $("alerts").append(row);
  });
  setText("event-count", `${num(data.event_count)} eventos persistidos`);
  $("events").replaceChildren();
  [...data.events].reverse().forEach(e => {
    const row = document.createElement("tr");
    [time(e.start), time(e.end), e.state === "running" ? "En marcha" : "Parada", num(e.total_count), num(e.good_count), e.event_id].forEach((text, i) => {
      const cell = document.createElement("td");
      if (i === 2) { const badge = document.createElement("span"); badge.className = `state ${e.state}`; badge.textContent = text; cell.append(badge); }
      else { cell.textContent=text; if (i===5) cell.className="mono"; }
      row.append(cell);
    }); $("events").append(row);
  });
  if (!data.events.length) { const row=document.createElement("tr"), cell=document.createElement("td"); cell.colSpan=6; cell.textContent="Aún no hay intervalos para este turno."; row.append(cell); $("events").append(row); }
}
async function refresh() {
  refreshing = true;
  const run = ++generation;
  controller?.abort(); controller = new AbortController(); const signal = controller.signal;
  const activeController = controller;
  const timer = setTimeout(() => activeController.abort(), 8000);
  try {
    const health = await request("/api/health", {}, signal);
    demo = health.demo_mode;
    const shifts = await request("/api/shifts", {}, signal);
    if (run !== generation) return;
    const signature = JSON.stringify(shifts.map(s => [s.shift_id,s.name,s.machine_id]));
    if (signature !== shiftSignature) {
      $("shift").replaceChildren();
      shifts.forEach(s => { const option = document.createElement("option"); option.value=s.shift_id; option.textContent=`${s.name} · ${s.machine_id}`; $("shift").append(option); });
      shiftSignature = signature;
    }
    if (!shifts.some(s => s.shift_id === selected)) selected = shifts.find(s=>s.shift_id==="reference")?.shift_id || shifts[0]?.shift_id || "";
    $("shift").value=selected; $("shift").disabled=!shifts.length;
    if (selected) {
      const data = await request(`/api/shifts/${encodeURIComponent(selected)}/snapshot`, {}, signal);
      if (run !== generation) return;
      render(data);
    } else { $("empty").hidden=false; $("dashboard").hidden=true; $("export").disabled=true; current=null; }
    $("error").hidden=true; $("connection").classList.remove("offline"); setText("connection", "Servicio disponible");
    setText("updated", `Última consulta: ${time(new Date())} UTC`);
    setText("rejected", `MQTT: ${num(health.rejected_messages)} mensajes rechazados en esta base de datos.`);
    $("demo-control").hidden=!demo;
    if (demo && $("scenario").options.length === 1) {
      const result=await request("/api/demo/scenarios", {}, signal);
      Object.entries(result.scenarios).forEach(([key,label]) => { const option=document.createElement("option"); option.value=key; option.textContent=label; $("scenario").append(option); });
    }
  } catch(error) { if(run===generation) setError(error.name==="AbortError" ? new Error("Tiempo de espera agotado.") : error); }
  finally { clearTimeout(timer); if (run===generation) { $("loading").hidden=true; refreshing=false; } }
}
$("shift").addEventListener("change", () => { selected=$("shift").value; refresh(); });
$("scenario").addEventListener("change", async () => {
  const name=$("scenario").value; if (!name || actionBusy) return;
  actionBusy=true; $("scenario").disabled=true;
  try { const result=await request(`/api/demo/${encodeURIComponent(name)}`, {method:"POST"}, AbortSignal.timeout(8000)); selected=result.shift_id; await refresh(); setText("announcement", `Escenario cargado: ${$("scenario").selectedOptions[0].textContent}`); }
  catch(error) { setError(error); }
  finally { actionBusy=false; $("scenario").disabled=false; }
});
$("retry").addEventListener("click", refresh);
$("export").addEventListener("click", () => {
  if (!current) return;
  const blob=new Blob([JSON.stringify({shift:current.shift, report:current.report, metadata:current.metadata},null,2)],{type:"application/json"});
  const url=URL.createObjectURL(blob), link=document.createElement("a"); link.href=url; link.download=`oee-${current.shift.shift_id}.json`; link.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
});
refresh();
setInterval(() => { if (!document.hidden && !actionBusy && !refreshing) refresh(); }, 5000);
