# Robô SISAB — Automação de Práticas Corporais / Atividade Física

Automação em Python que lê o relatório CSV mais recente do SISAB na rede
corporativa da SES-DF, insere os dados na planilha consolidada
(`Práticas_corporais_Atividade_Física_SISAB_atualizado.xlsx`, aba `sisab`)
e sobe a planilha no eCIEGES (formulário **SISAB**). Envia e-mail de status
ao final. Espelha o robô e-Gestor APS.

## O que ele faz

1. Localiza o CSV mais recente em `PASTA_CSV_SISAB` (ex.: `RelAtvColetivaMB ABR26.csv`).
2. Lê as colunas Uf→Num. Participantes a partir da linha de dados (após o cabeçalho),
   descartando cabeçalho institucional e rodapé.
3. Deriva a **competência** do nome do arquivo (`ABR26` → `01/04/2026`) e a grava na
   coluna A da planilha; os dados do CSV vão para as colunas B–I.
4. **Antiduplicidade**: se a competência já existe na aba `sisab`, não insere nada.
5. Faz append na primeira linha vazia, preservando as demais abas.
6. Sobe a planilha no eCIEGES (formulário SISAB → Importar Arquivo → aba `sisab` → Importar Essa Aba).
7. Envia e-mail de status (sucesso / sem novidades / erro).

## Setup

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

Copie `.env.example` para `.env` e preencha os valores.

Para o e-mail, reaproveite os arquivos `credentials.json` e `token.json` do
robô e-Gestor (aponte os caminhos em `GMAIL_CREDENTIALS` / `GMAIL_TOKEN` no `.env`).

## Uso

```bat
REM Fluxo completo (planilha + eCIEGES + e-mail)
python -m src.main

REM Só a parte da planilha (pula eCIEGES) — bom pra testar
python -m src.main --so-planilha
```

Primeira validação do eCIEGES: rode com `HEADLESS=false` no `.env` para
acompanhar visualmente e ajustar seletores se necessário.

## Agendador de Tarefas do Windows

1. Ajuste o caminho `PROJ` dentro de `executar_robo.bat`.
2. Abra o **Agendador de Tarefas** → **Criar Tarefa** (não "Tarefa Básica").
3. **Geral**: nome "Robô SISAB"; marque "Executar estando o usuário conectado ou não"
   e "Executar com privilégios mais altos".
4. **Disparadores**: novo disparador, ex. mensal no dia desejado, horário definido.
5. **Ações**: nova ação → "Iniciar um programa" → Programa: o caminho completo do
   `executar_robo.bat`. Em "Iniciar em", coloque a pasta do projeto.
6. **Condições/Configurações**: permita reexecução em caso de falha se quiser.

A antiduplicidade garante que rodar mais de uma vez no mesmo mês não duplica dados.

## Estrutura

```
robo-sisab-aps/
├─ src/
│  ├─ config.py          # configuração via .env
│  ├─ logger.py          # logging arquivo + console
│  ├─ csv_reader.py      # descoberta e leitura do CSV
│  ├─ planilha.py        # append + antiduplicidade na planilha consolidada
│  ├─ ecieges.py         # upload no eCIEGES (Playwright)
│  ├─ email_status.py    # e-mail de status (Gmail API)
│  └─ main.py            # orquestrador
├─ executar_robo.bat
├─ requirements.txt
├─ .env.example
└─ .gitignore
```

## Roadmap

- Baixar o CSV direto do site do SISAB com login (Playwright), salvar na pasta
  correta e então rodar todo o fluxo atual — eliminando o passo manual de download.
