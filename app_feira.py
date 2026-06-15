"""app_feira.py — Demo interativa do Tonico para a Feira de Extensão."""
from __future__ import annotations

import html as _html
import os
import random
import re
from pathlib import Path

import streamlit as st

from sentiment_analyzer import analyze_symbolic_sentiment

APP_MODE = os.getenv("TONICO_APP_MODE", "publico").strip().lower()
SHOW_PRESENTER_PANEL = APP_MODE in {"feira", "presenter", "apresentador"}

# ── configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Tonico — Analisador de Sentimentos",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded" if SHOW_PRESENTER_PANEL else "collapsed",
)

# ── constantes ──────────────────────────────────────────────────────────────
ASSETS = Path(__file__).parent / "assets"

BLOCKED_TERMS: set[str] = {
    "merda", "puta", "porra", "fodase", "foda-se", "caralho",
    "viado", "vadia", "vagabunda", "vagabundo", "idiota", "imbecil",
    "corno", "cretino", "bastardo", "filhodaputa", "desgraca", "desgraça",
}

EXAMPLES: dict[str, list[str]] = {
    "Simples": [
        "Eu adorei esse produto!",
        "O atendimento foi muito bom.",
        "Achei muito ruim.",
        "O produto chegou no prazo.",
    ],
    "Com negação": [
        "Não gostei do filme.",
        "Não foi ruim.",
        "Nunca vi atendimento tão bom.",
    ],
    "Com contraste": [
        "O começo foi legal, mas o final foi péssimo.",
        "A entrega atrasou, mas o produto é excelente.",
        "O produto é bonito, só que não funciona.",
    ],
    "Casos difíceis": [
        "Nossa, que ótimo, meu celular quebrou de novo.",
        "Amei esperar duas horas na fila.",
        "Adorei ter que devolver o produto três vezes.",
        "Que serviço incrível, só chegou errado.",
        "Perfeito! Já é a terceira vez que o produto chega com defeito.",
    ],
}

CHALLENGES: list[str] = [
    "Escreva uma frase positiva usando a palavra 'ruim'.",
    "Use 'não' para transformar um elogio em crítica.",
    "Escreva uma frase irônica: diga algo bom de um jeito que significa o contrário.",
    "Use um emoji que contradiz o que você escreveu. Ex: 'O produto quebrou em 2 dias 😍'",
    "Comece sua frase de forma positiva e termine de forma negativa.",
    "Use 'mas' para virar o sentido no meio da frase.",
    "Elogie e critique ao mesmo tempo na mesma frase.",
]

SENTIMENT_COLORS: dict[str, str] = {
    "positivo": "#27ae60",
    "negativo": "#e74c3c",
    "neutro": "#e67e22",
}

SENTIMENT_LABELS: dict[str, str] = {
    "positivo": "POSITIVO 😄",
    "negativo": "NEGATIVO 😟",
    "neutro": "NEUTRO 😐",
}

SENTIMENT_EMOJIS: dict[str, str] = {
    "positivo": "😄",
    "negativo": "😟",
    "neutro": "😐",
}

SENTIMENT_ADJECTIVES: dict[str, str] = {
    "positivo": "positiva",
    "negativo": "negativa",
    "neutro": "neutra",
}

# ── tokens de categorias linguísticas ────────────────────────────────────────

_NEGACAO_WORDS: frozenset[str] = frozenset({"não", "nao", "nem", "nunca", "jamais", "tampouco"})
_CONTRASTE_WORDS: frozenset[str] = frozenset({"mas", "porém", "porem", "contudo", "entretanto", "todavia"})
_INTENSIF_WORDS: frozenset[str] = frozenset({"muito", "demais", "super", "bastante", "extremamente", "incrivelmente"})


# ── funcoes auxiliares ──────────────────────────────────────────────────────

def moderate_text(text: str) -> tuple[bool, str]:
    """Verifica se o texto pode ser analisado na feira.

    Returns:
        (pode_analisar, mensagem_de_bloqueio)
    """
    if len(text.strip()) < 3:
        return False, "Escreva uma frase um pouco maior para o Tonico analisar."
    normalized = text.lower()
    for term in BLOCKED_TERMS:
        if re.search(r"\b" + re.escape(term) + r"\b", normalized):
            return (
                False,
                "Essa frase tem termos que o Tonico prefere não analisar na feira. "
                "Tente outra frase.",
            )
    return True, ""


