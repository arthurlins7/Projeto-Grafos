# [IA] ChatGPT - apoio na implementacao do comando de validacao dos mapas
# [IA] Claude - comandos da Parte 2 (--dataset, --alg, --source, --target, --recorte, --benchmark)
import argparse
from pathlib import Path

from src.graphs.io import ler_dataset, ler_mapa, montar_grafo_dataset
from src.parte2 import (
    ALGORITMOS,
    PERCENTUAIS,
    executar_algoritmo,
    executar_benchmark,
    localizar_arquivo_dataset,
    montar_recorte,
    nome_do_dataset,
    salvar_relatorio,
    salvar_resultado,
    sem_acentos,
)


PASTA_SAIDA_PARTE2 = Path("out/parte2")
CAMINHO_MAXIMO_NA_TELA = 20  # caminhos maiores aparecem resumidos (o JSON guarda o caminho inteiro)


def criar_parser():
    parser = argparse.ArgumentParser(
        description="Valida mapas de labirinto (Parte 1) e roda os algoritmos no dataset do Slashdot (Parte 2)."
    )
    entrada = parser.add_mutually_exclusive_group(required=True)
    entrada.add_argument("--mapa", help="Parte 1: caminho do arquivo do mapa.")
    entrada.add_argument("--dataset", help="Parte 2: pasta do dataset ou o proprio arquivo .txt/.txt.gz.")
    parser.add_argument(
        "--validar-mapa", action="store_true", help="Parte 1: valida o mapa sem executar buscas."
    )
    parser.add_argument(
        "--alg", type=str.upper, choices=ALGORITMOS, help="Parte 2: algoritmo a executar."
    )
    parser.add_argument("--source", type=int, help="Parte 2: usuario de partida.")
    parser.add_argument("--target", type=int, help="Parte 2: usuario de chegada (opcional).")
    parser.add_argument(
        "--recorte", type=int, choices=PERCENTUAIS,
        help="Parte 2: porcentagem dos usuarios usada no grafo (padrao: 100).",
    )
    parser.add_argument(
        "--benchmark", action="store_true",
        help="Parte 2: mede os quatro algoritmos (5 execucoes) e grava parte2_report.json.",
    )
    parser.add_argument("--out", help="Parte 2: pasta de saida (padrao: out/parte2).")
    return parser


def main(argv=None):
    parser = criar_parser()
    args = parser.parse_args(argv)
    if args.mapa is not None:
        return comando_mapa(parser, args)
    return comando_dataset(parser, args)


# ---------------------------------------------------------------- Parte 1

def comando_mapa(parser, args):
    opcoes_da_parte2 = [
        nome for nome, valor in (
            ("--alg", args.alg), ("--source", args.source), ("--target", args.target),
            ("--recorte", args.recorte), ("--out", args.out),
        )
        if valor is not None
    ]
    if args.benchmark:
        opcoes_da_parte2.append("--benchmark")
    if opcoes_da_parte2:
        parser.error(f"{', '.join(opcoes_da_parte2)}: opcao da Parte 2, use com --dataset.")

    if not args.validar_mapa:
        parser.error("Informe --validar-mapa para validar o arquivo.")

    try:
        linhas = ler_mapa(args.mapa)
    except OSError as erro:
        parser.error(f"Nao foi possivel ler o arquivo {args.mapa!r}: {erro.strerror}.")
    except UnicodeError:
        parser.error("O arquivo do mapa deve estar em UTF-8.")
    except ValueError as erro:
        parser.error(str(erro))

    print(f"Mapa valido: {len(linhas)} linhas e {len(linhas[0])} colunas.")
    return 0


# ---------------------------------------------------------------- Parte 2

