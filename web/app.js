// [IA] Claude Code – codigo do labirinto animado (canvas), graficos SVG, tabelas e galeria do site
/* Projeto Grafos · interface. Os dados vem de data.js (gerado por build_data.py). */
(() => {
const D = window.DADOS;
const $ = (s) => document.querySelector(s);
const fmt = (n) => n.toLocaleString("pt-BR");

const ALGS = [
  // [IA] Claude – cores dos algoritmos iguais as dos graficos dos notebooks (CORES_ALGORITMOS, notebook 02, secao 12)
  { id: "BFS", nome: "BFS", cor: "#0072B2" },
  { id: "DFS", nome: "DFS", cor: "#D55E00" },
  { id: "DIJKSTRA", nome: "Dijkstra", cor: "#009E73" },
  { id: "BELLMAN_FORD", nome: "Bellman-Ford", cor: "#CC79A7" },
  { id: "BELLMAN_FORD_FONTE_CONSUMIVEL", nome: "Bellman-Ford (fonte consumível)", cor: "#E3AFCB" },
];

/* ---------- regras das casas ---------- */
const CUSTO = { ".": 1, S: 1, G: 1, ",": 3, "~": 5 };
const TEMA = {
  "#": "#1a1d3a", ".": "#0f1226", S: "#10b981", G: "#f43f5e", ",": "#6b4f2a", "~": "#1d4ed8",
  "+": "#0f1226", "*": "#0f1226",
};
const LEGENDA = [
  ["#1a1d3a", "Parede"], ["#0f1226", "Chão (1)"], ["#6b4f2a", "Lama (3)"], ["#1d4ed8", "Água (5)"],
  ["#facc15", "Chave"], ["#f97316", "Porta"], ["#34d399", "Bônus (−4)"], ["#e879f9", "Fonte (−2)"],
  ["#10b981", "Início S"], ["#f43f5e", "Saída G"],
  ["rgba(244,63,94,.55)", "Estado-armadilha"], ["rgba(255,255,255,.08)", "Fora da camada"],
];
const SETA = { "^": [0, -1], ">": [1, 0], v: [0, 1], "<": [-1, 0] };

function custoEntrada(ch, pos, vistos, fonteConsumivel) {
  if (ch === "+") { const k = pos.join(","); const novo = !vistos.has(k); vistos.add(k); return novo ? -4 : 1; }
  if (ch === "*") {
    if (!fonteConsumivel) return -2;
    const k = pos.join(","); const novo = !vistos.has(k); vistos.add(k); return novo ? -2 : 1;
  }
  return CUSTO[ch] ?? 1;
}

/* percorre o caminho calculando custo e chaves em cada passo */
function indicesBonus(mapa) {
  if (mapa._bi) return mapa._bi;
  const m = {}; let n = 0;
  mapa.grade.forEach((l, r) => [...l].forEach((ch, c) => { if (ch === "+") m[r + "," + c] = n++; }));
  return (mapa._bi = m);
}

function simular(mapa, caminho, fonteConsumivel) {
  const out = []; let custo = 0; const chaves = new Set(); const vistos = new Set();
  const bonus = new Set(), idx = indicesBonus(mapa);
  caminho.forEach(([r, c], i) => {
    const ch = mapa.grade[r][c];
    if (i > 0) custo += custoEntrada(ch, [r, c], vistos, fonteConsumivel);
    if (i > 0 && ch === "+") bonus.add(idx[r + "," + c]);
    if (/[a-d]/.test(ch)) chaves.add(ch);
    out.push({ custo, chaves: [...chaves].sort().join(""), bonus: [...bonus].sort((a, b) => a - b) });
  });
  return out;
}

/* ---------- labirinto ---------- */
const cv = $("#cv"), ctx = cv ? cv.getContext("2d") : null;
const S = { mapa: null, alg: "BFS", sol: null, sim: [], passo: 0, tocando: false, acc: 0, ultimo: 0, cell: 24, camada: "auto", armadilha: false };

function solucaoDe(mapa, alg) {
  const s = D.solucoes[mapa][alg === "BELLMAN_FORD_FONTE_CONSUMIVEL" ? alg : alg];
  return s || null;
}

function montarMapas() {
  const sel = $("#selMapa");
  Object.values(D.mapas).forEach((m) => {
    const o = document.createElement("option");
    o.value = m.id; o.textContent = `${m.id.toUpperCase()} · ${m.nome}`;
    sel.appendChild(o);
  });
  sel.onchange = () => escolherMapa(sel.value);
  $("#legenda").innerHTML = LEGENDA.map(([c, t]) => `<span><i style="background:${c}"></i>${t}</span>`).join("");
}

/* ---------- camadas e estados-armadilha ---------- */
const rotCamada = (k) => (k === "" ? "sem chaves" : "chaves " + k.split("").join(" "));

function camadaVisivel() {
  return S.camada === "auto" ? (S.sim[S.passo]?.chaves || "") : S.camada;
}
function armadilhasDa(mapaId) { return D.armadilhas[mapaId] || []; }

function montarCamadas() {
  const info = D.camadas[S.mapa.id], seg = $("#segCamada");
  seg.parentElement.hidden = info.ordem.length < 2;
  seg.innerHTML = "";
  [["auto", "Seguir o percurso"], ...info.ordem.map((k) => [k, k === "" ? "−" : k])].forEach(([k, t]) => {
    const b = document.createElement("button");
    b.textContent = t; b.dataset.k = k; b.title = k === "auto" ? "A camada acompanha as chaves do jogador" : rotCamada(k);
    b.onclick = () => { S.camada = k; atualizarCamadas(); desenhar(); };
    seg.appendChild(b);
  });
  const chk = $("#chkArmadilha"), temArm = armadilhasDa(S.mapa.id).length > 0;
  chk.disabled = !temArm;
  chk.parentElement.style.opacity = temArm ? 1 : .45;
  chk.parentElement.title = temArm ? "Estados alcançáveis a partir de S, mas sem caminho até o ALVO" : "Este mapa não tem estados-armadilha";
  if (!temArm) { chk.checked = false; S.armadilha = false; }
  atualizarCamadas();
}

function atualizarCamadas() {
  const info = D.camadas[S.mapa.id], vis = camadaVisivel();
  [...$("#segCamada").children].forEach((b) => {
    b.classList.toggle("on", b.dataset.k === S.camada);
    b.classList.toggle("live", S.camada !== "auto" && b.dataset.k === (S.sim[S.passo]?.chaves || "") && b.dataset.k !== S.camada);
  });
  const casas = (info.casas[vis] || []).length;
  const arm = armadilhasDa(S.mapa.id).filter((a) => a[2] === vis).length;
  let h = `Camada exibida: <b>${rotCamada(vis)}</b> · <b>${casas}</b> casas alcançáveis`;
  if (arm) h += ` · <span class="trap"><b>${arm}</b> estados-armadilha</span>`;
  if (info.ordem.length > 1) h += `<br>Arcos entre camadas: <b>${info.arcos_entre_camadas}</b>`;
  $("#infoCamada").innerHTML = h;
}
if (cv) $("#chkArmadilha").onchange = (e) => { S.armadilha = e.target.checked; desenhar(); };
/* o realce pulsa: redesenha mesmo com o percurso parado */
(function pulsar() { if (S.armadilha && !S.tocando) desenhar(); requestAnimationFrame(pulsar); })();

function montarAlgs() {
  const seg = $("#segAlg"); seg.innerHTML = "";
  ALGS.forEach((a) => {
    const existe = !!D.solucoes[S.mapa.id][a.id];
    if (a.id === "BELLMAN_FORD_FONTE_CONSUMIVEL" && !existe) return;
    const b = document.createElement("button");
    b.textContent = a.nome; b.dataset.id = a.id; b.style.setProperty("--c", a.cor);
    if (!existe) b.disabled = true;
    b.onclick = () => escolherAlg(a.id);
    seg.appendChild(b);
  });
}

function escolherMapa(id) {
  S.mapa = D.mapas[id];
  $("#selMapa").value = id;
  S.camada = "auto";
  montarCamadas();
  montarAlgs();
  dimensionar();
  const ok = [...$("#segAlg").children].some((b) => b.dataset.id === S.alg);
  escolherAlg(ok ? S.alg : "BFS");
  tabela();
}

function escolherAlg(id) {
  S.alg = id;
  [...$("#segAlg").children].forEach((b) => b.classList.toggle("on", b.dataset.id === id));
  S.sol = solucaoDe(S.mapa.id, id);
  const consum = id === "BELLMAN_FORD_FONTE_CONSUMIVEL";
  S.sim = S.sol && S.sol.caminho.length ? simular(S.mapa, S.sol.caminho, consum) : [];
  S.passo = 0; S.acc = 0;
  const sc = $("#scrub"); sc.max = Math.max(0, S.sim.length - 1); sc.value = 0;
  resultado();
  desenhar();
  atualizarLeitura();
  if (S.sim.length) tocar(true); else tocar(false);
}

function resultado() {
  const { sol } = S, el = $("#resultado"), ov = $("#overlay");
  ov.hidden = true; ov.className = "overlay";
  let cls = "ok", html = "";
  const nome = ALGS.find((a) => a.id === S.alg).nome;
  if (sol.status === "OK") {
    html = `<b>${nome}</b> chegou à saída em <b>${sol.passos}</b> passos, com custo total <b>${sol.custo}</b>.`;
    if (sol.custo !== undefined && S.sim.length && S.sim.at(-1).custo !== sol.custo) {
      html += ` <span style="color:var(--gold)">(custo recalculado na tela: ${S.sim.at(-1).custo})</span>`;
    }
  } else if (sol.status === "RECUSA") {
    cls = "warn";
    html = `<b>${nome}</b> recusa este mapa: há casas com peso negativo e o Dijkstra só aceita pesos não negativos.`;
    mostrar(ov, "warn", "Dijkstra recusou o mapa", "Este mapa tem bônus ou fonte de energia com custo negativo.");
  } else if (sol.status === "CICLO_NEGATIVO") {
    cls = "warn";
    html = `<b>${nome}</b> detectou um <b>ciclo negativo</b> entre (3,5) e (3,4): cada volta custa −1, então o menor custo não existe.`;
    mostrar(ov, "warn", "Ciclo negativo detectado", "A fonte de energia vale −2 toda vez que se entra nela. Ir e voltar custa −1 por volta, para sempre.");
  } else {
    cls = "bad";
    html = `<b>${nome}</b> não achou caminho: a saída é inalcançável neste mapa.`;
    mostrar(ov, "bad", "Sem solução", "A porta que guarda a saída exige uma chave que está trancada atrás dela.");
  }
  el.className = "result " + cls; el.innerHTML = html;
}
function mostrar(ov, cls, t, s) { ov.className = "overlay " + cls; ov.innerHTML = `${t}<small>${s}</small>`; ov.hidden = false; }

/* ---------- desenho ---------- */
function dimensionar() {
  const g = S.mapa.grade, cols = g[0].length, rows = g.length;
  const w = Math.max(280, ($(".canvas-wrap").clientWidth || 700) - 28);
  S.cell = Math.max(7, Math.min(54, Math.floor(w / cols)));
  const dpr = window.devicePixelRatio || 1;
  cv.width = cols * S.cell * dpr; cv.height = rows * S.cell * dpr;
  cv.style.width = cols * S.cell + "px"; cv.style.height = rows * S.cell + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }

function desenhar() {
  if (!S.mapa) return;
  const g = S.mapa.grade, k = S.cell, rows = g.length, cols = g[0].length;
  ctx.clearRect(0, 0, cols * k, rows * k);
  const coletado = new Set(), comido = new Set();
  const cam = S.sol ? S.sol.caminho : [];
  for (let i = 0; i <= S.passo && i < cam.length; i++) {
    const [r, c] = cam[i], ch = g[r][c];
    if (/[a-d+]/.test(ch) || (ch === "*" && S.alg === "BELLMAN_FORD_FONTE_CONSUMIVEL")) coletado.add(r + "," + c);
  }
  const chavesAtuais = S.sim[S.passo]?.chaves || "";
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const ch = g[r][c], x = c * k, y = r * k, p = Math.max(1, k * 0.06);
    if (ch === "#") { ctx.fillStyle = TEMA["#"]; rr(x, y, k, k, k * 0.14); ctx.fill(); continue; }
    const base = TEMA[ch] || TEMA["."];
    ctx.fillStyle = (ch === "," || ch === "~" || ch === "S" || ch === "G") ? base : TEMA["."];
    rr(x + p, y + p, k - 2 * p, k - 2 * p, k * 0.14); ctx.fill();
    if (ch === "~") { ctx.strokeStyle = "rgba(147,197,253,.55)"; ctx.lineWidth = Math.max(1, k * .06);
      for (const f of [.38, .62]) { ctx.beginPath(); ctx.moveTo(x + k * .2, y + k * f); ctx.quadraticCurveTo(x + k * .35, y + k * (f - .1), x + k * .5, y + k * f); ctx.quadraticCurveTo(x + k * .65, y + k * (f + .1), x + k * .8, y + k * f); ctx.stroke(); } }
    if (ch === "," ) { ctx.fillStyle = "rgba(0,0,0,.25)"; [[.3,.35],[.65,.6],[.4,.7]].forEach(([a,b])=>{ctx.beginPath();ctx.arc(x+k*a,y+k*b,k*.07,0,7);ctx.fill();}); }
    const letra = (txt, cor, tam = .52) => { if (k < 11) return; ctx.fillStyle = cor; ctx.font = `800 ${Math.floor(k * tam)}px Inter`; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(txt, x + k / 2, y + k / 2 + k * .03); };
    if (ch === "S" || ch === "G") letra(ch, "#fff", .55);
    else if (/[a-d]/.test(ch)) { const got = coletado.has(r + "," + c);
      ctx.globalAlpha = got ? .3 : 1; ctx.fillStyle = "#facc15"; ctx.beginPath(); ctx.arc(x + k / 2, y + k / 2, k * .3, 0, 7); ctx.fill(); letra(ch, "#3b2f00", .42); ctx.globalAlpha = 1; }
    else if (/[A-D]/.test(ch)) { const aberta = chavesAtuais.includes(ch.toLowerCase());
      ctx.fillStyle = aberta ? "rgba(249,115,22,.22)" : "#f97316"; rr(x + k * .18, y + k * .12, k * .64, k * .76, k * .12); ctx.fill();
      ctx.strokeStyle = "#f97316"; ctx.lineWidth = Math.max(1, k * .06); ctx.stroke(); letra(ch, aberta ? "#fdba74" : "#3b1500", .42); }
    else if (SETA[ch]) { const [dx, dy] = SETA[ch]; ctx.strokeStyle = "#38bdf8"; ctx.fillStyle = "#38bdf8"; ctx.lineWidth = Math.max(1.5, k * .1); ctx.lineCap = "round";
      const cx = x + k / 2, cy = y + k / 2, L = k * .26; ctx.beginPath(); ctx.moveTo(cx - dx * L, cy - dy * L); ctx.lineTo(cx + dx * L, cy + dy * L); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(cx + dx * L * 1.5, cy + dy * L * 1.5); ctx.lineTo(cx + dx * L * .3 - dy * L * .9, cy + dy * L * .3 + dx * L * .9); ctx.lineTo(cx + dx * L * .3 + dy * L * .9, cy + dy * L * .3 - dx * L * .9); ctx.fill(); }
    else if (ch === "+") { const got = coletado.has(r + "," + c); ctx.globalAlpha = got ? .3 : 1; ctx.fillStyle = "#34d399"; ctx.beginPath();
      for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rad = (i % 2 ? .13 : .3) * k; ctx.lineTo(x + k / 2 + Math.cos(a) * rad, y + k / 2 + Math.sin(a) * rad); } ctx.fill(); ctx.globalAlpha = 1; }
    else if (ch === "*") { ctx.fillStyle = "#e879f9"; ctx.beginPath(); ctx.moveTo(x + k * .56, y + k * .12); ctx.lineTo(x + k * .3, y + k * .55); ctx.lineTo(x + k * .5, y + k * .55); ctx.lineTo(x + k * .42, y + k * .88); ctx.lineTo(x + k * .72, y + k * .42); ctx.lineTo(x + k * .5, y + k * .42); ctx.closePath(); ctx.fill(); }
  }
  /* camada exibida: esmaece casas que nao existem nela; realca armadilhas */
  const info = D.camadas[S.mapa.id], vis = camadaVisivel();
  if (info.ordem.length > 1) {
    const dentro = new Set((info.casas[vis] || []).map(([r, c]) => r + "," + c));
    ctx.fillStyle = "rgba(8,10,22,.72)";
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++)
      if (g[r][c] !== "#" && !dentro.has(r + "," + c)) { rr(c * k, r * k, k, k, k * 0.14); ctx.fill(); }
  }
  if (S.armadilha) {
    const pulso = 0.5 + 0.5 * Math.sin(performance.now() / 380);
    armadilhasDa(S.mapa.id).filter((a) => a[2] === vis).forEach(([r, c]) => {
      const x = c * k, y = r * k, p = Math.max(1, k * 0.06);
      ctx.fillStyle = `rgba(244,63,94,${0.38 + 0.2 * pulso})`; rr(x + p, y + p, k - 2 * p, k - 2 * p, k * 0.14); ctx.fill();
      ctx.strokeStyle = "#fb7185"; ctx.lineWidth = Math.max(1.5, k * .08); ctx.stroke();
      if (k >= 11) { ctx.strokeStyle = "#fff"; ctx.lineWidth = Math.max(1.2, k * .07); ctx.lineCap = "round"; const q = k * .3;
        ctx.beginPath(); ctx.moveTo(x + q, y + q); ctx.lineTo(x + k - q, y + k - q); ctx.moveTo(x + k - q, y + q); ctx.lineTo(x + q, y + k - q); ctx.stroke(); }
    });
  }
  /* trilha */
  if (cam.length && S.passo > 0) {
    const cor = ALGS.find((a) => a.id === S.alg).cor, cen = ([r, c]) => [c * k + k / 2, r * k + k / 2];
    ctx.lineJoin = "round"; ctx.lineCap = "round";
    ctx.shadowColor = cor; ctx.shadowBlur = k * .6; ctx.strokeStyle = cor; ctx.lineWidth = Math.max(2, k * .22); ctx.globalAlpha = .9;
    ctx.beginPath();
    for (let i = 0; i <= S.passo; i++) { const [x, y] = cen(cam[i]); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
    ctx.stroke(); ctx.shadowBlur = 0; ctx.globalAlpha = 1;
  }
  if (cam.length) {
    const [px, py] = [cam[S.passo][1] * k + k / 2, cam[S.passo][0] * k + k / 2];
    ctx.fillStyle = "#fff"; ctx.shadowColor = "#fff"; ctx.shadowBlur = k * .5; ctx.beginPath(); ctx.arc(px, py, Math.max(3, k * .27), 0, 7); ctx.fill(); ctx.shadowBlur = 0;
  }
}

