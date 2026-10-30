"""
YBT Army - chat web app.

Run:  streamlit run ybt_app.py
"""

import ast
import html
import json
import operator
import os
import re
import time
import uuid
from pathlib import Path
from threading import Thread

import streamlit as st
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

from ybt_brand import BRAND_NAME, BUILT_BY, MODEL_NAME, SYSTEM_PROMPT

APP_DIR = Path(__file__).parent
MODEL_DIR = APP_DIR / MODEL_NAME
CHATS_FILE = Path(os.environ.get("YBT_CHATS_DIR", APP_DIR / "chats")) / "chats.json"
AVATAR = ":material/bolt:"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

SUGGESTIONS = [
    (":material/lightbulb:", "Explain photosynthesis in simple words"),
    (":material/code:", "Write a Python function to check if a number is prime"),
    (":material/public:", "What is the capital of Japan?"),
    (":material/calculate:", "What is 128 * 46?"),
]

MODES = {
    "Balanced": "",
    "Concise": "Keep every answer to one or two sentences.",
    "Detailed": "Give thorough, well-structured answers using short paragraphs or bullet points.",
    "Hinglish": "Reply in Hinglish (Hindi written in the Latin alphabet) unless the user writes in another language.",
}

st.set_page_config(page_title=BRAND_NAME, page_icon=AVATAR, layout="centered", initial_sidebar_state="auto")

# --------------------------------------------------------------------------- #
# Theme
# --------------------------------------------------------------------------- #
THEMES = {
    "light": dict(bg="#FFFFFF", side="#F9F9F9", surface="#FFFFFF", surface2="#F0F0F0", text="#0D0D0D", muted="#6B6B76",
                  border="#E6E6E8", accent="#0D0D0D", onaccent="#FFFFFF", soft="#F2F2F3", link="#2563EB",
                  ok="#16A34A", ring="rgba(0,0,0,.10)"),
    "dark": dict(bg="#212121", side="#171717", surface="#2A2A2A", surface2="#303030", text="#ECECEC", muted="#A1A1AA",
                 border="#3A3A3D", accent="#FFFFFF", onaccent="#0D0D0D", soft="#2F2F2F", link="#60A5FA",
                 ok="#4ADE80", ring="rgba(255,255,255,.10)"),
}

