Friday Voice

Real-time Multilingual Voice AI Customer Support Agent.

Natural Hindi-English conversations • Real-time audio • Interruptible
voice interaction


1. Overview

Friday Voice is a real-time, voice-native customer support agent
designed for natural Indian conversations where users freely switch
between Hindi and English.

Instead of forcing a user to select a language before speaking, Friday
is designed around the way people actually communicate:

"Mera order abhi tak deliver nahi hua, can you check?"

The agent receives speech, transcribes it, generates a concise response,
converts that response into speech, and streams the audio back to the
user.

2. Problem

Traditional voice assistants often struggle with:

Hindi-English code-switching

Short conversational turns

Users interrupting the assistant

Streaming speech

Technical/product terminology

Natural conversational pacing

Maintaining a consistent voice

For customer support, these problems become especially noticeable
because users expect the interaction to feel like a conversation rather
than a sequence of API calls.

3. Solution

Friday combines a real-time communication layer with specialized speech,
language, and voice services.

High-Level Architecture

flowchart LR
    A["User<br/>Microphone"] --> B["LiveKit<br/>Realtime Audio"]
    B --> C["Deepgram Nova-3<br/>Speech-to-Text"]
    C --> D["Groq<br/>GPT-OSS 20B"]
    D --> E["Rime Coda<br/>Text-to-Speech"]
    E --> B
    B --> F["User<br/>Speaker"]

    style A fill:#111827,color:#fff
    style B fill:#4f46e5,color:#fff
    style C fill:#059669,color:#fff
    style D fill:#f59e0b,color:#111
    style E fill:#dc2626,color:#fff
    style F fill:#111827,color:#fff

Conversation Flow

User speaks
    ↓
Browser captures microphone audio
    ↓
LiveKit transports realtime audio
    ↓
Deepgram Nova-3
    ↓
Speech → Text
    ↓
Groq GPT-OSS 20B
    ↓
Text response
    ↓
Rime Coda
    ↓
Text → Speech
    ↓
LiveKit streams audio to browser
    ↓
User hears the response

4. Core Features

4.1 Natural Hinglish

Friday is designed for mixed Hindi-English speech.

Example

User:
"Mera refund abhi tak nahi aaya, can you check?"

Friday:
"Sure, main aapka refund status check karta hoon."

The agent's prompt is designed to keep responses short and
conversational instead of producing long written-style answers.

4.2 Real-Time Voice Communication

LiveKit provides the real-time WebRTC communication layer.

The browser connects to a LiveKit room and publishes microphone audio.
The agent joins the same room and processes the conversation in real
time.

This avoids building a custom audio transport layer.

4.3 Speech-to-Text

Deepgram Nova-3 handles speech recognition.

Current configuration:

deepgram.STT(
    model="nova-3",
    language="hi",
    interim_results=True,
    smart_format=True,
    endpointing_ms=100,
    keyterm=[
        # product / technical terms
    ],
)

The configuration is intended to support Hindi speech while preserving
important English product and technical vocabulary.

4.4 Conversational LLM

Friday uses the Groq OpenAI-compatible API with:

openai.LLM(
    model="openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    temperature=0.2,
    max_completion_tokens=60,
    top_p=0.9,
    reasoning_effort="low",
)

The short completion limit helps keep spoken responses concise.

4.5 Consistent Voice

Rime Coda generates the spoken response.

Current configuration:

rime.TTS(
    model="coda",
    speaker="luna",
    lang="eng",
    sample_rate=22050,
    use_websocket=True,
    segment="bySentence",
    speed_alpha=0.95,
)

Rime Configuration

Setting        Value

Model          coda
Speaker        luna
Language       eng
Sample Rate    22050 Hz
Transport      WebSocket
Segmentation   bySentence
Speed          0.95
Audio          PCM

The application uses an Indian customer-support persona. The selected
luna voice is the fixed Rime voice profile used by the implementation;
this should not be interpreted as a guarantee of a specific Indian
accent.

5. Turn-Taking & Interruption

Voice conversations need more than speech recognition and text
generation.

Friday uses interruption handling so that the assistant can stop
speaking when the user starts talking.

