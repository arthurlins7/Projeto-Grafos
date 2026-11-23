# [IA] Claude Code – script que converte os CSV/JSON de out/ em web/data.js (apoio com IO)
"""Gera web/data.js a partir dos mapas e das saidas ja produzidas em out/.

Uso (na raiz do projeto):
    python3 web/build_data.py
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PADRAO_ESTADO = re.compile(r"\((\d+),(\d+)\)\|([^|]*)\|")


def ler_mapas():
    mapas = {}
    for arq in sorted((RAIZ / "data" / "mapas").glob("m*.txt")):
        linhas = [l.rstrip("\n") for l in arq.read_text(encoding="utf-8").splitlines() if not l.startswith(";")]
        codigo = arq.stem[:3]
        mapas[codigo] = {
            "id": codigo,
            "nome": arq.stem[4:].replace("_", " ").capitalize(),
            "grade": linhas,
        }
    return mapas


def ler_solucoes():
    saida = defaultdict(dict)
    with open(RAIZ / "out" / "parte1" / "solucoes.csv", encoding="utf-8") as f:
        for lin in csv.DictReader(f):
            caminho = [[int(r), int(c)] for r, c, _ in PADRAO_ESTADO.findall(lin["caminho"])]
            saida[lin["mapa"]][lin["algoritmo"]] = {
                "passos": int(lin["passos"]) if lin["passos"] else None,
                "custo": int(lin["custo"]) if lin["custo"] else None,
                "status": lin["status"],
                "caminho": caminho,
            }
    return saida


def ler_parte2():
    rel = json.loads((RAIZ / "out" / "parte2" / "parte2_report.json").read_text(encoding="utf-8"))
    tempos = defaultdict(list)
    alcancados = defaultdict(list)
    piloto = []
    extras = {}
    for m in rel["medicoes"]:
        if m["tarefa"] == "escalabilidade nos recortes":
            alg = "Dijkstra" if m["algoritmo"].lower() == "dijkstra" else m["algoritmo"]
            tempos[(alg, m["recorte_percentual"])].append(m["tempo_mediano_ms"])
        elif m["tarefa"].startswith("volta"):
            piloto.append({
                "origem": m["usuario_partida"], "destino": m["destino"],
                "custo": m["custo"], "passos": m["passos"],
            })
        else:
            extras[m["tarefa"]] = m
    escala = []
    for (alg, rec), v in tempos.items():
        escala.append({"alg": alg, "recorte": rec, "ms": round(sum(v) / len(v), 2)})
    return {
        "dataset": rel["dataset"], "nos": rel["nos"], "arcos": rel["arcos"],
        "recortes": rel["recortes"], "escala": escala, "piloto": piloto,
        "ciclo": extras.get("detecção de ciclo negativo", {}).get("ciclo_negativo"),
        "custo_ciclo": extras.get("detecção de ciclo negativo", {}).get("custo_ciclo"),
    }


def main():
    dados = {
        "mapas": ler_mapas(),
        "solucoes": ler_solucoes(),
        "metricas": json.loads((RAIZ / "out" / "parte1" / "metricas_global.json").read_text(encoding="utf-8")),
        "parte2": ler_parte2(),
    }
    with open(RAIZ / "out" / "parte1" / "comparacao_modelagem.csv", encoding="utf-8") as f:
        dados["modelagem"] = list(csv.DictReader(f))
    destino = RAIZ / "web" / "data.js"
    destino.write_text("// [IA] Claude Code – arquivo gerado por web/build_data.py\nwindow.DADOS = " + json.dumps(dados, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"{destino} gerado ({destino.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
