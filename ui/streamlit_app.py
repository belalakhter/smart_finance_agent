import streamlit as st
import requests
import uuid
from typing import Dict, List

BACKEND_URL = "http://localhost:3000"

st.set_page_config(
    page_title="Smat Agent",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&display=swap');

:root {
    --bg: #08080e;
    --surface: #0e0e18;
    --surface-raised: #13131f;
    --surface-hover: #18182a;
    --border: #1a1a2c;
    --border-bright: #252538;
    --accent: #7c6af7;
    --accent-2: #a78bfa;
    --accent-glow: rgba(124, 106, 247, 0.2);
    --accent-subtle: rgba(124, 106, 247, 0.07);
    --text-primary: #eaeaf5;
    --text-secondary: #6e6e96;
    --text-muted: #3a3a55;
    --user-bubble: #14142a;
    --success: #34d399;
    --error: #f87171;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: var(--bg) !important;
    font-family: 'DM Mono', monospace !important;
    color: var(--text-primary) !important;
}

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    min-width: 290px !important;
    max-width: 290px !important;
    padding: 0 !important;
    transform: translateX(0) !important;
    margin-left: 0 !important;
    visibility: visible !important;
}

[data-testid="stSidebar"] > div {
    padding: 0 !important;
    height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
}

[data-testid="stSidebar"] section,
[data-testid="stSidebar"] .block-container {
    padding: 0 1rem !important;
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    gap: 0 !important;
}

[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
button[aria-label="Close sidebar"],
button[title="Close sidebar"] {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    pointer-events: none !important;
    position: absolute !important;
    overflow: hidden !important;
}

.sb-brand {
    padding: 1.2rem 0;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
}

.sb-brand-icon {
    width: 38px;
    height: 38px;
    background: linear-gradient(135deg, #7c6af7 0%, #a78bfa 100%);
    border-radius: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    box-shadow: 0 4px 18px rgba(124,106,247,0.4), inset 0 1px 0 rgba(255,255,255,0.15);
    flex-shrink: 0;
    color: white;
    font-weight: 900;
}

.sb-brand-name {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.03em;
    line-height: 1;
}

.sb-brand-tag {
    font-size: 0.58rem;
    color: var(--accent-2);
    letter-spacing: 0.16em;
    text-transform: uppercase;
    opacity: 0.65;
    margin-top: 3px;
}

.sb-new-wrap {
    padding: 0.9rem 0 0.7rem;
    flex-shrink: 0;
}

[data-testid="stSidebar"] button[kind="primary"] {
    background: var(--surface-raised) !important;
    border: 1px solid var(--border-bright) !important;
    color: var(--text-primary) !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    border-radius: 8px !important;
    padding: 0.68rem 1rem !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
    box-shadow: none !important;
    cursor: pointer;
}

[data-testid="stSidebar"] button[kind="primary"]:hover {
    background: var(--surface-hover) !important;
    border-color: var(--border) !important;
    box-shadow: none !important;
}

.sb-label {
    font-size: 0.58rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--text-muted);
    padding: 0 0 0.45rem;
    flex-shrink: 0;
}

.sb-threads {
    flex: 1;
    overflow-y: auto;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-height: 0;
}

.sb-threads::-webkit-scrollbar { width: 3px; }
.sb-threads::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }

.th-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.62rem 0.8rem;
    border-radius: 11px;
    border: 1px solid transparent;
    transition: all 0.17s ease;
    position: relative;
    overflow: hidden;
    cursor: pointer;
}

.th-item:hover { background: var(--surface-hover); border-color: var(--border); }

.th-item.active {
    background: rgba(124,106,247,0.09);
    border-color: rgba(124,106,247,0.22);
}

.th-item.active::before {
    content: '';
    position: absolute;
    left: 0; top: 18%; bottom: 18%;
    width: 3px;
    background: linear-gradient(to bottom, var(--accent), var(--accent-2));
    border-radius: 0 3px 3px 0;
}

.th-avatar {
    width: 34px; height: 34px;
    border-radius: 9px;
    background: var(--surface-raised);
    border: 1px solid var(--border-bright);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    flex-shrink: 0;
    transition: all 0.17s;
    color: var(--accent-2);
}

.th-item.active .th-avatar {
    background: rgba(124,106,247,0.14);
    border-color: rgba(124,106,247,0.28);
}

.th-body { flex: 1; min-width: 0; }

.th-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    display: flex;
    align-items: center;
    gap: 6px;
}

.th-item.active .th-title { color: var(--accent-2); }

