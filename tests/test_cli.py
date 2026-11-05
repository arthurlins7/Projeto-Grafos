import subprocess
import sys
from pathlib import Path

import pytest


PASTA_PROJETO = Path(__file__).resolve().parents[1]


def executar_cli(*argumentos):
    return subprocess.run(
        [sys.executable, "-m", "src.cli", *argumentos],
        cwd=PASTA_PROJETO,
        capture_output=True,
        text=True,
        timeout=10,
    )


@pytest.mark.parametrize("nome, altura, largura", [
    ("m01_terreno.txt", 5, 13),
    ("m02_uma_chave.txt", 5, 13),
    ("m03_tres_chaves.txt", 10, 17),
    ("m04_esteiras.txt", 5, 13),
    ("m05_bonus.txt", 7, 15),
    ("m06_fonte.txt", 5, 13),
    ("m07_impossivel.txt", 6, 13),
    ("m08_grande.txt", 31, 71),
])
def test_comando_valida_mapas_fornecidos(nome, altura, largura):
    caminho = str(Path("data") / "mapas" / nome)
    resultado = executar_cli("--mapa", caminho, "--validar-mapa")
    assert resultado.returncode == 0
    assert resultado.stdout.strip() == f"Mapa valido: {altura} linhas e {largura} colunas."
    assert resultado.stderr == ""


def test_comando_aceita_caminho_com_espacos_e_bom(tmp_path):
    caminho = tmp_path / "mapa com espacos.txt"
    conteudo = "; descricao\r\nS.a.\r\n.AGG\r\n"
    caminho.write_bytes(conteudo.encode("utf-8-sig"))
    resultado = executar_cli("--mapa", str(caminho), "--validar-mapa")
    assert resultado.returncode == 0
    assert resultado.stdout.strip() == "Mapa valido: 2 linhas e 4 colunas."
    assert resultado.stderr == ""


@pytest.mark.parametrize("conteudo, mensagem", [
    ("", "mapa nao pode estar vazio"),
    ("SG\n...\n", "linha 2 tem 3 colunas"),
    ("SSG\n", "exatamente um S"),
    ("S..\n", "pelo menos um G"),
    ("SXG\n", "Simbolo desconhecido 'X' na linha 1, coluna 2"),
])
def test_comando_informa_mapa_invalido(tmp_path, conteudo, mensagem):
    caminho = tmp_path / "mapa.txt"
    caminho.write_text(conteudo, encoding="utf-8")
    resultado = executar_cli("--mapa", str(caminho), "--validar-mapa")
    assert resultado.returncode == 2
    assert resultado.stdout == ""
    assert mensagem in resultado.stderr
    assert "Traceback" not in resultado.stderr


def test_comando_informa_arquivo_inexistente(tmp_path):
    caminho = tmp_path / "inexistente.txt"
    resultado = executar_cli("--mapa", str(caminho), "--validar-mapa")
    assert resultado.returncode == 2
    assert resultado.stdout == ""
    assert "Nao foi possivel ler o arquivo" in resultado.stderr
    assert "inexistente.txt" in resultado.stderr
    assert "Traceback" not in resultado.stderr


def test_comando_recusa_diretorio_no_lugar_do_arquivo(tmp_path):
    resultado = executar_cli("--mapa", str(tmp_path), "--validar-mapa")
    assert resultado.returncode == 2
    assert resultado.stdout == ""
    assert "Nao foi possivel ler o arquivo" in resultado.stderr
    assert "Traceback" not in resultado.stderr


def test_comando_informa_codificacao_invalida(tmp_path):
    caminho = tmp_path / "mapa.txt"
    caminho.write_bytes(b"S\xffG")
    resultado = executar_cli("--mapa", str(caminho), "--validar-mapa")
    assert resultado.returncode == 2
    assert resultado.stdout == ""
    assert "O arquivo do mapa deve estar em UTF-8" in resultado.stderr
    assert "Traceback" not in resultado.stderr


@pytest.mark.parametrize("argumentos", [
    [],
    ["--validar-mapa"],
    ["--mapa"],
    ["--mapa", "mapa.txt"],
    ["--mapa", "mapa.txt", "--validar-mapa", "--desconhecido"],
    ["--mapa", "mapa.txt", "--validar-mapa", "--alg", "BFS"],
])
def test_comando_recusa_argumentos_incorretos(argumentos):
    resultado = executar_cli(*argumentos)
    assert resultado.returncode == 2
    assert resultado.stdout == ""
    assert resultado.stderr
    assert "Traceback" not in resultado.stderr


def test_comando_mostra_ajuda():
    resultado = executar_cli("--help")
    assert resultado.returncode == 0
    assert "--mapa" in resultado.stdout
    assert "--validar-mapa" in resultado.stdout
    assert "--alg" not in resultado.stdout
    assert resultado.stderr == ""