STATIC_CSS = """
<style>
@keyframes ybt-fade-up { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
@keyframes ybt-pulse { 0% { box-shadow: 0 0 0 0 var(--ok); } 70% { box-shadow: 0 0 0 7px transparent; } 100% { box-shadow: 0 0 0 0 transparent; } }
@keyframes ybt-dot { 0%, 80%, 100% { transform: scale(.55); opacity: .3; } 40% { transform: scale(1); opacity: 1; } }
@keyframes ybt-float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: var(--bg) !important; color: var(--text) !important;
    font-family: "Segoe UI", system-ui, -apple-system, "SF Pro Text", Roboto, "Helvetica Neue", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
}
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, [data-testid="stMainMenu"], [data-testid="stToolbarActions"], [data-testid="stAppDeployButton"],
[data-testid="stDeployButton"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; visibility: hidden !important; }
/* keep the sidebar open/close button reachable on every screen size */
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapseButton"] button { visibility: visible !important; color: var(--text) !important; }
[data-testid="stExpandSidebarButton"] { background: var(--soft) !important; border-radius: 12px !important; }
[data-testid="stExpandSidebarButton"] * { color: var(--text) !important; }
.block-container { max-width: 768px; padding-top: 1rem; padding-bottom: 8.5rem; }

.stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp span,
[data-testid="stMarkdownContainer"] { color: var(--text); }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: var(--muted) !important; }
a { color: var(--link) !important; }

/* sidebar */
[data-testid="stSidebar"] { background: var(--side) !important; border-right: 1px solid var(--border); }
[data-testid="stSidebar"] .block-container, [data-testid="stSidebarUserContent"] { padding-top: 1rem; }
.ybt-side-brand { margin: 2px 0 14px 6px; }
.ybt-side-brand b { font-size: 1.25rem; font-weight: 800; letter-spacing: .01em; color: var(--text); }
.ybt-label { color: var(--muted); font-size: .72rem; font-weight: 600; margin: 18px 0 6px 6px; }

/* wordmark (no logo) */
.ybt-word { font-weight: 800; letter-spacing: .01em; font-size: 2.6rem; line-height: 1; color: var(--text); animation: ybt-fade-up .6s ease both; }

/* top bar */
.ybt-top { display: flex; align-items: center; gap: 10px; padding: 2px 0 12px; margin-bottom: 6px; min-height: 2.4rem; animation: ybt-fade-up .35s ease both; }
.ybt-top .b { font-weight: 800; letter-spacing: .01em; white-space: nowrap; }
.ybt-top .sep { color: var(--muted); }
.ybt-top .t { color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; flex: 1 1 auto; }
.ybt-status { margin-left: auto; flex: none; display: flex; align-items: center; gap: 6px; color: var(--muted); font-size: .78rem; }
.ybt-status i { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); animation: ybt-pulse 2s ease-out infinite; }

/* hero */
.ybt-hero { text-align: center; margin: 12vh 0 28px; animation: ybt-fade-up .5s ease both; }
.ybt-hero h1 { margin: 18px 0 6px; font-size: 1.5rem; font-weight: 500; letter-spacing: -.01em; padding: 0; color: var(--text); }
.ybt-hero p { color: var(--muted); margin: 0; }

/* messages */
.ybt-user { display: flex; justify-content: flex-end; margin: 18px 0 8px; animation: ybt-fade-up .25s ease both; }
.ybt-user div { max-width: 78%; background: var(--soft); color: var(--text); padding: 10px 16px;
    border-radius: 22px; line-height: 1.55; word-wrap: break-word; }
[data-testid="stChatMessage"] { background: transparent !important; padding: .3rem 0 !important; animation: ybt-fade-up .3s ease both; }
[data-testid="stChatMessage"] [data-testid^="stChatMessageAvatar"] { display: none !important; }
[data-testid="stChatMessage"] { gap: 0 !important; }
[data-testid="stChatMessage"] p { line-height: 1.72; margin-bottom: .6rem; }
.ybt-typing { display: inline-flex; gap: 5px; padding: 10px 0; }
.ybt-typing span { width: 8px; height: 8px; border-radius: 50%; background: var(--text); animation: ybt-dot 1.2s infinite ease-in-out; }
.ybt-typing span:nth-child(2) { animation-delay: .15s; }
.ybt-typing span:nth-child(3) { animation-delay: .3s; }
pre, code { background: var(--surface2) !important; color: var(--text) !important; border-radius: 10px; }

/* buttons */
.stButton button, .stDownloadButton button {
    background: var(--surface) !important; color: var(--text) !important; border: 1px solid var(--border) !important;
    border-radius: 12px !important; transition: background .15s ease, border-color .15s ease, transform .1s ease;
}
.stButton button:hover, .stDownloadButton button:hover { background: var(--surface2) !important; border-color: var(--border) !important; }
.stButton button:active, .stDownloadButton button:active { transform: scale(.98); }
.stButton button *, .stDownloadButton button * { color: inherit !important; }
[data-testid="stBaseButton-primary"] { background: var(--accent) !important; color: var(--onaccent) !important; border-color: var(--accent) !important; }
[data-testid="stBaseButton-primary"]:hover { opacity: .88; background: var(--accent) !important; }
[data-testid="stBaseButton-tertiary"] { border-color: transparent !important; background: transparent !important; color: var(--muted) !important; }
[data-testid="stBaseButton-tertiary"]:hover { background: var(--surface2) !important; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] { background: transparent !important; border-color: transparent !important; }
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover { background: var(--surface2) !important; }
.st-key-newchat button { border: 1px solid var(--border) !important; font-weight: 600; justify-content: flex-start; }
.st-key-newchat button > div, .st-key-newchat button [data-testid="stMarkdownContainer"] { justify-content: flex-start !important; text-align: left !important; }
[class*="st-key-chat_"] button, [class*="st-key-chatcur_"] button { justify-content: flex-start; text-align: left; font-size: .9rem; }
[class*="st-key-chat_"] button p, [class*="st-key-chatcur_"] button p { text-align: left; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: .25rem; }
[data-testid="stSidebar"] [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; }
[data-testid="stSidebar"] [data-testid="stColumn"]:first-child { flex: 1 1 auto !important; }
[data-testid="stSidebar"] [data-testid="stColumn"]:last-child { flex: 0 0 2.4rem !important; }
[class*="st-key-chatcur_"] button { background: var(--surface2) !important; }
[class*="st-key-sug_"] button { text-align: left; justify-content: flex-start; min-height: 3.6rem; border-radius: 16px !important; animation: ybt-fade-up .5s ease both; }
[class*="st-key-sug_"] button > div, [class*="st-key-chat_"] button > div, [class*="st-key-chatcur_"] button > div { justify-content: flex-start !important; width: 100%; }
[class*="st-key-sug_"] button [data-testid="stMarkdownContainer"], [class*="st-key-sug_"] button p { text-align: left !important; flex: 1 1 auto; }

/* input */
[data-testid="stBottom"], [data-testid="stBottom"] > div { background: transparent !important; }
[data-testid="stBottom"] > div { background: linear-gradient(to top, var(--bg) 62%, transparent) !important; padding-bottom: max(.6rem, env(safe-area-inset-bottom)); }
[data-testid="stChatInput"] { background: var(--soft) !important; border: 1px solid var(--border) !important;
    border-radius: 28px !important; box-shadow: 0 2px 14px var(--ring); transition: border-color .2s, box-shadow .2s; }
[data-testid="stChatInput"]:focus-within { border-color: var(--muted) !important; box-shadow: 0 4px 20px var(--ring); }
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] [data-baseweb="base-input"] { background: transparent !important; border-radius: 28px; }
[data-testid="stChatInput"] textarea { background: transparent !important; color: var(--text) !important; font-size: 1rem; }
[data-testid="stChatInput"] textarea::placeholder { color: var(--muted) !important; opacity: 1; }
[data-testid="stChatInputSubmitButton"] { background: var(--accent) !important; color: var(--onaccent) !important; border-radius: 50% !important; }
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="input"] input {
    background: var(--surface2) !important; color: var(--text) !important; border-radius: 10px; }
[data-testid="stExpander"] { background: transparent; border: 1px solid var(--border); border-radius: 12px; }
[data-testid="stExpander"] summary * { color: var(--text) !important; }
.ybt-foot { text-align: center; color: var(--muted); font-size: .75rem; margin-top: 22px; }

/* message action row (Copy / Regenerate / stats) stays on one line at every width */
[class*="st-key-act_"] [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: .25rem; align-items: center; }
[class*="st-key-act_"] [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 0 0 auto !important; }
[class*="st-key-act_"] [data-testid="stColumn"]:last-child { flex: 1 1 auto !important; }
[class*="st-key-act_"] button { min-height: 2.2rem; padding: .15rem .6rem; font-size: .85rem; }

/* desktop: wide screens keep a comfortable reading column */
@media (min-width: 1100px) {
    .block-container { padding-top: 1.4rem; }
    .ybt-hero { margin-top: 14vh; }
}

/* tablet */
@media (max-width: 900px) {
    .block-container { max-width: 100%; padding-left: 1.4rem; padding-right: 1.4rem; }
}

/* mobile: native-app feel */
@media (max-width: 640px) {
    .block-container { padding: 3.2rem .85rem 8rem; }
    .ybt-top { padding-top: 0; }
    .ybt-hero { margin: 4vh 0 18px; }
    .ybt-word { font-size: 2.1rem; }
    .ybt-hero h1 { font-size: 1.25rem; }
    [class*="st-key-act_"] [data-testid="stColumn"]:last-child { display: none; }
    .ybt-user div { max-width: 88%; }
    .ybt-status { display: none; }
    .stButton button, .stDownloadButton button { min-height: 46px; }
    [data-testid="stChatInput"] textarea { font-size: 16px; }
    [data-testid="stBottom"] > div { padding-left: .6rem; padding-right: .6rem; }
    [data-testid="stSidebar"] { box-shadow: 0 0 40px rgba(0,0,0,.25); }
}

@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
</style>
"""


