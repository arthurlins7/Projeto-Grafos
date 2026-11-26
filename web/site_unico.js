// [IA] Claude – navegacao do site num arquivo so (out/parte1/labirinto_interativo.html):
// cada pagina de web/ vira uma secao, e o # do endereco escolhe qual aparece (#labirintos, #modelagem...)
(() => {
  const paginas = [...document.querySelectorAll(".pagina")].map((p) => p.dataset.pagina);

  function mostrar() {
    const alvo = decodeURIComponent(location.hash.slice(1));
    let pagina = paginas.includes(alvo) ? alvo : null;
    let elemento = null;
    if (!pagina && alvo) {
      // um # de dentro de uma pagina (ex.: #exploratorias, nos graficos): abre a pagina dele e rola ate la
      elemento = document.getElementById(alvo);
      const dono = elemento && elemento.closest(".pagina");
      pagina = dono ? dono.dataset.pagina : null;
    }
    if (!pagina) pagina = window.MAPA_INICIAL ? "labirintos" : "inicio";

    document.querySelectorAll(".pagina").forEach((p) => (p.hidden = p.dataset.pagina !== pagina));
    document.querySelectorAll(".nav nav a").forEach((a) => {
      const ligado = a.dataset.pagina === pagina;
      a.classList.toggle("on", ligado);
      if (ligado) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
    window.dispatchEvent(new Event("resize"));   // o canvas do labirinto se ajusta ao aparecer
    if (elemento) elemento.scrollIntoView(); else window.scrollTo(0, 0);
  }

  window.addEventListener("hashchange", mostrar);
  mostrar();
})();