def run_tonico_analysis(text: str) -> dict:
    """Chama o analisador simbólico e retorna o resultado para a UI."""
    return analyze_symbolic_sentiment(text)


def sentiment_asset(label: str) -> Path:
    """Retorna caminho local da imagem de sentimento por classe."""
    mapping: dict[str, Path] = {
        "positivo": ASSETS / "images" / "emoji-feliz.png",
        "negativo": ASSETS / "images" / "emoji-triste.png",
        "neutro":   ASSETS / "images" / "emoji-apatico.png",
    }
    return mapping.get(label, ASSETS / "images" / "emoji-apatico.png")


def build_short_explanation(result: dict) -> str:
    """Explicação curta com pistas encontradas (para crianças)."""
    hits = result.get("rule_hits", [])
    pos = [h["excerpt"] for h in hits if h.get("polarity") == "positivo"]
    neg = [h["excerpt"] for h in hits if h.get("polarity") == "negativo"]

    parts: list[str] = []
    if pos:
        parts.append(f"Pistas positivas: **{', '.join(pos[:3])}**")
    if neg:
        parts.append(f"Pistas negativas: **{', '.join(neg[:3])}**")

    if not parts:
        return "O Tonico não encontrou pistas claras. Provavelmente é um caso difícil!"
    return " | ".join(parts)


def build_detailed_explanation(result: dict) -> str:
    """Explicação técnica detalhada (para adolescentes e professores)."""
    hits = result.get("rule_hits", [])
    lines: list[str] = []
    for h in hits:
        pol = h.get("polarity", "")
        icon = "✅" if pol == "positivo" else ("❌" if pol == "negativo" else "➡️")
        lines.append(
            f"{icon} `{h['excerpt']}` — {h.get('reason', h.get('rule', ''))} "
            f"(peso {h.get('weight', 0):.1f})"
        )

    score = result.get("score", 0)
    pos_s = result.get("positive_score", 0)
    neg_s = result.get("negative_score", 0)
    lines.append(f"\nEscore final: **{score:+.2f}** (positivo: {pos_s:.2f} | negativo: {neg_s:.2f})")
    return "\n".join(lines) if lines else "Sem pistas detectadas."


def has_mixed_evidence(result: dict) -> bool:
    """Retorna True quando há pistas positivas e negativas simultâneas."""
    return result.get("positive_score", 0) > 0.5 and result.get("negative_score", 0) > 0.5


def pick_random_challenge() -> str:
    """Seleciona um desafio aleatório da lista."""
    return random.choice(CHALLENGES)


def avaliar_placar_desafio(result: dict) -> bool:
    """Retorna True se o usuário conseguiu confundir o Tonico."""
    return result.get("confidence", 1.0) < 0.5 or has_mixed_evidence(result)


def compare_phrases(text_a: str, text_b: str) -> tuple[dict, dict]:
    """Analisa duas frases e retorna (result_a, result_b)."""
    return run_tonico_analysis(text_a), run_tonico_analysis(text_b)


def _tokens(text: str) -> set[str]:
    """Divide texto em tokens minúsculos para checagem de palavras-chave."""
    return set(re.split(r"\W+", text.lower()))


def categorize_hits(result: dict) -> dict[str, list[str]]:
    """Categoriza rule_hits por tipo: pos, neg, negação, contraste, emoji, intensif.

    Cada hit pode cair em apenas uma categoria (prioridade: emoji > negação >
    contraste > intensif > pos/neg por polarity).

    Returns:
        Dict com chaves 'pos', 'neg', 'negacao', 'contraste', 'emoji', 'intensif',
        cada uma contendo lista de excerpts correspondentes.
    """
    hits = result.get("rule_hits", [])
    categories: dict[str, list[str]] = {
        "pos": [],
        "neg": [],
        "negacao": [],
        "contraste": [],
        "emoji": [],
        "intensif": [],
    }

    for h in hits:
        rule = h.get("rule", "").lower()
        excerpt = h.get("excerpt", "")
        polarity = h.get("polarity", "")
        tokens = _tokens(excerpt)

        if "emoji" in rule:
            categories["emoji"].append(excerpt)
        elif "negacao" in rule or bool(tokens & _NEGACAO_WORDS):
            categories["negacao"].append(excerpt)
        elif "contraste" in rule or bool(tokens & _CONTRASTE_WORDS):
            categories["contraste"].append(excerpt)
        elif "intensif" in rule or bool(tokens & _INTENSIF_WORDS):
            categories["intensif"].append(excerpt)
        elif polarity == "positivo":
            categories["pos"].append(excerpt)
        elif polarity == "negativo":
            categories["neg"].append(excerpt)

    return categories


