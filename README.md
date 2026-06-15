# Tonico - Analisador de Sentimentos

Demo interativa em Streamlit para feira de extensão.

O Tonico classifica frases em:

- positivo;
- neutro;
- negativo.

A aplicação usa:

- analisador simbólico local;
- comparação opcional com TF-IDF + modelo linear salvo em `models/feira/tfidf_pipeline.pkl`;
- assets locais em `assets/images/`;
- filtro simples para termos inadequados no contexto da feira.

Este repositório é uma versão enxuta de deploy. Ele não inclui o pipeline de treino, datasets ou relatórios acadêmicos do projeto original.

## Rodar localmente

```powershell
pip install -r requirements.txt
streamlit run app_feira.py
```

Depois acesse:

```text
http://localhost:8501
```

## Modo da interface

Por padrão, o app abre em modo público, sem o painel do apresentador:

```powershell
streamlit run app_feira.py
```

Para usar localmente na feira com o painel do apresentador, defina a variável `TONICO_APP_MODE` antes de iniciar:

```powershell
$env:TONICO_APP_MODE="feira"
streamlit run app_feira.py
```

Valores aceitos para ativar o painel: `feira`, `presenter` ou `apresentador`.

## Deploy no Streamlit Community Cloud

Configurar:

- repository: `alecsmatos1/Tonico-Analisador-de-Sentimentos`
- branch: `main`
- main file path: `app_feira.py`

## Privacidade

As frases digitadas não são salvas por padrão.

## O que não está neste repositório

- datasets brutos;
- arquivos `.env`;
- chaves de API;
- caches;
- modelos grandes;
- saídas de experimentos.
