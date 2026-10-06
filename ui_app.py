"""Streamlit Web UI for EasyPrompt Multi-Agent Pipeline."""

import time
import streamlit as st

from core.config import settings
from core.llm_clients import (
    BaseLLMClient,
    GeminiClient,
    GroqClient,
    DeepSeekClient,
    OpenRouterClient,
)
from domain.profiles import DOMAIN_PROFILES, get_domain_profile
from agents.factory import AgentFactory
from orchestrator.pipeline import AgentPipeline


def init_llm_client(provider: str, model_name: str, key_override: str = "") -> BaseLLMClient:
    """Instantiate the corresponding LLM client with fallback to settings."""
    if provider == "Gemini":
        api_key = key_override or settings.gemini_api_key
        return GeminiClient(api_key=api_key, model_name=model_name)
    elif provider == "Groq":
        api_key = key_override or settings.groq_api_key
        return GroqClient(api_key=api_key, model_name=model_name)
    elif provider == "DeepSeek":
        api_key = key_override or settings.deepseek_api_key
        return DeepSeekClient(api_key=api_key, model_name=model_name)
    elif provider == "OpenRouter":
        api_key = key_override or settings.openrouter_api_key
        return OpenRouterClient(api_key=api_key, model_name=model_name)
    raise ValueError(f"Unsupported provider: {provider}")


# Page configuration
st.set_page_config(
    page_title="EasyPrompt | Multi-Agent Orchestrator",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ EasyPrompt: Domain-Adaptive Pipeline")
st.caption(
    "Architecture: **PromptCrafter** (Analysis & Plan) ➔ "
    "**LogicVerifier** (Audit & Logic Critique) ➔ "
    "**Executor** (Final Synthesis)"
)

# ----------------- SIDEBAR CONFIGURATION -----------------
with st.sidebar:
    st.header("⚙️ Configuration")

    # Domain selection
    st.subheader("1. Select Domain")
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

    # Model providers per stage
    st.subheader("2. Stage Models")

    PROVIDERS = ["Gemini", "Groq", "DeepSeek", "OpenRouter"]
    DEFAULT_MODELS = {
        "Gemini": "gemini-2.5-flash",
        "Groq": "llama-3.3-70b-versatile",
        "DeepSeek": "deepseek-chat",
        "OpenRouter": "anthropic/claude-3.5-sonnet",
    }

    # PromptCrafter
    st.markdown("**Stage 1: PromptCrafter**")
    crafter_provider = st.selectbox("Provider", PROVIDERS, index=0, key="crafter_p")
    crafter_model = st.text_input(
        "Model Name", value=DEFAULT_MODELS[crafter_provider], key="crafter_m"
    )

    # LogicVerifier
    st.markdown("**Stage 2: LogicVerifier**")
    verifier_provider = st.selectbox("Provider", PROVIDERS, index=1, key="verifier_p")
    verifier_model = st.text_input(
        "Model Name", value=DEFAULT_MODELS[verifier_provider], key="verifier_m"
    )

    # Executor
    st.markdown("**Stage 3: Executor**")
    executor_provider = st.selectbox("Provider", PROVIDERS, index=0, key="executor_p")
    executor_model = st.text_input(
        "Model Name", value=DEFAULT_MODELS[executor_provider], key="executor_m"
    )

    st.divider()
    st.subheader("🔑 API Keys & Direct Links")

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


# ----------------- MAIN INTERFACE -----------------
col_main, col_stats = st.columns([3, 1])

with col_main:
    user_goal = st.text_area(
        "Enter your initial prompt or task requirement:",
        height=140,
        placeholder="e.g., Write a high-performance LRU Cache in Python with thread-safety and O(1) complexity.",
    )

start_button = st.button("🚀 Start Pipeline", type="primary", use_container_width=True)

if start_button:
    if not user_goal.strip():
        st.warning("Please provide a prompt or task before starting the pipeline.")
    else:
        try:
            # Instantiate clients
            crafter_client = init_llm_client(
                crafter_provider,
                crafter_model,
                override_gemini if crafter_provider == "Gemini" else (
                    override_groq if crafter_provider == "Groq" else (
                        override_deepseek if crafter_provider == "DeepSeek" else override_openrouter
                    )
                ),
            )

            verifier_client = init_llm_client(
                verifier_provider,
                verifier_model,
                override_gemini if verifier_provider == "Gemini" else (
                    override_groq if verifier_provider == "Groq" else (
                        override_deepseek if verifier_provider == "DeepSeek" else override_openrouter
                    )
                ),
            )

            executor_client = init_llm_client(
                executor_provider,
                executor_model,
                override_gemini if executor_provider == "Gemini" else (
                    override_groq if executor_provider == "Groq" else (
                        override_deepseek if executor_provider == "DeepSeek" else override_openrouter
                    )
                ),
            )

            # Build agents and pipeline
            crafter_agent, verifier_agent, executor_agent = AgentFactory.create_pipeline_agents(
                domain_profile=domain_profile,
                crafter_client=crafter_client,
                verifier_client=verifier_client,
                executor_client=executor_client,
            )

            pipeline = AgentPipeline(
                domain_key=selected_domain_key,
                crafter=crafter_agent,
                verifier=verifier_agent,
                executor=executor_agent,
            )

            st.divider()
            st.subheader("Progressive Pipeline Results")

            # Progressive UI Placeholders
            stage1_container = st.empty()
            stage2_container = st.empty()
            stage3_container = st.empty()

            progress_bar = st.progress(0, text="Starting pipeline...")

            # Run generator
            stage_gen = pipeline.run_stages(user_goal=user_goal)
            start_total = time.perf_counter()

            # Stage 1
            progress_bar.progress(15, text=f"Stage 1: PromptCrafter ({crafter_provider}) running...")
            stage1_name, crafter_res = next(stage_gen)
            with stage1_container.container():
                st.markdown(
                    f"### 📝 1. PromptCrafter Output "
                    f"`{crafter_res.execution_time_seconds:.2f}s`"
                )
                with st.expander("View Crafted Plan & Structured Specification", expanded=True):
                    st.markdown(crafter_res.content)

            # Stage 2
            progress_bar.progress(50, text=f"Stage 2: LogicVerifier ({verifier_provider}) running...")
            stage2_name, verifier_res = next(stage_gen)
            with stage2_container.container():
                st.markdown(
                    f"### 🔍 2. LogicVerifier Output "
                    f"`{verifier_res.execution_time_seconds:.2f}s`"
                )
                with st.expander("View Logic Audit & Criticisms", expanded=True):
                    st.markdown(verifier_res.content)

            # Stage 3
            progress_bar.progress(80, text=f"Stage 3: Executor ({executor_provider}) running...")
            stage3_name, executor_res = next(stage_gen)
            with stage3_container.container():
                st.markdown(
                    f"### 🎯 3. Final Execution Result "
                    f"`{executor_res.execution_time_seconds:.2f}s`"
                )
                st.markdown(executor_res.content)

            total_time = time.perf_counter() - start_total
            progress_bar.progress(100, text=f"Pipeline complete in {total_time:.2f}s! ✅")
            st.success(f"Pipeline finished successfully in {total_time:.2f}s")

        except Exception as ex:
            st.error(f"Pipeline Execution Error: {ex}")