def build_explanation_cards(result: dict) -> list[str]:
    """Retorna lista de cartões explicativos baseados nas pistas encontradas.

    Cada cartão é uma string com uma dica educativa sobre o fenômeno linguístico
    detectado no texto analisado.
    """
    hits = result.get("rule_hits", [])
    confidence = result.get("confidence", 1.0)
    cards: list[str] = []

    # verifica negação
    negacao_detectada = any(
        "negacao" in h.get("rule", "").lower()
        or bool(_tokens(h.get("excerpt", "")) & _NEGACAO_WORDS)
        for h in hits
    )
    if negacao_detectada:
        cards.append("A palavra 'não' pode inverter o sentido de uma frase.")

    # verifica contraste
    contraste_detectado = any(
        "contraste" in h.get("rule", "").lower()
        or bool(_tokens(h.get("excerpt", "")) & _CONTRASTE_WORDS)
        for h in hits
    )
    if contraste_detectado:
        cards.append("A palavra 'mas' costuma mudar o foco para a segunda parte da frase.")

    # verifica emoji
    emoji_detectado = any("emoji" in h.get("rule", "").lower() for h in hits)
    if emoji_detectado:
        cards.append("Emojis podem reforçar ou contradizer o texto.")

    # confiança baixa (ironia)
    if confidence < 0.5:
        cards.append("Ironia depende de contexto que nem sempre está escrito.")

    return cards



# ── modelo aprendiz (TF-IDF) ─────────────────────────────────────────────────

_TFIDF_MODEL_PATH = Path(__file__).parent / "models" / "feira" / "tfidf_pipeline.pkl"


@st.cache_resource
def _load_tfidf_pipeline():
    """Carrega o pipeline TF-IDF serializado, ou retorna None se ausente."""
    try:
        import joblib
        if _TFIDF_MODEL_PATH.exists():
            return joblib.load(_TFIDF_MODEL_PATH)
        return None
    except Exception:
        return None


def _normalize_for_tfidf(text: str) -> str:
    """Aplica a mesma normalizacao usada no treino do TF-IDF."""
    import re as _re
    import unicodedata as _unicodedata
    text = _unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if _unicodedata.category(c) != "Mn")
    text = _re.sub(r"[^a-z0-9\s]", " ", text)
    text = _re.sub(r"\s+", " ", text).strip()
    return text


def run_aprendiz_analysis(text: str) -> dict | None:
    """Classifica o texto com o pipeline TF-IDF. Retorna None se modelo ausente."""
    pipeline = _load_tfidf_pipeline()
    if pipeline is None:
        return None
    try:
        normalized = _normalize_for_tfidf(text)
        label = pipeline.predict([normalized])[0]
        proba = pipeline.predict_proba([normalized])[0]
        classes = list(pipeline.classes_)
        score = float(proba[classes.index(label)]) if label in classes else 0.5
        return {"label": label, "confidence": score}
    except Exception:
        return None


# ── estado de sessão ────────────────────────────────────────────────────────

