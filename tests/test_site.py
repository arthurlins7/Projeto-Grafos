# [IA] Claude - testes do site do grupo (web/data.js e o site num arquivo so)
from pathlib import Path

from src.pagina_site import dados_do_site, gerar_data_js, gerar_site_unico


PASTA_PROJETO = Path(__file__).resolve().parents[1]


def test_site_tem_os_mapas_fornecidos_e_os_do_grupo():
    dados, chave = dados_do_site()
    for nome in ["m01", "m04", "m07", "m08", "g01", "g02"]:
        assert nome in dados["mapas"]
        assert nome in dados["solucoes"] and nome in dados["camadas"] and nome in dados["numeros"]
    assert len(dados["armadilhas"]["g02"]) == 11   # o destaque das armadilhas do g02 entra no site
    assert chave is None


def test_m07_anima_a_busca_e_m06_tem_a_fonte_consumivel():
    dados, _ = dados_do_site()
    m07 = dados["solucoes"]["m07"]["BFS"]
    assert m07["status"] == "SEM_SOLUCAO"
    assert len(m07["visitas"]) == 16
    m06 = dados["solucoes"]["m06"]
    assert m06["BELLMAN_FORD"]["status"] == "CICLO_NEGATIVO"
    assert m06["BELLMAN_FORD"]["custo_ciclo"] == -1
    fonte = m06["BELLMAN_FORD_FONTE_CONSUMIVEL"]
    assert fonte["status"] == "OK" and fonte["estados"][-1][4] == 10
    assert "BELLMAN_FORD_FONTE_CONSUMIVEL" not in dados["solucoes"]["m05"]


def test_camada_conta_estado_isolado(tmp_path):
    # S cercado de paredes: o estado inicial existe, mesmo sem nenhum arco
    mapa = tmp_path / "isolado.txt"
    mapa.write_text("#####\n#S#G#\n#####\n", encoding="utf-8")
    dados, chave = dados_do_site(mapa)
    assert chave == "isolado"
    assert dados["camadas"]["isolado"]["casas"][""] == [[1, 1]]
    assert dados["solucoes"]["isolado"]["BFS"]["status"] == "SEM_SOLUCAO"


def test_site_unico_tem_tudo_dentro(tmp_path):
    html = gerar_site_unico(tmp_path / "site.html").read_text(encoding="utf-8")
    assert "<script src=" not in html and 'href="style.css"' not in html
    for pagina in ["inicio", "labirintos", "modelagem", "slashdot", "graficos", "equipe"]:
        assert f'id="pg-{pagina}"' in html
    assert 'href="labirintos.html"' not in html   # os links viram #labirintos
    assert "data:image/png;base64," in html          # figuras embutidas
    assert "window.DADOS = " in html and "window.IMAGENS = " in html


def test_data_js(tmp_path):
    destino = gerar_data_js(tmp_path / "data.js")
    texto = destino.read_text(encoding="utf-8")
    assert texto.startswith("// [IA]") and "window.DADOS = " in texto and '"g01"' in texto


def test_site_tem_o_grafo_e_os_arquivos_de_out():
    dados, _ = dados_do_site()
    g = dados["grafos"]["m02"]
    assert len(g["estados"]) == 39 and len(g["arcos"]) == 74      # mesmo G_est do metricas_global.json
    assert g["estados"][0][6] == 0 and g["estados"][0][7] == -1     # o inicio e o nivel 0 da BFS, sem pai
    nomes = [a["nome"] for a in dados["arquivos"]]
    assert "solucoes.csv" in nomes and "arestas_m08.csv" in nomes and "ciclo_negativo_m06.json" in nomes
    assert not any(n.endswith((".html", ".png")) for n in nomes)