.th-badge {
    font-family: 'DM Mono', monospace;
    font-size: 0.5rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    padding: 1px 5px;
    background: rgba(124,106,247,0.15);
    border: 1px solid rgba(124,106,247,0.25);
    border-radius: 4px;
    color: var(--accent-2);
    text-transform: uppercase;
}

.th-preview {
    font-size: 0.64rem;
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 3px;
    font-style: italic;
}

.th-count {
    font-size: 0.62rem;
    color: var(--text-muted);
    flex-shrink: 0;
    letter-spacing: 0.03em;
}

.sb-divider {
    height: 1px;
    background: var(--border);
    margin: 0.6rem 0;
    flex-shrink: 0;
}

.sb-footer {
    padding: 0.75rem 0 1rem;
    flex-shrink: 0;
}

.sb-footer-label {
    font-size: 0.58rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
    padding: 0;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background: var(--surface-raised) !important;
    border: 1px dashed var(--border-bright) !important;
    border-radius: 10px !important;
    padding: 0.85rem !important;
    transition: all 0.2s ease !important;
    min-height: unset !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--border) !important;
    background: var(--surface-hover) !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] {
    display: none !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] small {
    display: none !important;
}

[data-testid="stSidebar"] button:not([kind="primary"]) {
    all: unset !important;
    display: inline-flex !important;
    justify-content: center;
    align-items: center;
    cursor: pointer;
    padding: 0 6px;
    color: var(--accent-2);
    font-size: 1rem;
    transition: color 0.2s ease;
}

[data-testid="stSidebar"] button:not([kind="primary"]):hover {
    color: var(--accent);
}

[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:last-child button {
    font-size: 0 !important;
    padding: 4px 8px !important;
    min-width: unset !important;
    height: auto !important;
    border-radius: 4px !important;
    background: transparent !important;
    border: 1px solid rgba(248,113,113,0.3) !important;
    color: transparent !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
}

[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:last-child button::before {
    content: "×";
    font-size: 0.7rem;
    color: var(--error);
    font-weight: 500;
    line-height: 1;
}

[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:last-child:hover button {
    background: rgba(248,113,113,0.08) !important;
    border-color: rgba(248,113,113,0.4) !important;
}

[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:last-child:hover button::before {
    content: "Delete";
}

.main .block-container {
    max-width: 820px !important;
    padding: 0 2rem 2rem !important;
    margin: 0 auto !important;
}

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.15rem 0 0.75rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
    gap: 12px;
}

.topbar-left { display: flex; align-items: center; gap: 11px; }

.topbar-icon {
    width: 36px; height: 36px;
    border-radius: 10px;
    background: var(--accent-subtle);
    border: 1px solid rgba(124,106,247,0.2);
    display: flex; align-items: center; justify-content: center;
    font-size: 16px;
    color: var(--accent-2);
}

.topbar-title {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    line-height: 1;
}

.topbar-sub {
    font-size: 0.65rem;
    color: var(--text-muted);
    letter-spacing: 0.04em;
    margin-top: 3px;
}

.status-pill {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 11px;
    background: rgba(52,211,153,0.07);
    border: 1px solid rgba(52,211,153,0.18);
    border-radius: 20px;
    font-size: 0.6rem;
    color: var(--success);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 500;
}

.status-dot {
    width: 5px; height: 5px;
    background: var(--success);
    border-radius: 50%;
    animation: statusPulse 2.5s infinite;
}

@keyframes statusPulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(52,211,153,0.5); }
    50% { opacity: 0.5; box-shadow: 0 0 0 4px rgba(52,211,153,0); }
}

[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0.45rem 0 !important;
}

[data-testid="stChatMessageContent"] {
    background: var(--surface-raised) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    padding: 0.9rem 1.15rem !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.875rem !important;
    line-height: 1.8 !important;
    color: var(--text-primary) !important;
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    background: var(--user-bubble) !important;
    border-color: rgba(124,106,247,0.14) !important;
}

[data-testid="stChatInput"] {
    border-top: 1px solid var(--border) !important;
    background: var(--surface) !important;
    padding: 1rem !important;
}

[data-testid="stChatInputContainer"] {
    background: var(--surface-raised) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 14px !important;
    transition: all 0.2s ease !important;
}

[data-testid="stChatInputContainer"]:focus-within {
    border-color: var(--border) !important;
    box-shadow: none !important;
}

[data-testid="stChatInputTextArea"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.875rem !important;
    color: var(--text-primary) !important;
    background: transparent !important;
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 55vh;
    gap: 14px;
    text-align: center;
}

.empty-glyph {
    width: 76px; height: 76px;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(124,106,247,0.1), rgba(167,139,250,0.04));
    border: 1px solid rgba(124,106,247,0.14);
    display: flex; align-items: center; justify-content: center;
    font-size: 2.2rem;
    margin-bottom: 6px;
    color: var(--accent-2);
    font-weight: 900;
}

