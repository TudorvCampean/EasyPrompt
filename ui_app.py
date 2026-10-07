"""Streamlit Web UI for EasyPrompt Multi-Agent Pipeline with Auto-Fallback Gateway."""

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
    page_title="EasyPrompt",
    layout="wide",
)

st.title("EasyPrompt")
st.caption("Domain-Adaptive Multi-Agent Pipeline with Auto-Fallback Gateway")

# ----------------- SIDEBAR CONFIGURATION -----------------
with st.sidebar:
    st.header("Configuration")

    # 1. Domain Selection
    st.subheader("Domain")
    domain_options = list(DOMAIN_PROFILES.keys())
    domain_format = {k: v.display_name for k, v in DOMAIN_PROFILES.items()}
    selected_domain_key = st.selectbox(
        "Domain Profile",
        options=domain_options,
        format_func=lambda x: domain_format[x],
        index=0,
    )
    domain_profile = get_domain_profile(selected_domain_key)
    st.caption(domain_profile.description)

    st.divider()

    # 2. Routing Combo
    st.subheader("Routing Combo")
    combos = list_routing_profiles()
    combo_ids = [c.id for c in combos]
    combo_labels = {c.id: c.name for c in combos}

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
    )
    routing_profile = get_routing_profile(selected_combo_id)
    st.caption(routing_profile.description)

    with st.expander("Fallback Chains", expanded=False):
        st.markdown(f"**Crafter:** `{' → '.join(routing_profile.crafter_chain)}`")
        st.markdown(f"**Verifier:** `{' → '.join(routing_profile.verifier_chain)}`")
        st.markdown(f"**Executor:** `{' → '.join(routing_profile.executor_chain)}`")

    st.divider()

    # 3. API Keys Configuration
    st.subheader("API Keys")

    # Gemini
    override_gemini = st.text_input(
        "Google Gemini Key",
        value=settings.gemini_api_key,
        type="password",
        placeholder="AIzaSy...",
    )
    st.markdown(
        "<small><a href='https://aistudio.google.com/app/apikey' target='_blank'>Get Gemini Key</a></small>",
        unsafe_allow_html=True,
    )

    # Groq
    override_groq = st.text_input(
        "Groq Key",
        value=settings.groq_api_key,
        type="password",
        placeholder="gsk_...",
    )
    st.markdown(
        "<small><a href='https://console.groq.com/keys' target='_blank'>Get Groq Key</a></small>",
        unsafe_allow_html=True,
    )

    # DeepSeek
    override_deepseek = st.text_input(
        "DeepSeek Key",
        value=settings.deepseek_api_key,
        type="password",
        placeholder="sk-...",
    )
    st.markdown(
        "<small><a href='https://platform.deepseek.com/api_keys' target='_blank'>Get DeepSeek Key</a></small>",
        unsafe_allow_html=True,
    )

    # OpenRouter
    override_openrouter = st.text_input(
        "OpenRouter Key",
        value=settings.openrouter_api_key,
        type="password",
        placeholder="sk-or-v1-...",
    )
    st.markdown(
        "<small><a href='https://openrouter.ai/settings/keys' target='_blank'>Get OpenRouter Key</a></small>",
        unsafe_allow_html=True,
    )

    # Status check
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
        st.caption(f"Active providers: {', '.join(active_keys)}")
    else:
        st.caption("No API keys detected.")


# ----------------- MAIN INTERFACE -----------------
user_goal = st.text_area(
    "Prompt / Task Requirement",
    height=130,
    placeholder="Describe your request or task...",
)

start_button = st.button("Start Pipeline", type="primary", use_container_width=True)

if start_button:
    if not user_goal.strip():
        st.warning("Please provide a prompt or task requirement.")
    elif not active_keys:
        st.error("No API keys configured. Please configure at least one key in the sidebar.")
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

            # Progressive UI Placeholders
            stage1_container = st.empty()
            stage2_container = st.empty()
            stage3_container = st.empty()

            progress_bar = st.progress(0, text="Initializing gateway...")

            # Run generator
            stage_gen = pipeline.run_stages(user_goal=user_goal)
            start_total = time.perf_counter()

            # Stage 1: PromptCrafter
            progress_bar.progress(15, text="Running Stage 1: PromptCrafter...")
            stage1_name, crafter_res = next(stage_gen)
            with stage1_container.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader("1. PromptCrafter")
                with col2:
                    st.caption(f"{crafter_res.execution_time_seconds:.2f}s | {crafter_res.provider_used}/{crafter_res.model_used}")

                if crafter_res.was_fallback:
                    st.info(
                        f"Auto-fallback active: {crafter_res.provider_used}/{crafter_res.model_used} "
                        f"(skipped: {', '.join(crafter_res.fallback_history)})"
                    )

                with st.expander("Crafted Plan & Specification", expanded=True):
                    st.markdown(crafter_res.content)

            # Stage 2: LogicVerifier
            progress_bar.progress(50, text="Running Stage 2: LogicVerifier...")
            stage2_name, verifier_res = next(stage_gen)
            with stage2_container.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader("2. LogicVerifier")
                with col2:
                    st.caption(f"{verifier_res.execution_time_seconds:.2f}s | {verifier_res.provider_used}/{verifier_res.model_used}")

                if verifier_res.was_fallback:
                    st.info(
                        f"Auto-fallback active: {verifier_res.provider_used}/{verifier_res.model_used} "
                        f"(skipped: {', '.join(verifier_res.fallback_history)})"
                    )

                with st.expander("Logic Audit & Criticisms", expanded=True):
                    st.markdown(verifier_res.content)

            # Stage 3: Executor
            progress_bar.progress(80, text="Running Stage 3: Executor...")
            stage3_name, executor_res = next(stage_gen)
            with stage3_container.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader("3. Final Execution Result")
                with col2:
                    st.caption(f"{executor_res.execution_time_seconds:.2f}s | {executor_res.provider_used}/{executor_res.model_used}")

                if executor_res.was_fallback:
                    st.info(
                        f"Auto-fallback active: {executor_res.provider_used}/{executor_res.model_used} "
                        f"(skipped: {', '.join(executor_res.fallback_history)})"
                    )

                st.markdown(executor_res.content)

            total_time = time.perf_counter() - start_total
            progress_bar.progress(100, text=f"Pipeline finished in {total_time:.2f}s")
            st.success(f"Pipeline completed successfully in {total_time:.2f}s")

        except Exception as ex:
            st.error(f"Execution Error: {ex}")
