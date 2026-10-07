# 🚀 EasyPrompt: Plan de Integrare a Arhitecturii OmniRoute

Acest document reprezintă planul tehnic detaliat pentru refactorizarea nivelului de infrastructură și LLM din **EasyPrompt**, inspirat din arhitectura gateway-ului open-source **[OmniRoute](https://github.com/diegosouzapw/OmniRoute)**.

Planul este redactat pentru a fi citit și executat de un agent AI (ex: Claude) sau de către echipa de dezvoltare înainte de implementarea codului.

---

## 1. Viziunea și Obiectivele Refactorizării

În arhitectura curentă, fiecare agent (`PromptCrafter`, `LogicVerifier`, `Executor`) folosește clienți independenți cu SDK-uri specifice (`google-genai`, `groq`, `httpx`). Dacă un model generează o eroare (ex. `404 Not Found` pentru modele retrase, `429 Rate Limit` sau `503 Service Unavailable`), întregul pipeline se oprește și UI-ul Streamlit crapă.

Împrumutând principiile cheie din **OmniRoute**, transformăm infrastructura EasyPrompt într-un **Gateway Multi-Provider cu Auto-Fallback și Rutare Agnostică**.

### Cele 3 Principii Fundamentale de Adoptat:
1. **Unified Endpoint Protocol**: Toți agenții comunică cu un singur `RouterClient` prin formatul universal standardizat OpenAI (`messages: [{"role": "...", "content": "..."}]`), eliminând cuplarea strânsă de SDK-uri proprietare.
2. **Auto-Fallback System**: Orice apel de model este configurat ca un lanț (Chain) sau Combo de rezervă. La erori de tip `429`, `404`, `5xx` sau `Timeout`, routerul comută instant pe modelul următor din lanț, fără ca pipeline-ul sau utilizatorul să sufere întreruperi.
3. **Provider Agnosticism & Routing Combos**: Interfața UI nu mai obligă utilizatorul să aleagă manual provideri tehnici la fiecare pas, ci oferă **Profiluri / Combos de Rutare** de nivel înalt (ex: *Best for Coding*, *Fastest / High-Throughput*, *Free Tier Optimized*, *Cost-Efficient*), iar Routerul alege și gestionează modelele sub capotă folosind cheile din `.env`.

---

## 2. Diagrama de Arhitectură Comparativă

### Înainte (Cuplare directă și fragilitate):
```
[Agent] ──> [GeminiClient (SDK)] ──> Google API (Dacă dă 404/429 ➔ Crash!)
[Agent] ──> [GroqClient (SDK)]   ──> Groq API   (Dacă dă 429 ➔ Crash!)
```

### După (Arhitectura inspirată din OmniRoute):
```
[PromptCrafter / LogicVerifier / Executor]
                    │
                    ▼ (Format standardizat role/content)
            ┌─────────────────┐
            │  RouterClient   │ (Unified Gateway)
            └────────┬────────┘
                     │
         ┌───────────┴───────────┐
         │ Combo: "Best for Coding"│
         └───────────┬───────────┘
                     │
    1. Primar: Claude 3.5 Sonnet / DeepSeek Reasoner
       ├─► [Succes] ──► Răspuns livrat
       └─► [Eroare: 429 / 404 / 5xx]
             │
    2. Fallback 1: Gemini 3.8 Flash
       ├─► [Succes] ──► Răspuns livrat (Log Failover)
       └─► [Eroare]
             │
    3. Fallback 2: Groq Llama 3.3 70B
       └─► [Succes Garantat]
```

---

## 3. Detalierea Celor 3 Componente Majore

### Componenta 1: Unified Endpoint Protocol (`RouterClient`)
- **Format Unic:** Implementarea clasei `RouterClient` care expune o singură metodă principală:
  ```python
  def complete(self, messages: list[dict], model: str, temperature: float = 0.7, fallback_chain: list[str] = None) -> CompletionResponse:
  ```
- **Drivere Unificate (HTTP-First):**
  - Fiecare furnizor (`google`, `groq`, `deepseek`, `openrouter`) este reprezentat ca un adaptor HTTP simplu (fie prin `httpx`, fie prin clientul standardizat `openai` configurat cu `base_url` diferit).
  - Elimină necesitatea importării a 4 SDK-uri diferite în logica agenților.
- **Model Addressing:** Identificarea modelelor printr-un identificator clar, de tipul:
  - `gemini/gemini-3.8-flash`
  - `groq/llama-3.3-70b-versatile`
  - `deepseek/deepseek-chat`
  - `openrouter/anthropic/claude-3.5-sonnet`

### Componenta 2: Auto-Fallback & Circuit Breaker System
- **Clasificare Erori Tranzitorii:**
  - `RateLimitError` (`429`)
  - `ModelNotFoundError` / `ModelDeprecated` (`404`)
  - `ServerError` (`500`, `502`, `503`, `504`)
  - `TimeoutError`
- **Mecanismul de Failover:**
  - Când `RouterClient.complete()` este apelat pentru un profil, acesta primește o listă ordonată de modele `[Primary, Fallback1, Fallback2]`.
  - Routerul încearcă `Primary`. Dacă aruncă o eroare tranzitorie, înregistrează un avertisment în telemetrie/log și încearcă imediat `Fallback1`.
  - În `CompletionResponse`, se returnează metadate despre ruta executată:
    ```python
    class CompletionResponse(BaseModel):
        content: str
        model_used: str
        provider_used: str
        was_fallback: bool
        fallback_history: list[str] = []
        latency_seconds: float
    ```
- **Rezultat în UI:** Utilizatorul vede un badge mic de informare: `⚠️ Primary rate-limited. Auto-switched to gemini-3.8-flash (0.4s)`. Zero erori afișate, zero blocaje.

### Componenta 3: Provider Agnosticism & Routing Combos
Definirea unui modul `core/combos.py` care grupează modelele în strategii clare:
- **`coding_pro` ("Best for Coding"):**
  - Primary: `openrouter/anthropic/claude-3.5-sonnet` sau `deepseek/deepseek-chat`
  - Fallback 1: `gemini/gemini-3.8-flash`
  - Fallback 2: `groq/llama-3.3-70b-versatile`
- **`fast_throughput` ("Ultra Fast / Low Latency"):**
  - Primary: `groq/llama-3.3-70b-versatile` (Groq LPU hardware)
  - Fallback 1: `gemini/gemini-3.8-flash`
  - Fallback 2: `deepseek/deepseek-chat`
- **`free_tier` ("100% Free Tier Optimized"):**
  - Primary: `groq/llama-3.3-70b-versatile` (Free API)
  - Fallback 1: `gemini/gemini-3.8-flash` (Google AI Studio Free)
  - Fallback 2: `openrouter/meta-llama/llama-3.3-70b-instruct:free`
- **`balanced` ("Balanced Reasoning"):**
  - Primary: `gemini/gemini-3.8-flash`
  - Fallback 1: `groq/llama-3.3-70b-versatile`
  - Fallback 2: `deepseek/deepseek-chat`

În Streamlit UI, utilizatorul alege doar:
1. **Domeniul** (`Software Engineering`, `Mathematics`, `Creative Writing`, etc.)
2. **Preset-ul de Rulare** (`Best for Coding`, `Fastest`, `Free Tier Optimized`)
*(Opțional, un tab 'Advanced / Custom Combo' pentru utilizatorii avansați care vor să aleagă modele specifice).*

---

## 4. Plan de Implementare Pas cu Pas (Faza de Execuție)

### Pasul 1: `core/router.py` (Nucleul Gateway-ului)
- Crearea claselor:
  - `ProviderAdapter` (Interfață cu `send_chat_completion(messages, model, temperature)`)
  - `GeminiAdapter`, `GroqAdapter`, `DeepSeekAdapter`, `OpenRouterAdapter`
  - `RouterClient`: implementează bucla de auto-fallback, detectarea cheilor active și maparea numelor de modele.

### Pasul 2: `core/combos.py` (Definirea Preset-urilor)
- Crearea modelelor de date pentru Combos:
  ```python
  class RoutingProfile(BaseModel):
      id: str
      name: str
      description: str
      crafter_chain: list[str]
      verifier_chain: list[str]
      executor_chain: list[str]
  ```
- Maparea preset-urilor standard și a mecanismului de filtrare dinamică (dacă o cheie lipsește din `.env`, routerul exclude automat providerul respectiv din lanț fără eroare).

### Pasul 3: Actualizarea Agenților (`agents/`)
- Simplificarea clasei `BaseAgent` din [agents/base_agent.py](file:///home/tudor/Python/EasyPrompt/agents/base_agent.py):
  - Agentul primește doar instanța unică `RouterClient` și lanțul de modele aferent rolului său.
  - Agenții nu mai au cunoștință despre Gemini vs Groq, ci doar trimit promptul către router.

### Pasul 4: Actualizarea Orchestratorului (`orchestrator/pipeline.py`)
- Salvarea metadatelor de failover în fiecare etapă (`was_fallback`, `model_used`, `latency_seconds`).
- Transmiterea acestor metadate către rezultatul final al pipeline-ului pentru afișare în consolă și în UI.

### Pasul 5: Refactorizarea UI-ului Streamlit (`ui_app.py`)
- Înlocuirea celor 3 blocuri tehnice de selectare manuală de modele cu un selector de **Routing Preset / Combo**.
- Afișarea vizuală a lanțului de fallback selectat (ex: `Claude 3.5 ➔ Gemini 3.8 ➔ Groq Llama`).
- În timpul execuției fiecărui stadiu, afișarea unui badge verde (dacă primarul a răspuns) sau galben (dacă s-a declanșat auto-fallback-ul, indicând modelul de rezervă folosit).

### Pasul 6: Testare & Verificare
- Test unitar cu un model invalid intenționat (ex: `gemini-fake-model`) pentru a valida că routerul prinde eroarea și comută automat pe modelul secundar fără oprirea execuției.
- Verificarea integrității pipeline-ului CLI (`main.py`) și Streamlit (`ui_app.py`).

---

## 5. Criterii de Succes

1. **Zero Crash-uri pe erori externe**: Nicio eroare de tip `404`, `429` sau `500` de la un furnizor nu trebuie să oprească pipeline-ul atâta timp cât există cel puțin un model de rezervă valid.
2. **Cod curat & Decuplat**: Agenții nu mai depind de biblioteci terțe disparate, ci doar de protocolul standard OpenAI prin `RouterClient`.
3. **Experiență UI Superioară**: Utilizatorul selectează un Combo simplu în loc de configurări tehnice manuale, beneficiind de stabilitate la nivel de enterprise.
