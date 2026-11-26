// [IA] Claude Code – codigo do labirinto animado (canvas), graficos SVG, tabelas e galeria do site
// [IA] Claude – labirinto e modelagem refeitos: comparar 2x2, busca animada sem solucao, numeros do mapa, passo a passo e textos vindos dos dados
/* Projeto Grafos · interface. Os dados vem de data.js (gerado por src/pagina_site.py). */
(() => {
const D = window.DADOS;
const $ = (s) => document.querySelector(s);
const fmt = (n) => n.toLocaleString("pt-BR");
// figura: no site unico vem embutida (window.IMAGENS); nas paginas de web/ vem de ../out/
const IMG = (f) => (window.IMAGENS && window.IMAGENS[f]) || "../out/" + f;

const ALGS = [
  // [IA] Claude – cores dos algoritmos iguais as dos graficos dos notebooks (CORES_ALGORITMOS, notebook 02, secao 12)
  { id: "BFS", nome: "BFS", cor: "#0072B2", desc: "menos passos" },
  { id: "DFS", nome: "DFS", cor: "#D55E00", desc: "um caminho qualquer" },
  { id: "DIJKSTRA", nome: "Dijkstra", cor: "#009E73", desc: "menor custo, pesos ≥ 0" },
  { id: "BELLMAN_FORD", nome: "Bellman-Ford", cor: "#CC79A7", desc: "menor custo, aceita negativo" },
  { id: "BELLMAN_FORD_FONTE_CONSUMIVEL", nome: "Bellman-Ford (fonte consumível)", cor: "#E3AFCB", desc: "correção do m06" },
];
const alg = (id) => ALGS.find((a) => a.id === id);

/* ---------- regras das casas ---------- */
const TEMA = {
  "#": "#1a1d3a", ".": "#0f1226", S: "#10b981", G: "#f43f5e", ",": "#6b4f2a", "~": "#1d4ed8",
  "+": "#0f1226", "*": "#0f1226",
};
const LEGENDA = [
  ["#1a1d3a", "Parede"], ["#0f1226", "Chão (1)"], ["#6b4f2a", "Lama (3)"], ["#1d4ed8", "Água (5)"],
  ["#facc15", "Chave"], ["#f97316", "Porta"], ["#34d399", "Bônus (−4)"], ["#e879f9", "Fonte (−2)"],
  ["#10b981", "Início S"], ["#f43f5e", "Saída G"],
  ["rgba(244,63,94,.55)", "Estado-armadilha"], ["rgba(255,255,255,.08)", "Fora da camada"],
  ["rgba(76,141,219,.55)", "Visitado pela busca"],
];
const SETA = { "^": [0, -1], ">": [1, 0], v: [0, 1], "<": [-1, 0] };
// passos por segundo de cada posicao do controle de velocidade
const VELOCIDADES = [1, 2, 3, 5, 8, 12, 20, 35, 60, 120];

/* ---------- labirinto: estado da pagina ---------- */
const cv = $("#cv"), ctx = cv ? cv.getContext("2d") : null;
const S = { mapa: null, alg: "BFS", modo: "um", passo: 0, tocando: false, acc: 0, ultimo: 0, camada: "auto", armadilha: false };

function solucaoDe(mapaId, algId) { return (D.solucoes[mapaId] || {})[algId] || null; }

// quadros da animacao: os estados do caminho (com custo) ou, sem solucao, os estados visitados pela busca
function quadros(sol) {
  if (!sol) return [];
  if (sol.estados.length) return sol.estados;
  return sol.visitas.map(([r, c, k, b]) => [r, c, k, b, null]);
}
const emBusca = (sol) => !!sol && !sol.estados.length && sol.visitas.length > 0;
const quadroEm = (sol, passo) => { const q = quadros(sol); return q[Math.min(passo, q.length - 1)]; };
const algsComparar = () => ["BFS", "DFS", "DIJKSTRA", "BELLMAN_FORD"].filter((a) => solucaoDe(S.mapa.id, a));

function maiorPasso() {
  const ids = S.modo === "comparar" ? algsComparar() : [S.alg];
  return Math.max(0, ...ids.map((a) => quadros(solucaoDe(S.mapa.id, a)).length - 1));
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
  $("#segModo").querySelectorAll("button").forEach((b) => (b.onclick = () => escolherModo(b.dataset.modo)));
}

/* ---------- camadas e estados-armadilha ---------- */
const rotCamada = (k) => (k === "" ? "sem chaves" : "chaves " + k.split("").join(" "));

function camadaVisivel(sol) {
  if (S.camada !== "auto") return S.camada;
  const q = quadroEm(sol || solucaoDe(S.mapa.id, S.alg), S.passo);
  return q ? q[2] : "";
}
function armadilhasDa(mapaId) { return D.armadilhas[mapaId] || []; }

function montarCamadas() {
  const info = D.camadas[S.mapa.id], seg = $("#segCamada");
  seg.parentElement.hidden = info.ordem.length < 2;
  seg.innerHTML = "";
  [["auto", "Seguir o percurso"], ...info.ordem.map((k) => [k, k === "" ? "−" : k])].forEach(([k, t]) => {
    const b = document.createElement("button");
    b.textContent = t; b.dataset.k = k; b.title = k === "auto" ? "A camada acompanha as chaves do jogador" : rotCamada(k);
    b.onclick = () => { S.camada = k; atualizar(); };
    seg.appendChild(b);
  });
  const chk = $("#chkArmadilha"), temArm = armadilhasDa(S.mapa.id).length > 0;
  chk.disabled = !temArm;
  chk.parentElement.style.opacity = temArm ? 1 : .45;
  chk.parentElement.title = temArm ? "Estados alcançáveis a partir de S, mas sem caminho até o ALVO" : "Este mapa não tem estados-armadilha";
  if (!temArm) { chk.checked = false; S.armadilha = false; }
}

function atualizarCamadas() {
  const info = D.camadas[S.mapa.id], vis = camadaVisivel();
  const atual = (quadroEm(solucaoDe(S.mapa.id, S.alg), S.passo) || [0, 0, ""])[2];
  [...$("#segCamada").children].forEach((b) => {
    b.classList.toggle("on", b.dataset.k === S.camada);
    b.classList.toggle("live", S.camada !== "auto" && b.dataset.k === atual && b.dataset.k !== S.camada);
  });
  const casas = (info.casas[vis] || []).length;
  const arm = armadilhasDa(S.mapa.id).filter((a) => a[2] === vis).length;
  let h = `Camada exibida: <b>${rotCamada(vis)}</b> · <b>${casas}</b> casas alcançáveis`;
  if (arm) h += ` · <span class="trap"><b>${arm}</b> estados-armadilha</span>`;
  if (info.ordem.length > 1) h += `<br>Arcos entre camadas: <b>${info.arcos_entre_camadas}</b>`;
  $("#infoCamada").innerHTML = h;
}
if (cv) $("#chkArmadilha").onchange = (e) => { S.armadilha = e.target.checked; atualizar(); };
/* o realce pulsa: redesenha mesmo com o percurso parado */
(function pulsar() { if (cv && S.armadilha && !S.tocando && S.mapa) desenhar(); requestAnimationFrame(pulsar); })();

function montarAlgs() {
  const seg = $("#segAlg"); seg.innerHTML = "";
  ALGS.forEach((a) => {
    if (!solucaoDe(S.mapa.id, a.id)) return;
    const b = document.createElement("button");
    b.textContent = a.nome; b.dataset.id = a.id; b.style.setProperty("--c", a.cor);
    b.onclick = () => escolherAlg(a.id);
    seg.appendChild(b);
  });
}

function montarComparar() {
  $("#vistaComparar").innerHTML = algsComparar().map((id) => {
    const a = alg(id), s = solucaoDe(S.mapa.id, id);
    const resumo = s.status === "OK" ? `${s.passos} passos · custo ${s.custo}` : rotStatus[s.status];
    return `<div class="cmp" style="--c:${a.cor}"><h4>${a.nome} <small>${a.desc} · ${resumo}</small></h4>
      <div class="tela"><canvas id="cv-${id}"></canvas></div><p id="info-${id}"></p></div>`;
  }).join("");
}

function escolherMapa(id) {
  S.mapa = D.mapas[id];
  $("#selMapa").value = id;
  S.camada = "auto";
  montarCamadas();
  montarAlgs();
  montarComparar();
  const ok = !!solucaoDe(id, S.alg);
  tabela();
  numeros();
  escolherAlg(ok ? S.alg : "BFS");
}

function escolherModo(modo) {
  S.modo = modo;
  $("#segModo").querySelectorAll("button").forEach((b) => b.classList.toggle("on", b.dataset.modo === modo));
  $("#vistaUm").hidden = modo !== "um";
  $("#vistaComparar").hidden = modo !== "comparar";
  $("#campoAlg").style.visibility = modo === "um" ? "visible" : "hidden";
  S.passo = 0; S.acc = 0;
  atualizar();
  tocar(maiorPasso() > 0);
}

function escolherAlg(id) {
  S.alg = id;
  [...$("#segAlg").children].forEach((b) => b.classList.toggle("on", b.dataset.id === id));
  S.passo = 0; S.acc = 0; EXP.passo = -1;
  resultado();
  explorar();
  atualizar();
  tocar(maiorPasso() > 0);
}

/* ---------- textos do resultado (vem dos dados, servem para qualquer mapa) ---------- */
const rotStatus = { OK: "OK", RECUSA: "Recusa", CICLO_NEGATIVO: "Ciclo negativo", SEM_SOLUCAO: "Sem solução" };

function casasDoCiclo(sol) {
  const vistas = [];
  sol.caminho.forEach(([r, c]) => { const t = `(${r},${c})`; if (!vistas.includes(t)) vistas.push(t); });
  return vistas.join(", ");
}

function resultado() {
  const sol = solucaoDe(S.mapa.id, S.alg), el = $("#resultado"), ov = $("#overlay");
  ov.hidden = true; ov.className = "overlay";
  let cls = "ok", html = "";
  const nome = alg(S.alg).nome;
  if (sol.status === "OK") {
    html = `<b>${nome}</b> chegou à saída em <b>${sol.passos}</b> passos, com custo total <b>${sol.custo}</b>.`;
    if (S.alg === "DFS") html += " A DFS acha <b>um</b> caminho, não necessariamente o menor.";
    if (sol.ciclo_fora_da_rota !== null && sol.ciclo_fora_da_rota !== undefined) {
      html += ` Existe um ciclo negativo alcançável (custo ${sol.ciclo_fora_da_rota} por volta), mas dele não dá para chegar na saída, então o custo continua definido.`;
    }
  } else if (sol.status === "RECUSA") {
    cls = "warn";
    html = `<b>${nome}</b> recusa este mapa: há casas com peso negativo e o Dijkstra só aceita pesos não negativos. Use o Bellman-Ford.`;
    mostrar(ov, "warn", "Dijkstra recusou o mapa", "Este mapa tem bônus ou fonte de energia com custo negativo.");
  } else if (sol.status === "CICLO_NEGATIVO") {
    cls = "warn";
    html = `<b>${nome}</b> detectou um <b>ciclo negativo</b> passando por ${casasDoCiclo(sol)}: cada volta custa <b>${sol.custo_ciclo}</b>, então o menor custo não existe. A animação mostra uma volta.`;
    if (solucaoDe(S.mapa.id, "BELLMAN_FORD_FONTE_CONSUMIVEL")) html += " Compare com o <b>Bellman-Ford (fonte consumível)</b>, a correção de regra.";
  } else {
    cls = "bad";
    const n = sol.visitas.length;
    html = `<b>${nome}</b> não achou caminho. A animação mostra a busca visitando os <b>${n}</b> estados alcançáveis a partir de S, e nenhum deles chega na saída. Ligue o realce para ver os estados-armadilha.`;
  }
  el.className = "result " + cls; el.innerHTML = html;
}
function mostrar(ov, cls, t, s) { ov.className = "overlay " + cls; ov.innerHTML = `${t}<small>${s}</small>`; ov.hidden = false; }

/* ---------- desenho ---------- */
function dimensionarCanvas(canvas, largura) {
  const g = S.mapa.grade, cols = g[0].length, rows = g.length;
  const k = Math.max(5, Math.min(54, Math.floor(Math.max(200, largura) / cols)));
  const dpr = window.devicePixelRatio || 1;
  canvas.width = cols * k * dpr; canvas.height = rows * k * dpr;
  canvas.style.width = cols * k + "px"; canvas.style.height = rows * k + "px";
  const c2d = canvas.getContext("2d");
  c2d.setTransform(dpr, 0, 0, dpr, 0, 0);
  return k;
}

function desenharEm(canvas, k, algId) {
  const c2d = canvas.getContext("2d");
  const rr = (x, y, w, h, r) => { c2d.beginPath(); c2d.roundRect(x, y, w, h, r); };
  const g = S.mapa.grade, rows = g.length, cols = g[0].length;
  const sol = solucaoDe(S.mapa.id, algId), q = quadros(sol), busca = emBusca(sol);
  const passo = Math.min(S.passo, Math.max(0, q.length - 1));
  c2d.clearRect(0, 0, cols * k, rows * k);

  const coletado = new Set();
  if (!busca) for (let i = 0; i <= passo && i < q.length; i++) {
    const [r, c] = q[i], ch = g[r][c];
    if (/[a-d+]/.test(ch) || (ch === "*" && algId === "BELLMAN_FORD_FONTE_CONSUMIVEL")) coletado.add(r + "," + c);
  }
  const chavesAtuais = q[passo] ? q[passo][2] : "";
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const ch = g[r][c], x = c * k, y = r * k, p = Math.max(1, k * 0.06);
    if (ch === "#") { c2d.fillStyle = TEMA["#"]; rr(x, y, k, k, k * 0.14); c2d.fill(); continue; }
    const base = TEMA[ch] || TEMA["."];
    c2d.fillStyle = (ch === "," || ch === "~" || ch === "S" || ch === "G") ? base : TEMA["."];
    rr(x + p, y + p, k - 2 * p, k - 2 * p, k * 0.14); c2d.fill();
    if (ch === "~") { c2d.strokeStyle = "rgba(147,197,253,.55)"; c2d.lineWidth = Math.max(1, k * .06);
      for (const f of [.38, .62]) { c2d.beginPath(); c2d.moveTo(x + k * .2, y + k * f); c2d.quadraticCurveTo(x + k * .35, y + k * (f - .1), x + k * .5, y + k * f); c2d.quadraticCurveTo(x + k * .65, y + k * (f + .1), x + k * .8, y + k * f); c2d.stroke(); } }
    if (ch === ",") { c2d.fillStyle = "rgba(0,0,0,.25)"; [[.3, .35], [.65, .6], [.4, .7]].forEach(([a, b]) => { c2d.beginPath(); c2d.arc(x + k * a, y + k * b, k * .07, 0, 7); c2d.fill(); }); }
    const letra = (txt, cor, tam = .52) => { if (k < 11) return; c2d.fillStyle = cor; c2d.font = `800 ${Math.floor(k * tam)}px Inter, Segoe UI, sans-serif`; c2d.textAlign = "center"; c2d.textBaseline = "middle"; c2d.fillText(txt, x + k / 2, y + k / 2 + k * .03); };
    const usado = coletado.has(r + "," + c);
    if (ch === "S" || ch === "G") letra(ch, "#fff", .55);
    else if (/[a-d]/.test(ch)) {
      c2d.globalAlpha = usado ? .3 : 1; c2d.fillStyle = "#facc15"; c2d.beginPath(); c2d.arc(x + k / 2, y + k / 2, k * .3, 0, 7); c2d.fill(); letra(ch, "#3b2f00", .42); c2d.globalAlpha = 1; }
    else if (/[A-D]/.test(ch)) {
      const aberta = chavesAtuais.includes(ch.toLowerCase());
      c2d.fillStyle = aberta ? "rgba(249,115,22,.22)" : "#f97316"; rr(x + k * .18, y + k * .12, k * .64, k * .76, k * .12); c2d.fill();
      c2d.strokeStyle = "#f97316"; c2d.lineWidth = Math.max(1, k * .06); c2d.stroke(); letra(ch, aberta ? "#fdba74" : "#3b1500", .42); }
    else if (SETA[ch]) {
      const [dx, dy] = SETA[ch]; c2d.strokeStyle = "#38bdf8"; c2d.fillStyle = "#38bdf8"; c2d.lineWidth = Math.max(1.5, k * .1); c2d.lineCap = "round";
      const cx = x + k / 2, cy = y + k / 2, L = k * .26; c2d.beginPath(); c2d.moveTo(cx - dx * L, cy - dy * L); c2d.lineTo(cx + dx * L, cy + dy * L); c2d.stroke();
      c2d.beginPath(); c2d.moveTo(cx + dx * L * 1.5, cy + dy * L * 1.5); c2d.lineTo(cx + dx * L * .3 - dy * L * .9, cy + dy * L * .3 + dx * L * .9); c2d.lineTo(cx + dx * L * .3 + dy * L * .9, cy + dy * L * .3 - dx * L * .9); c2d.fill(); }
    else if (ch === "+") {
      c2d.globalAlpha = usado ? .3 : 1; c2d.fillStyle = "#34d399"; c2d.beginPath();
      for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rad = (i % 2 ? .13 : .3) * k; c2d.lineTo(x + k / 2 + Math.cos(a) * rad, y + k / 2 + Math.sin(a) * rad); } c2d.fill(); c2d.globalAlpha = 1; }
    else if (ch === "*") {
      c2d.globalAlpha = usado ? .3 : 1; c2d.fillStyle = "#e879f9"; c2d.beginPath(); c2d.moveTo(x + k * .56, y + k * .12); c2d.lineTo(x + k * .3, y + k * .55); c2d.lineTo(x + k * .5, y + k * .55); c2d.lineTo(x + k * .42, y + k * .88); c2d.lineTo(x + k * .72, y + k * .42); c2d.lineTo(x + k * .5, y + k * .42); c2d.closePath(); c2d.fill(); c2d.globalAlpha = 1; }
  }
  /* camada exibida: esmaece casas que nao existem nela; realca armadilhas */
  const info = D.camadas[S.mapa.id], vis = camadaVisivel(sol);
  if (info.ordem.length > 1) {
    const dentro = new Set((info.casas[vis] || []).map(([r, c]) => r + "," + c));
    c2d.fillStyle = "rgba(8,10,22,.72)";
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++)
      if (g[r][c] !== "#" && !dentro.has(r + "," + c)) { rr(c * k, r * k, k, k, k * 0.14); c2d.fill(); }
  }
  if (S.armadilha) {
    const pulso = 0.5 + 0.5 * Math.sin(performance.now() / 380);
    armadilhasDa(S.mapa.id).filter((a) => a[2] === vis).forEach(([r, c]) => {
      const x = c * k, y = r * k, p = Math.max(1, k * 0.06);
      c2d.fillStyle = `rgba(244,63,94,${0.38 + 0.2 * pulso})`; rr(x + p, y + p, k - 2 * p, k - 2 * p, k * 0.14); c2d.fill();
      c2d.strokeStyle = "#fb7185"; c2d.lineWidth = Math.max(1.5, k * .08); c2d.stroke();
      if (k >= 11) { c2d.strokeStyle = "#fff"; c2d.lineWidth = Math.max(1.2, k * .07); c2d.lineCap = "round"; const m = k * .3;
        c2d.beginPath(); c2d.moveTo(x + m, y + m); c2d.lineTo(x + k - m, y + k - m); c2d.moveTo(x + k - m, y + m); c2d.lineTo(x + m, y + k - m); c2d.stroke(); }
    });
  }
  if (!q.length) return;
  const cor = alg(algId).cor, cen = ([r, c]) => [c * k + k / 2, r * k + k / 2];
  if (busca) {
    /* sem solucao: pinta as casas que a busca ja visitou */
    c2d.fillStyle = "rgba(76,141,219,.42)";
    for (let i = 0; i <= passo; i++) { const [r, c] = q[i]; rr(c * k + 2, r * k + 2, k - 4, k - 4, k * 0.14); c2d.fill(); }
  } else if (passo > 0) {
    /* trilha */
    c2d.lineJoin = "round"; c2d.lineCap = "round";
    c2d.shadowColor = cor; c2d.shadowBlur = k * .6; c2d.strokeStyle = cor; c2d.lineWidth = Math.max(2, k * .22); c2d.globalAlpha = .9;
    c2d.beginPath();
    for (let i = 0; i <= passo; i++) { const [x, y] = cen(q[i]); i ? c2d.lineTo(x, y) : c2d.moveTo(x, y); }
    c2d.stroke(); c2d.shadowBlur = 0; c2d.globalAlpha = 1;
  }
  const [px, py] = cen(q[passo]);
  c2d.fillStyle = "#fff"; c2d.shadowColor = "#fff"; c2d.shadowBlur = k * .5; c2d.beginPath(); c2d.arc(px, py, Math.max(3, k * .27), 0, 7); c2d.fill(); c2d.shadowBlur = 0;
}