Current Interruption Configuration

interruption={
    "enabled": True,
    "mode": "vad",
    "min_duration": 0.35,
    "min_words": 2,
    "false_interruption_timeout": 1.5,
    "resume_false_interruption": True,
}

Endpointing

endpointing={
    "mode": "fixed",
    "min_delay": 0.0,
    "max_delay": 0.6,
}

This is intended to balance:

Fast response time

Avoiding premature turn completion

Natural user interruptions

False-interruption recovery

6. Latency-Oriented Design

Friday is built as a streaming pipeline rather than waiting for every
stage to finish before starting the next.

sequenceDiagram
    participant U as User
    participant LK as LiveKit
    participant STT as Deepgram
    participant LLM as Groq
    participant TTS as Rime

    U->>LK: Speak
    LK->>STT: Audio stream
    STT-->>LLM: Transcript
    LLM-->>TTS: Response text
    TTS-->>LK: Audio stream
    LK-->>U: Spoken response

Important latency-oriented choices include:

LiveKit realtime audio transport

Deepgram interim transcription

Short LLM responses

Rime WebSocket streaming

Sentence-based TTS segmentation

VAD-based interruption handling

Disabled preemptive generation to avoid unnecessary speculative LLM
calls

7. Technology Stack

Layer         Technology                Purpose

Frontend      React + TypeScript        Voice UI
Build Tool    Vite                      Frontend development/build
Realtime      LiveKit                   WebRTC audio transport
STT           Deepgram Nova-3           Speech recognition
LLM           Groq GPT-OSS 20B          Response generation
TTS           Rime Coda                 Speech synthesis
Backend       Node.js + Express         LiveKit token server
Agent         Python + LiveKit Agents   Voice orchestration
Environment   .env                    Secret configuration

8. Project Structure

friday/
│
├── frontend/
│   └── friday-voice/
│       ├── public/
│       ├── src/
│       │   ├── components/
│       │   ├── services/
│       │   │   └── livekitClient.ts
│       │   ├── App.tsx
│       │   └── ...
│       ├── package.json
│       └── vite.config.*
│
├── backend/
│   ├── agent.py
│   ├── server.js
│   ├── package.json
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
│
├── README.md
├── RIME_EVIDENCE.md
└── .gitignore

9. Backend Architecture

The backend has two separate responsibilities.

Node.js Server

server.js is responsible for generating temporary LiveKit access
tokens.

Frontend
   │
   │ GET /api/livekit/token
   ▼
Express Server
   │
   │ creates JWT
   ▼
LiveKit Token
   │
   ▼
Frontend connects to LiveKit

The LiveKit API key and secret remain on the backend and are never
placed in the frontend.

Python Agent

agent.py is the actual voice agent.

It connects to LiveKit and coordinates:

LiveKit
   ↓
Deepgram STT
   ↓
Groq LLM
   ↓
Rime TTS
   ↓
LiveKit

10. Frontend ↔ Backend Integration

The frontend does not contain LiveKit server credentials.

Instead:

React Frontend
      │
      │ HTTP request
      ▼
Node.js Backend
      │
      │ generates token
      ▼
LiveKit JWT
      │
      ▼
React Frontend
      │
      │ connects with token
      ▼
LiveKit Room

The frontend service is:

frontend/friday-voice/src/services/livekitClient.ts

It requests:

GET /api/livekit/token

and uses the returned:

token
url
room

to connect to LiveKit.

11. Environment Variables

Create:

backend/.env

Example:

LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

DEEPGRAM_API_KEY=your_deepgram_api_key
GROQ_API_KEY=your_groq_api_key
RIME_API_KEY=your_rime_api_key

Important

Never commit real credentials.

The repository should contain:

.env.example

with placeholder values only.

12. Installation

Backend

cd backend
npm install

Create the Python environment using Python 3.12:

py -3.12 -m venv .venv

Activate it:

.\.venv\Scripts\activate

Install Python dependencies:

pip install -r requirements.txt

Frontend

cd frontend/friday-voice
npm install

13. Running the Project

Friday currently runs as three processes.

