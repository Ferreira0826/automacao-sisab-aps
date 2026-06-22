"""
Configuração central do Robô SISAB.
Lê tudo do arquivo .env (na raiz do projeto).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Raiz do projeto (pasta acima de src/)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def _get_bool(key: str, default: bool = False) -> bool:
    v = os.getenv(key, str(default)).strip().lower()
    return v in ("1", "true", "yes", "sim", "on")


# ----------------------------------------------------------------------
# CAMINHOS DE ARQUIVO (rede corporativa SES-DF)
# ----------------------------------------------------------------------
# Pasta onde ficam os CSVs brutos do SISAB (RelAtvColetivaMB XXX26.csv)
PASTA_CSV_SISAB = _get(
    "PASTA_CSV_SISAB",
    r"\\SERVIDOR\caminho\para\relatorios-sisab\sisab",
)

# Planilha consolidada de destino (a que o eCIEGES importa)
PLANILHA_CONSOLIDADA = _get(
    "PLANILHA_CONSOLIDADA",
    r"\\SERVIDOR\caminho\para\Praticas_corporais_Atividade_Fisica_SISAB_atualizado.xlsx",
)

# Aba da planilha consolidada que recebe os dados do SISAB
ABA_DESTINO = _get("ABA_DESTINO", "sisab")

# Padrão de nome dos CSVs (prefixo). Ex.: "RelAtvColetivaMB"
PREFIXO_CSV = _get("PREFIXO_CSV", "RelAtvColetivaMB")

# ----------------------------------------------------------------------
# eCIEGES
# ----------------------------------------------------------------------
ECIEGES_URL = _get("ECIEGES_URL", "https://ecieges.saude.df.gov.br")
ECIEGES_USER = _get("ECIEGES_USER")
ECIEGES_PASS = _get("ECIEGES_PASS")
# Nome do formulário a procurar na tela "Formulário"
ECIEGES_FORM_NOME = _get("ECIEGES_FORM_NOME", "SISAB")
# Nome da aba a escolher no diálogo "Selecione a aba da planilha"
ECIEGES_ABA_IMPORT = _get("ECIEGES_ABA_IMPORT", "sisab")

# ----------------------------------------------------------------------
# COMPORTAMENTO / EXECUÇÃO
# ----------------------------------------------------------------------
HEADLESS = _get_bool("HEADLESS", True)
TIMEOUT_MS = int(_get("TIMEOUT_MS", "60000"))
MAX_RETRIES = int(_get("MAX_RETRIES", "3"))
RETRY_DELAY_S = int(_get("RETRY_DELAY_S", "10"))

# Pula a etapa do eCIEGES (útil pra testar só a parte da planilha)
PULAR_ECIEGES = _get_bool("PULAR_ECIEGES", False)

# ----------------------------------------------------------------------
# E-MAIL (Gmail API) - reaproveita credenciais do robô e-Gestor
# ----------------------------------------------------------------------
ENVIAR_EMAIL = _get_bool("ENVIAR_EMAIL", True)
EMAIL_DESTINO = _get("EMAIL_DESTINO")
EMAIL_REMETENTE = _get("EMAIL_REMETENTE")
# Caminhos dos arquivos de credencial do Gmail (mesmos do robô e-Gestor, se quiser)
GMAIL_CREDENTIALS = _get("GMAIL_CREDENTIALS", str(BASE_DIR / "credentials.json"))
GMAIL_TOKEN = _get("GMAIL_TOKEN", str(BASE_DIR / "token.json"))

# ----------------------------------------------------------------------
# LOG
# ----------------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
