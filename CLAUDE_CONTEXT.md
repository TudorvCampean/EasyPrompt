# 🧠 EasyPrompt — Context & Architecture Handover Briefing (for Claude / Developers)

Acest document conține sinteza completă a stării proiectului **EasyPrompt**, structura de module, protocolul de rutare și modul de rulare. Permite oricărui agent (ex: Claude Sonnet) să preia contextul instantaneu, fără a re-analiza întregul repository.

---

## 1. Misiunea Proiectului
**EasyPrompt** este un orchestrator multi-agent de tip pipeline adaptabil la domenii de lucru:
$$\text{User Query} \xrightarrow{} \text{PromptCrafter (Plan)} \xrightarrow{} \text{LogicVerifier (Critic/Audit)} \xrightarrow{} \text{Executor (Soluție Finală)}$$

Inspirat din **OmniRoute**, nivelul de infrastructură folosește acum un **Gateway Unificat cu Auto-Fallback**:
- **Unified Protocol**: Toți providerii (Gemini, Groq, DeepSeek, OpenRouter) sunt accesați prin SDK-ul oficial `openai` cu `base_url` personalizat.
- **Auto-Fallback & Resilience**: Dacă un model eșuează (`429 Rate Limit`, `404 Not Found`, `402 Insufficient Balance`, `5xx`), routerul comută instant pe modelul următor din lanț fără a crăpa pipeline-ul.
- **Provider Agnostic (Combos)**: Utilizatorul alege un preset de rutare (ex: *Best for Coding*, *Ultra Fast*, *Free Tier Optimized*), iar routerul gestionează modelele sub capotă.

---

## 2. Structura Proiectului & Modulelor

```text
EasyPrompt/
├── core/
│   ├── config.py         # Setări globale, încărcare .env
│   ├── router.py         # RouterClient: Gateway unificat OpenAI-compatibil cu buclă de auto-fallback
│   ├── combos.py         # RoutingProfile & preseturi (coding_pro, fast_throughput, free_tier, etc.)
│   └── llm_clients.py    # (Legacy) Implementări de clienți per SDK
├── domain/
│   ├── profiles.py       # DomainProfile (coding, math, creative_writing, general)
│   └── prompts/          # Șabloane opționale de prompt
├── agents/
│   ├── base_agent.py     # BaseAgent & AgentResponse (include metadate de fallback)
│   ├── prompt_crafter.py # PromptCrafter (Agent 1)
│   ├── logic_verifier.py # LogicVerifier (Agent 2)
│   ├── executor.py       # Executor (Agent 3)
│   └── factory.py        # AgentFactory (instanțiază agenții injectând RouterClient & Combo)
├── orchestrator/
│   └── pipeline.py       # AgentPipeline (execuție secvențială CLI & generator run_stages pentru UI)
├── ui_app.py             # Interfață Web Streamlit (Sidebar cu combos, chei API și badge-uri de fallback)
├── main.py               # Interfață CLI cu rich formatting
├── OMNIROUTE_INTEGRATION_PLAN.md # Planul arhitectural complet
├── requirements.txt      # Dependențele Python
└── .env                  # Cheile API (ignorat în git)
```

---

## 3. Chei API & Provideri Suportați

| Provider | Base URL | Model Exempar | Note |
|---|---|---|---|
| **Gemini** | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-3.8-flash` | Suportă protocol OpenAI nativ |
| **Groq** | `https://api.groq.com/openai/v1` | `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b` | Viteză LPU foarte mare |
| **DeepSeek** | `https://api.deepseek.com` | `deepseek-chat`, `deepseek-reasoner` | Necesită balanță activă |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `meta-llama/llama-3.3-70b-instruct:free` | Agregator multi-model |

---

## 4. Rulare & Testare

### Activare Mediu Virtual
```bash
source .venv/bin/activate
```

### Pornire Interfață Web Streamlit
```bash
.venv/bin/streamlit run ui_app.py
```

### Pornire CLI
```bash
.venv/bin/python main.py
```

### Testare Auto-Fallback
```bash
.venv/bin/python -c "
from core.config import settings
from core.router import RouterClient

router = RouterClient(api_keys={
    'gemini': settings.gemini_api_key,
    'groq': settings.groq_api_key,
    'deepseek': settings.deepseek_api_key,
})
chain = ['deepseek/deepseek-chat', 'groq/invalid-model', 'groq/openai/gpt-oss-120b']
res = router.complete(messages=[{'role': 'user', 'content': 'Test'}], model_chain=chain)
print('Success via fallback:', res.model_used, 'Fallback?:', res.was_fallback)
"
```