function desenhar() {
  if (!S.mapa) return;
  if (S.modo === "um") {
    const k = dimensionarCanvas(cv, ($(".canvas-wrap").clientWidth || 700) - 28);
    desenharEm(cv, k, S.alg);
  } else {
    algsComparar().forEach((id) => {
      const canvas = $("#cv-" + id);
      const k = dimensionarCanvas(canvas, (canvas.parentElement.clientWidth || 340) - 4);
      desenharEm(canvas, k, id);
    });
  }
}

function textoQuadro(sol, passo) {
  const q = quadros(sol), i = Math.min(passo, q.length - 1), e = q[i];
  if (sol.status === "RECUSA") return "Recusou: o mapa tem peso negativo.";
  if (sol.status === "CICLO_NEGATIVO") return `Ciclo negativo: <b>${sol.custo_ciclo}</b> por volta.`;
  if (emBusca(sol)) return `Busca: <b>${i + 1}</b> de ${q.length} estados visitados${i >= q.length - 1 ? " · nenhum chega na saída" : ""}.`;
  if (!e) return "";
  return `Passo <b>${i}</b> de ${q.length - 1} · custo <b>${e[4]}</b>${i >= q.length - 1 ? " · chegou na saída" : ""}`;
}

function atualizarLeitura() {
  const sol = solucaoDe(S.mapa.id, S.alg), q = quadros(sol);
  const i = Math.min(S.passo, Math.max(0, q.length - 1)), e = q[i], busca = emBusca(sol);
  $("#rotPasso").textContent = busca ? "Estados visitados" : "Passo";
  $("#rdPasso").textContent = !q.length ? "—" : busca ? `${i + 1}/${q.length}` : i;
  $("#rdCusto").textContent = e && e[4] !== null ? e[4] : "—";
  $("#rdChaves").textContent = e ? (e[2] ? e[2].split("").join(" ") : "nenhuma") : "—";
  const temBonus = S.mapa.grade.some((l) => l.includes("+"));
  $("#rdBonus").textContent = !e ? "—" : !temBonus ? "sem bônus" : e[3].length ? "{" + e[3].join(",") + "}" : "nenhum";
  atualizarCamadas();
  if (S.modo === "comparar") algsComparar().forEach((id) => { $("#info-" + id).innerHTML = textoQuadro(solucaoDe(S.mapa.id, id), S.passo); });
  const sc = $("#scrub"); sc.max = maiorPasso(); sc.value = S.passo;
}