def theme_css(name):
    t = THEMES[name]
    vars_ = ";".join(f"--{k}:{v}" for k, v in t.items())
    return f"<style>:root{{{vars_}}}</style>" + STATIC_CSS


# --------------------------------------------------------------------------- #
# Quick replies (identity, greetings, simple maths) - answered by code
# --------------------------------------------------------------------------- #
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Mod: operator.mod, ast.Pow: operator.pow, ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _safe_eval(node.left), _safe_eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("exponent too large")
        return _OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("unsupported")


def _fmt_number(x):
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    if isinstance(x, int):
        return f"{x:,}" if abs(x) >= 10000 else str(x)
    return f"{x:.6g}"


def quick_reply(text):
    """Return a reply for greetings, identity questions and simple maths, else None."""
    t = text.strip()
    low = re.sub(r"[^a-z0-9\s]", "", t.lower()).strip()

    if re.fullmatch(r"(hi+|hello+|hey+|hii+|namaste|hola|yo|good (morning|afternoon|evening))( there)?", low):
        return f"Hello! I'm {BRAND_NAME}. Ask me anything and I'll do my best to help."
    if re.fullmatch(r"(how are you|how r u|whats up|sup)( today)?", low):
        return "I'm doing well, thanks for asking! How can I help you?"
    if re.fullmatch(
        r"(who are you|what are you|your name|what is your name|whats your name|who made you|who built you|"
        r"who created you|who developed you|who trained you|who is your creator|which company made you|"
        r"tell me about yourself|introduce yourself|are you (chat ?gpt|gpt ?4|claude|gemini|made by openai)|"
        r"which (ai )?model are you)",
        low,
    ):
        return f"I'm {BRAND_NAME}, an AI assistant built by the {BUILT_BY} team."
    if re.fullmatch(
        r"((tum|tu|aap) kaun (ho|hai|hain)|(tumhara|tera|aapka) naam kya (hai|hain)|"
        r"(tumhe|tujhe|aapko) kisne (banaya|bnaya)( hai)?|(tumhe|tujhe|aapko) kisne train kiya( hai)?|"
        r"(tumhara|aapka) creator kaun (hai|hain)|apne (bare|baare) mein batao|kya (tum|aap) chat ?gpt (ho|hain))",
        low,
    ):
        return f"Main {BRAND_NAME} hoon, ek AI assistant. Mujhe {BUILT_BY} team ne banaya hai."
    if re.fullmatch(r"(thanks|thank you|thx|ty|thanks a lot|shukriya|dhanyavaad)", low):
        return "You're welcome!"
    if re.fullmatch(r"(bye|goodbye|see you|see ya|alvida)", low):
        return "Goodbye! Come back anytime."

    expr = re.sub(r"(?i)\b(what|whats|is|calculate|solve|equals?|the|answer|of|result)\b", " ", t)
    expr = expr.replace("×", "*").replace("÷", "/").replace("^", "**").replace("=", " ").replace("?", " ")
    expr = re.sub(r"(?<=\d)\s*x\s*(?=\d)", "*", expr).strip()
    if re.fullmatch(r"[\d\s.+\-*/()%]+", expr) and re.search(r"\d", expr) and re.search(r"[+\-*/%]", expr.lstrip("+-")):
        try:
            value = _safe_eval(ast.parse(expr.strip(), mode="eval"))
            return f"{expr.strip()} = **{_fmt_number(value)}**"
        except Exception:
            return None
    return None


