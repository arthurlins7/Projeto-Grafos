# [IA] ChatGPT - apoio na implementacao do comando de validacao dos mapas
# [IA] Claude - comandos da Parte 2 (--dataset, --alg, --source, --target, --recorte, --benchmark)
# [IA] Claude - comandos da Parte 1 (--alg com --mapa, --fonte-consumivel, --armadilhas, --interactive, --out)
import argparse
import os
import webbrowser
import zlib
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
from src.solve import (
    PAGINA_INTERATIVA,
    armadilhas_do_mapa,
    gerar_pagina_interativa,
    nome_curto,
    resolver_mapa,
    salvar_armadilhas_csv,
    salvar_json,
)


PASTA_SAIDA_PARTE2 = Path("out/parte2")
CAMINHO_MAXIMO_NA_TELA = 20  # caminhos maiores aparecem resumidos (o JSON guarda o caminho inteiro)


def criar_parser():
    parser = argparse.ArgumentParser(
        description="Valida e resolve mapas de labirinto (Parte 1) e roda os algoritmos no dataset do Slashdot (Parte 2)."
    )
    entrada = parser.add_mutually_exclusive_group()
    entrada.add_argument("--mapa", help="Parte 1: caminho do arquivo do mapa.")
    entrada.add_argument("--dataset", help="Parte 2: pasta do dataset ou o proprio arquivo .txt/.txt.gz.")
    parser.add_argument(
        "--interactive", action="store_true",
        help=f"Parte 1: abre a pagina interativa ({PAGINA_INTERATIVA.as_posix()}) no navegador; "
             "com --mapa, a pagina ja abre nesse mapa.",
    )
    parser.add_argument(
        "--validar-mapa", action="store_true", help="Parte 1: valida o mapa sem executar buscas."
    )
    parser.add_argument(
        "--alg", type=str.upper, choices=ALGORITMOS,
        help="Algoritmo a executar: no mapa (Parte 1, com --mapa) ou no dataset (Parte 2, com --dataset).",
    )
    parser.add_argument(
        "--fonte-consumivel", action="store_true",
        help="Parte 1: a fonte (*) vale -2 so na primeira vez, como o bonus (corrige o ciclo do m06).",
    )
    parser.add_argument(
        "--armadilhas", action="store_true",
        help="Parte 1: lista os estados alcancaveis de onde nao da mais para chegar na saida.",
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
    parser.add_argument(
        "--out",
        help="Pasta de saida: na Parte 1 grava o resultado do --alg (JSON), do --armadilhas (CSV) "
             "ou a pagina do --interactive; na Parte 2 grava o JSON (padrao: out/parte2).",
    )
    return parser


def main(argv=None):
    parser = criar_parser()
    args = parser.parse_args(argv)
    if args.interactive:
        return comando_interativo(parser, args)
    if args.mapa is not None:
        return comando_mapa(parser, args)
    if args.dataset is not None:
        return comando_dataset(parser, args)
    parser.error("Informe --mapa (Parte 1), --dataset (Parte 2) ou --interactive.")


# ---------------------------------------------------------------- Parte 1

def pasta_de_saida(parser, out):
    # --out da Parte 1 tem que ser uma pasta (se nao existir, e criada depois)
    pasta = Path(out)
    if pasta.exists() and not pasta.is_dir():
        parser.error(f"--out deve ser uma pasta, mas {pasta} e um arquivo.")
    return pasta


def ler_mapa_do_cli(parser, caminho):
    try:
        return ler_mapa(caminho)
    except OSError as erro:
        parser.error(f"Nao foi possivel ler o arquivo {caminho!r}: {erro.strerror}.")
    except UnicodeError:
        parser.error("O arquivo do mapa deve estar em UTF-8.")
    except ValueError as erro:
        parser.error(str(erro))


def comando_interativo(parser, args):
    extras = [nome for nome, valor in (
        ("--dataset", args.dataset), ("--validar-mapa", args.validar_mapa), ("--alg", args.alg),
        ("--fonte-consumivel", args.fonte_consumivel), ("--armadilhas", args.armadilhas),
        ("--source", args.source), ("--target", args.target), ("--recorte", args.recorte),
        ("--benchmark", args.benchmark),
    ) if valor]
    if extras:
        parser.error(f"--interactive nao usa {', '.join(extras)}.")

    destino = PAGINA_INTERATIVA
    if args.out:
        destino = Path(args.out)
        if destino.suffix.lower() != ".html":
            destino = pasta_de_saida(parser, args.out) / PAGINA_INTERATIVA.name
    if args.mapa is not None:
        ler_mapa_do_cli(parser, args.mapa)   # mapa invalido vira mensagem clara, antes de gerar a pagina

    # sem --mapa e sem --out, abre a pagina que ja existe (se nao existir, gera)
    if args.mapa is not None or args.out or not destino.exists():
        print(f"Gerando {destino.as_posix()}...")
        try:
            gerar_pagina_interativa(destino, args.mapa)
        except OSError as erro:
            parser.exit(1, f"Erro: nao foi possivel salvar a pagina em {destino}: {erro}\n")

    if os.environ.get("NAO_ABRIR_NAVEGADOR"):
        # usado nos testes: so gera a pagina, sem abrir o navegador
        print(f"Pagina pronta em {destino.as_posix()}")
        return 0

    print(f"Abrindo {destino.as_posix()} no navegador...")
    if not webbrowser.open(destino.resolve().as_uri()):
        parser.exit(1, f"Erro: nao foi possivel abrir o navegador. "
                       f"Abra o arquivo manualmente: {destino.resolve()}\n")
    return 0


def comando_mapa(parser, args):
    opcoes_da_parte2 = [
        nome for nome, valor in (
            ("--source", args.source), ("--target", args.target), ("--recorte", args.recorte),
        )
        if valor is not None
    ]
    if args.benchmark:
        opcoes_da_parte2.append("--benchmark")
    if opcoes_da_parte2:
        parser.error(f"{', '.join(opcoes_da_parte2)}: opcao da Parte 2, use com --dataset.")

    acoes = [nome for nome, valor in (
        ("--validar-mapa", args.validar_mapa), ("--alg", args.alg), ("--armadilhas", args.armadilhas),
    ) if valor]
    if not acoes:
        parser.error("Informe --validar-mapa, --alg, --armadilhas ou --interactive.")
    if args.validar_mapa and len(acoes) > 1:
        parser.error("--validar-mapa so valida o arquivo; nao use junto com --alg ou --armadilhas.")
    if args.fonte_consumivel and args.validar_mapa:
        parser.error("--fonte-consumivel so faz sentido com --alg ou --armadilhas.")
    if args.out and args.validar_mapa:
        parser.error("--validar-mapa nao grava arquivo; use --out com --alg ou --armadilhas.")
    pasta = pasta_de_saida(parser, args.out) if args.out else None

    linhas = ler_mapa_do_cli(parser, args.mapa)

    if args.validar_mapa:
        print(f"Mapa valido: {len(linhas)} linhas e {len(linhas[0])} colunas.")
        return 0

    nome = Path(args.mapa).stem
    sufixo = "_fonte_consumivel" if args.fonte_consumivel else ""
    if args.alg:
        resultado = resolver_mapa(linhas, args.alg, args.fonte_consumivel)
        imprimir_resultado_mapa(nome, resultado)
        if pasta is not None:
            arquivo = pasta / f"{nome_curto(args.mapa)}_{args.alg.lower()}{sufixo}.json"
            try:
                salvar_json({"mapa": nome, **resultado}, arquivo)
            except OSError as erro:
                parser.exit(1, f"Erro: nao foi possivel salvar o resultado em {pasta}: {erro}\n")
            print(f"Resultado salvo em {arquivo.as_posix()}")
    if args.armadilhas:
        if args.alg:
            print()
        armadilhas, total = armadilhas_do_mapa(linhas, args.fonte_consumivel)
        imprimir_armadilhas(nome, armadilhas, total)
        if pasta is not None:
            # mesmo formato (e mesma ordem) do armadilhas_m04.csv gerado pelo solve.py
            arquivo = pasta / f"armadilhas_{nome_curto(args.mapa)}{sufixo}.csv"
            try:
                salvar_armadilhas_csv(linhas, arquivo, args.fonte_consumivel)
            except OSError as erro:
                parser.exit(1, f"Erro: nao foi possivel salvar as armadilhas em {pasta}: {erro}\n")
            print(f"Armadilhas salvas em {arquivo.as_posix()}")
    return 0


def imprimir_resultado_mapa(nome, resultado):
    extra = " | fonte consumivel" if resultado["fonte_consumivel"] else ""
    print(f"Mapa: {nome} | {resultado['estados']} estados{extra}")
    print(f"Algoritmo: {resultado['algoritmo']}")
    print(f"Status: {resultado['status']}")

    if resultado["status"] == "RECUSA":
        print(resultado["mensagem"])
        print("Use --alg BELLMAN_FORD, que aceita pesos negativos.")
    elif resultado["status"] == "CICLO_NEGATIVO":
        print(f"Ciclo negativo: {formatar_caminho(resultado['ciclo'], 'estados')} (custo {resultado['custo_ciclo']})")
        print("Com um ciclo negativo alcancavel, o menor custo nao fica definido.")
        if not resultado["fonte_consumivel"]:
            print("Tente de novo com --fonte-consumivel.")
    elif resultado["status"] == "SEM_SOLUCAO":
        print("Nao existe caminho do inicio ate a saida.")
    else:
        rotulo = "Caminho na arvore da DFS (nao e necessariamente o menor)" if resultado["algoritmo"] == "DFS" else "Caminho"
        print(f"{rotulo}: {formatar_caminho(resultado['caminho'], 'estados')}")
        print(f"Passos: {resultado['passos']} | custo: {resultado['custo']}")

    if "ciclo_fora_da_rota" in resultado:
        print(f"Aviso: existe um ciclo negativo alcancavel (custo {resultado['custo_ciclo_fora_da_rota']} por volta), "
              "mas dele nao da pra chegar na saida; por isso o custo ate a saida continua definido.")

    if resultado["algoritmo"] == "DFS":
        tipos = ", ".join(f"{tipo}={qtd}" for tipo, qtd in resultado["arcos_por_tipo"].items())
        print(f"Arcos por tipo (DFS): {tipos}")
        print(f"Tem ciclo: {'sim' if resultado['tem_ciclo'] else 'nao'}")


def imprimir_armadilhas(nome, armadilhas, total):
    print(f"Mapa: {nome} | estados-armadilha: {len(armadilhas)} de {total} "
          f"({100 * len(armadilhas) / total:.1f}%)")
    for estado in armadilhas:
        print(f"  {estado}")


# ---------------------------------------------------------------- Parte 2

def comando_dataset(parser, args):
    if args.validar_mapa:
        parser.error("--validar-mapa so pode ser usado com --mapa.")
    if args.fonte_consumivel or args.armadilhas:
        parser.error("--fonte-consumivel e --armadilhas so podem ser usados com --mapa.")
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
    # [IA] Claude – confere o --out antes de rodar a busca ou o benchmark
    if pasta_saida.exists() and not pasta_saida.is_dir():
        parser.error(f"--out deve ser uma pasta, mas {pasta_saida} e um arquivo.")
    arquivo = args.dataset
    try:
        arquivo = localizar_arquivo_dataset(args.dataset)
        dados = ler_dataset(arquivo)
    except (EOFError, zlib.error):
        # [IA] Claude – .gz cortado ou danificado vira mensagem clara, sem traceback
        parser.error(f"Arquivo do dataset incompleto ou corrompido: {arquivo}")
    except (OSError, ValueError) as erro:
        parser.error(str(erro))

    if args.benchmark:
        try:
            relatorio = executar_benchmark(dados, nome_do_dataset(arquivo))
        except ValueError as erro:
            parser.error(str(erro))
        imprimir_resumo_benchmark(relatorio)
        # [IA] Claude – falha ao gravar encerra com erro, sem anunciar sucesso
        try:
            caminho = salvar_relatorio(relatorio, pasta_saida)
        except OSError as erro:
            parser.exit(1, f"Erro: nao foi possivel salvar parte2_report.json em {pasta_saida}: {erro}\n")
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
    # [IA] Claude – falha ao gravar encerra com erro, sem anunciar sucesso
    try:
        caminho = salvar_resultado(resultado, pasta_saida, recorte)
    except OSError as erro:
        parser.exit(1, f"Erro: nao foi possivel salvar o resultado em {pasta_saida}: {erro}\n")
    print(f"Resultado salvo em {caminho}")
    return 0


def formatar_caminho(caminho, unidade="usuarios"):
    if len(caminho) <= CAMINHO_MAXIMO_NA_TELA:
        return " -> ".join(map(str, caminho))
    inicio = " -> ".join(map(str, caminho[:10]))
    fim = " -> ".join(map(str, caminho[-10:]))
    return f"{inicio} -> ... -> {fim} ({len(caminho)} {unidade})"


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
        if resultado["destino"] is not None:
            # [IA] Claude – com destino alcancavel, avisa que o custo nao foi calculado (o algoritmo para no ciclo)
            print("Foi detectado um ciclo negativo alcancavel a partir da origem. "
                  "A busca foi interrompida e o custo ate o destino nao foi calculado.")
        else:
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