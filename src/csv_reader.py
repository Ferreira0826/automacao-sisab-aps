"""
Descoberta e leitura do CSV bruto do SISAB.

Regras (validadas contra arquivos reais):
- Encoding típico: cp1252 / latin-1 (detectado automaticamente).
- Separador: ';' (ponto-e-vírgula).
- Cabeçalho real começa na linha que tem 'Uf' na 1ª coluna (linha 11 no exemplo).
- Dados: somente linhas cuja 1ª coluna == 'DF' (descarta cabeçalho institucional e rodapé "Fonte:" / "Dado gerado em:").
- O CSV NÃO tem coluna Competencia; ela é derivada do nome do arquivo (ex.: ABR26 -> 01/04/2026).
- Valores numéricos podem vir com separador de milhar ('1.481' -> 1481).
"""
import csv
import re
from datetime import datetime
from pathlib import Path

from . import config
from .logger import get_logger

log = get_logger()

MESES = {
    "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6,
    "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12,
}


def detectar_encoding(path: Path) -> str:
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"  # fallback que nunca falha


def competencia_do_nome(nome_arquivo: str) -> datetime:
    """'RelAtvColetivaMB ABR26.csv' -> datetime(2026, 4, 1)."""
    m = re.search(r"([A-Z]{3})\s*(\d{2})", nome_arquivo.upper())
    if not m:
        raise ValueError(
            f"Não consegui extrair mês/ano do nome do arquivo: {nome_arquivo!r}. "
            "Esperado algo como 'ABR26'."
        )
    sigla, aa = m.group(1), m.group(2)
    if sigla not in MESES:
        raise ValueError(f"Sigla de mês desconhecida: {sigla!r}")
    return datetime(2000 + int(aa), MESES[sigla], 1)


def _to_int(s: str):
    """'1.481' -> 1481 ; '02' -> 2 ; '' -> None."""
    s = (s or "").strip().replace(".", "").replace(" ", "")
    return int(s) if s else None


def encontrar_csv_mais_recente(pasta: str | None = None) -> Path:
    """Encontra o CSV mais recente na pasta (por data de modificação)."""
    pasta = Path(pasta or config.PASTA_CSV_SISAB)
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta de CSVs não encontrada: {pasta}")

    candidatos = sorted(
        pasta.glob(f"{config.PREFIXO_CSV}*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidatos:
        raise FileNotFoundError(
            f"Nenhum CSV '{config.PREFIXO_CSV}*.csv' encontrado em {pasta}"
        )
    escolhido = candidatos[0]
    log.info("CSV mais recente encontrado: %s", escolhido.name)
    return escolhido


def ler_csv(path: Path) -> tuple[datetime, list[list]]:
    """
    Lê o CSV e retorna (competencia, linhas).
    Cada linha já vem no formato final da planilha consolidada:
    [competencia(datetime), Uf, Ibge(int), Municipio, CNES(int),
     TipoUnidade(int), DescUnidade, QtdAtividade(int), NumParticipantes(int)]
    """
    path = Path(path)
    enc = detectar_encoding(path)
    comp = competencia_do_nome(path.name)
    log.info("Encoding detectado: %s | Competência: %s", enc, comp.strftime("%d/%m/%Y"))

    with open(path, encoding=enc, newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))

    # localizar cabeçalho (linha cuja 1ª coluna == 'Uf')
    try:
        hidx = next(
            i for i, r in enumerate(rows) if r and r[0].strip().lower() == "uf"
        )
    except StopIteration:
        raise ValueError("Cabeçalho 'Uf;Ibge;...' não encontrado no CSV.")

    dados: list[list] = []
    for r in rows[hidx + 1:]:
        # só linhas de dado de verdade (descarta rodapé "Fonte:" etc.)
        if len(r) >= 8 and r[0].strip().upper() == "DF":
            dados.append([
                comp,
                r[0].strip(),          # Uf
                _to_int(r[1]),         # Ibge
                r[2].strip(),          # Municipio
                _to_int(r[3]),         # Unidade de Saúde - CNES
                _to_int(r[4]),         # Tipo Unidade
                r[5].strip(),          # Desc Unidade
                _to_int(r[6]),         # Quantidade Atividade
                _to_int(r[7]),         # Num. Participantes
            ])

    if not dados:
        raise ValueError("Nenhuma linha de dado (DF) encontrada no CSV.")

    log.info("Linhas de dados lidas do CSV: %d", len(dados))
    return comp, dados
