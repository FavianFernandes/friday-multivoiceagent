# 🎙️ Friday — Multilingual Voice-First Customer Support Agent

> **From answering questions → to real resolutions.**

Friday is an AI-powered, voice-first customer support agent that can speak fluently in multiple languages (Hindi, English, Hinglish and more), understands the customer's actual intent, and responds naturally using an AI backend LLM via API.

---

## 📌 Current Project Status (Please Read First)

> **⚠️ Important Note**
> > >
> The frontend and backend code in this repository is a **basic working version**. It is **not yet implemented to the full specifications** described in the project proposal (PPT).
> > >
> **What the current code CAN do:**
> - ✅ Speak with users fluently in **multiple languages** (Hindi, English, Hinglish, and extensible to more)
> - ✅ Natural, real-time **voice conversations** (speech-to-text → LLM → text-to-speech)
> - ✅ Uses an **AI backend LLM via API** (Groq `gpt-oss-20b` via OpenAI-compatible API) to generate proper, context-aware responses
> - ✅ Delivers useful customer-facing outcomes to the user (order queries, refund conversations, etc.)
> - ✅ Female Hinglish personality ("Friday") with natural fillers and correct grammar handling
> > >
> **What the current code CANNOT do yet (full PPT specification — needs upgrade):**
> - ❌ Multi-system investigation (refund, orders integration)
> - ❌ Real actions / tool calling (initiate refund, rebooking, status checks)
> - ❌ Urgency mode, live progress bar, and autonomous resolution workflow
> - ❌ Intelligent human handoff with full context
> - ❌ PostgreSQL + pgvector (RAG) knowledge base
> - ❌ Secure identity & transaction verification
> > >
> **👉 To fulfill the required specifications given in the PPT, the code needs to be upgraded.** See the [Roadmap](#-roadmap--upgrade-plan-ppt-specification) below.

---

## 🧩 Problem Statement

Today's customer support systems (rule-based chatbots, FAQ keyword search) cannot truly understand customer queries:

- They rely on **keyword matching** and return fixed, generic answers.
- They lack reasoning, context, and the ability to **take action** or **escalate complex issues**.
- Customers with urgent problems (failed payments, refunds, cancellations) receive incomplete or irrelevant responses — leading to frustration.

**Example of today's broken flow:**

```javascript
Customer: "Mera ₹2,450 deduct ho gaya but ticket book nahi hua. Refund kab milega?"
Bot:      "For refund-related queries, please check the refund policy."
Customer: "But mera specific refund status kya hai?"
Bot:      "Please check the refund policy."
Customer: "Can I talk to someone?"
Bot:      "Please contact customer care."
          → Customer Frustration 💢
```

## 💡 Proposed Solution — "Friday"

Friday goes from **answering questions → to real resolutions**, following the pipeline:

```javascript
UNDERSTAND → INVESTIGATE → REASON → ACT & VERIFY → RESOLVE / ESCALATE
(Intent &   (Across       (Find     (Take Action)  (Keep You
 Identity)   Systems)      Root Cause)              Informed)
```

### Planned Key Features 

| # | Feature | Description |
| --- | --- | --- |
| 1 | **Multilingual & Voice-First** | Supports Hindi, English, Hinglish & more; natural voice interaction; accessible for all ages |
| 2 | **Progress Assurance** | Live case status with a progress bar (Checking → Investigating → Processing → Resolved) |
| 3 | **Urgency Mode** | Special flow for urgent cases (e.g., refund needed immediately); tries all options to resolve faster; quick human connection if unresolved |
| 4 | **Secure & Reliable** | Verifies customer identity, transaction signals & policy rules; prevents misuse and fraud |
| 5 | **Multi-System Investigation** | Connects booking, payment, refund, order and policy data; finds the actual root cause |
| 6 | **Autonomous Resolution** | Handles multi-step issues; takes real actions (status checks, refund initiation, rebooking) |
| 7 | **Intelligent Human Handoff** | Predicts when human intervention is needed; transfers complete investigation context; no repetition |
| 8 | **Beyond FAQ Answers** | Actually investigates and resolves issues — voice-first, multilingual, urgency-aware, context-aware |

---

## 🏗️ Architecture / System Design

### Current Implementation (Basic Working Version)

```javascript
┌──────────────────────────────────────────────────────────────────┐
│                         CURRENT PIPELINE                         │
└──────────────────────────────────────────────────────────────────┘

  [ Browser Mic ] 
        │ 
        ▼ 
┌──────────────┐      ┌──────────────┐ 
│   LiveKit    │────▶│   Deepgram    │ 
│   (WebRTC)   │      │ Nova-3 (STT) │ 
└──────────────┘      └──────────────┘ 
                             │ (Transcribed Text)
                             ▼
                     ┌──────────────┐ 
                     │   Groq LLM   │◀─── Tool Calling / Function Dispatch 
                     │  (Reasoning) │ 
                     └──────┬───────┘ 
                            │ 
              ┌─────────────┴─────────────┐ 
              ▼                           ▼  
     [ General Query ]           [ System Investigation ] 
              │                           │
              │                 ┌─────────┴─────────┐
              │                 │ External APIs / DB│ 
              │                 │ (IRCTC, Payments, │
              │                 │ Refunds, Orders)  │
              │                 └─────────┬─────────┘
              │                           │ (Fetched Records & Status)
              │                           ▼ 
              └─────────────┬─────────────┘ 
                            ▼ 
                    ┌───────────────┐ 
                    │ LLM Response  │ 
                    │  Formulation  │ 
                    └───────┬───────┘
                            │ 
                            ▼ 
                    ┌───────────────┐
                    │      Text     │
                    │  Normalizer*  │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   Rime Coda   │
                    │    TTS (hi)   │
                    └───────┬───────┘
                            │
                            ▼
┌──────────────┐      ┌───────────────┐
│ User Speaker │◀────│   LiveKit      │
│   (Audio)    │      │  Audio Egress │
└──────────────┘      └───────────────┘

* Text Normalizer (agent.py): PNR/digit-by-digit splitting, bilingual price expansion, Devanagari conversion, and female Hinglish grammar formatting.
```

### Target Architecture 

| Stage | Step | Component (Planned) |
| --- | --- | --- |
| 1. Input | Customer voice query (multilingual) | React / Next.js + LiveKit |
| 2. Connect | Real-time audio, VAD, low latency | LiveKit Cloud (WebRTC) |
| 3. Transcribe | Multilingual speech-to-text | Deepgram Nova-3 |
| 4. Understand | Intent, reasoning, planning, tool calling | Qwen3 + Qwen-Agent |
| 5. Investigate | Context, multi-system investigation, policy check | Friday Investigation Engine |
| 6. Fetch | refund, orders, customer history, KB | Tools / Data layer |
| 7. Execute | Authorized action, status update, verification | Action + Verify |
| 8. Output | Resolution or human handoff with full context | Agent UI |

### Tech Stack

#### ✅ Currently Implemented

| Layer | Technology |
| --- | --- |
| Voice transport | LiveKit (WebRTC, `livekit-agents` SDK) |
| Speech-to-Text | Deepgram Nova-3 (`hi` + keyterm boosting) |
| LLM (via API) | Groq `openai/gpt-oss-20b` (OpenAI-compatible API) |
| Text-to-Speech | Rime Coda (`luna` female voice, `hi`) |
| VAD | Silero VAD |
| Language | Python 3.10+ |

#### 🚧 Planned Upgrade 

| Layer | Technology |
| --- | --- |
| Frontend | React / Next.js + Tailwind CSS, LiveKit Components, voice-first multilingual UI, live transcript, progress bar |
| Backend | Python 3.10+, FastAPI, livekit-agents, async event-driven worker, context & session management, REST APIs for business tools |
| AI Engine | Qwen3 (LLM), Qwen-Agent (tool calling), Deepgram Nova-3 (STT), Rime Coda (TTS), Silero VAD, policy & safety guardrails |
| Data + Knowledge | PostgreSQL (operational data), pgvector (RAG / knowledge base), bookings/payments/refunds, customer history, company policies & FAQs, previous tickets |
| Deployment | Cloud deployment (Enter Pro / any cloud) |

---

## 🚀 Local Development Lifecycle

### Prerequisites

- Python **3.10+**
- Node.js **18+** (for frontend) 
- `pip` / `virtualenv`
- API keys: [LiveKit](https://livekit.io/), [Deepgram](https://deepgram.com/), [Groq](https://groq.com/), [Rime](https://rime.ai/)

### 1️⃣ Clone the repository

```bash
git clone https://github.com/FavianFernandes/friday-multivoiceagent.git 
cd friday-multivoiceagent
```

### 2️⃣ Backend setup (Voice Agent)

```bash
```bash 

cd backend 



# Create and activate a Python 3.12 virtual environment 

py -3.12 -m venv .venv 



# Windows 

.venv\Scripts\activate 



# Install Python dependencies 

pip install -r requirements.txt
```

### 3️⃣ Environment variables

```text
```text
backend/
├── .env.example
└── .env

# From the backend folder, run:

copy .env.example .env

# Then open backend/.env and add your API credentials:
```

```ini
# ── LiveKit ──────────────────────────────────────────────
LIVEKIT_URL=wss://your-livekit-server           # TODO
LIVEKIT_API_KEY=your-livekit-api-key            # TODO
LIVEKIT_API_SECRET=your-livekit-api-secret      # TODO

# ── Deepgram (STT) ───────────────────────────────────────
DEEPGRAM_API_KEY=your-deepgram-api-key          # TODO

# ── Groq (LLM via API) ───────────────────────────────────
GROQ_API_KEY=your-groq-api-key                  # TODO

# ── Rime (TTS) ───────────────────────────────────────────
RIME_API_KEY=your-rime-api-key                  # TODO
```

### 4️⃣ Run the agent worker

```bash
From the `backend` folder, run: 

```powershell 
python agent.py dev

```

### 5️⃣ Frontend setup 

```powershell
Open a new terminal and run:

```powershell
cd frontend\friday-voice 
npm install 
npm run dev                     
```

### 6️⃣ Run tests 

```bash
cd backend 
pytest
```

---

## 🗺️ Roadmap / Upgrade Plan 

- [x] **Phase 0 — Basic voice agent (current)**
- [x] LiveKit voice pipeline (mic → STT → LLM → TTS → speaker)
- [x] Multilingual fluent speech (Hindi / English / Hinglish)
- [x] Hinglish text normalization (numbers, prices, OTPs, female grammar, fillers)
- [ ] **Phase 1 — Investigation engine**
- [ ] Qwen3 + Qwen-Agent tool calling
- [ ] Connect booking / payment / refund / order data sources
- [ ] PostgreSQL + pgvector RAG knowledge base
- [ ] **Phase 2 — Autonomous actions**
- [ ] Real tool actions (status checks, refund initiation, rebooking)
- [ ] Action verification & policy guardrails
- [ ] Identity & transaction verification
- [ ] **Phase 3 — Experience & scale**
- [ ] Live progress bar (Checking → Investigating → Processing → Resolved)
- [ ] Urgency mode for critical cases
- [ ] Intelligent human handoff with full context transfer
- [ ] React / Next.js voice-first frontend
- [ ] Multi-channel support: Web • Mobile • Voice • Telephony

---

## 🧠 Agent Behavior Notes (agent.py)

The production agent (`agent.py`) includes careful text-processing before TTS:

| Concern | Solution |
| --- | --- |
| Numbers split across stream fragments | Sentence-level buffering before normalization |
| "17" read as "1-7" | Numbers ≤ 4 digits spelled as words (`num2words`) |
| OTPs / Order IDs / PINs | Kept as digits, split digit-by-digit (e.g., `OTP 1234 → OTP 1 2 3 4`) |
| Devanagari digits (१७) | Converted to ASCII before processing |
| Prices (₹79,900) | Expanded bilingually: *"seventy-nine thousand nine hundred rupees, यानी उन्यासी हज़ार नौ सौ रुपये"* |
| Product models (iPhone 17) | Spelled in English (*"iPhone seventeen"*) |
| Female grammar | Male verb forms auto-corrected (e.g., `करुंगा → करूँगी`) |
| Robotic delivery | Human-like fillers injected (~30% chance): *उम्म…, हम्म…, hmm…* |

**Turn handling:** STT-based endpointing (Deepgram), VAD interruptions enabled, preemptive generation enabled for low-latency responses.

---

## 👥 Team

| Field | Value |
| --- | --- |
| **Team** | MindMesh |
| **Team ID** | BDC2A25011AD |
| **Track** | 2. Customer Support |
| **College** | Dayananda Sagar University |
| **Event** | HackDriven — Build Bengaluru |