# --------------------------------------------------------------------------- #
# Chat storage (JSON file next to the app)
# --------------------------------------------------------------------------- #
def load_chats():
    try:
        return json.loads(CHATS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_chats():
    chats = {k: v for k, v in st.session_state.chats.items() if v["messages"]}
    try:
        CHATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CHATS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(chats, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(CHATS_FILE)
    except OSError:
        pass  # chats still work for this session if the disk is read-only


def new_chat():
    cur = st.session_state.chats.get(st.session_state.get("chat_id"))
    if cur is not None and not cur["messages"]:
        return  # already on an empty chat
    cid = uuid.uuid4().hex[:8]
    st.session_state.chats[cid] = {"title": "New chat", "updated": time.time(), "messages": []}
    st.session_state.chat_id = cid


def open_chat(cid):
    st.session_state.chat_id = cid


def delete_chat(cid):
    st.session_state.chats.pop(cid, None)
    save_chats()
    if st.session_state.get("chat_id") == cid:
        st.session_state.chat_id = None
        new_chat()


def delete_all_chats():
    st.session_state.chats = {}
    st.session_state.chat_id = None
    save_chats()
    new_chat()


def chat_to_markdown(chat):
    lines = [f"# {chat['title']}", f"_{BRAND_NAME}_", ""]
    for m in chat["messages"]:
        lines += [f"**{'You' if m['role'] == 'user' else BRAND_NAME}:**", "", m["content"], ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner=f"Loading {BRAND_NAME}...")
def load_model():
    dtype = torch.float16 if DEVICE == "cuda" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(MODEL_DIR, torch_dtype=dtype)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    return model.eval().to(DEVICE), tokenizer


def generate_reply(model, tokenizer, history, placeholder, settings):
    """Stream a reply into `placeholder`; returns (text, token_count, seconds)."""
    system = (SYSTEM_PROMPT + " " + MODES[settings["mode"]]).strip()
    messages = [{"role": "system", "content": system}] + history
    inputs = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt", return_dict=True
    ).to(DEVICE)
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    Thread(
        target=model.generate,
        kwargs=dict(**inputs, streamer=streamer, max_new_tokens=settings["max_tokens"], do_sample=True,
                    temperature=settings["temperature"], top_p=0.9, repetition_penalty=1.1),
    ).start()
    t0, text = time.time(), ""
    for chunk in streamer:
        text += chunk
        placeholder.markdown(text + " ▌")
    text = text.strip()
    secs = max(time.time() - t0, 1e-6)
    return text, len(tokenizer(text)["input_ids"]), secs


# --------------------------------------------------------------------------- #
# UI pieces
# --------------------------------------------------------------------------- #
def user_bubble(text):
    st.markdown(f'<div class="ybt-user"><div>{html.escape(text).replace(chr(10), "<br>")}</div></div>',
                unsafe_allow_html=True)


def copy_button(text, key):
    """Copy via st.code's built-in copy icon (no custom JavaScript, so model output is never executed)."""
    with st.popover("Copy", icon=":material/content_copy:", type="tertiary"):
        st.code(text, language=None, wrap_lines=True)


def render_sidebar():
    sb = st.sidebar
    sb.markdown(
        f'<div class="ybt-side-brand"><b>{BRAND_NAME}</b></div>',
        unsafe_allow_html=True,
    )
    sb.button("New chat", key="newchat", icon=":material/edit_square:", use_container_width=True, on_click=new_chat)

    sb.markdown('<div class="ybt-label">Chats</div>', unsafe_allow_html=True)
    query = sb.text_input("Search chats", placeholder="Search chats", label_visibility="collapsed").strip().lower()
    items = sorted(
        ((cid, c) for cid, c in st.session_state.chats.items() if c["messages"]),
        key=lambda kv: kv[1]["updated"], reverse=True,
    )
    shown = 0
    for cid, c in items:
        if query and query not in c["title"].lower() and not any(query in m["content"].lower() for m in c["messages"]):
            continue
        shown += 1
        col_a, col_b = sb.columns([5, 1], vertical_alignment="center")
        is_cur = cid == st.session_state.chat_id
        col_a.button(c["title"], key=f"{'chatcur' if is_cur else 'chat'}_{cid}", use_container_width=True,
                     on_click=open_chat, args=(cid,))
        col_b.button("", key=f"del_{cid}", icon=":material/delete:", type="tertiary", on_click=delete_chat, args=(cid,))
    if not shown:
        sb.caption("No chats yet." if not items else "No matches.")

    sb.markdown('<div class="ybt-label">Settings</div>', unsafe_allow_html=True)
    with sb.expander("Preferences", icon=":material/tune:"):
        if "dark" not in st.session_state:  # first visit: follow the device theme
            try:
                st.session_state.dark = st.context.theme.type == "dark"
            except Exception:
                st.session_state.dark = False
        dark = st.toggle("Dark mode", key="dark")
        mode = st.segmented_control("Style", list(MODES), default="Balanced", key="mode", selection_mode="single") or "Balanced"
        temperature = st.slider("Creativity", 0.1, 1.2, 0.5, 0.05, help="Lower is more precise, higher is more varied.")
        max_tokens = st.slider("Max reply length", 32, 1024, 384, 16, help="Maximum tokens per reply.")
        memory = st.slider("Memory (messages)", 0, 10, 4, 2, help="How many earlier messages the model sees.")

    chat = st.session_state.chats[st.session_state.chat_id]
    if chat["messages"]:
        sb.download_button("Export chat", chat_to_markdown(chat), file_name="ybt-army-chat.md", mime="text/markdown",
                           icon=":material/download:", use_container_width=True)
    with sb.popover("Delete all chats", icon=":material/delete_sweep:", use_container_width=True):
        st.caption("This removes every saved chat.")
        st.button("Yes, delete all", on_click=delete_all_chats, type="primary")

    return dict(dark=dark, mode=mode, temperature=temperature, max_tokens=max_tokens, memory=memory)


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #
def main():
    if "chats" not in st.session_state:
        st.session_state.chats = load_chats()
        st.session_state.chat_id = None
        new_chat()

    settings = render_sidebar()
    theme = "dark" if settings["dark"] else "light"
    st.markdown(theme_css(theme), unsafe_allow_html=True)

    if not MODEL_DIR.exists():
        st.error(f"Model folder '{MODEL_NAME}' was not found next to the app.")
        st.stop()
    chat = st.session_state.chats[st.session_state.chat_id]
    msgs = chat["messages"]

    queued = st.session_state.pop("queued_prompt", None)
    user_input = st.chat_input(f"Message {BRAND_NAME}") or queued
    pending = False

    if st.session_state.pop("regen", False) and msgs and msgs[-1]["role"] == "assistant":
        msgs.pop()
        pending = True
    if user_input:
        msgs.append({"role": "user", "content": user_input})
        if chat["title"] == "New chat":
            chat["title"] = (user_input[:38] + "...") if len(user_input) > 40 else user_input
        pending = True
    if pending:
        chat["updated"] = time.time()
        save_chats()

    # header / hero
    if not msgs:
        st.markdown(
            f'<div class="ybt-hero"><div class="ybt-word">{BRAND_NAME}</div><h1>How can I help you today?</h1>'
            f"<p>{BRAND_NAME} answers questions, explains ideas and writes code.</p></div>",
            unsafe_allow_html=True,
        )
        cols = st.columns(2)
        for i, (icon, prompt) in enumerate(SUGGESTIONS):
            if cols[i % 2].button(prompt, key=f"sug_{i}", icon=icon, use_container_width=True):
                st.session_state.queued_prompt = prompt
                st.rerun()
    else:
        st.markdown(
            f'<div class="ybt-top"><span class="b">{BRAND_NAME}</span><span class="sep">/</span><span class="t">{html.escape(chat["title"])}</span>'
            f'<span class="ybt-status"><i></i>Online</span></div>',
            unsafe_allow_html=True,
        )

    # history
    for i, m in enumerate(msgs):
        if m["role"] == "user":
            user_bubble(m["content"])
            continue
        with st.chat_message("assistant", avatar=AVATAR):
            st.markdown(m["content"])
            with st.container(key=f"act_{i}"):
                c1, c2, c3 = st.columns(3, vertical_alignment="center")
                with c1:
                    copy_button(m["content"], i)
                if i == len(msgs) - 1 and not pending:
                    c2.button("Regenerate", key="regen_btn", icon=":material/refresh:", type="tertiary",
                              on_click=lambda: st.session_state.update(regen=True))
                if m.get("meta"):
                    c3.caption(m["meta"])

    # reply
    if pending:
        question = msgs[-1]["content"]
        reply, meta = quick_reply(question), ""
        with st.chat_message("assistant", avatar=AVATAR):
            ph = st.empty()
            if reply is None:
                ph.markdown('<div class="ybt-typing"><span></span><span></span><span></span></div>', unsafe_allow_html=True)
                model, tokenizer = load_model()  # loaded on first use so the page appears instantly
                history = msgs[-(settings["memory"] + 1):]
                if history and history[0]["role"] != "user":
                    history = history[1:]
                reply, n_tok, secs = generate_reply(model, tokenizer, history, ph, settings)
                meta = f"{n_tok} tokens · {n_tok / secs:.0f} tok/s"
            reply = reply or "Sorry, I couldn't come up with an answer. Please try rephrasing."
            ph.markdown(reply)
        msgs.append({"role": "assistant", "content": reply, "meta": meta})
        chat["updated"] = time.time()
        save_chats()
        st.rerun()

    if not msgs:
        st.markdown(f'<div class="ybt-foot">{BRAND_NAME} can make mistakes. Please verify important answers.</div>',
                    unsafe_allow_html=True)


main()