function atualizarLeitura() {
  const e = S.sim[S.passo];
  $("#rdPasso").textContent = S.sim.length ? S.passo : "—";
  $("#rdCusto").textContent = e ? e.custo : "—";
  $("#rdChaves").textContent = e ? (e.chaves ? e.chaves.split("").join(" ") : "nenhuma") : "—";
  const total = Object.keys(indicesBonus(S.mapa)).length;
  $("#rdBonus").textContent = !e ? "—" : !total ? "sem bônus" : e.bonus.length ? "{" + e.bonus.join(",") + "}" : "nenhum";
  atualizarCamadas();
  $("#scrub").value = S.passo;
}

/* ---------- reproducao ---------- */
function tocar(sim) {
  S.tocando = sim; $("#btnPlay").textContent = sim ? "❚❚" : "▶"; S.ultimo = 0;
  if (sim) requestAnimationFrame(loop);
}
function loop(t) {
  if (!S.tocando) return;
  if (!S.ultimo) S.ultimo = t;
  const dt = (t - S.ultimo) / 1000; S.ultimo = t;
  const n = S.sim.length, dur = 22 / +$("#speed").value, sps = Math.max(3, n / dur);
  S.acc += dt * sps;
  while (S.acc >= 1 && S.passo < n - 1) { S.passo++; S.acc -= 1; }
  desenhar(); atualizarLeitura();
  if (S.passo >= n - 1) return tocar(false);
  requestAnimationFrame(loop);
}
if (cv) {
  $("#btnPlay").onclick = () => {
    if (!S.sim.length) return;
    if (!S.tocando && S.passo >= S.sim.length - 1) S.passo = 0;
    tocar(!S.tocando);
  };
  $("#btnReset").onclick = () => { tocar(false); S.passo = 0; desenhar(); atualizarLeitura(); };
  $("#scrub").oninput = (e) => { tocar(false); S.passo = +e.target.value; desenhar(); atualizarLeitura(); };
}
let rz; window.addEventListener("resize", () => { clearTimeout(rz); rz = setTimeout(() => { if (S.mapa) { dimensionar(); desenhar(); } }, 120); });