Terminal 1 --- Node.js Token Server

cd C:\Users\sukan\friday\backend
npm run dev

Expected:

Server running on http://localhost:5000

Terminal 2 --- Python Voice Agent

cd C:\Users\sukan\friday\backend
.\.venv\Scripts\activate
python agent.py dev

Terminal 3 --- React Frontend

cd C:\Users\sukan\friday\frontend\friday-voice
npm run dev

Open the Vite URL shown in the terminal.

14. LiveKit Connection

The frontend creates a room name and requests a token from the backend.

Conceptually:

Browser
   │
   ├── Request token ──────────► Node.js
   │                              │
   │                              └── Sign LiveKit JWT
   │
   ◄── token + LiveKit URL ──────┘
   │
   └── Connect to LiveKit

The backend signs the token because the LiveKit API secret must remain
private.

15. Failure Handling

The application should fail gracefully when an external service is
unavailable.

LiveKit

If a connection fails:

Connection error
      ↓
Frontend reports failure
      ↓
User can retry

Speech Recognition

If STT fails:

No transcript
      ↓
No LLM request
      ↓
Conversation remains available for retry

LLM

If the Groq API returns an error such as a rate-limit/usage-limit
response:

Groq error
      ↓
No valid response
      ↓
Agent session may stop/retry depending on LiveKit behavior

A quota error cannot be fixed by restarting the frontend; the relevant
API quota must become available again.

TTS

If Rime fails:

Generated text
      ↓
TTS error
      ↓
No playable voice response

16. Security

Secrets are intentionally kept outside the frontend.

Never expose

LIVEKIT_API_SECRET
DEEPGRAM_API_KEY
GROQ_API_KEY
RIME_API_KEY

Safe pattern

Browser
   │
   │ temporary token
   ▼
Backend
   │
   ├── LiveKit secret
   ├── Deepgram key
   ├── Groq key
   └── Rime key

Only the backend/agent environment should have access to these
credentials.

17. Known Limitations

Current limitations include:

The agent depends on external STT, LLM, and TTS services.

Groq usage/rate limits can prevent response generation.

The current STT configuration is Hindi-oriented and may require
further tuning for different accents and languages.

Voice quality and accent characteristics depend on the selected Rime
voice.

The project currently runs locally rather than as a production
deployment.

LiveKit token generation is currently handled by a lightweight
Express server.

The system is optimized for short support responses rather than
long-form conversations.

18. Demo Conversation

User:
"Mera order abhi tak nahi aaya."

Friday:
"Sure, main order status check karta hoon."

User:
"Actually payment bhi deduct ho gaya."

Friday:
"Samajh gaya. Payment issue bhi check karte hain."

User:
"Wait, order number 4582 hai."

Friday:
"Got it, order 4582 note kar liya."

The goal is not simply to translate Hindi into English.

The goal is to maintain a natural bilingual conversation.

19. Evaluation Goals

The project can be evaluated across:

Metric                  Goal

STT accuracy            Correct Hindi-English transcription
Code-switch handling    Preserve mixed-language meaning
Response latency        Fast conversational response
TTS latency             Begin speaking quickly
Interruption recovery   Stop/resume naturally
Voice consistency       Stable agent identity
Response length         Short, voice-friendly replies
Conversation quality    Natural customer-support interaction

20. Roadmap

Current

React voice interface

LiveKit integration

Backend token generation

Deepgram STT

Groq LLM

Rime TTS

Hindi-English conversational prompt

VAD interruption handling

Realtime audio pipeline

Next

Production deployment

Persistent conversation/session storage

Better multilingual language detection

Customer-support tool integrations

Latency benchmarking

Automated evaluation

More voice profiles

Robust fallback handling

Detailed observability and telemetry

21. Documentation & Evidence

Additional implementation evidence:

RIME_EVIDENCE.md --- Rime integration details and configuration
evidence.

Official service documentation:

LiveKit

LiveKit Agents

Deepgram

Groq

Rime

22. License

This project is intended as a hackathon/project prototype.

Friday Voice

Speak naturally. Switch languages freely. Get help instantly.
