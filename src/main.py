"""
Robô SISAB - orquestrador principal.

Fluxo:
1. Encontra o CSV mais recente na pasta de rede.
2. Lê o CSV (competência derivada do nome).
3. Insere na planilha consolidada (aba 'sisab') com antiduplicidade.
4. Se inseriu algo novo, faz upload no eCIEGES (formulário SISAB).
5. Envia e-mail de status.

Uso:
    python -m src.main
    python -m src.main --so-planilha   # pula etapa eCIEGES
"""
import sys
import time
import traceback

from . import config
from .logger import get_logger
from . import csv_reader, planilha, ecieges, email_status

log = get_logger()


def _com_retry(func, descricao: str):
    """Executa func com retry em falhas (timeouts de rede/site)."""
    ultima_exc = None
    for tentativa in range(1, config.MAX_RETRIES + 1):
        try:
            return func()
        except Exception as e:
            ultima_exc = e
            log.warning("Falha em '%s' (tentativa %d/%d): %s",
                        descricao, tentativa, config.MAX_RETRIES, e)
            if tentativa < config.MAX_RETRIES:
                time.sleep(config.RETRY_DELAY_S)
    raise ultima_exc


def executar(pular_ecieges: bool = False) -> int:
    log.info("=" * 60)
    log.info("INÍCIO - Robô SISAB")
    log.info("=" * 60)

    try:
        # 1 + 2) Encontrar e ler o CSV
        csv_path = _com_retry(csv_reader.encontrar_csv_mais_recente, "localizar CSV")
        comp, linhas = csv_reader.ler_csv(csv_path)

        # 3) Inserir na planilha consolidada
        res = planilha.inserir(linhas, comp)

        if not res["inseriu"]:
            # Competência já existia: nada a fazer, não sobe no eCIEGES
            assunto = f"[Robô SISAB] Nada a inserir - {comp.strftime('%m/%Y')}"
            corpo = (f"O CSV mais recente ({csv_path.name}) refere-se à competência "
                     f"{comp.strftime('%m/%Y')}, que já consta na planilha.\n\n{res['motivo']}")
            email_status.enviar_status(assunto, corpo)
            log.info("FIM - sem novidades.")
            return 0

        # 4) Upload no eCIEGES
        if pular_ecieges or config.PULAR_ECIEGES:
            log.info("Etapa eCIEGES pulada (config/flag).")
        else:
            _com_retry(lambda: ecieges.enviar(config.PLANILHA_CONSOLIDADA),
                       "upload eCIEGES")

        # 5) E-mail de sucesso
        assunto = f"[Robô SISAB] Sucesso - {comp.strftime('%m/%Y')}"
        corpo = (f"Processamento concluído com sucesso.\n\n"
                 f"Arquivo: {csv_path.name}\n"
                 f"{res['motivo']}\n"
                 f"eCIEGES: {'pulado' if (pular_ecieges or config.PULAR_ECIEGES) else 'importado (formulário SISAB)'}")
        email_status.enviar_status(assunto, corpo)
        log.info("FIM - sucesso.")
        return 0

    except Exception as e:
        erro = f"{type(e).__name__}: {e}"
        log.error("ERRO FATAL: %s", erro)
        log.error(traceback.format_exc())
        email_status.enviar_status(
            "[Robô SISAB] ERRO na execução",
            f"O robô falhou.\n\nErro: {erro}\n\n{traceback.format_exc()}",
        )
        return 1


if __name__ == "__main__":
    pular = "--so-planilha" in sys.argv
    sys.exit(executar(pular_ecieges=pular))