.empty-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-secondary);
    letter-spacing: -0.02em;
}

.empty-sub {
    font-size: 0.76rem;
    color: var(--text-muted);
    line-height: 1.8;
    max-width: 260px;
}

.stAlert, div[data-testid="stAlert"] {
    background: var(--surface-raised) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 10px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
}

[data-testid="stVerticalBlock"] {
    padding: 0 !important;
}

</style>
""", unsafe_allow_html=True)

if "chats" not in st.session_state:
    st.session_state.chats = {}  
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

def send_message(chat_id: str, message: str) -> str:
    """Send user message to backend and receive assistant reply."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"chatId": chat_id, "message": message},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("reply", "")
    except Exception as e:
        return f"Error contacting backend: {str(e)}"

def add_message(chat_id: str, role: str, content: str) -> None:
    if chat_id not in st.session_state.chats:
        st.session_state.chats[chat_id] = []
    st.session_state.chats[chat_id].append({"role": role, "content": content})

with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
        <div class="sb-brand-name">Smat Agent</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-new-wrap">', unsafe_allow_html=True)
    if st.button("＋ New Conversation", type="primary", use_container_width=True):
        new_id = str(uuid.uuid4())[:8]
        st.session_state.chats[new_id] = []
        st.session_state.current_chat = new_id
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.chats:
        st.markdown('<div class="sb-label">Conversations</div>', unsafe_allow_html=True)
        st.markdown('<div class="sb-threads">', unsafe_allow_html=True)

        for cid in list(st.session_state.chats.keys()):
            msgs = st.session_state.chats[cid]
            count = len(msgs) // 2
            is_active = st.session_state.current_chat == cid
            cls = "active" if is_active else ""

            user_msgs = [m for m in msgs if m["role"] == "user"]
            preview = "No messages yet"
            if user_msgs:
                raw = user_msgs[-1]["content"]
                preview = raw[:30] + ("…" if len(raw) > 30 else "")

            badge = ""
            if is_active:
                badge = '<span class="th-badge">Active</span>'

            container = st.container()
            with container:
                cols = st.columns([9, 3])
                with cols[0]:
                    if st.button(f"#{cid} {preview}", key=f"select_{cid}", help=f"Select conversation {cid}", use_container_width=True):
                        st.session_state.current_chat = cid
                        st.experimental_rerun()
                    st.markdown(f"""
                    <style>
                    button[key="select_{cid}"] {{
                        text-align: left;
                        font-family: 'DM Mono', monospace;
                        font-size: 0.85rem;
                        color: {'var(--accent-2)' if is_active else 'var(--text-primary)'};
                        background-color: {'rgba(124,106,247,0.09)' if is_active else 'transparent'};
                        border-radius: 11px;
                        padding: 10px 12px;
                        width: 100%;
                    }}
                    </style>
                    """, unsafe_allow_html=True)
                with cols[1]:
                    if st.button("×", key=f"delete_{cid}", help="Delete"):
                        del st.session_state.chats[cid]
                        if st.session_state.current_chat == cid:
                            st.session_state.current_chat = None
                        st.experimental_rerun()

        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="padding:1.5rem 0;text-align:center;color:var(--text-muted);font-size:0.85rem;">
            No conversations yet
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-footer-label">Documents</div>', unsafe_allow_html=True)
    st.file_uploader("Upload file", type=["pdf", "txt", "md"], key="doc_upload")

st.markdown("""
<div class="topbar">
  <div class="topbar-title">Smat Agent</div>
</div>
""", unsafe_allow_html=True)

if st.session_state.current_chat is None:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-title">Start a new conversation</div>
    </div>
    """, unsafe_allow_html=True)
else:
    chat_id = st.session_state.current_chat
    msgs = st.session_state.chats.get(chat_id, [])

    if not msgs:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-title">New conversation</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for message in msgs:
            if message["role"] == "user":
                st.chat_message("user").markdown(message["content"])
            else:
                st.chat_message("assistant").markdown(message["content"])

    user_input = st.chat_input("Type your message here...")

    if user_input:
        add_message(chat_id, "user", user_input)
        with st.chat_message("user"):
            st.markdown(user_input)
        reply = send_message(chat_id, user_input)
        add_message(chat_id, "assistant", reply)
        with st.chat_message("assistant"):
            st.markdown(reply)