/* ---------- tabela comparativa ---------- */
function tabela() {
  const sols = D.solucoes[S.mapa.id];
  $("#tbMapa").textContent = S.mapa.id.toUpperCase();
  const oks = Object.values(sols).filter((s) => s.status === "OK" && s.custo !== null);
  const melhor = oks.length ? Math.min(...oks.map((s) => s.custo)) : null;
  const rot = { OK: "OK", RECUSA: "Recusa", CICLO_NEGATIVO: "Ciclo negativo", SEM_SOLUCAO: "Sem solução" };
  const linhas = Object.entries(sols).map(([id, s]) => {
    const a = ALGS.find((x) => x.id === id);
    return `<tr class="${s.status === "OK" && s.custo === melhor ? "best" : ""}"><td class="alg" style="color:${a.cor}">${a.nome}</td>
      <td>${s.passos ?? "—"}</td><td>${s.custo ?? "—"}</td><td><span class="badge ${s.status}">${rot[s.status]}</span></td></tr>`;
  }).join("");
  $("#tbl").innerHTML = `<thead><tr><th>Algoritmo</th><th>Passos</th><th>Custo</th><th>Resultado</th></tr></thead><tbody>${linhas}</tbody>`;
}

/* ---------- modelagem ---------- */
function modelagem() {
  const L = (n) => Math.max(4, (Math.log10(n) / Math.log10(3200)) * 100);
  $("#chartModel").innerHTML = Object.entries(D.metricas).map(([id, m]) =>
    `<div class="row"><span>${id.toUpperCase()}</span><div class="track">
      <div class="bar p" data-w="${L(m.G_pos.ordem)}"></div><div class="bar e" data-w="${L(m.G_est.ordem)}"></div></div>
      <em>${fmt(m.G_pos.ordem)} → ${fmt(m.G_est.ordem)}</em></div>`).join("");
  const nomes = {
    "G_pos portas como chao": ["Porta vira chão", "Atravessa a porta sem ter a chave: caminho inválido."],
    "G_pos portas como parede": ["Porta vira parede", "Nunca vai pegar a chave e voltar: não acha caminho."],
    G_est: ["Grafo de estados", "Pega a chave antes da porta: caminho válido."],
  };
  const m02 = D.modelagem.filter((r) => r.mapa === "m03");
  $("#armadilhas").innerHTML = m02.map((r) => {
    const [t, d] = nomes[r.abordagem]; const ok = r.caminho_valido === "True";
    return `<div class="t ${ok ? "good" : "badx"}"><b>${t}<span>${r.passos ? r.passos + " passos" : "sem caminho"} ${ok ? "✓" : "✗"}</span></b><span>${d}</span></div>`;
  }).join("") + `<p class="note">Exemplo do mapa M03 (três chaves).</p>`;
}

