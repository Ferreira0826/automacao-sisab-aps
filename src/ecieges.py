"""
Upload da planilha consolidada no eCIEGES (formulário SISAB) via Playwright.

Fluxo (espelha o robô e-Gestor, adaptado ao SISAB):
1. Login no eCIEGES.
2. Menu Gestor Formulários -> Formulário.
3. Localiza a linha do formulário 'SISAB' na tabela.
4. Entra no formulário, rola até o fim.
5. Clica em 'Importar Arquivo' -> confirma ('Sim').
6. Seleciona o arquivo da planilha consolidada no diálogo de upload do SO.
7. Escolhe a aba 'sisab' no diálogo "Selecione a aba da planilha".
8. Clica em 'Importar Essa Aba'.

OBS: seletores marcados com #AJUSTE podem precisar de pequeno ajuste conforme
o HTML real do eCIEGES. Rode 1x com HEADLESS=false pra validar visualmente.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from . import config
from .logger import get_logger

log = get_logger()


def _login(page):
    log.info("Acessando eCIEGES: %s", config.ECIEGES_URL)
    page.goto(config.ECIEGES_URL, timeout=config.TIMEOUT_MS)

    # #AJUSTE: confirmar os seletores de login conforme a tela real
    page.fill("input[type='text'], input[name='usuario'], input[name='login']",
              config.ECIEGES_USER)
    page.fill("input[type='password'], input[name='senha']",
              config.ECIEGES_PASS)
    page.click("button[type='submit'], button:has-text('Entrar'), button:has-text('Acessar')")
    page.wait_for_load_state("networkidle", timeout=config.TIMEOUT_MS)
    log.info("Login efetuado.")


def _abrir_formulario_sisab(page):
    # Menu lateral: Gestor Formulários -> Formulário
    log.info("Abrindo menu Gestor Formulários > Formulário")
    page.click("text=Gestor Formulários")
    page.click("text=Formulário")
    page.wait_for_load_state("networkidle", timeout=config.TIMEOUT_MS)

    # Usa o campo de busca da tabela pra filtrar pelo nome do formulário
    log.info("Localizando formulário '%s' na tabela", config.ECIEGES_FORM_NOME)
    try:
        page.fill("input[placeholder*='Search'], input[placeholder*='Pesquisar']",
                  config.ECIEGES_FORM_NOME)
        page.wait_for_timeout(1500)
    except PWTimeout:
        log.warning("Campo de busca não encontrado; tentando localizar pelo link direto.")

    # Clica no nome do formulário (link na coluna NOME)
    page.click(f"a:has-text('{config.ECIEGES_FORM_NOME}'), "
               f"td:has-text('{config.ECIEGES_FORM_NOME}') a")
    page.wait_for_load_state("networkidle", timeout=config.TIMEOUT_MS)
    log.info("Formulário SISAB aberto.")


def _importar_arquivo(page, caminho_planilha: str):
    # Rola até o fim da página pra revelar os botões
    page.mouse.wheel(0, 20000)
    page.wait_for_timeout(1000)

    log.info("Clicando em 'Importar Arquivo'")
    # O clique abre o diálogo de arquivo do SO -> capturamos via file_chooser
    with page.expect_file_chooser(timeout=config.TIMEOUT_MS) as fc_info:
        page.click("button:has-text('Importar Arquivo')")
        # Alguns fluxos pedem confirmação 'Sim' antes do file picker
        try:
            page.click("button:has-text('Sim')", timeout=3000)
        except PWTimeout:
            pass
    file_chooser = fc_info.value
    file_chooser.set_files(caminho_planilha)
    log.info("Arquivo selecionado: %s", caminho_planilha)
    page.wait_for_timeout(2000)


def _escolher_aba_e_confirmar(page):
    # Diálogo "Selecione a aba da planilha" -> selecionar 'sisab'
    log.info("Selecionando aba '%s' no diálogo de importação", config.ECIEGES_ABA_IMPORT)
    try:
        # Tenta como <select>
        page.select_option("select", label=config.ECIEGES_ABA_IMPORT, timeout=4000)
    except Exception:
        # Dropdown customizado (Material): abre e clica na opção
        page.click("text=Aba")
        page.click(f"text={config.ECIEGES_ABA_IMPORT}")

    page.wait_for_timeout(500)
    log.info("Clicando em 'Importar Essa Aba'")
    page.click("button:has-text('Importar Essa Aba')")
    page.wait_for_load_state("networkidle", timeout=config.TIMEOUT_MS)
    log.info("Importação no eCIEGES concluída.")


def enviar(caminho_planilha: str | None = None):
    """Executa todo o fluxo de upload no eCIEGES."""
    caminho_planilha = str(Path(caminho_planilha or config.PLANILHA_CONSOLIDADA))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.HEADLESS)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(config.TIMEOUT_MS)
        try:
            _login(page)
            _abrir_formulario_sisab(page)
            _importar_arquivo(page, caminho_planilha)
            _escolher_aba_e_confirmar(page)
        finally:
            context.close()
            browser.close()
