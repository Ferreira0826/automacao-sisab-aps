"""
Append dos dados do SISAB na planilha consolidada (aba 'sisab').

Regras (validadas):
- Append a partir da 1ª linha vazia da coluna A da aba destino.
- Antiduplicidade por competência (ano, mês): se o mês já existe na coluna A,
  NÃO insere nada (mantém o comportamento pedido).
- Preserva todas as outras abas do arquivo.
- Coluna A (Competencia) gravada como datetime com formato 'dd/mm/yy'
  para ficar idêntica às linhas já existentes.
"""
from copy import copy
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Font

from . import config
from .logger import get_logger

log = get_logger()

FORMATO_DATA = "dd/mm/yy"


def competencias_existentes(ws) -> set[tuple[int, int]]:
    """Retorna o conjunto de (ano, mês) já presentes na coluna A."""
    existentes = set()
    for (valor,) in ws.iter_rows(min_row=2, min_col=1, max_col=1, values_only=True):
        if isinstance(valor, datetime):
            existentes.add((valor.year, valor.month))
    return existentes


def primeira_linha_vazia(ws) -> int:
    """Primeira linha sem dado na coluna A (ponto de append)."""
    ultima = 1  # cabeçalho
    for i, (valor,) in enumerate(
        ws.iter_rows(min_col=1, max_col=1, values_only=True), start=1
    ):
        if valor is not None and str(valor).strip() != "":
            ultima = i
    return ultima + 1


def inserir(linhas: list[list], comp: datetime,
            caminho: str | None = None, aba: str | None = None) -> dict:
    """
    Insere as linhas na aba destino, respeitando antiduplicidade.
    Retorna dict com status: {'inseriu': bool, 'qtd': int, 'linha_inicio': int, 'motivo': str}
    """
    caminho = Path(caminho or config.PLANILHA_CONSOLIDADA)
    aba = aba or config.ABA_DESTINO

    if not caminho.exists():
        raise FileNotFoundError(f"Planilha consolidada não encontrada: {caminho}")

    log.info("Abrindo planilha consolidada: %s", caminho.name)
    wb = openpyxl.load_workbook(caminho)  # mantém todas as abas
    if aba not in wb.sheetnames:
        raise ValueError(
            f"Aba '{aba}' não existe. Abas disponíveis: {wb.sheetnames}"
        )
    ws = wb[aba]

    # ---- Antiduplicidade ----
    chave = (comp.year, comp.month)
    existentes = competencias_existentes(ws)
    if chave in existentes:
        msg = f"Competência {comp.strftime('%m/%Y')} já existe na aba '{aba}'. Nada inserido."
        log.warning(msg)
        wb.close()
        return {"inseriu": False, "qtd": 0, "linha_inicio": None, "motivo": msg}

    # ---- Append ----
    inicio = primeira_linha_vazia(ws)
    log.info("Inserindo %d linhas a partir da linha %d", len(linhas), inicio)

    # Linha-modelo: última linha de dados já existente (inicio - 1).
    # Copiamos a fonte/alinhamento dela para que as novas linhas fiquem
    # idênticas (ex.: Arial 10), sem fixar isso no código.
    modelo_row = inicio - 1 if inicio - 1 >= 2 else None
    fonte_padrao = Font(name="Arial", size=10)

    for offset, linha in enumerate(linhas):
        r = inicio + offset
        for c, valor in enumerate(linha, start=1):
            cell = ws.cell(row=r, column=c, value=valor)
            # Estilo: copia da célula-modelo correspondente; senão usa Arial 10.
            if modelo_row:
                modelo = ws.cell(row=modelo_row, column=c)
                cell.font = copy(modelo.font)
                cell.alignment = copy(modelo.alignment)
            else:
                cell.font = copy(fonte_padrao)
            if c == 1:  # coluna Competencia -> formato de data
                cell.number_format = FORMATO_DATA

    wb.save(caminho)
    wb.close()

    msg = (f"Inseridas {len(linhas)} linhas (competência {comp.strftime('%m/%Y')}) "
           f"na aba '{aba}', linhas {inicio}–{inicio + len(linhas) - 1}.")
    log.info(msg)
    return {"inseriu": True, "qtd": len(linhas), "linha_inicio": inicio, "motivo": msg}