function atualizar() { desenhar(); atualizarLeitura(); explorarPasso(); }

/* ---------- reproducao ---------- */
function tocar(sim) {
  S.tocando = sim; $("#btnPlay").textContent = sim ? "❚❚" : "▶"; S.ultimo = 0;
  if (sim) requestAnimationFrame(loop);
}
function passosPorSegundo() { return VELOCIDADES[+$("#speed").value - 1]; }
function loop(t) {
  if (!S.tocando) return;
  if (!S.ultimo) S.ultimo = t;
  const dt = (t - S.ultimo) / 1000; S.ultimo = t;
  const n = maiorPasso();
  S.acc += dt * passosPorSegundo();
  while (S.acc >= 1 && S.passo < n) { S.passo++; S.acc -= 1; }
  atualizar();
  if (S.passo >= n) return tocar(false);
  requestAnimationFrame(loop);
}
function andar(delta) { tocar(false); S.passo = Math.max(0, Math.min(maiorPasso(), S.passo + delta)); atualizar(); }
if (cv) {
  $("#btnPlay").onclick = () => {
    if (!maiorPasso()) return;
    if (!S.tocando && S.passo >= maiorPasso()) S.passo = 0;
    tocar(!S.tocando);
  };
  $("#btnVoltar").onclick = () => andar(-1);
  $("#btnAvancar").onclick = () => andar(1);
  $("#btnReset").onclick = () => { tocar(false); S.passo = 0; atualizar(); };
  $("#scrub").oninput = (e) => { tocar(false); S.passo = +e.target.value; atualizar(); };
  const mostrarVel = () => { $("#speedTxt").textContent = passosPorSegundo() + " passos/s"; };
  $("#speed").oninput = mostrarVel; mostrarVel();
}
let rz; window.addEventListener("resize", () => { clearTimeout(rz); rz = setTimeout(() => { if (cv && S.mapa) desenhar(); }, 120); });

