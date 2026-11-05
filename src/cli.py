import argparse

from src.graphs.io import ler_mapa


def main():
    parser = argparse.ArgumentParser(description="Valida o formato dos mapas de labirinto.")
    parser.add_argument("--mapa", required=True, help="Caminho do arquivo do mapa.")
    parser.add_argument(
        "--validar-mapa", action="store_true", help="Valida o mapa sem executar buscas."
    )
    args = parser.parse_args()

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


if __name__ == "__main__":
    raise SystemExit(main())
