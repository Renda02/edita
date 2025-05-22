import streamlit as st
import os
import asyncio
import json
from edita.agents.agent import Agent
from edita.agents.runner import Runner
from edita.agents.file_search import FileSearchTool
from dotenv import load_dotenv

def load_prompts():
    try:
        with open('prompts.json', 'r', encoding='utf-8') as file:
            prompts = json.load(file)
        return prompts
    except Exception as e:
        st.error(f"❌ Failed to load prompts.json: {e}")
        return {}

load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
vector_store_id = os.getenv("vector_store_id")
if not OPENAI_API_KEY or not vector_store_id:
    st.error("❌ Missing environment variables: OPENAI_API_KEY or vector_store_id")
    st.stop()

PROMPTS = load_prompts()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "editing_mode" not in st.session_state:
    st.session_state.editing_mode = "comprehensive"
if "content_type" not in st.session_state:
    st.session_state.content_type = "general"

EDITING_MODES = {
    "comprehensive": "Full Analysis & Editing",
    "quick_fix": "Quick Problem Detection",
    "specific_issue": "Target Specific Issues",
    "newsletter": "Newsletter Optimization",
    "social_media": "Social Media Posts"
}

EDITING_FOCUS = {
    "filler_removal": "Remove Filler Text",
    "add_outcomes": "Add Specific Outcomes", 
    "power_language": "Add Power Language",
    "visualization": "Strengthen Visualization",
    "redundancy": "Fix Redundancy",
    "parallelism": "Fix Parallelism",
    "add_context": "Add Missing Context",
    "passive_voice": "Address Passive Voice",
    "takeaways": "Add Compelling Takeaways",
    "vague_language": "Fix Vague Language"
}

def create_content_editor():
    if not PROMPTS:
        st.error("❌ No prompts loaded. Check prompts.json")
        return None

    file_search_tool = FileSearchTool(
        max_num_results=5,
        vector_store_ids=[vector_store_id],
    )

    base = PROMPTS.get("base_instructions", "")
    mode_specific = PROMPTS.get("mode_instructions", {}).get(st.session_state.editing_mode, "")
    if not base or not mode_specific:
        st.warning("⚠️ Missing instructions in prompts.json")
    instructions = base + "\n\n**Mode-Specific Focus:**\n" + mode_specific

    return Agent(
        name="ContentFlow Editor",
        instructions=instructions,
        tools=[file_search_tool],
    )

async def get_editing_response(content, context):
    editor = create_content_editor()
    if not editor:
        return "❌ Unable to create editor."

    focus_text = ""
    if st.session_state.editing_mode == "specific_issue":
        focus_areas = [EDITING_FOCUS[area] for area in context.get("focus_areas", [])]
        focus_text = f"Focus specifically on these areas: {', '.join(focus_areas)}"

    template = PROMPTS.get("analysis_prompt", "Please analyze and improve this content:\n\n{content}")
    try:
        prompt = template.format(
            content_type=st.session_state.content_type,
            editing_mode=EDITING_MODES[st.session_state.editing_mode],
            focus_text=focus_text,
            content=content
        )
    except KeyError as e:
        prompt = f"Analyze and improve:\n\n{content}"
        st.warning(f"⚠️ Missing variable in prompt template: {e}")

    result = await Runner.run(editor, prompt)
    return result.final_output

st.set_page_config(page_title="ContentFlow - AI Content Editor", layout="wide", page_icon="✍️")
st.title("✍️ ContentFlow")
st.markdown("**AI-Powered Content Editor** | Transform your writing with professional editing principles")

st.sidebar.title("⚙️ Editing Settings")
if st.sidebar.button("🔄 Reload Prompts"):
    PROMPTS = load_prompts()
    if PROMPTS:
        st.sidebar.success("✅ Prompts reloaded")
    else:
        st.sidebar.error("❌ Reload failed")

with st.sidebar.expander("📋 Loaded Prompts Info"):
    if PROMPTS:
        st.write("**Sections:**")
        for key in PROMPTS:
            st.write(f"• {key}")
        if "mode_instructions" in PROMPTS:
            st.write("**Modes:**")
            for mode in PROMPTS["mode_instructions"]:
                st.write(f"• {mode}")
    else:
        st.write("⚠️ No prompts loaded")

st.session_state.editing_mode = st.sidebar.selectbox(
    "Choose editing mode:",
    options=list(EDITING_MODES.keys()),
    format_func=lambda x: EDITING_MODES[x],
    index=list(EDITING_MODES).index(st.session_state.editing_mode)
)

st.session_state.content_type = st.sidebar.selectbox(
    "Select content type:",
    ["general", "blog_post", "newsletter", "social_media", "email", "landing_page", "ad_copy"],
    index=0
)

focus_areas = []
if st.session_state.editing_mode == "specific_issue":
    st.sidebar.subheader("Focus Areas")
    for key, label in EDITING_FOCUS.items():
        if st.sidebar.checkbox(label, key=f"focus_{key}"):
            focus_areas.append(key)

if st.sidebar.button("Clear History"):
    st.session_state.messages = []
    st.rerun()

with st.sidebar.expander("💡 How to Use"):
    st.markdown("""
    **1. Select Mode**  
    **2. Paste Content**  
    **3. Get Edits**
    """)

with st.sidebar.expander("🎯 Editing Principles"):
    st.markdown("""
    - ✂️ Remove Filler
    - 💪 Add Power
    - 🧠 Add Context
    - 🔄 Fix Redundancy
    - ⚖️ Ensure Parallelism
    - 🔍 Improve Precision
    """)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Your Content")
    content_input = st.text_area(
        "Paste your content:",
        height=400,
        placeholder="Enter blog post, email, social media content, etc...",
        key="content_input"
    )
    if st.button("✍️ Edit My Content", type="primary", disabled=not content_input.strip()):
        editing_context = {
            "mode": st.session_state.editing_mode,
            "content_type": st.session_state.content_type,
            "focus_areas": focus_areas
        }
        st.session_state.messages.append({"role": "user", "content": content_input, "context": editing_context})

with col2:
    st.subheader("🚀 ContentFlow Analysis")
    if st.session_state.messages:
        latest = st.session_state.messages[-1]
        if latest["role"] == "user":
            with st.spinner("🔍 Analyzing..."):
                try:
                    response = asyncio.run(get_editing_response(latest["content"], latest.get("context", {})))
                except RuntimeError:
                    response = asyncio.get_event_loop().run_until_complete(get_editing_response(latest["content"], latest.get("context", {})))
                st.session_state.messages.append({"role": "assistant", "content": response})
        if len(st.session_state.messages) > 1 and st.session_state.messages[-1]["role"] == "assistant":
            st.markdown(st.session_state.messages[-1]["content"])
    else:
        st.info("👈 Paste your content and click 'Edit My Content'")

if len(st.session_state.messages) > 2:
    st.markdown("---")
    st.subheader("📚 History")
    for i in range(0, len(st.session_state.messages)-2, 2):
        with st.expander(f"Session {(i//2)+1}"):
            st.markdown("**Original:**")
            st.text_area("", value=st.session_state.messages[i]["content"], height=100, key=f"orig_{i}", disabled=True)
            st.markdown("**Edited:**")
            st.markdown(st.session_state.messages[i+1]["content"])

st.markdown("---")
st.markdown("*ContentFlow applies editorial principles to help you write with clarity, impact, and confidence.*")