/* ---------- tabela comparativa ---------- */
function tabela() {
  const sols = D.solucoes[S.mapa.id];
  $("#tbMapa").textContent = S.mapa.id.toUpperCase();
  // a fonte consumivel muda a regra do jogo, entao nao entra na disputa de menor custo
  const oks = Object.entries(sols).filter(([id, s]) => id !== "BELLMAN_FORD_FONTE_CONSUMIVEL" && s.status === "OK");
  const melhor = oks.length ? Math.min(...oks.map(([id, s]) => s.custo)) : null;
  const linhas = Object.entries(sols).map(([id, s]) => {
    const a = alg(id), best = id !== "BELLMAN_FORD_FONTE_CONSUMIVEL" && s.status === "OK" && s.custo === melhor;
    const custo = s.status === "CICLO_NEGATIVO" ? `${s.custo_ciclo}/volta` : (s.custo ?? "—");
    return `<tr class="${best ? "best" : ""}"><td class="alg" style="color:${a.cor}">${a.nome}</td>
      <td>${s.passos ?? "—"}</td><td>${custo}</td><td><span class="badge ${s.status}">${rotStatus[s.status]}</span></td></tr>`;
  }).join("");
  $("#tbl").innerHTML = `<thead><tr><th>Algoritmo</th><th>Passos</th><th>Custo</th><th>Resultado</th></tr></thead><tbody>${linhas}</tbody>`;
}

/* ---------- numeros do mapa ---------- */
const num = (x, casas = 0) => (x === null || x === undefined ? "—" : Number(x).toLocaleString("pt-BR", { maximumFractionDigits: casas }));
function numeros() {
  const id = S.mapa.id, m = D.metricas[id], n = D.numeros[id], cam = D.camadas[id], tipos = n.dfs.arcos_por_tipo;
  $("#numMapa").textContent = id.toUpperCase();
  $("#numeros").className = "numeros";
  $("#numeros").innerHTML = `
    <h4>G_pos × G_est</h4>
    <table><thead><tr><th></th><th>G_pos</th><th>G_est</th></tr></thead><tbody>
      <tr><td>Ordem (vértices)</td><td>${num(m.G_pos.ordem)}</td><td>${num(m.G_est.ordem)}</td></tr>
      <tr><td>Tamanho (arcos)</td><td>${num(m.G_pos.tamanho)}</td><td>${num(m.G_est.tamanho)}</td></tr>
      <tr><td>Densidade</td><td>${num(m.G_pos.densidade, 4)}</td><td>${num(m.G_est.densidade, 4)}</td></tr>
      <tr><td>Teto teórico · ocupação</td><td colspan="2">${num(m.teto_teorico)} estados · ${num(100 * m.taxa_ocupacao, 1)}% alcançáveis</td></tr>
    </tbody></table>
    <h4>Camadas</h4>
    <table><thead><tr><th>Chaves</th><th>Estados</th><th>Arcos dentro</th></tr></thead><tbody>
      ${cam.ordem.map((k) => `<tr><td>${k === "" ? "nenhuma" : k.split("").join(", ")}</td><td>${num(cam.info[k].ordem)}</td><td>${num(cam.info[k].tamanho)}</td></tr>`).join("")}
      <tr><td colspan="3">Arcos que mudam de camada (pegar chave): <b>${num(cam.arcos_entre_camadas)}</b></td></tr>
    </tbody></table>
    <h4>Graus e armadilhas</h4>
    <table><tbody>
      <tr><td>Maior grau de saída</td><td><span class="mono">${n.maior_grau_saida.estado}</span> (${n.maior_grau_saida.grau})</td></tr>
      <tr><td>Maior grau de entrada</td><td><span class="mono">${n.maior_grau_entrada.estado}</span> (${n.maior_grau_entrada.grau})</td></tr>
      <tr><td>Multiplicidade máxima de uma casa</td><td>${num(n.multiplicidade_maxima)} estados</td></tr>
      <tr><td>Becos (sem saída, fora do G)</td><td>${num(n.becos)}</td></tr>
      <tr><td>Estados-armadilha</td><td>${num(n.armadilhas)} de ${num(n.estados)} (${num(100 * n.armadilhas / n.estados, 1)}%)</td></tr>
    </tbody></table>
    <h4>DFS: classificação dos arcos (ordem N, L, S, O)</h4>
    <table><thead><tr><th>Árvore</th><th>Retorno</th><th>Avanço</th><th>Cruzamento</th></tr></thead><tbody>
      <tr><td>${num(tipos.arvore)}</td><td>${num(tipos.retorno)}</td><td>${num(tipos.avanco)}</td><td>${num(tipos.cruzamento)}</td></tr>
      <tr><td colspan="4">Tem ciclo: <b>${n.dfs.tem_ciclo ? "sim (há arco de retorno)" : "não"}</b></td></tr>
    </tbody></table>`;
}

