"""
Upload da planilha consolidada no eCIEGES (formulário SISAB) via Playwright.

Seletores baseados no robô e-Gestor (já testados em produção), adaptados ao SISAB:
- Login: input[name='login'] / input[name='password'] / button submit 'Login'
- Importação: botão 'Importar arquivo' -> modal 'Importação de Planilha' -> 'Sim'
  -> input[type=file].set_input_files -> modal 'Selecione a aba da planilha'
  -> dropdown MUI -> aba 'sisab' -> 'Importar essa aba'

Diferença principal vs e-Gestor: o e-Gestor ia direto para a URL do form 472.
Aqui localizamos o formulário SISAB pela tabela de formulários (Gestor Formulários).
Se você souber a URL direta do form SISAB, pode preenchê-la em ECIEGES_FORM_URL
no .env que o robô vai direto, igual ao e-Gestor.
"""
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

from . import config
from .logger import get_logger

log = get_logger()


def _login(page):
    log.info("Acessando página de login do eCIEGES...")
    base = config.ECIEGES_URL.rstrip("/")
    login_url = base if base.endswith("/login") else base + "/login"
    page.goto(login_url, wait_until="networkidle", timeout=config.TIMEOUT_MS)

    # Seletores específicos do eCIEGES (Material UI / React) - iguais ao e-Gestor
    page.fill("input[name='login']", config.ECIEGES_USER)
    page.fill("input[name='password']", config.ECIEGES_PASS)
    page.click("button[type='submit']:has-text('Login')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)
    log.info("Login efetuado.")


def _abrir_formulario_sisab(page):
    """
    Abre o formulario SISAB. Duas estrategias:
    1. Se ECIEGES_FORM_URL estiver definido no .env, navega direto (igual e-Gestor).
    2. Senao, vai em Gestor Formularios > Formulario e clica no link 'SISAB' da tabela.
    """
    form_url = os.getenv("ECIEGES_FORM_URL", "").strip()
    if form_url:
        log.info("Navegando direto para o formulario SISAB: %s", form_url)
        page.goto(form_url, wait_until="networkidle", timeout=config.TIMEOUT_MS)
        page.wait_for_timeout(3000)
        return

    log.info("Abrindo menu Gestor Formulários > Formulário")
    page.locator("text=Gestor Formulários").first.click()
    page.wait_for_timeout(1000)
    page.locator("text=Formulário").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    log.info("Localizando formulario '%s' na tabela", config.ECIEGES_FORM_NOME)
    try:
        busca = page.locator(
            "input[placeholder*='Search'], input[placeholder*='Pesquisar']"
        ).first
        busca.fill(config.ECIEGES_FORM_NOME)
        page.wait_for_timeout(1500)
    except Exception:
        log.warning("Campo de busca nao encontrado; tentando o link direto.")

    page.locator(f"a:has-text('{config.ECIEGES_FORM_NOME}')").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    log.info("Formulario SISAB aberto.")


def _importar(page, caminho_planilha):
    log.info("Aguardando o botao 'Importar arquivo' aparecer no DOM...")
    botao_importar = page.locator("button:has-text('Importar arquivo')").first
    try:
        botao_importar.wait_for(state="attached", timeout=config.TIMEOUT_MS)
    except Exception:
        _diagnostico(page)
        raise

    log.info("Rolando ate o botao...")
    botao_importar.scroll_into_view_if_needed()
    page.wait_for_timeout(1500)

    log.info("Clicando em 'Importar arquivo'...")
    botao_importar.click()
    page.wait_for_timeout(2000)

    log.info("Aguardando modal de confirmacao 'Importacao de Planilha'...")
    page.locator("text=Importação de Planilha").wait_for(state="visible", timeout=15000)
    log.info("Confirmando importacao (clicando em 'Sim')...")
    page.locator("button:has-text('Sim')").first.click()
    page.wait_for_timeout(2000)

    log.info("Selecionando arquivo: %s", caminho_planilha)
    input_file = page.locator("input[type='file']").first
    input_file.wait_for(state="attached", timeout=10000)
    input_file.set_input_files(caminho_planilha)
    page.wait_for_timeout(3000)

    log.info("Aguardando modal de selecao de aba...")
    page.locator("text=Selecione a aba da planilha").wait_for(state="visible", timeout=15000)

    log.info("Abrindo dropdown de abas...")
    page.locator("[aria-haspopup='listbox']").last.click()
    page.wait_for_timeout(1500)

    log.info("Selecionando aba '%s'...", config.ECIEGES_ABA_IMPORT)
    page.locator(f"li:has-text('{config.ECIEGES_ABA_IMPORT}')").first.click()
    page.wait_for_timeout(1500)

    log.info("Clicando em 'Importar essa aba'...")
    page.locator("button:has-text('Importar essa aba')").first.click()

    log.info("Aguardando processamento do upload...")
    page.wait_for_load_state("networkidle", timeout=120000)
    page.wait_for_timeout(5000)
    log.info("Upload no eCIEGES concluido com sucesso.")


def _diagnostico(page):
    """Salva screenshot e HTML para diagnostico quando um seletor falha."""
    try:
        screenshot_path = config.LOG_DIR / "erro_ecieges.png"
        html_path = config.LOG_DIR / "erro_ecieges.html"
        page.screenshot(path=str(screenshot_path), full_page=True)
        html_path.write_text(page.content(), encoding="utf-8")
        log.error("Screenshot salvo em: %s", screenshot_path)
        log.error("HTML da pagina salvo em: %s", html_path)
    except Exception as e:
        log.warning("Nao foi possivel salvar diagnostico: %s", e)


def enviar(caminho_planilha=None):
    """Executa todo o fluxo de upload no eCIEGES."""
    caminho_planilha = str(Path(caminho_planilha or config.PLANILHA_CONSOLIDADA))

    if not all([config.ECIEGES_USER, config.ECIEGES_PASS]):
        raise ValueError("Credenciais do eCIEGES ausentes no .env (ECIEGES_USER/ECIEGES_PASS).")
    if not Path(caminho_planilha).exists():
        raise FileNotFoundError(f"Planilha nao encontrada para upload: {caminho_planilha}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.HEADLESS)
        # ignore_https_errors: o eCIEGES usa certificado interno que o navegador
        # rejeita (ERR_CERT_COMMON_NAME_INVALID). Permite acessar mesmo assim.
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.set_default_timeout(config.TIMEOUT_MS)
        try:
            _login(page)
            _abrir_formulario_sisab(page)
            _importar(page, caminho_planilha)
        except Exception:
            _diagnostico(page)
            raise
        finally:
            context.close()
            browser.close()