def _init_session() -> None:
    defaults = {
        "history": [],
        "phrase_count": 0,
        "show_details": False,
        "challenge_text": "",
        "disclaimer_shown": False,
        "last_result": None,
        "last_input": "",
        "input_livre": "",
        "input_desafio": "",
        "desafio_tentativas": 0,
        "desafio_confusoes": 0,
        "sentiment_counts": {"positivo": 0, "negativo": 0, "neutro": 0},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ── componentes de interface ─────────────────────────────────────────────────

def _render_result_block(result: dict) -> None:
    label = result.get("label", "neutro")
    color = SENTIMENT_COLORS.get(label, "#888888")
    label_str = SENTIMENT_LABELS.get(label, label.upper())

    if has_mixed_evidence(result):
        st.warning(
            "⚠️ Essa frase tem pistas misturadas. O Tonico escolheu uma classe, "
            "mas encontrou sinais positivos e negativos."
        )

    col_img, col_txt = st.columns([1, 4])
    with col_img:
        img = sentiment_asset(label)
        if img.exists():
            st.image(str(img), width=110)
    with col_txt:
        st.markdown(
            f"""<div style="
                background:{color}18;
                border-left:6px solid {color};
                padding:18px 20px;
                border-radius:10px;
                margin-top:4px;">
                <h2 style="color:{color};margin:0;font-size:2rem;">{label_str}</h2>
                <p style="font-size:1.15rem;margin:6px 0 0 0;">
                Essa frase é
                <b style="color:{color};">{SENTIMENT_ADJECTIVES.get(label, label)}</b>.</p>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown(" ")
    st.markdown(f"🔍 {build_short_explanation(result)}")

    if result.get("confidence", 1.0) < 0.4:
        st.info(
            "🤔 Boa! Você encontrou um caso difícil. "
            "Frases com ironia ou contexto escondido podem confundir analisadores de sentimento. "
            "Isso faz parte do aprendizado!"
        )

    if st.session_state.show_details:
        with st.expander("🔬 Como o Tonico pensou (detalhes técnicos)", expanded=True):
            st.markdown(build_detailed_explanation(result))
            st.caption(
                "💡 A palavra **'mas'** costuma mudar o foco para a segunda parte da frase. "
                "**'Não'** pode inverter o sentido. "
                "**Ironia** depende de contexto que nem sempre está escrito."
            )


def _render_clue_blocks(result: dict) -> None:
    """Renderiza blocos visuais de pistas categorizadas com etapas didáticas."""
    cats = categorize_hits(result)
    cards = build_explanation_cards(result)

    st.markdown("#### 🗂️ Pistas que o Tonico encontrou")

    # etapas didaticas em 3 passos
    st.markdown(
        """
        <div style="
            background:#f0f4ff;
            border-radius:10px;
            padding:14px 20px;
            margin-bottom:14px;
            font-size:0.97rem;
            color:#111111;
        ">
        <b>📖 Passo 1 — Tonico leu as palavras</b><br>
        O Tonico varreu cada palavra e trecho da sua frase procurando pistas de sentimento.<br><br>
        <b>🔍 Passo 2 — Tonico identificou as pistas</b><br>
        Cada pista recebe um peso: palavras positivas somam pontos, negativas subtraem.<br><br>
        <b>🎯 Passo 3 — Tonico decidiu o sentimento</b><br>
        O placar final determina se a frase é positiva, negativa ou neutra.
        </div>
        """,
        unsafe_allow_html=True,
    )

    def _badge(items: list[str], color: str, icon: str, label: str) -> None:
        if not items:
            return
        shown = items[:3]
        extra = len(items) - len(shown)
        safe_items = " &nbsp;·&nbsp; ".join(
            f"<code>{_html.escape(x)}</code>" for x in shown
        )
        if extra:
            safe_items += f" &nbsp;<span style='color:#666;font-size:0.85em;'>+{extra}</span>"
        st.markdown(
            f"<div style='border-left:4px solid {color};padding:8px 14px;"
            f"margin:6px 0;border-radius:6px;background:{color}22;color:#111111;'>"
            f"<b style='color:{color};'>{icon} {_html.escape(label)}</b>"
            f"<br><span style='color:#111111;'>{safe_items}</span></div>",
            unsafe_allow_html=True,
        )

    _badge(cats["pos"],      "#27ae60", "✅", "Pistas positivas")
    _badge(cats["neg"],      "#e74c3c", "❌", "Pistas negativas")
    _badge(cats["negacao"],  "#8e44ad", "🚫", "Negações")
    _badge(cats["contraste"],"#2980b9", "↔️", "Contrastes")
    _badge(cats["emoji"],    "#f39c12", "😀", "Emojis")
    _badge(cats["intensif"], "#16a085", "🔊", "Intensificadores")

    # cartões didáticos
    if cards:
        st.markdown("#### 💡 Sabia disso?")
        for card in cards:
            st.info(f"💬 {card}")


def _render_history() -> None:
    if not st.session_state.history:
        return
    st.markdown("---")
    st.markdown("### 📜 Últimas análises")
    for item in reversed(st.session_state.history[-5:]):
        lbl = item.get("label", "neutro")
        color = SENTIMENT_COLORS.get(lbl, "#888888")
        emoji = SENTIMENT_EMOJIS.get(lbl, "")
        raw = item.get("text", "")
        trunc = _html.escape(raw[:80] + ("…" if len(raw) > 80 else ""))
        label_display = _html.escape(f"{emoji} {lbl.upper()}")
        st.markdown(
            f"<div style='border-left:4px solid {color};padding:6px 12px;"
            f"margin:4px 0;border-radius:4px;background:{color}0d;'>"
            f"<span style='color:{color};font-weight:bold;'>{label_display}</span>"
            f" — <i>{trunc}</i></div>",
            unsafe_allow_html=True,
        )


def _render_sidebar() -> None:
    with st.sidebar:
        robo = ASSETS / "images" / "robo-feliz-face.png"
        if robo.exists():
            st.image(str(robo), width=100)

        st.markdown("## 🎛️ Painel do Apresentador")
        st.markdown(f"**Frases analisadas nessa sessão:** {st.session_state.phrase_count}")
        counts = st.session_state.sentiment_counts
        total = sum(counts.values())
        if total > 0:
            pos_pct = counts["positivo"] * 100 // total
            neg_pct = counts["negativo"] * 100 // total
            neu_pct = 100 - pos_pct - neg_pct
            st.caption(f"😄 {pos_pct}% positivo | 😟 {neg_pct}% negativo | 😐 {neu_pct}% neutro")

        if st.button("🗑️ Limpar histórico", use_container_width=True):
            st.session_state.history = []
            st.rerun()

        if st.button("🔄 Resetar demonstração", use_container_width=True):
            st.session_state.history = []
            st.session_state.phrase_count = 0
            st.session_state.challenge_text = ""
            st.session_state.last_result = None
            st.session_state.last_input = ""
            st.session_state.desafio_tentativas = 0
            st.session_state.desafio_confusoes = 0
            st.session_state.sentiment_counts = {"positivo": 0, "negativo": 0, "neutro": 0}
            st.rerun()

        detail_lbl = (
            "🔎 Ocultar detalhes técnicos"
            if st.session_state.show_details
            else "🔎 Mostrar detalhes técnicos"
        )
        if st.button(detail_lbl, use_container_width=True):
            st.session_state.show_details = not st.session_state.show_details
            st.rerun()

        st.markdown("---")
        st.markdown("### 📋 Exemplos prontos")
        for group, phrases in EXAMPLES.items():
            st.markdown(f"**{group}**")
            for phrase in phrases:
                short = phrase[:38] + "…" if len(phrase) > 38 else phrase
                if st.button(f"↩ {short}", key=f"ex_{phrase[:30]}", use_container_width=True):
                    st.session_state["input_livre"] = phrase
                    st.rerun()


def _run_analysis_and_store(user_input: str) -> dict | None:
    """Executa moderação + análise, atualiza histórico e retorna resultado (ou None)."""
    ok, msg = moderate_text(user_input)
    if not ok:
        st.warning(f"🚫 {msg}")
        st.session_state["input_livre"] = ""
        st.session_state["input_desafio"] = ""
        return None
    try:
        result = run_tonico_analysis(user_input)
    except Exception:
        st.info(
            "🤔 O Tonico ficou confuso com essa frase. "
            "Tente uma frase diferente!"
        )
        return None

    st.session_state.phrase_count += 1
    label = result.get("label", "neutro")
    st.session_state.history.append({"text": user_input, "label": label})
    if label in st.session_state.sentiment_counts:
        st.session_state.sentiment_counts[label] += 1
    st.session_state.last_result = result
    st.session_state.last_input = user_input
    return result


# ── app principal ────────────────────────────────────────────────────────────

def main() -> None:
    _init_session()
    if SHOW_PRESENTER_PANEL:
        _render_sidebar()

    col_logo, col_titulo = st.columns([1, 5])
    with col_logo:
        robo_header = ASSETS / "images" / "robo-inteligente-face.png"
        if robo_header.exists():
            st.image(str(robo_header), width=110)
    with col_titulo:
        st.markdown("# 🤖 Tonico — Analisador de Sentimentos")

    st.markdown(
        "O **Tonico** lê o que você escreve, identifica pistas de significado "
        "e decifra se o sentimento é **positivo**, **neutro** ou **negativo**."
    )

    # aviso discreto — exibido uma vez por sessão
    if not st.session_state.disclaimer_shown:
        st.caption(
            "⚠️ Este sistema aprende por regras e pode errar "
            "— especialmente com ironia e contexto escondido."
        )
        st.session_state.disclaimer_shown = True

    st.markdown("---")

    # ── tres modos de experiencia ─────────────────────────────────────────────
    tab_livre, tab_pensa, tab_desafio = st.tabs([
        "✍️ Teste livre",
        "🧠 Como o Tonico pensou",
        "🎯 Desafio: Enganar o Tonico",
    ])

    # ── TAB 1: Teste livre ────────────────────────────────────────────────────
    with tab_livre:
        st.markdown("### ✍️ Escreva uma frase")
        user_input = st.text_area(
            label="frase",
            height=110,
            max_chars=500,
            label_visibility="collapsed",
            placeholder="Ex: Adorei o produto, chegou rápido e funciona perfeitamente!",
            key="input_livre",
        )
        analyze_btn = st.button(
            "🔍 Analisar com o Tonico",
            type="primary",
            use_container_width=True,
            key="btn_livre",
        )

        if analyze_btn:
            if not user_input.strip():
                st.warning("Escreva alguma coisa para o Tonico analisar.")
            else:
                result = _run_analysis_and_store(user_input)
                if result is not None:
                    st.markdown("---")
                    st.markdown("### 🧠 O que o Tonico descobriu")
                    _render_result_block(result)

                    if not st.session_state.show_details:
                        st.caption(
                            "💡 Abra a aba **Como o Tonico pensou** para ver "
                            "as pistas usadas na análise."
                        )

        _render_history()

    # ── TAB 2: Como o Tonico pensou ───────────────────────────────────────────
    with tab_pensa:
        st.markdown("### 🧠 Como o Tonico pensou")
        st.markdown(
            "Analise uma frase e veja as **pistas** que o Tonico usou para "
            "chegar ao resultado — separadas por tipo."
        )

        user_input_pensa = st.text_area(
            label="frase_pensa",
            height=100,
            max_chars=500,
            label_visibility="collapsed",
            placeholder="Ex: Adorei a entrega, mas o produto chegou quebrado.",
            key="input_pensa",
        )
        btn_pensa = st.button(
            "🔍 Analisar e ver as pistas",
            type="primary",
            use_container_width=True,
            key="btn_pensa",
        )

        if btn_pensa:
            if not user_input_pensa.strip():
                st.warning("Escreva alguma coisa para o Tonico analisar.")
            else:
                result = _run_analysis_and_store(user_input_pensa)
                if result is not None:
                    st.markdown("---")
                    _render_result_block(result)
                    st.markdown("---")
                    _render_clue_blocks(result)

        # ── Modelo Aprendiz: comparacao opcional ─────────────────────────────
        with st.expander("🤖 O que o Modelo Aprendiz acha?", expanded=False):
            last = st.session_state.get("last_result")
            if last is None:
                st.info("Analise uma frase primeiro.")
            elif _load_tfidf_pipeline() is None:
                st.info(
                    "Modelo Aprendiz não carregado. "
                    "O arquivo `models/feira/tfidf_pipeline.pkl` precisa estar disponível."
                )
            else:
                aprendiz = run_aprendiz_analysis(
                    st.session_state.get("last_input", "")
                )
                if aprendiz is None:
                    st.info(
                        "Modelo Aprendiz não carregado. "
                        "O arquivo `models/feira/tfidf_pipeline.pkl` precisa estar disponível."
                    )
                else:
                    tonico_label = last.get("label", "neutro")
                    aprendiz_label = aprendiz.get("label", "neutro")

                    col_tonico, col_aprendiz = st.columns([1, 1])
                    with col_tonico:
                        color_t = SENTIMENT_COLORS.get(tonico_label, "#888888")
                        label_t = SENTIMENT_LABELS.get(tonico_label, tonico_label.upper())
                        st.markdown("**🧠 Tonico (regras escritas)**")
                        st.markdown(
                            f"<div style='border-left:5px solid {color_t};"
                            f"padding:10px 14px;border-radius:8px;"
                            f"background:{color_t}18;margin:6px 0;'>"
                            f"<b style='color:{color_t};font-size:1.1rem;'>{label_t}</b>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                        st.caption("Segue regras escritas por humanos.")
                    with col_aprendiz:
                        color_a = SENTIMENT_COLORS.get(aprendiz_label, "#888888")
                        label_a = SENTIMENT_LABELS.get(aprendiz_label, aprendiz_label.upper())
                        st.markdown("**📚 Modelo Aprendiz (aprendeu com dados)**")
                        st.markdown(
                            f"<div style='border-left:5px solid {color_a};"
                            f"padding:10px 14px;border-radius:8px;"
                            f"background:{color_a}18;margin:6px 0;'>"
                            f"<b style='color:{color_a};font-size:1.1rem;'>{label_a}</b>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                        st.caption("Aprendeu com milhares de avaliações reais.")

                    if tonico_label == aprendiz_label:
                        st.success("Os dois chegaram ao mesmo resultado! ✅")
                    else:
                        st.warning("Interessante! Por que será que eles discordam? 🤔")
                        st.caption(
                            "O Tonico usa regras escritas à mão. O Modelo Aprendiz "
                            "aprendeu com dados — e cada um pode ter pontos cegos diferentes."
                        )

        # ── Comparador de frases ──────────────────────────────────────────────
        with st.expander("🔄 Compare duas frases"):
            st.markdown("### 🔄 Compare duas frases")
            col_a, col_b = st.columns([1, 1])
            with col_a:
                text_cmp_a = st.text_area(
                    "Frase A",
                    height=90,
                    max_chars=500,
                    placeholder="Adorei o produto!",
                    key="cmp_a",
                )
            with col_b:
                text_cmp_b = st.text_area(
                    "Frase B",
                    height=90,
                    max_chars=500,
                    placeholder="Não adorei o produto.",
                    key="cmp_b",
                )
            btn_comparar = st.button("Comparar", key="btn_comparar", type="primary")
            if btn_comparar:
                if not text_cmp_a.strip() or not text_cmp_b.strip():
                    st.warning("Preencha as duas frases para comparar.")
                else:
                    ok_a, msg_a = moderate_text(text_cmp_a)
                    ok_b, msg_b = moderate_text(text_cmp_b)
                    if not ok_a:
                        st.warning(f"Frase A: {msg_a}")
                    elif not ok_b:
                        st.warning(f"Frase B: {msg_b}")
                    else:
                        result_a, result_b = compare_phrases(text_cmp_a, text_cmp_b)
                        res_col_a, res_col_b = st.columns([1, 1])
                        with res_col_a:
                            lbl_a = result_a.get("label", "neutro")
                            color_a = SENTIMENT_COLORS.get(lbl_a, "#888888")
                            score_a = result_a.get("score", 0.0)
                            st.markdown(
                                f"<div style='border-left:5px solid {color_a};"
                                f"padding:10px 14px;border-radius:8px;background:{color_a}18;'>"
                                f"<b style='color:{color_a};font-size:1.1rem;'>"
                                f"{SENTIMENT_EMOJIS.get(lbl_a, '')} {lbl_a.upper()}</b>"
                                f"<br>Escore: {score_a:+.2f}</div>",
                                unsafe_allow_html=True,
                            )
                        with res_col_b:
                            lbl_b = result_b.get("label", "neutro")
                            color_b = SENTIMENT_COLORS.get(lbl_b, "#888888")
                            score_b = result_b.get("score", 0.0)
                            st.markdown(
                                f"<div style='border-left:5px solid {color_b};"
                                f"padding:10px 14px;border-radius:8px;background:{color_b}18;'>"
                                f"<b style='color:{color_b};font-size:1.1rem;'>"
                                f"{SENTIMENT_EMOJIS.get(lbl_b, '')} {lbl_b.upper()}</b>"
                                f"<br>Escore: {score_b:+.2f}</div>",
                                unsafe_allow_html=True,
                            )
                        diff = abs(result_a.get("score", 0) - result_b.get("score", 0))
                        st.metric("Diferença de escore", f"{diff:.2f}")

    # ── TAB 3: Desafio ────────────────────────────────────────────────────────
    with tab_desafio:
        st.markdown("### 🎯 Desafio: Enganar o Tonico")
        st.markdown(
            "Use ironia, negação ou contraste para ver se o Tonico se confunde. "
            "Quando ele errar, você ganhou!"
        )

        col_desafio_btn, col_desafio_info = st.columns([1, 2])
        with col_desafio_btn:
            if st.button("🎲 Surpreenda o Tonico", use_container_width=True, key="btn_surpresa"):
                import random as _random
                st.session_state["input_desafio"] = _random.choice(EXAMPLES["Casos difíceis"])
                st.session_state.challenge_text = "Será que o Tonico consegue detectar a ironia?"
                st.rerun()
            if st.button("🗑️ Limpar desafio", use_container_width=True, key="btn_limpar_desafio"):
                st.session_state["input_desafio"] = ""
                st.session_state.challenge_text = ""

        with col_desafio_info:
            if st.session_state.challenge_text:
                st.info(f"💡 **Desafio:** {st.session_state.challenge_text}")

        with st.expander("📋 Frases prontas para desafiar o Tonico", expanded=False):
            for i, phrase in enumerate(EXAMPLES["Casos difíceis"]):
                if st.button(
                    f"↗ {phrase}",
                    key=f"desafio_phrase_{i}",
                    use_container_width=True,
                ):
                    st.session_state["input_desafio"] = phrase
                    st.rerun()

        user_input_desafio = st.text_area(
            label="frase_desafio",
            height=100,
            max_chars=500,
            label_visibility="collapsed",
            placeholder="Tente enganar o Tonico aqui! Ex: Amei esperar duas horas na fila.",
            key="input_desafio",
        )
        btn_desafio = st.button(
            "🔍 Analisar — Consegui enganar o Tonico?",
            type="primary",
            use_container_width=True,
            key="btn_desafio",
        )

        if btn_desafio:
            if not user_input_desafio.strip():
                st.warning("Escreva alguma coisa para tentar enganar o Tonico.")
            else:
                result = _run_analysis_and_store(user_input_desafio)
                if result is not None:
                    st.session_state.desafio_tentativas += 1
                    if avaliar_placar_desafio(result):
                        st.session_state.desafio_confusoes += 1

                    st.markdown("---")
                    _render_result_block(result)
                    st.markdown("---")

                    # placar do desafio
                    tentativas = st.session_state.desafio_tentativas
                    confusoes = st.session_state.desafio_confusoes
                    st.markdown(
                        f"🏆 **Placar:** Você confundiu o Tonico {confusoes} de {tentativas} tentativas"
                    )

                    confidence = result.get("confidence", 1.0)
                    if confidence < 0.4:
                        st.success(
                            "🎉 **Você conseguiu!** O Tonico ficou confuso com essa frase. "
                            "Boa! Você encontrou um caso difícil. "
                            "Frases com ironia ou contexto escondido podem confundir "
                            "analisadores de sentimento. Isso faz parte do aprendizado!"
                        )
                    elif has_mixed_evidence(result):
                        st.warning(
                            "⚠️ **Quase!** O Tonico detectou sinais misturados. "
                            "Tente uma frase com ironia ainda mais explicita!"
                        )
                    else:
                        st.info(
                            "🤖 **O Tonico acertou desta vez!** Tente usar ironia mais sutil, "
                            "negação dupla ou um emoji que contradiz o texto."
                        )

                    _render_clue_blocks(result)

    st.markdown("---")
    st.caption("🔒 As frases digitadas **não são salvas**. Esta é uma demonstração educativa.")
    st.caption("USP — Processamento de Linguagem Natural | Feira de Extensão")


if __name__ == "__main__":
    main()