/* ---------- modelagem ---------- */
function modelagem() {
  const maior = Math.max(...Object.values(D.metricas).map((m) => m.G_est.ordem), 10) * 1.1;
  const L = (n) => Math.max(4, (Math.log10(n) / Math.log10(maior)) * 100);
  $("#chartModel").innerHTML = Object.entries(D.metricas).map(([id, m]) =>
    `<div class="row"><span>${id.toUpperCase()}</span><div class="track">
      <div class="bar p" data-w="${L(m.G_pos.ordem)}"></div><div class="bar e" data-w="${L(m.G_est.ordem)}"></div></div>
      <em>${fmt(m.G_pos.ordem)} → ${fmt(m.G_est.ordem)}</em></div>`).join("");

  /* o que da errado so com posicoes: um botao por mapa da comparacao (m02, m03, m04) */
  const nomes = {
    "G_pos portas como chao": ["Porta vira chão", "Atravessa a porta sem ter a chave: caminho inválido."],
    "G_pos portas como parede": ["Porta vira parede", "Nunca vai pegar a chave e voltar: não acha caminho."],
    G_est: ["Grafo de estados", "Pega a chave antes da porta: caminho válido."],
  };
  const mapasComp = [...new Set(D.modelagem.map((r) => r.mapa))];
  const mostrarComp = (mapa) => {
    [...$("#segModelagem").children].forEach((b) => b.classList.toggle("on", b.dataset.m === mapa));
    $("#armadilhas").innerHTML = D.modelagem.filter((r) => r.mapa === mapa).map((r) => {
      const [t, d] = nomes[r.abordagem] || [r.abordagem, r.observacao]; const ok = r.caminho_valido === "True";
      return `<div class="t ${ok ? "good" : "badx"}"><b>${t}<span>${r.passos ? r.passos + " passos" : "sem caminho"} ${ok ? "✓" : "✗"}</span></b><span>${d}</span></div>`;
    }).join("") + `<p class="note">Mapa ${mapa.toUpperCase()} · ${D.mapas[mapa] ? D.mapas[mapa].nome : ""}.</p>`;
  };
  $("#segModelagem").innerHTML = mapasComp.map((m) => `<button data-m="${m}">${m.toUpperCase()}</button>`).join("");
  [...$("#segModelagem").children].forEach((b) => (b.onclick = () => mostrarComp(b.dataset.m)));
  if (mapasComp.length) mostrarComp(mapasComp.includes("m03") ? "m03" : mapasComp[0]);

  /* estados alcancaveis x teto teorico */
  $("#tblTeto").innerHTML = `<thead><tr><th>Mapa</th><th>Casas (G_pos)</th><th>Teto teórico</th><th>Estados alcançáveis</th><th>Ocupação</th><th>Arcos (G_est)</th></tr></thead><tbody>` +
    Object.entries(D.metricas).map(([id, m]) => `<tr><td><b>${id.toUpperCase()}</b> <span class="note">${D.mapas[id].nome}</span></td>
      <td>${fmt(m.G_pos.ordem)}</td><td>${fmt(m.teto_teorico)}</td><td>${fmt(m.G_est.ordem)}</td>
      <td>${num(100 * m.taxa_ocupacao, 1)}%</td><td>${fmt(m.G_est.tamanho)}</td></tr>`).join("") + "</tbody>";

  /* ciclo negativo do m06 e a correcao */
  const c = D.ciclo_m06;
  if (c && c.tem_ciclo_negativo) {
    const nos = c.ciclo.slice(0, -1);
    const corr = c.com_fonte_consumivel;
    $("#cicloM06").innerHTML = `<div class="ciclo-seq">${nos.map((n) => `<i>${n}</i><s>→</s>`).join("")}<i>${c.ciclo.at(-1)}</i></div>
      <table><thead><tr><th>Arco</th><th>Peso</th></tr></thead><tbody>
      ${c.arcos.map((a) => `<tr><td class="mono">${a.origem} → ${a.destino}</td><td>${a.peso}</td></tr>`).join("")}
      <tr><td><b>Custo do ciclo</b></td><td><b>${c.custo_do_ciclo}</b></td></tr></tbody></table>
      <p class="note">Com <code>--fonte-consumivel</code> a fonte vale −2 só na primeira vez (como o bônus):
      ${corr.tem_ciclo_negativo ? "ainda há ciclo negativo." : `o ciclo some e o Bellman-Ford dá resposta finita, <b>custo ${corr.custo_ate_alvo}</b>.`}</p>`;
  } else {
    $("#cardCiclo").hidden = true;
  }

  /* gabarito dos mapas do grupo */
  if (D.gabarito) {
    $("#tblGabarito").innerHTML = `<thead><tr><th>Mapa</th><th>Estados</th><th>Arcos</th><th>Passos (BFS)</th><th>Custo</th><th>Armadilhas</th></tr></thead><tbody>` +
      Object.entries(D.gabarito).map(([id, g]) => `<tr><td><b>${id.toUpperCase()}</b></td><td>${fmt(g.estados)}</td><td>${fmt(g.arcos)}</td>
        <td>${g.passos_bfs ?? "—"}</td><td>${g.custo ?? "—"} <span class="note">${g.algoritmo_custo === "BELLMAN_FORD" ? "Bellman-Ford" : g.algoritmo_custo === "DIJKSTRA" ? "Dijkstra" : ""}</span></td>
        <td>${g.armadilhas} (${num(g.porcentagem_armadilhas, 1)}%)</td></tr>`).join("") + "</tbody>";
  }
}

/* ---------- utilitarios das partes interativas novas ---------- */
const rotulo = (e) => `(${e[0]},${e[1]})|${e[2] || "-"}|{${e[3].join(",")}}`;
const esc2 = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
// cores das camadas, sempre na mesma ordem (camada 0 = sem chaves, 1 = primeira chave...)
const COR_CAMADA = ["#4c8ddb", "#e8a06a", "#2fafa3", "#c084fc", "#facc15", "#f472b6", "#a3e635", "#94a3b8"];
const corDaCamada = (ordem, k) => { const i = ordem.indexOf(k); return i >= 0 && i < COR_CAMADA.length ? COR_CAMADA[i] : "#64748b"; };
const nomeCamada = (k) => (k === "" ? "sem chaves" : "chaves " + k.split("").join(", "));
const NOME_CASA = { ".": "chão", ",": "lama", "~": "água", "+": "bônus", "*": "fonte", S: "início", G: "saída",
  ">": "esteira", "<": "esteira", "^": "esteira", v: "esteira" };
const nomeCasa = (ch) => NOME_CASA[ch] || (/[a-d]/.test(ch) ? "chave " + ch : /[A-D]/.test(ch) ? "porta " + ch : ch);

let dica = null;
function mostrarDica(html, ev) {
  if (!dica) { dica = document.createElement("div"); dica.className = "dica"; document.body.appendChild(dica); }
  dica.innerHTML = html; dica.hidden = false;
  const x = Math.min(ev.clientX + 14, window.innerWidth - dica.offsetWidth - 10);
  const y = Math.min(ev.clientY + 14, window.innerHeight - dica.offsetHeight - 10);
  dica.style.left = x + "px"; dica.style.top = y + "px";
}
function esconderDica() { if (dica) dica.hidden = true; }

// tabela com busca, ordenacao por coluna e paginas de 50 linhas
function tabelaInterativa(el, colunas, linhas, opcoes = {}) {
  const T = { busca: "", col: null, desc: false, pagina: 0, por: opcoes.porPagina || 50 };
  function filtradas() {
    let r = linhas.map((l, i) => ({ l, i }));
    if (T.busca) { const b = T.busca.toLowerCase(); r = r.filter(({ l }) => l.some((v) => String(v).toLowerCase().includes(b))); }
    if (T.col !== null) {
      const c = T.col, num = colunas[c].num;
      r.sort((a, b) => { const x = a.l[c], y = b.l[c]; const d = num ? x - y : String(x).localeCompare(String(y), "pt-BR", { numeric: true }); return T.desc ? -d : d; });
    }
    return r;
  }
  function render() {
    const r = filtradas(), paginas = Math.max(1, Math.ceil(r.length / T.por));
    T.pagina = Math.min(T.pagina, paginas - 1);
    const vis = r.slice(T.pagina * T.por, (T.pagina + 1) * T.por);
    const destaque = opcoes.destaque ? opcoes.destaque() : -1;
    el.querySelector(".info").textContent = `${fmt(r.length)} de ${fmt(linhas.length)} linhas · página ${T.pagina + 1} de ${paginas}`;
    el.querySelector(".ant").disabled = T.pagina === 0;
    el.querySelector(".prox").disabled = T.pagina >= paginas - 1;
    el.querySelector("thead").innerHTML = "<tr>" + colunas.map((c, i) =>
      `<th data-c="${i}" class="${T.col === i ? "ord" + (T.desc ? " desc" : "") : ""}">${c.t}</th>`).join("") + "</tr>";
    el.querySelector("tbody").innerHTML = vis.map(({ l, i }) =>
      `<tr data-i="${i}" class="${i === destaque ? "atual" : ""} ${opcoes.aoClicar ? "clicavel" : ""}">` +
      l.map((v, c) => {
        // textos muito longos (o caminho inteiro no solucoes.csv) aparecem cortados; o texto todo fica no title
        const t = String(v), curto = t.length > 70 ? t.slice(0, 67) + "…" : t;
        return `<td class="${colunas[c].mono ? "mono" : ""}"${curto !== t ? ` title="${esc2(t)}"` : ""}>${esc2(curto)}</td>`;
      }).join("") + "</tr>").join("");
  }
  el.innerHTML = `<div class="ferramentas"><input type="search" placeholder="Buscar (estado, casa, movimento...)" aria-label="Buscar na tabela">
    <button class="ant">‹ anterior</button><button class="prox">próxima ›</button><span class="info"></span></div>
    <div class="table-scroll"><table class="t-interativa"><thead></thead><tbody></tbody></table></div>`;
  el.querySelector("input").oninput = (e) => { T.busca = e.target.value; T.pagina = 0; render(); };
  el.querySelector(".ant").onclick = () => { T.pagina--; render(); };
  el.querySelector(".prox").onclick = () => { T.pagina++; render(); };
  el.querySelector("thead").onclick = (e) => {
    const th = e.target.closest("th"); if (!th) return;
    const c = +th.dataset.c; if (T.col === c) T.desc = !T.desc; else { T.col = c; T.desc = false; } render();
  };
  if (opcoes.aoClicar) el.querySelector("tbody").onclick = (e) => { const tr = e.target.closest("tr"); if (tr) opcoes.aoClicar(+tr.dataset.i); };
  render();
  return { render, irPara: (i) => { if (T.busca || T.col !== null) return render(); T.pagina = Math.floor(i / T.por); render(); } };
}

