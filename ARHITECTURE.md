# Arhitectura și Principiile de Bază pentru EasyPrompt

Acest document definește regulile de arhitectură, scalabilitate și structură pentru aplicația Python `EasyPrompt`. Orice cod generat pentru acest proiect trebuie să adere strict la aceste principii.

## 1. Obiectivul Arhitectural
EasyPrompt este o aplicație de tip multi-agent (PromptCrafter -> LogicVerifier -> Executor). Sistemul trebuie să fie **extensibil**, permițând utilizatorului să selecteze un domeniu specific (ex: `coding`, `math`, `creative_writing`), iar pipeline-ul de agenți să își adapteze dinamic comportamentul, prompt-urile de sistem și verificările în funcție de domeniu.

## 2. Scalabilitate prin "Domain Profiles" (Strategy / Factory Pattern)
Pentru a suporta multiple domenii fără a scrie instrucțiuni `if/else` interminabile:
*   **Fără hardcodare:** System prompt-urile nu trebuie hardcodate în interiorul funcțiilor. Ele trebuie extrase în fișiere de configurare (ex. `JSON`, `YAML`) sau într-un modul separat de definiții de domenii (ex. `domains.py`).
*   **Factory Pattern:** Implementează un `AgentFactory` care, pe baza input-ului utilizatorului (ex: `domain="coding"`), încarcă automat "persona" potrivită pentru PromptCrafter, LogicVerifier și Executor.
    *   *Exemplu:* Dacă userul alege `coding`, LogicVerifier trebuie instruit special să verifice logica de programare, securitatea codului și complexitatea temporală (Big O). Dacă alege `math`, trebuie să verifice corectitudinea teoremelor sau a calculelor.
*   **Design Modular:** Adăugarea unui domeniu nou în viitor (ex. `legal_analysis`) ar trebui să necesite doar adăugarea unei noi configurații (un fișier sau dicționar nou), **zero modificări** în logica principală a pipeline-ului.

## 3. Principii de Structură (SOLID & Clean Code)
*   **Single Responsibility Principle (SRP):** Fiecare modul face un singur lucru.
    *   `llm_clients.py` -> Gestionează strict comunicarea cu API-urile (Gemini, Groq) și rate-limit-urile. Nu conține logică de business.
    *   `agents.py` -> Definește rolurile agenților, dar folosește clienții LLM pentru a executa.
    *   `pipeline.py` -> Gestionează exclusiv fluxul datelor: cum trece output-ul Agentului 1 la Agentul 2.
*   **Dependency Injection:** Agenții ar trebui să primească clientul LLM (Gemini/Groq) la inițializare, facilitând testarea unitară (mocking) sau schimbarea rapidă a unui model.
*   **Type Hinting & Pydantic:** Folosește Type Hints (`-> str`, `dict`, etc.) peste tot. Utilizează biblioteci ușoare (ex. `Pydantic` sau `dataclasses`) pentru a defini structura input-ului și output-ului între agenți (ex: `class AgentResponse(BaseModel): ...`).

## 4. Structura de Directoare Impusă
Aplicația trebuie să aibă o structură clară, separată pe module:

```text
easyprompt/
├── main.py                  # Punctul de intrare (CLI / interacțiunea cu userul)
├── .env                     # Cheile API (nu va fi comitat)
├── requirements.txt         # Dependențele proiectului
├── core/
│   ├── config.py            # Încărcarea variabilelor de mediu și setărilor globale
│   ├── llm_clients.py       # Wrappere generice pentru Gemini API și Groq API
├── domain/
│   ├── profiles.py          # Definițiile domeniilor (Math, Coding, General etc.)
│   ├── prompts/             # (Opțional) Fisiere text/json cu system prompts pe domenii
├── agents/
│   ├── base_agent.py        # Clasa/Interfața de bază pentru agenți
│   ├── prompt_crafter.py    # Logica primului agent (Gemini)
│   ├── logic_verifier.py    # Logica agentului critic (Groq)
│   ├── executor.py          # Logica agentului final (Gemini)
└── orchestrator/
    ├── pipeline.py          # Leagă agenții împreună secvențial
```
## 5. Reguli de Execuție și Rulare
Folosește exclusiv SDK-urile oficiale (google-genai și groq). Fără framework-uri greoaie de agenți care ascund logica.

Afișează log-uri bogate și formatate curat în consolă (ex. folosind librăria rich), arătând clar ce domeniu a fost selectat și timpul de execuție al fiecărui agent din pipeline.