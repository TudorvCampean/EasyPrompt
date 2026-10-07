"""Streamlit Web UI for EasyPrompt Multi-Agent Pipeline with OmniRoute Auto-Fallback."""

import time
from typing import Dict, List
import streamlit as st

from core.config import settings
from core.router import RouterClient
from core.combos import ROUTING_PROFILES, get_routing_profile, list_routing_profiles
from domain.profiles import DOMAIN_PROFILES, get_domain_profile
from agents.factory import AgentFactory
from orchestrator.pipeline import AgentPipeline


# Page configuration
st.set_page_config(
    page_title="EasyPrompt | Multi-Agent Orchestrator",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ EasyPrompt: Domain-Adaptive Pipeline")
st.caption(
    "OmniRoute Gateway: **Auto-Fallback** ➔ **Provider Agnosticism** ➔ **Unified Protocol** | "
    "Stages: **PromptCrafter** ➔ **LogicVerifier** ➔ **Executor**"
)

# ----------------- SIDEBAR CONFIGURATION -----------------
with st.sidebar:
    st.header("⚙️ Configuration")

    # 1. Domain selection
    st.subheader("1. 🎯 Select Domain")
    domain_options = list(DOMAIN_PROFILES.keys())
    domain_format = {k: f"{v.display_name} ({k})" for k, v in DOMAIN_PROFILES.items()}
    selected_domain_key = st.selectbox(
        "Domain Profile",
        options=domain_options,
        format_func=lambda x: domain_format[x],
        index=0,
    )
    domain_profile = get_domain_profile(selected_domain_key)
    st.info(domain_profile.description)

    st.divider()

    # 2. Routing Combo (OmniRoute Auto-Fallback)
    st.subheader("2. 🔀 Routing Combo (Auto-Fallback)")
    combos = list_routing_profiles()
    combo_ids = [c.id for c in combos]
    combo_labels = {c.id: f"{c.icon} {c.name}" for c in combos}

    # Intelligent default based on selected domain
    default_combo_idx = 0
    if selected_domain_key == "coding":
        default_combo_idx = combo_ids.index("coding_pro") if "coding_pro" in combo_ids else 0
    elif selected_domain_key == "math":
        default_combo_idx = combo_ids.index("deep_reasoning") if "deep_reasoning" in combo_ids else 0
    else:
        default_combo_idx = combo_ids.index("balanced") if "balanced" in combo_ids else 0

    selected_combo_id = st.selectbox(
        "Routing Preset",
        options=combo_ids,
        format_func=lambda x: combo_labels[x],
        index=default_combo_idx,
        help="OmniRoute automatically tries the primary model and falls back to alternatives upon 429/404/5xx errors.",
    )
    routing_profile = get_routing_profile(selected_combo_id)
    st.markdown(f"*{routing_profile.description}*")

    with st.expander("🔍 View Fallback Chains", expanded=False):
        st.markdown(f"**Crafter Chain:** `{' ➔ '.join(routing_profile.crafter_chain)}`")
        st.markdown(f"**Verifier Chain:** `{' ➔ '.join(routing_profile.verifier_chain)}`")
        st.markdown(f"**Executor Chain:** `{' ➔ '.join(routing_profile.executor_chain)}`")

    st.divider()

    # 3. API Keys & Portal Links
    st.subheader("3. 🔑 API Keys & Provider Status")

    # Gemini
    override_gemini = st.text_input(
        "Google Gemini API Key",
        value=settings.gemini_api_key,
        type="password",
        placeholder="AIzaSy...",
    )
    st.link_button(
        "🔗 Obține Cheie Gratuită Gemini (AI Studio)",
        "https://aistudio.google.com/app/apikey",
        use_container_width=True,
    )

    # Groq
    override_groq = st.text_input(
        "Groq API Key",
        value=settings.groq_api_key,
        type="password",
        placeholder="gsk_...",
    )
    st.link_button(
        "🔗 Obține Cheie Gratuită Groq (Console)",
        "https://console.groq.com/keys",
        use_container_width=True,
    )

    # DeepSeek
    override_deepseek = st.text_input(
        "DeepSeek API Key",
        value=settings.deepseek_api_key,
        type="password",
        placeholder="sk-...",
    )
    st.link_button(
        "🔗 Obține Cheie DeepSeek (Platform)",
        "https://platform.deepseek.com/api_keys",
        use_container_width=True,
    )

    # OpenRouter
    override_openrouter = st.text_input(
        "OpenRouter API Key",
        value=settings.openrouter_api_key,
        type="password",
        placeholder="sk-or-v1-...",
    )
    st.link_button(
        "🔗 Obține Cheie OpenRouter (Free tier)",
        "https://openrouter.ai/settings/keys",
        use_container_width=True,
    )

    # Active status indicator
    active_keys = []
    if override_gemini:
        active_keys.append("Gemini")
    if override_groq:
        active_keys.append("Groq")
    if override_deepseek:
        active_keys.append("DeepSeek")
    if override_openrouter:
        active_keys.append("OpenRouter")

    if active_keys:
        st.success(f"Active Providers: {', '.join(active_keys)}")
    else:
        st.warning("No API keys detected! Please enter at least one key.")


# ----------------- MAIN INTERFACE -----------------
col_main, col_info = st.columns([3, 1])

with col_main:
    user_goal = st.text_area(
        "Enter your initial prompt or task requirement:",
        height=140,
        placeholder="e.g., Write a high-performance LRU Cache in Python with thread-safety and O(1) complexity.",
    )

with col_info:
    st.markdown("### 🛡️ Resilience Status")
    st.markdown(f"**Domain:** `{domain_profile.display_name}`")
    st.markdown(f"**Combo:** `{routing_profile.name}`")
    st.markdown("**Failover:** `Active (Auto-Fallback enabled)`")

start_button = st.button("🚀 Start Pipeline", type="primary", use_container_width=True)

if start_button:
    if not user_goal.strip():
        st.warning("Please provide a prompt or task before starting the pipeline.")
    elif not active_keys:
        st.error("Cannot start: No API keys configured. Please add at least one key in the sidebar.")
    else:
        try:
            # Build unified RouterClient
            api_keys: Dict[str, str] = {
                "gemini": override_gemini,
                "groq": override_groq,
                "deepseek": override_deepseek,
                "openrouter": override_openrouter,
            }
            router = RouterClient(api_keys=api_keys)

            # Factory generates domain-specific agents with routing fallback chains
            crafter_agent, verifier_agent, executor_agent = AgentFactory.create_pipeline_agents(
                domain_profile=domain_profile,
                router=router,
                routing_profile=routing_profile,
            )

            pipeline = AgentPipeline(
                domain_key=selected_domain_key,
                routing_profile_id=routing_profile.id,
                crafter=crafter_agent,
                verifier=verifier_agent,
                executor=executor_agent,
            )

            st.divider()
            st.subheader(f"Pipeline Execution ({routing_profile.name})")

            # Progressive UI Placeholders
            stage1_container = st.empty()
            stage2_container = st.empty()
            stage3_container = st.empty()

            progress_bar = st.progress(0, text="Initializing OmniRoute gateway...")

            # Run generator
            stage_gen = pipeline.run_stages(user_goal=user_goal)
            start_total = time.perf_counter()

            # Stage 1: PromptCrafter
            progress_bar.progress(15, text="Stage 1: PromptCrafter running...")
            stage1_name, crafter_res = next(stage_gen)
            with stage1_container.container():
                header_col1, header_col2 = st.columns([3, 1])
                with header_col1:
                    st.markdown(f"### 📝 1. PromptCrafter Output")
                with header_col2:
                    st.caption(f"⏱️ `{crafter_res.execution_time_seconds:.2f}s` | Model: `{crafter_res.provider_used}/{crafter_res.model_used}`")

                if crafter_res.was_fallback:
                    st.warning(
                        f"⚠️ **Auto-fallback activated!** Model used: `{crafter_res.provider_used}/{crafter_res.model_used}`. "
                        f"Skipped: {', '.join(crafter_res.fallback_history)}"
                    )
                else:
                    st.success(f"✅ Primary model responded: `{crafter_res.provider_used}/{crafter_res.model_used}`")

                with st.expander("View Crafted Plan & Structured Specification", expanded=True):
                    st.markdown(crafter_res.content)

            # Stage 2: LogicVerifier
            progress_bar.progress(50, text="Stage 2: LogicVerifier running...")
            stage2_name, verifier_res = next(stage_gen)
            with stage2_container.container():
                header_col1, header_col2 = st.columns([3, 1])
                with header_col1:
                    st.markdown(f"### 🔍 2. LogicVerifier Output")
                with header_col2:
                    st.caption(f"⏱️ `{verifier_res.execution_time_seconds:.2f}s` | Model: `{verifier_res.provider_used}/{verifier_res.model_used}`")

                if verifier_res.was_fallback:
                    st.warning(
                        f"⚠️ **Auto-fallback activated!** Model used: `{verifier_res.provider_used}/{verifier_res.model_used}`. "
                        f"Skipped: {', '.join(verifier_res.fallback_history)}"
                    )
                else:
                    st.success(f"✅ Primary model responded: `{verifier_res.provider_used}/{verifier_res.model_used}`")

                with st.expander("View Logic Audit & Criticisms", expanded=True):
                    st.markdown(verifier_res.content)

            # Stage 3: Executor
            progress_bar.progress(80, text="Stage 3: Executor running...")
            stage3_name, executor_res = next(stage_gen)
            with stage3_container.container():
                header_col1, header_col2 = st.columns([3, 1])
                with header_col1:
                    st.markdown(f"### 🎯 3. Final Execution Result")
                with header_col2:
                    st.caption(f"⏱️ `{executor_res.execution_time_seconds:.2f}s` | Model: `{executor_res.provider_used}/{executor_res.model_used}`")

                if executor_res.was_fallback:
                    st.warning(
                        f"⚠️ **Auto-fallback activated!** Model used: `{executor_res.provider_used}/{executor_res.model_used}`. "
                        f"Skipped: {', '.join(executor_res.fallback_history)}"
                    )
                else:
                    st.success(f"✅ Primary model responded: `{executor_res.provider_used}/{executor_res.model_used}`")

                st.markdown(executor_res.content)

            total_time = time.perf_counter() - start_total
            progress_bar.progress(100, text=f"Pipeline complete in {total_time:.2f}s! ✅")
            st.success(f"🎉 Pipeline finished successfully in {total_time:.2f}s with OmniRoute auto-fallback!")

        except Exception as ex:
            st.error(f"❌ Pipeline Execution Error: {ex}")