/* ---------- labirintos: explorar os dados do mapa ---------- */
const EXP = { aba: "caminho", tabela: null, passo: -1 };
function explorar() {
  if (!$("#tabelaDados") || !S.mapa) return;
  const id = S.mapa.id, g = D.grafos[id], el = $("#tabelaDados");
  $("#expMapa").textContent = id.toUpperCase();
  [...$("#segDados").children].forEach((b) => b.classList.toggle("on", b.dataset.aba === EXP.aba));
  EXP.tabela = null;
  if (EXP.aba === "caminho") {
    const sol = solucaoDe(id, S.alg), q = quadros(sol), busca = emBusca(sol);
    if (!q.length) { el.innerHTML = `<p class="note">${alg(S.alg).nome}: ${rotStatus[sol.status]}, não há caminho para listar.</p>`; return; }
    const linhas = q.map((e, i) => [i, rotulo(e), S.mapa.grade[e[0]][e[1]], e[2] ? e[2].split("").join(" ") : "—",
      e[3].length ? "{" + e[3].join(",") + "}" : "—", busca ? "—" : (i ? e[4] - q[i - 1][4] : 0), busca ? "—" : e[4]]);
    const cols = [{ t: busca ? "Visita" : "Passo", num: true }, { t: "Estado", mono: true }, { t: "Casa" }, { t: "Chaves" }, { t: "Bônus" },
      { t: "Custo do passo", num: true }, { t: "Custo acumulado", num: true }];
    el.insertAdjacentHTML("afterbegin", "");
    EXP.tabela = tabelaInterativa(el, cols, linhas, {
      destaque: () => Math.min(S.passo, q.length - 1),
      aoClicar: (i) => { tocar(false); S.passo = i; atualizar(); },
    });
    $("#tabelaDados").insertAdjacentHTML("afterbegin", `<p class="note top">${alg(S.alg).nome}${busca ? ": ordem em que a busca visitou os estados (não há caminho até a saída)." : ": clique numa linha para levar a animação até aquele passo."}</p>`);
    return;
  }
  if (g.cortado) { el.innerHTML = `<p class="note">Este mapa tem estados demais para listar aqui; veja os arquivos CSV em <code>out/parte1/</code>.</p>`; return; }
  if (EXP.aba === "arcos") {
    const E = g.estados;
    EXP.tabela = tabelaInterativa(el, [{ t: "Origem", mono: true }, { t: "Destino", mono: true }, { t: "Movimento" }, { t: "Casa de destino" }, { t: "Peso", num: true }],
      g.arcos.map(([o, d, mv, casa, peso]) => [rotulo(E[o]), rotulo(E[d]), mv, casa, peso]));
  } else if (EXP.aba === "graus") {
    EXP.tabela = tabelaInterativa(el, [{ t: "Estado", mono: true }, { t: "Nível na BFS", num: true }, { t: "Grau de entrada", num: true }, { t: "Grau de saída", num: true }],
      g.estados.map((e) => [rotulo(e), e[6], e[4], e[5]]));
  } else {
    const arm = armadilhasDa(id);
    if (!arm.length) { el.innerHTML = `<p class="note">Este mapa não tem estados-armadilha: de todo estado alcançável ainda dá para chegar na saída.</p>`; return; }
    const lista = g.estados.filter((e) => arm.some(([r, c, k]) => r === e[0] && c === e[1] && k === e[2]));
    EXP.tabela = tabelaInterativa(el, [{ t: "Estado", mono: true }, { t: "Casa" }, { t: "Chaves" }, { t: "Grau de saída", num: true }],
      lista.map((e) => [rotulo(e), S.mapa.grade[e[0]][e[1]], e[2] ? e[2].split("").join(" ") : "—", e[5]]));
    el.insertAdjacentHTML("afterbegin", `<p class="note top">${fmt(lista.length)} estados alcançáveis de onde não dá mais para chegar na saída (busca a partir do ALVO no grafo transposto).</p>`);
  }
}
function explorarPasso() {
  // durante a animacao, a linha do passo atual acompanha
  if (EXP.aba !== "caminho" || !EXP.tabela || EXP.passo === S.passo) return;
  EXP.passo = S.passo; EXP.tabela.irPara(S.passo);
}

/* ---------- modelagem: o grafo de estados interativo ---------- */
const VIZ = { mapa: null, tipo: "camadas" };
function montarViz() {
  if (!$("#vizArea")) return;
  const sel = $("#selMapaViz");
  sel.innerHTML = Object.values(D.mapas).map((m) => `<option value="${m.id}">${m.id.toUpperCase()} · ${m.nome}</option>`).join("");
  VIZ.mapa = D.mapas[window.MAPA_INICIAL] ? window.MAPA_INICIAL : (D.mapas.m02 ? "m02" : Object.keys(D.mapas)[0]);
  sel.value = VIZ.mapa;
  sel.onchange = () => { VIZ.mapa = sel.value; desenharViz(); };
  [...$("#segViz").children].forEach((b) => (b.onclick = () => {
    VIZ.tipo = b.dataset.viz; [...$("#segViz").children].forEach((x) => x.classList.toggle("on", x === b)); desenharViz();
  }));
  $("#vizArea").onmouseleave = esconderDica;
  desenharViz();
}

function desenharViz() {
  const g = D.grafos[VIZ.mapa], area = $("#vizArea");
  esconderDica();
  if (g.cortado) { area.innerHTML = `<p class="note">Este mapa tem estados demais para desenhar aqui.</p>`; $("#vizLegenda").innerHTML = ""; return; }
  if (VIZ.tipo === "camadas") vizCamadas(g, area);
  else if (VIZ.tipo === "arvore") vizArvore(g, area);
  else vizHeatmap(g, area);
}

function legendaCamadas(ordem, extra = "") {
  $("#vizLegenda").innerHTML = ordem.map((k) => `<span><i style="background:${corDaCamada(ordem, k)}"></i>${nomeCamada(k)}</span>`).join("") + extra;
}

function dicaEstado(e, extra = "") {
  return `<b>${rotulo(e)}</b><span class="mono">nível ${e[6]} na BFS · entrada ${e[4]} · saída ${e[5]}</span>${extra}`;
}

