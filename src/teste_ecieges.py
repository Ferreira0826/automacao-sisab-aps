"""
Teste isolado do módulo eCIEGES.

Roda SOMENTE o fluxo de upload no eCIEGES (login -> formulário SISAB ->
importar arquivo -> escolher aba -> importar), usando a planilha definida
em PLANILHA_CONSOLIDADA no .env. Não toca em CSV nem na lógica de planilha.

Uso:
    python -m src.teste_ecieges

Recomendado: rodar com HEADLESS=false no .env para acompanhar na tela.
"""
from . import config, ecieges
from .logger import get_logger

log = get_logger()

if __name__ == "__main__":
    log.info("=" * 60)
    log.info("TESTE ISOLADO - eCIEGES")
    log.info("Planilha que será enviada: %s", config.PLANILHA_CONSOLIDADA)
    log.info("URL: %s | Form: %s | Aba import: %s",
             config.ECIEGES_URL, config.ECIEGES_FORM_NOME, config.ECIEGES_ABA_IMPORT)
    log.info("HEADLESS: %s", config.HEADLESS)
    log.info("=" * 60)

    try:
        ecieges.enviar(config.PLANILHA_CONSOLIDADA)
        log.info("TESTE eCIEGES: concluído sem exceções.")
    except Exception as e:
        log.error("TESTE eCIEGES: FALHOU -> %s: %s", type(e).__name__, e)
        raise
