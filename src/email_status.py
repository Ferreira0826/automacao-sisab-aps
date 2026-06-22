"""
Envio de e-mail de status via Gmail API.
Reaproveita as MESMAS credentials.json / token.json do robô e-Gestor
(basta apontar GMAIL_CREDENTIALS e GMAIL_TOKEN no .env para os arquivos existentes).
"""
import base64
from email.mime.text import MIMEText
from pathlib import Path

from . import config
from .logger import get_logger

log = get_logger()

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _servico():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    token_path = Path(config.GMAIL_TOKEN)
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.GMAIL_CREDENTIALS, SCOPES
            )
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


def enviar_status(assunto: str, corpo: str):
    """Envia e-mail de status. Não derruba o robô se falhar."""
    if not config.ENVIAR_EMAIL:
        log.info("Envio de e-mail desativado (ENVIAR_EMAIL=false).")
        return
    if not config.EMAIL_DESTINO:
        log.warning("EMAIL_DESTINO vazio; e-mail não enviado.")
        return
    try:
        service = _servico()
        msg = MIMEText(corpo, "plain", "utf-8")
        msg["to"] = config.EMAIL_DESTINO
        if config.EMAIL_REMETENTE:
            msg["from"] = config.EMAIL_REMETENTE
        msg["subject"] = assunto
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        log.info("E-mail de status enviado: %s", assunto)
    except Exception as e:
        log.error("Falha ao enviar e-mail (ignorada): %s", e)