function vizCamadas(g, area) {
  const grade = D.mapas[VIZ.mapa].grade, rows = grade.length, cols = grade[0].length;
  const ordem = D.camadas[VIZ.mapa].ordem, E = g.estados;
  const k = Math.max(10, Math.min(30, Math.floor(((area.clientWidth || 900) - 40) / cols)));
  const topo = 26, banda = rows * k + topo + 10, W = cols * k + 20, H = ordem.length * banda;
  // estados na mesma casa e camada (bonus diferentes) ficam lado a lado
  const vizinhos = {};
  const pos = E.map((e) => {
    const chave = e[0] + "," + e[1] + "|" + e[2]; const n = (vizinhos[chave] = (vizinhos[chave] || 0) + 1) - 1;
    const b = ordem.indexOf(e[2]);
    return [10 + e[1] * k + k / 2 + (n % 3 - 1) * k * 0.22, b * banda + topo + e[0] * k + k / 2 + Math.floor(n / 3) * k * 0.22];
  });
  let s = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="Grafo de estados em camadas">`;
  ordem.forEach((kk, b) => {
    const y = b * banda, qtd = E.filter((e) => e[2] === kk).length;
    s += `<rect x="2" y="${y + 2}" width="${W - 4}" height="${banda - 6}" rx="10" fill="rgba(255,255,255,.025)" stroke="rgba(255,255,255,.07)"/>`;
    s += `<text x="12" y="${y + 18}" fill="${corDaCamada(ordem, kk)}" font-size="12" font-weight="700">${nomeCamada(kk)} · ${qtd} estados</text>`;
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) if (grade[r][c] === "#")
      s += `<rect x="${10 + c * k}" y="${y + topo + r * k}" width="${k}" height="${k}" fill="rgba(255,255,255,.035)"/>`;
  });
  let dentro = "", entre = "";
  g.arcos.forEach(([o, d]) => {
    const [x1, y1] = pos[o], [x2, y2] = pos[d];
    if (E[o][2] === E[d][2]) dentro += `M${x1.toFixed(1)} ${y1.toFixed(1)}L${x2.toFixed(1)} ${y2.toFixed(1)}`;
    else entre += `<path d="M${x1.toFixed(1)} ${y1.toFixed(1)}C${(x1 + 40).toFixed(1)} ${y1.toFixed(1)} ${(x2 + 40).toFixed(1)} ${y2.toFixed(1)} ${x2.toFixed(1)} ${y2.toFixed(1)}" fill="none" stroke="#fb7185" stroke-width="1.6" opacity=".85"/>`;
  });
  s += `<path d="${dentro}" stroke="rgba(207,216,245,.28)" stroke-width="1" fill="none"/>` + entre + `<g id="vizRealce"></g>`;
  const r = Math.max(2.5, k * 0.2);
  E.forEach((e, i) => { const [x, y] = pos[i]; s += `<circle class="no" data-i="${i}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r}" fill="${corDaCamada(ordem, e[2])}"/>`; });
  area.innerHTML = s + "</svg>";
  legendaCamadas(ordem, `<span><b class="linha" style="border-color:rgba(207,216,245,.5)"></b>arco dentro da camada</span><span><b class="linha" style="border-color:#fb7185"></b>arco que muda de camada (pegou uma chave)</span>`);
  $("#vizTexto").textContent = `Cada faixa é uma camada (um conjunto de chaves) e cada ponto é um estado, desenhado na casa onde o jogador está. ${fmt(g.arcos.length)} arcos ao todo; passe o mouse num estado para ver os arcos dele.`;
  area.onmousemove = (ev) => {
    const no = ev.target.closest(".no"); const realce = area.querySelector("#vizRealce");
    if (!no) { esconderDica(); realce.innerHTML = ""; return; }
    const i = +no.dataset.i, [x0, y0] = pos[i];
    realce.innerHTML = g.arcos.filter(([o, d]) => o === i || d === i).map(([o, d]) =>
      `<line x1="${pos[o][0]}" y1="${pos[o][1]}" x2="${pos[d][0]}" y2="${pos[d][1]}" stroke="#fff" stroke-width="2"/>`).join("") +
      `<circle cx="${x0}" cy="${y0}" r="${r + 3}" fill="none" stroke="#fff" stroke-width="2"/>`;
    mostrarDica(dicaEstado(E[i], `<span>casa: ${nomeCasa(grade[E[i][0]][E[i][1]])}</span>`), ev);
  };
}

function vizArvore(g, area) {
  const E = g.estados, ordem = D.camadas[VIZ.mapa].ordem, grade = D.mapas[VIZ.mapa].grade;
  const porNivel = {};
  E.forEach((e, i) => { if (e[6] >= 0) (porNivel[e[6]] = porNivel[e[6]] || []).push(i); });
  const niveis = Object.keys(porNivel).map(Number).sort((a, b) => a - b), maxLargura = Math.max(...niveis.map((n) => porNivel[n].length));
  const dx = niveis.length > 120 ? 14 : 30, dy = maxLargura > 40 ? 10 : 18, mx = 40, my = 30;
  const W = mx * 2 + niveis.length * dx, H = my * 2 + maxLargura * dy;
  const pos = [];
  niveis.forEach((n) => porNivel[n].forEach((i, j) => { pos[i] = [mx + n * dx, my + (j + 0.5) * dy + (maxLargura - porNivel[n].length) * dy / 2]; }));
  let s = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="Árvore da BFS no grafo de estados">`;
  const passo = niveis.length > 60 ? 10 : 5;
  niveis.forEach((n) => { if (n % passo === 0) s += `<text x="${mx + n * dx}" y="16" text-anchor="middle" fill="#9aa0c3" font-size="11">${n}</text><line x1="${mx + n * dx}" x2="${mx + n * dx}" y1="22" y2="${H - 8}" stroke="rgba(255,255,255,.05)"/>`; });
  let arestas = "";
  E.forEach((e, i) => { if (e[7] >= 0 && pos[i] && pos[e[7]]) arestas += `M${pos[e[7]][0]} ${pos[e[7]][1].toFixed(1)}L${pos[i][0]} ${pos[i][1].toFixed(1)}`; });
  s += `<path d="${arestas}" stroke="rgba(207,216,245,.3)" stroke-width="1" fill="none"/><g id="vizRealce"></g>`;
  const r = dy > 12 ? 4.5 : 3;
  E.forEach((e, i) => {
    if (!pos[i]) return;
    const saida = grade[e[0]][e[1]] === "G";
    s += `<circle class="no" data-i="${i}" cx="${pos[i][0]}" cy="${pos[i][1].toFixed(1)}" r="${saida ? r + 1.5 : r}" fill="${corDaCamada(ordem, e[2])}" ${saida ? 'stroke="#f43f5e" stroke-width="2"' : ""}/>`;
  });
  area.innerHTML = s + "</svg>";
  legendaCamadas(ordem, `<span><i style="background:transparent;border:2px solid #f43f5e"></i>estado na saída G</span>`);
  $("#vizTexto").textContent = `Cada coluna é um nível da BFS (número de passos desde o início), de 0 a ${niveis.at(-1)}. A cor é a camada do estado. Passe o mouse num estado para ver o caminho da árvore até ele.`;
  area.onmousemove = (ev) => {
    const no = ev.target.closest(".no"); const realce = area.querySelector("#vizRealce");
    if (!no) { esconderDica(); realce.innerHTML = ""; return; }
    let i = +no.dataset.i; const pts = [];
    while (i >= 0 && pos[i]) { pts.push(pos[i].map((v) => v.toFixed(1)).join(",")); i = E[i][7]; }
    realce.innerHTML = `<polyline points="${pts.join(" ")}" fill="none" stroke="#fff" stroke-width="2.2"/>`;
    mostrarDica(dicaEstado(E[+no.dataset.i], `<span>caminho da árvore: ${pts.length - 1} passos</span>`), ev);
  };
}