/* ---------- parte 2 ---------- */
function parte2() {
  const P = D.parte2;
  $("#dsNome").textContent = P.dataset;
  $("#tblRec").innerHTML = `<thead><tr><th>Usuários</th><th>Nós</th><th>Arcos</th><th>% dos arcos</th></tr></thead><tbody>` +
    P.recortes.map((r) => `<tr><td>${r["usuarios (%)"]}%</td><td>${fmt(r.nos)}</td><td>${fmt(r.arcos)}</td><td>${r["arcos (%)"].toString().replace(".", ",")}%</td></tr>`).join("") + "</tbody>";
  if (P.ciclo) {
    const nos = P.ciclo.slice(0, -1);
    $("#negCycle").innerHTML = `<b>Ciclo negativo na rede completa</b> (Bellman-Ford)
      <div class="loop">${nos.map((n) => `<i>${n}</i><s>→</s>`).join("")}<i>${P.ciclo.at(-1)}</i></div>
      Custo do ciclo: <b>${P.custo_ciclo}</b>. Dois usuários que se marcam como inimigos permitem reduzir o custo indefinidamente.`;
  }
  /* grafico de barras agrupadas, escala log */
  const algs = ALGS.slice(0, 4).map((a) => [a.nome, a.cor]); // [IA] Claude – mesmas cores dos notebooks
  const W = 640, H = 330, m = { l: 52, r: 10, t: 14, b: 62 }, iw = W - m.l - m.r, ih = H - m.t - m.b;
  const lo = Math.log10(.5), hi = Math.log10(1000), y = (v) => m.t + ih - ((Math.log10(v) - lo) / (hi - lo)) * ih;
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Tempo por recorte">`;
  [1, 10, 100, 1000].forEach((v) => { s += `<line x1="${m.l}" x2="${W - m.r}" y1="${y(v)}" y2="${y(v)}" stroke="rgba(255,255,255,.09)"/><text x="${m.l - 8}" y="${y(v) + 4}" text-anchor="end" fill="#9aa0c3" font-size="11">${v} ms</text>`; });
  const gw = iw / 3;
  [10, 50, 100].forEach((rec, gi) => {
    const bw = Math.min(30, (gw - 30) / 4), x0 = m.l + gi * gw + (gw - bw * 4 - 9) / 2;
    algs.forEach(([a, cor], ai) => {
      const e = P.escala.find((q) => q.alg === a && q.recorte === rec); if (!e) return;
      const x = x0 + ai * (bw + 3), top = y(e.ms);
      s += `<rect x="${x}" y="${top}" width="${bw}" height="${m.t + ih - top}" rx="4" fill="${cor}"><title>${a}, ${rec}%: ${e.ms} ms</title></rect>
            <text x="${x + bw / 2}" y="${top - 5}" text-anchor="middle" fill="#cfd3f0" font-size="10">${e.ms >= 100 ? Math.round(e.ms) : e.ms.toFixed(1)}</text>`;
    });
    s += `<text x="${m.l + gi * gw + gw / 2}" y="${H - 38}" text-anchor="middle" fill="#e8eaf6" font-size="13" font-weight="700">${rec}% dos usuários</text>`;
  });
  algs.forEach(([a, cor], i) => { const x = m.l + i * 140; s += `<rect x="${x}" y="${H - 18}" width="12" height="12" rx="3" fill="${cor}"/><text x="${x + 18}" y="${H - 8}" fill="#cfd3f0" font-size="12">${a}</text>`; });
  $("#chartEscala").innerHTML = s + "</svg>";

  const f = (n) => (n === null || n === undefined ? "—" : n);
  $("#tblPiloto").innerHTML = `<thead><tr><th>Quem recebeu</th><th>Quem marcou</th><th>Passos de volta</th><th>Custo</th><th>Situação</th></tr></thead><tbody>` +
    P.piloto.map((p) => `<tr><td>${p.origem}</td><td>${p.destino}</td><td>${f(p.passos)}</td><td>${f(p.custo)}</td>
      <td>${p.custo === null ? '<span class="badge SEM_SOLUCAO">sem volta</span>' : '<span class="badge OK">volta existe</span>'}</td></tr>`).join("") + "</tbody>";
}

