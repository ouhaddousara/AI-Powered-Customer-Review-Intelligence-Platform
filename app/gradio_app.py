"""
Layer 7 — Gradio interface for the RAG Q&A system.

Sources are rendered as styled HTML cards (not plain text) — each
shows the product ID, star rating, and the original review text,
so the citation is immediately scannable rather than a wall of text.
"""

import os

import gradio as gr
import markdown as md
from dotenv import load_dotenv

from src.rag.qa import answer_question

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

CUSTOM_CSS = """
@property --beam-angle {
    syntax: '<angle>';
    initial-value: 0deg;
    inherits: false;
}

.header-section {
    text-align: center;
    padding: 36px 0 24px 0;
}
.header-badge {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    border: 1px solid #2d3648;
    border-radius: 999px;
    padding: 6px 16px;
    background: #161c27;
    color: #c4c9d4;
    font-size: 0.85em;
    margin-bottom: 18px;
}
.badge-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #f0b429;
    position: relative;
}
.badge-dot::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background: #f0b429;
    animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;
}
@keyframes ping {
    75%, 100% { transform: scale(2.4); opacity: 0; }
}
.header-title {
    font-size: 2.3em;
    font-weight: 700;
    margin-bottom: 10px;
    background: linear-gradient(90deg, #f0b429, #ff7a45);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: inline-block;
}
.header-subtitle {
    color: #8b93a3;
    font-size: 1.05em;
    max-width: 620px;
    margin: 0 auto;
    line-height: 1.5;
}

.search-row {
    max-width: 820px;
    margin: 0 auto;
    gap: 0 !important;
}
#question-box textarea {
    border-radius: 14px 0 0 14px !important;
    border-right: none !important;
    font-size: 1.02em;
    padding: 14px 18px !important;
}
#ask-button {
    border-radius: 0 14px 14px 0 !important;
    font-size: 1em;
    font-weight: 600;
    min-width: 110px;
}

.beam-panel {
    position: relative;
    border-radius: 16px;
    padding: 1.5px;
    background: conic-gradient(
        from var(--beam-angle),
        transparent 0deg,
        transparent 250deg,
        #f0b429 300deg,
        #ff7a45 325deg,
        color-mix(in srgb, #ff7a45 30%, transparent) 335deg,
        transparent 350deg
    );
    animation: rotate-beam 5s linear infinite;
}
@keyframes rotate-beam {
    to { --beam-angle: 360deg; }
}
.answer-box {
    background: #1e2530;
    border-radius: 14.5px;
    padding: 20px 24px;
    line-height: 1.7;
    color: #e8eaed;
}
.answer-box p { margin: 0 0 12px 0; }
.answer-box p:last-child { margin-bottom: 0; }
.answer-box ul, .answer-box ol {
    margin: 0 0 12px 0;
    padding-left: 22px;
}
.answer-box li { margin-bottom: 8px; line-height: 1.55; }
.answer-box strong { color: #f0b429; font-weight: 600; }
.answer-thinking { color: #8b93a3; font-style: italic; }

.sources-header {
    font-size: 0.85em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #8b93a3;
    margin: 24px 0 12px 0;
    font-weight: 600;
}
#answer-output, #sources-output {
    min-height: 60px;
}
"""

EXAMPLE_QUESTIONS = [
    "What do customers complain about most?",
    "What do customers love about these products?",
    "Are there any mentions of shipping issues?",
]

THINKING_HTML = """
<div class="beam-panel">
    <div class="answer-box answer-thinking">Thinking…</div>
</div>
"""


def rating_to_stars(rating) -> str:
    if rating is None or rating < 0:
        return "<span style='color:#8b93a3; font-size:0.85em;'>No rating</span>"
    filled = int(round(rating))
    stars = "".join(
        f"<span style='color:{'#f0b429' if i < filled else '#3a4257'};'>★</span>"
        for i in range(5)
    )
    return stars


def render_source_card(source: dict) -> str:
    return f"""
    <div style="border:1px solid #2d3648; border-radius:10px; padding:14px 18px;
                margin-bottom:12px; background:#161c27; transition:border-color 0.15s;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-weight:600; color:#e8eaed; font-size:0.9em;
                         letter-spacing:0.02em;">Product {source['product_id']}</span>
            <span style="font-size:1.05em;">{rating_to_stars(source['rating'])}</span>
        </div>
        <div style="color:#c4c9d4; font-size:0.92em; line-height:1.5;">
            {source['text_raw']}
        </div>
    </div>
    """


def render_answer_html(answer_text: str) -> str:
    body_html = md.markdown(answer_text, extensions=["nl2br"])
    return f'<div class="beam-panel"><div class="answer-box">{body_html}</div></div>'


def ask(question: str):
    if not question.strip():
        yield "Please enter a question.", ""
        return

    if not GROQ_API_KEY:
        yield "GROQ_API_KEY not found — check your .env file.", ""
        return

    # Immediate feedback so the user knows the click registered.
    yield THINKING_HTML, ""

    result = answer_question(question=question, groq_api_key=GROQ_API_KEY)

    answer_html = render_answer_html(result["answer"])
    sources_html = "".join(render_source_card(s) for s in result["sources"])
    yield answer_html, sources_html


theme = gr.themes.Soft(
    primary_hue="orange",
    neutral_hue="slate",
).set(
    body_background_fill="*neutral_950",
    block_background_fill="*neutral_900",
)

with gr.Blocks(title="AI-Powered Customer Review Intelligence Platform") as demo:
    gr.HTML(
        """
        <div class="header-section">
            <div class="header-badge">
                <span class="badge-dot"></span>
                Powered by RAG · Qwen 3.6 27B
            </div>
            <div class="header-title">🔍 AI-Powered Customer Review Intelligence Platform</div>
            <div class="header-subtitle">
                Ask a question about customer reviews — answers are grounded
                only in the reviews retrieved below, never invented.
            </div>
        </div>
        """
    )

    with gr.Row(elem_classes="search-row"):
        question_input = gr.Textbox(
            show_label=False,
            placeholder="e.g. What do customers complain about most?",
            elem_id="question-box",
            scale=5,
        )
        submit_btn = gr.Button("Ask", variant="primary", elem_id="ask-button", scale=1)

    gr.Examples(examples=EXAMPLE_QUESTIONS, inputs=question_input)

    answer_output = gr.HTML(elem_id="answer-output")

    gr.Markdown("Sources", elem_classes="sources-header")
    sources_output = gr.HTML(elem_id="sources-output")

    submit_btn.click(fn=ask, inputs=question_input, outputs=[answer_output, sources_output])
    question_input.submit(fn=ask, inputs=question_input, outputs=[answer_output, sources_output])


if __name__ == "__main__":
    demo.launch(theme=theme, css=CUSTOM_CSS)