function vizHeatmap(g, area) {
  const grade = D.mapas[VIZ.mapa].grade, rows = grade.length, cols = grade[0].length, E = g.estados;
  const porCasa = {};
  E.forEach((e) => (porCasa[e[0] + "," + e[1]] = porCasa[e[0] + "," + e[1]] || []).push(e));
  const max = Math.max(1, ...Object.values(porCasa).map((v) => v.length));
  // uma cor so (azul), do escuro (poucos estados) ao claro (muitos)
  const cor = (n) => `hsl(212 72% ${(22 + 56 * (max === 1 ? 1 : (n - 1) / (max - 1))).toFixed(0)}%)`;
  const k = Math.max(10, Math.min(36, Math.floor(((area.clientWidth || 900) - 30) / cols)));
  let s = `<svg width="${cols * k}" height="${rows * k}" viewBox="0 0 ${cols * k} ${rows * k}" role="img" aria-label="Heatmap de multiplicidade">`;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const ch = grade[r][c], lista = porCasa[r + "," + c], x = c * k, y = r * k;
    if (ch === "#") { s += `<rect x="${x}" y="${y}" width="${k}" height="${k}" fill="#1a1d3a"/>`; continue; }
    const fill = lista ? cor(lista.length) : "#0f1226";
    s += `<rect class="no" data-c="${r},${c}" x="${x + 1}" y="${y + 1}" width="${k - 2}" height="${k - 2}" rx="${k * 0.15}" fill="${fill}"/>`;
    if (k >= 18 && lista) s += `<text x="${x + k / 2}" y="${y + k / 2 + 4}" text-anchor="middle" font-size="${Math.floor(k * 0.38)}" font-weight="700" fill="${lista.length > max * 0.55 ? "#0b0d1a" : "#e8eaf6"}" pointer-events="none">${lista.length}</text>`;
    else if (k >= 18 && ch !== ".") s += `<text x="${x + k / 2}" y="${y + k / 2 + 4}" text-anchor="middle" font-size="${Math.floor(k * 0.38)}" fill="#64748b" pointer-events="none">${esc2(ch)}</text>`;
  }
  area.innerHTML = s + "</svg>";
  $("#vizLegenda").innerHTML = `<span>1 estado<b class="degrade" style="background:linear-gradient(90deg,${cor(1)},${cor(max)})"></b>${max} estados por casa</span><span><i style="background:#0f1226;border-radius:3px;border:1px solid rgba(255,255,255,.2)"></i>casa livre que nunca é alcançada</span>`;
  $("#vizTexto").textContent = `Quantos estados do G_est existem em cada casa (mesma posição com chaves ou bônus diferentes). A casa mais "multiplicada" tem ${max} estados.`;
  area.onmousemove = (ev) => {
    const no = ev.target.closest(".no"); if (!no) return esconderDica();
    const [r, c] = no.dataset.c.split(",").map(Number), lista = porCasa[r + "," + c] || [];
    mostrarDica(`<b>casa (${r},${c}) · ${nomeCasa(grade[r][c])}</b><span>${lista.length} estado${lista.length === 1 ? "" : "s"} nesta casa</span>` +
      lista.slice(0, 8).map((e) => `<span class="mono">${rotulo(e)}</span>`).join("") + (lista.length > 8 ? `<span>… e mais ${lista.length - 8}</span>` : ""), ev);
  };
}

/* ---------- modelagem: arquivos de out/parte1 ---------- */
function arquivosOut() {
  if (!$("#listaArquivos") || !D.arquivos) return;
  if (!D.arquivos.length) { $("#arquivosOut").hidden = true; return; }
  $("#listaArquivos").innerHTML = D.arquivos.map((a, i) => `<button data-i="${i}">${a.nome}</button>`).join("");
  const abrir = (i) => {
    const a = D.arquivos[i];
    [...$("#listaArquivos").children].forEach((b) => b.classList.toggle("on", +b.dataset.i === i));
    $("#nomeArquivo").textContent = a.nome + ` · ${fmt(Math.round(a.texto.length / 1024 * 10) / 10)} KB`;
    $("#btnBaixar").onclick = () => {
      const url = URL.createObjectURL(new Blob([a.texto], { type: a.tipo === "csv" ? "text/csv" : "application/json" }));
      const link = document.createElement("a"); link.href = url; link.download = a.nome; link.click(); URL.revokeObjectURL(url);
    };
    const ver = $("#verArquivo");
    if (a.tipo === "csv") {
      const linhas = a.texto.trim().split(/\r?\n/).map(lerLinhaCsv);
      tabelaInterativa(ver, linhas[0].map((t) => ({ t, num: linhas.slice(1, 30).every((l) => l[linhas[0].indexOf(t)] !== "" && !isNaN(l[linhas[0].indexOf(t)])), mono: /estado|origem|destino|caminho/.test(t) })),
        linhas.slice(1).map((l) => l.map((v) => (v !== "" && !isNaN(v) ? Number(v) : v))));
    } else {
      let texto = a.texto; try { texto = JSON.stringify(JSON.parse(a.texto), null, 2); } catch (e) { /* mostra como esta */ }
      ver.innerHTML = `<pre class="json-ver">${esc2(texto)}</pre>`;
    }
  };
  $("#listaArquivos").onclick = (e) => { const b = e.target.closest("button"); if (b) abrir(+b.dataset.i); };
  const inicial = D.arquivos.findIndex((a) => a.nome === "solucoes.csv");
  abrir(inicial >= 0 ? inicial : 0);
}

// CSV simples: separa por virgula, respeitando campos entre aspas (os rotulos dos estados tem virgula)
function lerLinhaCsv(linha) {
  const campos = []; let atual = "", aspas = false;
  for (let i = 0; i < linha.length; i++) {
    const ch = linha[i];
    if (ch === '"') { if (aspas && linha[i + 1] === '"') { atual += '"'; i++; } else aspas = !aspas; }
    else if (ch === "," && !aspas) { campos.push(atual); atual = ""; }
    else atual += ch;
  }
  campos.push(atual);
  return campos;
}

/* ---------- parte 2 ---------- */
function parte2() {
  const P = D.parte2;
  $("#dsNome").textContent = P.dataset;
  $("#tblRec").innerHTML = `<thead><tr><th>Usuários</th><th>Nós</th><th>Arcos</th><th>% dos arcos</th></tr></thead><tbody>` +
    P.recortes.map((r) => `<tr><td>${r["usuarios (%)"]}%</td><td>${fmt(r.nos)}</td><td>${fmt(r.arcos)}</td><td>${r["arcos (%)"].toString().replace(".", ",")}%</td></tr>`).join("") + "</tbody>";
  if (P.ciclo) {
    const nos = P.ciclo.slice(0, -1);
    // [IA] Claude – a frase dos "dois usuarios" so aparece quando o ciclo e uma dupla de inimigos mutuos (custo -2)
    const explicacao = nos.length === 2 && P.custo_ciclo === -2
      ? "Dois usuários que se marcam como inimigos permitem reduzir o custo indefinidamente."
      : "O custo diminui a cada volta completa pelo ciclo.";
    $("#negCycle").innerHTML = `<b>Ciclo negativo na rede completa</b> (Bellman-Ford)
      <div class="loop">${nos.map((n) => `<i>${n}</i><s>→</s>`).join("")}<i>${P.ciclo.at(-1)}</i></div>
      Custo do ciclo: <b>${P.custo_ciclo}</b>. ${explicacao}`;
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
    insight: "Os 10% do topo fizeram 94,41% das marcações de inimigo e receberam 77,33%. Elas se concentram mais em quem marca." },
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
  { f: "parte2/alg_passos_volta_piloto.png", titulo: "Custo da volta na amostra", grupo: "alg", origem: "Notebook 02 · seção 12.3",
    mostra: "Cada barra é a porcentagem das 1.291 voltas da amostra em que o Dijkstra teve o mesmo custo da BFS, um custo menor com os mesmos passos ou um custo menor com um passo a mais.",
    insight: "O custo foi o mesmo em 75,9% das voltas, menor com os mesmos passos em 21,5% e menor com um passo a mais em 2,6%." },
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
      <figure class="topico-img" data-src="${IMG(x.f)}" data-t="${esc(x.titulo)}"><img loading="lazy" src="${IMG(x.f)}" alt="${esc(x.titulo)}"></figure>
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
if ($("#vizArea")) montarViz();
if ($("#listaArquivos")) arquivosOut();
if ($("#segDados")) [...$("#segDados").children].forEach((b) => (b.onclick = () => { EXP.aba = b.dataset.aba; EXP.passo = -1; explorar(); }));
if ($("#chartEscala")) parte2();
if ($("#topicos")) graficosEmTopicos();
efeitos();
if (cv) {
  const q = new URLSearchParams(location.search);
  if (q.get("alg")) S.alg = q.get("alg");
  const inicial = q.get("mapa") || window.MAPA_INICIAL; // MAPA_INICIAL: mapa passado no --mapa do cli
  escolherMapa(D.mapas[inicial] ? inicial : "m02");
  if (q.has("armadilha")) { const c = $("#chkArmadilha"); if (!c.disabled) { c.checked = true; c.dispatchEvent(new Event("change")); } }
}
window.__S = S; /* depuracao */
})();