/* ---------- graficos em topicos ---------- */
// [IA] Claude – pagina de graficos em topicos (um cartao por grafico). Os textos sao copiados das notas analiticas escritas pelo grupo nos notebooks
const BLOCOS = [
  { id: "exploratorias", grupo: "exp", eyebrow: "Parte 2 · AVD", titulo: "Visualizações exploratórias", texto: "Quatro gráficos para entender o comportamento dos dados do Slashdot (notebook 01)." },
  { id: "explanatorias", grupo: "expl", eyebrow: "Parte 2 · AVD", titulo: "Visualizações explanatórias", texto: "Dois gráficos que comunicam a resposta à pergunta de pesquisa (notebook 01)." },
  { id: "algoritmos", grupo: "alg", eyebrow: "Parte 2 · Grafos", titulo: "Comparação dos algoritmos", texto: "Tempo, comportamento e caminhos de BFS, DFS, Dijkstra e Bellman-Ford (notebook 02, seção 12)." },
  { id: "labirintos", grupo: "p1", eyebrow: "Parte 1", titulo: "Labirintos", texto: "Figuras dos mapas geradas pelo src/solve.py." },
];
const FOTOS = [
  { f: "parte2/distribuicao_graus.png", titulo: "Distribuição dos graus", grupo: "exp", origem: "Notebook 01 · seção 5.4 · exploratória 1",
    mostra: "O gráfico compara, em cada faixa de grau, a porcentagem dos 82.140 usuários do Slashdot que receberam aquela quantidade de marcações (azul) e a porcentagem que fizeram aquela quantidade (laranja).",
    insight: "A diferença é especialmente clara na faixa zero. Quase metade dos usuários (46,4%) não fez nenhuma marcação, enquanto 14,4% não receberam nenhuma. No outro extremo, alguns usuários receberam 501 marcações ou mais. Nenhum usuário fez tantas marcações: o maior grau de saída foi 428." },
  { f: "parte2/avd_concentracao_negativas.png", titulo: "Concentração das marcações de inimigo", grupo: "exp", origem: "Notebook 01 · seção 5.5 · exploratória 2",
    mostra: "A porcentagem acumulada das 124.130 marcações de inimigo conforme se incluem os usuários, de quem tem mais para quem tem menos, com uma curva para as feitas (laranja) e outra para as recebidas (azul).",
    insight: "Os 10% do topo fizeram 94,41% das negativas e receberam 77,33%. Elas se concentram mais em quem marca." },
  { f: "parte2/avd_recebidas_feitas.png", titulo: "Marcações recebidas e feitas", grupo: "exp", origem: "Notebook 01 · seção 6.2 · exploratória 3",
    mostra: "A porcentagem dos 82.140 usuários em três grupos: recebeu mais do que fez (azul), recebeu e fez igual (cinza) e fez mais do que recebeu (cinza).",
    insight: "A maioria (59,2%) recebeu mais do que fez, contra 33,7% que fizeram mais e 7,1% com a mesma quantidade." },
  { f: "parte2/avd_boxplot_graus.png", titulo: "Boxplot dos graus", grupo: "exp", origem: "Notebook 01 · seção 7.2 · exploratória 4",
    mostra: "Boxplots das marcações recebidas e feitas, com a mediana em linha escura e, em vermelho, os graus sinalizados pelo IQR.",
    insight: "A mediana foi 1 nos dois lados, mas os extremos diferem: 2.543 recebidas contra 428 feitas." },
  { f: "parte2/avd_caminhos_de_volta.png", titulo: "Caminhos de volta", grupo: "expl", origem: "Notebook 01 · seção 8.2 · explanatória 1",
    mostra: "A porcentagem das 1.000 marcações de cada tipo por passos de volta, de 1 a 7, e nos dois casos sem volta, com amigo em azul e inimigo em verde-azulado.",
    insight: "A volta direta foi mais comum em amigo (22,5% contra 9,8%), e a de três passos, em inimigo (24,8% contra 15,0%)." },
  { f: "parte2/avd_retorno_por_grau_saida.png", titulo: "Retorno por grau de saída", grupo: "expl", origem: "Notebook 01 · seção 9.1 · explanatória 2",
    mostra: "A porcentagem de casos com volta por faixa de marcações feitas por quem recebeu (1 a 3, 4 a 10 e 11 ou mais), com amigo em azul e inimigo em verde-azulado.",
    insight: "Inimigo teve volta mais vezes nas três faixas: 79,6% contra 70,4%, 97,7% contra 88,7% e 96,7% contra 92,5%." },
  { f: "parte2/alg_tempo_recortes.png", titulo: "Tempo por recorte", grupo: "alg", origem: "Notebook 02 · seção 12.1",
    mostra: "Cada linha é um algoritmo, e cada ponto é o tempo médio de 15 execuções. Dijkstra e Bellman-Ford usaram peso 1 para amigo e 2 para inimigo.",
    insight: "Nos recortes de 50% e 100%, a ordem do mais lento ao mais rápido foi DFS, Bellman-Ford, Dijkstra e BFS. Na rede completa, os tempos foram de cerca de 542, 394, 300 e 152 ms." },
  { f: "parte2/alg_profundidade_buscas.png", titulo: "Profundidade das buscas", grupo: "alg", origem: "Notebook 02 · seção 12.2",
    mostra: "Cada par compara a maior distância mínima da BFS com o ramo mais profundo da DFS, para a mesma origem e o mesmo recorte. Os dois máximos podem ser de usuários diferentes.",
    insight: "Nos nove casos, a BFS ficou entre 1 e 10 passos, enquanto a DFS chegou a 6.636. Por isso a BFS mede a menor volta. Na seção 6.2, ela encontrou 2 passos para o mesmo destino que a DFS alcançou em 775." },
  { f: "parte2/alg_passos_volta_piloto.png", titulo: "Passos de volta do piloto", grupo: "alg", origem: "Notebook 02 · seção 12.3",
    mostra: "Cada par de barras compara os passos de volta da BFS e do Dijkstra para uma marcação. A de 8068 para 48080 aparece sem barra porque nenhum dos dois encontrou volta.",
    insight: "Das nove marcações com volta, oito tiveram o mesmo número de passos, e só a de 3381 para 29495 passou de 5 na BFS para 6 no Dijkstra. Em três das oito, os caminhos passaram por usuários diferentes, como mostram as seções 6.1 e 7.1." },
  { f: "parte1/percurso_m03.png", titulo: "Percurso no mapa M03", grupo: "p1", origem: "Parte 1 · gerada pelo src/solve.py" },
  { f: "parte1/percurso_m08.png", titulo: "Percurso no mapa M08", grupo: "p1", origem: "Parte 1 · gerada pelo src/solve.py" },
  { f: "parte1/heatmap_multiplicidade_m08.png", titulo: "Multiplicidade de estados (M08)", grupo: "p1", origem: "Parte 1 · gerada pelo src/solve.py" },
  { f: "parte1/camadas_m02.png", titulo: "Grafo de estados por conjunto de chaves (M02)", grupo: "p1", origem: "Parte 1 · gerada pelo src/solve.py" },
  { f: "parte1/arvore_bfs_m02.png", titulo: "Árvore BFS (M02)", grupo: "p1", origem: "Parte 1 · gerada pelo src/solve.py" },
];
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
function graficosEmTopicos() {
  const alvo = $("#topicos"), lb = $("#lightbox");
  let n = 0;
  const topico = (x) => {
    n += 1;
    const texto = x.mostra
      ? `<div class="topico-texto"><div><h4>O que está sendo mostrado</h4><p>${esc(x.mostra)}</p></div><div><h4>Insight</h4><p>${esc(x.insight)}</p></div></div>`
      : "";
    return `<article class="card topico">
      <div class="topico-head"><span class="num">${n}</span><div><h3>${esc(x.titulo)}</h3><p class="note">${esc(x.origem)}</p></div></div>
      <figure class="topico-img" data-src="../out/${x.f}" data-t="${esc(x.titulo)}"><img loading="lazy" src="../out/${x.f}" alt="${esc(x.titulo)}"></figure>
      ${texto}</article>`;
  };
  $("#indice").innerHTML = BLOCOS.map((b) => `<a href="#${b.id}">${b.titulo}</a>`).join("");
  alvo.innerHTML = BLOCOS.map((b) => `<section class="block" id="${b.id}">
    <div class="head"><span class="eyebrow">${b.eyebrow}</span><h2>${b.titulo}</h2><p>${b.texto}</p></div>
    <div class="topicos">${FOTOS.filter((x) => x.grupo === b.grupo).map(topico).join("")}</div></section>`).join("");
  alvo.onclick = (e) => {
    const f = e.target.closest(".topico-img"); if (!f) return;
    lb.querySelector("img").src = f.dataset.src; lb.querySelector("p").textContent = f.dataset.t; lb.hidden = false;
  };
  lb.onclick = () => (lb.hidden = true);
  document.addEventListener("keydown", (e) => e.key === "Escape" && (lb.hidden = true));
}

