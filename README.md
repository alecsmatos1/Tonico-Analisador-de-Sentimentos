# Tonico - Analisador de Sentimentos

Demo interativa em Streamlit para feira de extensao.

O Tonico classifica frases em:

- positivo;
- neutro;
- negativo.

A aplicacao usa:

- analisador simbolico local;
- comparacao opcional com TF-IDF + modelo linear salvo em `models/feira/tfidf_pipeline.pkl`;
- assets locais em `assets/images/`;
- filtro simples para termos inadequados no contexto da feira.

Este repositorio e uma versao enxuta de deploy. Ele nao inclui o pipeline de treino, datasets ou relatorios academicos do projeto original.

## Rodar localmente

```powershell
pip install -r requirements.txt
streamlit run app_feira.py
```

Depois acesse:

```text
http://localhost:8501
```

## Deploy no Streamlit Community Cloud

Configurar:

- repository: `alecsmatos1/Tonico-Analisador-de-Sentimentos`
- branch: `main`
- main file path: `app_feira.py`

## Privacidade

As frases digitadas nao sao salvas por padrao.

## O que nao esta neste repositorio

- datasets brutos;
- arquivos `.env`;
- chaves de API;
- caches;
- modelos grandes;
- saidas de experimentos.