def comando_dataset(parser, args):
    if args.validar_mapa:
        parser.error("--validar-mapa so pode ser usado com --mapa.")
    if args.benchmark:
        extras = [nome for nome, valor in (
            ("--alg", args.alg), ("--source", args.source), ("--target", args.target), ("--recorte", args.recorte),
        ) if valor is not None]
        if extras:
            parser.error(f"--benchmark nao usa {', '.join(extras)}.")
    elif args.alg is None:
        parser.error("Informe --alg (com --source) ou --benchmark.")
    elif args.source is None:
        parser.error("Informe --source com o usuario de partida.")

    pasta_saida = Path(args.out) if args.out else PASTA_SAIDA_PARTE2
    try:
        arquivo = localizar_arquivo_dataset(args.dataset)
        dados = ler_dataset(arquivo)
    except (OSError, ValueError) as erro:
        parser.error(str(erro))

    if args.benchmark:
        try:
            relatorio = executar_benchmark(dados, nome_do_dataset(arquivo))
        except ValueError as erro:
            parser.error(str(erro))
        caminho = salvar_relatorio(relatorio, pasta_saida)
        imprimir_resumo_benchmark(relatorio)
        print(f"{len(relatorio['medicoes'])} medicoes salvas em {caminho}")
        return 0

    recorte = args.recorte or 100
    grafo = montar_grafo_dataset(dados)
    if recorte != 100:
        grafo = montar_recorte(grafo, recorte)

    try:
        resultado = executar_algoritmo(grafo, args.alg, args.source, args.target)
    except KeyError as erro:
        parser.error(f"{erro.args[0]} (recorte de {recorte}%)")

    resultado["dataset"] = nome_do_dataset(arquivo)
    resultado["recorte_percentual"] = recorte
    imprimir_resultado(resultado, grafo)
    caminho = salvar_resultado(resultado, pasta_saida, recorte)
    print(f"Resultado salvo em {caminho}")
    return 0


def formatar_caminho(caminho):
    if len(caminho) <= CAMINHO_MAXIMO_NA_TELA:
        return " -> ".join(map(str, caminho))
    inicio = " -> ".join(map(str, caminho[:10]))
    fim = " -> ".join(map(str, caminho[-10:]))
    return f"{inicio} -> ... -> {fim} ({len(caminho)} usuarios)"


def imprimir_resultado(resultado, grafo):
    print(
        f"Dataset: {resultado['dataset']} | recorte de {resultado['recorte_percentual']}%: "
        f"{grafo.ordem()} usuarios, {grafo.tamanho()} marcacoes"
    )
    print(f"Algoritmo: {resultado['algoritmo']} | pesos: {resultado['pesos']}")
    destino = resultado["destino"] if resultado["destino"] is not None else "-"
    print(f"Origem: {resultado['origem']} | destino: {destino}")
    print(f"Status: {resultado['status']}")

    if resultado["status"] == "CICLO_NEGATIVO":
        print(f"Ciclo negativo: {formatar_caminho(resultado['ciclo_negativo'])} (custo {resultado['custo_ciclo']})")
        if resultado["caminho_ate_ciclo"]:
            print(f"Caminho da origem ate o ciclo (BFS): {formatar_caminho(resultado['caminho_ate_ciclo'])}")
        print("Com um ciclo negativo alcancavel, o menor custo nao fica definido.")
    else:
        print(f"Usuarios alcancados a partir da origem: {resultado['alcancados']}")
        if resultado["algoritmo"] == "DFS":
            tipos = ", ".join(f"{tipo}={qtd}" for tipo, qtd in resultado["arcos_por_tipo"].items())
            print(f"Arcos por tipo (DFS): {tipos}")
            print(f"Ciclo alcancavel a partir da origem: {'sim' if resultado['tem_ciclo'] else 'nao'}")
        if resultado["status"] == "SEM_SOLUCAO":
            print(f"Nao existe caminho de {resultado['origem']} ate {resultado['destino']}.")
        elif "caminho" in resultado:
            rotulo = "Caminho na arvore da DFS (nao e necessariamente o menor)" if resultado["algoritmo"] == "DFS" else "Caminho"
            print(f"{rotulo}: {formatar_caminho(resultado['caminho'])}")
            linha = f"Passos: {resultado['passos']}"
            if "custo" in resultado:
                linha += f" | custo: {resultado['custo']}"
            print(linha)

    print(f"Tempo de execucao: {resultado['tempo_ms']:.3f} ms")


def imprimir_resumo_benchmark(relatorio):
    print("Tempo medio por algoritmo e tarefa (ms):")
    grupos = {}
    for m in relatorio["medicoes"]:
        grupos.setdefault((m["algoritmo"], m["tarefa"]), []).append(m["tempo_medio_ms"])
    for (algoritmo, tarefa), tempos in grupos.items():
        print(f"  {algoritmo:<13} {sem_acentos(tarefa):<34} {len(tempos):>2} medicoes  {sum(tempos) / len(tempos):>10.3f}")

    for m in relatorio["medicoes"]:
        if m["tarefa"] == "peso negativo sem ciclo negativo":
            print(f"Bellman-Ford sem ciclo negativo: usuario {m['usuario_partida']} no recorte de 10% "
                  f"({m['alcancados']} alcancados)")
        if m["tarefa"] == "detecção de ciclo negativo":
            print(f"Ciclo negativo na rede completa: {formatar_caminho(m['ciclo_negativo'])} "
                  f"(custo {m['custo_ciclo']})")


if __name__ == "__main__":
    raise SystemExit(main())