/* ---------- efeitos ---------- */
function efeitos() {
  document.querySelectorAll(".block .head, .block .card, .block .gallery, .stat, .algo, .person").forEach((el) => el.classList.add("reveal"));
  const io = new IntersectionObserver((es) => es.forEach((e) => {
    if (!e.isIntersecting) return; e.target.classList.add("in");
    e.target.querySelectorAll?.(".bar").forEach((b) => (b.style.width = b.dataset.w + "%"));
    io.unobserve(e.target);
  }), { threshold: 0.01, rootMargin: "0px 0px -40px 0px" });
  if (new URLSearchParams(location.search).has("estatico") || !("IntersectionObserver" in window)) {
    document.querySelectorAll(".reveal").forEach((el) => { el.classList.add("in"); el.querySelectorAll(".bar").forEach((b) => (b.style.width = b.dataset.w + "%")); });
  }
  document.querySelectorAll(".reveal").forEach((el) => io.observe(el));
  const co = new IntersectionObserver((es) => es.forEach((e) => {
    if (!e.isIntersecting) return; co.unobserve(e.target);
    const b = e.target.querySelector("b"), alvo = +b.dataset.count, t0 = performance.now();
    (function passo(t) { const p = Math.min(1, (t - t0) / 1400), v = Math.round(alvo * (1 - Math.pow(1 - p, 3)));
      b.textContent = fmt(v); if (p < 1) requestAnimationFrame(passo); })(t0);
  }), { threshold: .5 });
  document.querySelectorAll(".stat").forEach((s) => co.observe(s));
}

if (cv) montarMapas();
if ($("#chartModel")) modelagem();
if ($("#chartEscala")) parte2();
if ($("#topicos")) graficosEmTopicos();
efeitos();
if (cv) {
  const q = new URLSearchParams(location.search);
  if (q.get("alg")) S.alg = q.get("alg");
  escolherMapa(D.mapas[q.get("mapa")] ? q.get("mapa") : "m02");
  if (q.has("armadilha")) { const c = $("#chkArmadilha"); if (!c.disabled) { c.checked = true; c.dispatchEvent(new Event("change")); } }
}
window.__S = S; /* depuracao */
})();
