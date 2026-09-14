"""
agent.py — Production Hinglish Voice Agent
===========================================
Pipeline:

Browser Microphone
        ↓
LiveKit
        ↓
Deepgram Nova-3 STT
        ↓
Groq GPT-OSS 120B
        ↓
Rime Coda TTS
        ↓
LiveKit
        ↓
Browser Speaker

Agent personality:
- Sporthi
- Female Indian customer-support agent
- Natural Hinglish
- Hindi in Devanagari
- English in English script
- Short responses
- Upbeat, energetic tone
- Human-like fillers (ums and ahs)

NOTE ON DEPENDENCIES:
This file requires the `num2words` package for number-to-speech
normalization. Add it to requirements.txt:

    num2words

and install with:

    pip install num2words
"""

import os
import re
import random
import logging
from typing import AsyncIterable

import numpy as np
from dotenv import load_dotenv
from num2words import num2words

from livekit import agents, rtc
from livekit.plugins import deepgram, openai, rime, silero

from livekit.agents import (
    Agent,
    AgentSession,
    TurnHandlingOptions,
    RoomInputOptions,
    UserInputTranscribedEvent,
    llm,
)


load_dotenv()


# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("hinglish-agent")


# ------------------------------------------------------------------------------
# SYSTEM PROMPT
# ------------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are Sporthi, a friendly Indian female customer support agent "
    "for an e-commerce platform.\n\n"

    "CRITICAL HINGLISH SCRIPT & VOICE RULES:\n"

    "1. When speaking Hinglish, ALWAYS write Hindi words in Devanagari "
    "script and English words in English letters.\n"

    "   DO NOT write Hindi using English letters.\n"

    "   NEVER write examples like:\n"
    "   'Main aapki help kar rahi hoon.'\n"
    "   'Bata dijiye.'\n\n"

    "   Instead use mixed script like:\n"
    "   'हाँजी! मैं तुरंत आपका order track कर देती हूँ।'\n"
    "   'Sure! आप मुझे अपना Order ID बता दीजिए।'\n"
    "   'Don't worry, आपका refund process हो रहा है।'\n"
    "   'I can help with that! Order में क्या problem आ रही है?'\n\n"

    "2. FEMALE GRAMMAR ONLY.\n"
    "Always use female endings such as:\n"
    "'कर देती हूँ', 'बता देती हूँ', 'देखूँगी', 'समझ गई', 'कर सकती हूँ'.\n"
    "Never use male endings such as 'करूँगा', 'गया', 'करता हूँ'.\n\n"

    "3. Keep responses very short.\n"
    "Maximum 1-2 sentences and preferably under 12 words.\n\n"

    "4. Speak naturally and energetically, like a happy Indian "
    "customer-support executive.\nNever flat, dull or robotic.\n\n"

    "5. Preserve important English technical/business terms naturally:\n"
    "order, Order ID, refund, payment, delivery, account, UPI, EMI, OTP.\n\n"

    "6. Never explain your internal reasoning.\n"
    "Give only the useful customer-facing response.\n\n"

    "7. Write plain quantities and prices as normal digits "
    "(e.g. '17', '10,000', '₹499'). Do not spell them out yourself — "
    "the system will convert them to speech correctly. "
    "For Order IDs, OTPs, and phone numbers, keep them as plain digit "
    "strings with no separators (e.g. '482913'), since those are read "
    "out digit-by-digit.\n\n"

    "8. Product model numbers: always write the digits in English "
    "(e.g. 'iPhone 17', 'Galaxy S25'). Prices: always use the ₹ symbol "
    "with digits (e.g. '₹79,900'). Never write numbers in Devanagari.\n\n"

    "9. TONE: upbeat, warm and enthusiastic — like a cheerful Indian "
    "sales/support executive, never flat or robotic. Sound genuinely "
    "happy for the customer.\n\n"

    "10. Use natural energy in your words: end good-news replies with an "
    "exclamation mark and cheerful Hinglish words like 'हाँजी!', "
    "'बिल्कुल!', 'ज़रूर!', 'वाह!',  'शानदार!'.\n"
    "   Examples:\n"
    "   'हाँजी! आपका order confirm हो गया है! Thankyou '\n"
    "   'वाह! iPhone 17 पर आज बढ़िया discount चल रहा है!'\n"
    "   EXCEPTION: if the customer is angry or reporting a problem, be "
    "calm and empathetic instead — no exclamation marks.\n"
)


# ------------------------------------------------------------------------------
# Female grammar protection
# ------------------------------------------------------------------------------

_MALE_TO_FEMALE_MAP = {
    "karunga": "karungi",
    "karungaa": "karungi",

    "jaunga": "jaungi",
    "jaungaa": "jaungi",

    "bataunga": "bataungi",
    "bataungaa": "bataungi",

    "dekhunga": "dekhungi",
    "dekhungaa": "dekhungi",

    "sununga": "sunungi",

    "dunga": "dungi",

    "lung": "lungi",

    "samajh gaya": "samajh gayi",
    "samajh gaya hai": "samajh gayi hai",

    "sakta hoon": "sakti hoon",
    "sakta hu": "sakti hoon",

    "raha hoon": "rahi hoon",
    "raha hu": "rahi hoon",

    "chuka hoon": "chuki hoon",
    "chuka hu": "chuki hoon",

    "liya hai": "li hai",
    "diya hai": "di hai",

    "gaya hai": "gayi hai",
    "gaya": "gayi",

    "liya": "li",
    "diya": "di",
}


def _enforce_female_pronouns(text: str) -> str:
    """
    Rewrite common male Hindi verb forms
    into female equivalents before TTS.
    """

    for male, female in _MALE_TO_FEMALE_MAP.items():
        pattern = r"\b" + re.escape(male) + r"\b"

        text = re.sub(
            pattern,
            female,
            text,
            flags=re.IGNORECASE,
        )

    return text


# ------------------------------------------------------------------------------
# Number-to-speech normalization
# ------------------------------------------------------------------------------
#
# Problem this solves:
#   TTS engines (including Rime) will sometimes read digit groups one
#   character at a time ("1", "7") instead of as a whole number
#   ("seventeen"), especially when the digits arrive to the TTS as
#   separate streamed text fragments.
#
# Fix:
#   Before text reaches the TTS, we detect "plain" numbers (with
#   optional commas/decimals, e.g. "17", "10,000", "499.50") and spell
#   them out as English words. IDs / OTPs / phone numbers are
#   deliberately left as digits, since those should be read digit by
#   digit — we detect these heuristically as long digit runs (5+
#   digits) with no comma formatting.
# ------------------------------------------------------------------------------

_NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9])\d{1,3}(?:,\d{2,3})+(?:\.\d+)?(?![A-Za-z0-9])"  # comma-grouped, e.g. 10,000
    r"|(?<![A-Za-z0-9])\d{1,4}(?:\.\d+)?(?![A-Za-z0-9])"              # plain short numbers, e.g. 17, 499.50
)


def _spell_number(raw: str) -> str:
    cleaned = raw.replace(",", "")

    try:
        if "." in cleaned:
            whole, frac = cleaned.split(".")
            whole_words = num2words(int(whole), lang="en")
            frac_words = " ".join(
                num2words(int(d), lang="en") for d in frac
            )
            return f"{whole_words} point {frac_words}"

        return num2words(int(cleaned), lang="en")

    except (ValueError, OverflowError):
        return raw


def _normalize_numbers(text: str) -> str:
    """
    Convert standalone plain numbers (with optional commas/decimals)
    into spoken English words. Long unformatted digit runs (5+ digits,
    no commas — typical of Order IDs / OTPs / phone numbers) are left
    untouched so they're read digit-by-digit, which is what customers
    expect for those.
    """

    def repl(match: "re.Match[str]") -> str:
        raw = match.group(0)

        # Long, comma-less digit strings are treated as IDs/OTPs and
        # left alone (e.g. "482913", "9876543210").
        if "," not in raw and "." not in raw and len(raw) >= 5:
            return raw

        return _spell_number(raw)

    return _NUMBER_RE.sub(repl, text)


# ------------------------------------------------------------------------------
# Devanagari digits, product numbers, and price pronunciation
# ------------------------------------------------------------------------------
#
# Rime Coda has NO inline lang/SSML pronunciation tags (Mist v2 only), and a
# Coda voice serves one language per request. So we cannot "tag" a number as
# English — we must rewrite the TEXT so Coda's LLM backbone reads it right:
#   - Product model numbers  -> spelled as English words (Latin script)
#     ("iPhone 17" -> "iPhone seventeen"). Also fixes the real bug: the LLM
#     sometimes emits Devanagari digits ("iPhone १७"), which bypass the ASCII
#     number regex and get read as Hindi ("सत्रह").
#   - Prices (₹ / Rs. / रुपये) -> spoken in English FIRST, then repeated in
#     Hindi ("seventy-nine thousand nine hundred rupees, यानी उन्यासी हज़ार
#     नौ सौ रुपये").
# No new dependencies — uses only stdlib + the existing num2words.
# ------------------------------------------------------------------------------

_DEV_DIGIT_MAP = str.maketrans("०१२३४५६७८९", "0123456789")


def _devanagari_to_ascii(text: str) -> str:
    """Convert Devanagari digits to ASCII before any number processing."""
    return text.translate(_DEV_DIGIT_MAP)


# Hindi number words, 0-99 (Indian compounds), then lakh/crore scales.
_HINDI_0_99 = ["शून्य","एक","दो","तीन","चार","पाँच","छह","सात","आठ","नौ","दस",
"ग्यारह","बारह","तेरह","चौदह","पंद्रह","सोलह","सत्रह","अठारह","उन्नीस","बीस",
"इकीस","बाईस","तेईस","चौबीस","पच्चीस","छब्बीस","सत्ताईस","अट्ठाईस","उनतीस","तीस",
"इकतीस","बत्तीस","तैंतीस","चौंतीस","पैंतीस","छत्तीस","सैंतीस","अड़तीस","उनतालीस","चालीस",
"इकतालीस","बयालीस","तैंतालीस","चौवालीस","पैंतालीस","छियालीस","सैंतालीस","अड़तालीस","उनचास","पचास",
"इक्यावन","बावन","तिरेपन","चौवन","पचपन","छप्पन","सत्तावन","अट्ठावन","उनसठ","साठ",
"इकसठ","बासठ","तिरेसठ","चौंसठ","पैंसठ","छियासठ","सड़सठ","अड़सठ","उनहत्तर","सत्तर",
"इकहत्तर","बहत्तर","तिहत्तर","चौहत्तर","पचहत्तर","छिहत्तर","सतहत्तर","अठहत्तर","उन्यासी","अस्सी",
"इक्यासी","बयासी","तिरासी","चौरासी","पचासी","छियासी","सत्तासी","अट्ठासी","नवासी","नब्बे",
"इक्यानवे","बानवे","तिरानवे","चौरानवे","पचानवे","छियानवे","सत्तानवे","अट्ठानवे","निन्यानवे"]


def _hindi_words(n: int) -> str:
    """Spell an integer in Hindi words using the Indian numbering system."""
    if n < 100:
        return _HINDI_0_99[n]
    parts, rem = [], n
    for scale, name in [(10**7, "करोड़"), (10**5, "लाख"),
                        (10**3, "हज़ार"), (100, "सौ")]:
        q, rem = divmod(rem, scale)
        if q:
            parts.append(_HINDI_0_99[q] if scale == 100 else _hindi_words(q))
            parts.append(name)
    if rem:
        parts.append(_HINDI_0_99[rem])
    return " ".join(parts)


def _expand_price(raw: str) -> str:
    """'79,900' -> 'seventy-nine thousand nine hundred rupees, यानी उन्यासी
    हज़ार नौ सौ रुपये'. Decimals become paise on both sides."""
    cleaned = raw.replace(",", "")
    if "." in cleaned:
        whole_s, frac_s = cleaned.split(".")
        frac_s = frac_s.ljust(2, "0")[:2]
    else:
        whole_s, frac_s = cleaned, ""
    try:
        whole = int(whole_s)
        paise = int(frac_s) if frac_s else 0
    except ValueError:
        return raw
    eng = f"{num2words(whole, lang='en')} rupees"
    hin = f"{_hindi_words(whole)} रुपये"
    if paise:
        eng += f" and {num2words(paise, lang='en')} paise"
        hin += f" {_hindi_words(paise)} पैसे"
    return f"{eng}, यानी {hin}"


_PRICE_PREFIX_RE = re.compile(
    r"(?:₹|Rs\.?|रु\.?)\s*(\d{1,3}(?:,\d{2,3})*(?:\.\d{1,2})?)(?:\s*रुपये)?")
_PRICE_SUFFIX_RE = re.compile(
    r"(\d{1,3}(?:,\d{2,3})*(?:\.\d{1,2})?)\s*रुपये")


# OTPs / PINs / IDs of 4-6 digits must stay digit-by-digit. The old code only
# protected 5+ digit runs, so a 4-digit OTP got spelled as a number word.
# Splitting into single digits makes the existing normalizer speak each digit.
_CODE_SPLIT_RE = re.compile(
    r"\b(order\s+id|tracking\s+id|otp|pin|code|id)\s*(\d{4,6})\b",
    re.IGNORECASE,
)


def _split_codes(text: str) -> str:
    return _CODE_SPLIT_RE.sub(
        lambda m: f"{m.group(1)} " + " ".join(m.group(2)), text)


# Words after which a number is an ID/code, NOT a product model.
_CODE_WORDS = {
    "otp", "pin", "code", "id", "order", "no", "number", "ref",
    "upi", "emi", "neft",
    "the", "a", "an", "is", "are", "was", "in", "on", "at",
    "for", "to", "of", "and", "page",
}

# Attached model tokens: S25, iPhone17, Note14, ...
_MODEL_ATTACHED_RE = re.compile(r"\b([A-Za-z]+)(\d+)\b")
# Brand + spaced small number: "iPhone 17", "Galaxy 25", ...
_MODEL_SPACED_RE = re.compile(r"\b([A-Z][A-Za-z0-9]*)\s+(\d{1,2})\b")


def _product_numbers_to_english(text: str) -> str:
    """Spell model numbers in English words so Coda pronounces them English."""
    def _sub(m: "re.Match[str]") -> str:
        word = m.group(1)
        if word.lower() in _CODE_WORDS:
            return m.group(0)
        return f"{word} {_spell_number(m.group(2))}"

    text = _MODEL_ATTACHED_RE.sub(_sub, text)
    return _MODEL_SPACED_RE.sub(_sub, text)


# ------------------------------------------------------------------------------
# Human-like fillers (ums and ahs)
# ------------------------------------------------------------------------------
# Randomly injected at sentence starts so the voice sounds human instead of
# read from a script. Runs LAST in _clean_sentence so it never interferes with
# number/price/grammar processing. The ~30% randomness means no detectable
# pattern; fillers match the sentence's script (Hindi fillers for Devanagari
# sentences, English fillers for Latin-script ones).
# ------------------------------------------------------------------------------

_FILLER_CHANCE = 0.30

_FILLERS_DEVANAGARI = ["उम्म...", "हम्म...", "अच्छा,", "देखिए,"]
_FILLERS_LATIN = ["uh,", "umm,", "hmm,"]

# Never put a filler before greetings/thanks — sounds unnatural.
_FILLER_SKIP_START = {
    "हाँजी", "हांजी", "नमस्ते", "hello", "hi", "hey",
    "sorry", "धन्यवाद", "thank", "shukriya", "thanks",
}


def _humanize_fillers(text: str) -> str:
    stripped = text.strip()
    if not stripped or len(stripped.split()) < 2:
        return text

    first_word = re.split(r"[\s,।.!?'\"]+", stripped, maxsplit=1)[0].lower()
    if first_word in _FILLER_SKIP_START:
        return text

    if random.random() >= _FILLER_CHANCE:
        return text

    # Devanagari Unicode block U+0900–U+097F
    if "\u0900" <= stripped[0] <= "\u097F":
        filler = random.choice(_FILLERS_DEVANAGARI)
    else:
        filler = random.choice(_FILLERS_LATIN)

    return f"{filler} {stripped}"


# ------------------------------------------------------------------------------
# Sentence-safe text buffering
# ------------------------------------------------------------------------------
#
# We must NOT clean/normalize raw streamed fragments one at a time —
# a number or a grammar-sensitive word can be split across two
# fragments (e.g. "1" then "7,000"), breaking both the female-grammar
# regex and number normalization above. Instead we buffer incoming
# text until we have a complete sentence (or the stream ends), then
# run all cleanup on the complete sentence before handing it to TTS.
# ------------------------------------------------------------------------------

_SENTENCE_BOUNDARY_RE = re.compile(r"[।.!?\n]")

_STRIP_CHARS_RE = re.compile(r"""[*_`#"'“”'–—]""")


def _clean_sentence(sentence: str) -> str:
    cleaned = _STRIP_CHARS_RE.sub("", sentence)
    cleaned = _devanagari_to_ascii(cleaned)                      # १७ -> 17
    cleaned = _split_codes(cleaned)                              # OTP 1234 -> OTP 1 2 3 4
    cleaned = _PRICE_PREFIX_RE.sub(lambda m: _expand_price(m.group(1)), cleaned)
    cleaned = _PRICE_SUFFIX_RE.sub(lambda m: _expand_price(m.group(1)), cleaned)
    cleaned = _product_numbers_to_english(cleaned)               # iPhone 17 -> iPhone seventeen
    cleaned = _enforce_female_pronouns(cleaned)
    cleaned = _normalize_numbers(cleaned)
    cleaned = _humanize_fillers(cleaned)                         # ums and ahs (last step)
    return cleaned


# ------------------------------------------------------------------------------
# Output volume boost
# ------------------------------------------------------------------------------
# Rime has no loudness parameter, so we amplify the raw int16 PCM frames
# here. 1.8 ≈ +5 dB. If you hear distortion on loud words, lower to 1.5.
# ------------------------------------------------------------------------------

_TTS_GAIN = 1.8


def _apply_gain(frame: rtc.AudioFrame) -> rtc.AudioFrame:
    samples = np.frombuffer(frame.data, dtype=np.int16)
    boosted = np.clip(
        samples.astype(np.int32) * _TTS_GAIN, -32768, 32767
    ).astype(np.int16)
    return rtc.AudioFrame(
        data=boosted.tobytes(),
        sample_rate=frame.sample_rate,
        num_channels=frame.num_channels,
        samples_per_channel=frame.samples_per_channel,
    )


# ------------------------------------------------------------------------------
# Agent
# ------------------------------------------------------------------------------

class HinglishSupportAgent(Agent):

    def __init__(self):
        super().__init__(
            instructions=SYSTEM_PROMPT
        )

        # Keep conversation history controlled.
        self._max_history_turns = 6


    # --------------------------------------------------------------------------
    # LLM node
    # --------------------------------------------------------------------------

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[llm.FunctionTool],
        model_settings,
    ) -> AsyncIterable[llm.ChatChunk]:

        async for chunk in Agent.default.llm_node(
            self,
            chat_ctx,
            tools,
            model_settings,
        ):
            yield chunk


    # --------------------------------------------------------------------------
    # TTS node
    # --------------------------------------------------------------------------

    async def tts_node(
        self,
        text: AsyncIterable[str],
        model_settings,
    ):

        async def clean_text_stream():
            buffer = ""

            async for chunk in text:
                buffer += chunk

                # Release complete sentences as soon as we see a
                # sentence-ending character, so numbers/words never
                # get split across what we send to TTS.
                while True:
                    match = _SENTENCE_BOUNDARY_RE.search(buffer)
                    if not match:
                        break

                    idx = match.end()
                    sentence, buffer = buffer[:idx], buffer[idx:]

                    if sentence.strip():
                        yield _clean_sentence(sentence)

            # Flush whatever's left when the stream ends (covers
            # short replies with no terminal punctuation).
            if buffer.strip():
                yield _clean_sentence(buffer)


        async for audio_frame in Agent.default.tts_node(
            self,
            clean_text_stream(),
            model_settings,
        ):
            yield _apply_gain(audio_frame)


# ------------------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------------------

async def entrypoint(ctx: agents.JobContext):

    logger.info(
        f"Connecting to room: {ctx.room.name}"
    )

    # Connect to LiveKit audio.
    await ctx.connect(
        auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY
    )


    # --------------------------------------------------------------------------
    # Silero VAD
    # --------------------------------------------------------------------------

    vad = silero.VAD.load(
        min_silence_duration=0.45,
        min_speech_duration=0.25,
        prefix_padding_duration=0.15,
        activation_threshold=0.60,
    )


    # --------------------------------------------------------------------------
    # Turn handling
    # --------------------------------------------------------------------------

    turn_handling = TurnHandlingOptions(

        # Deepgram handles endpointing.
        turn_detection="stt",

        endpointing={
            "mode": "fixed",
            "min_delay": 0.0,
            "max_delay": 0.6,        # removes dead air before responding
        },

        interruption={
            "enabled": True,
            "mode": "vad",
            "min_duration": 0.35,
            "min_words": 2,
            "false_interruption_timeout": 1.5,
            "resume_false_interruption": True,
        },

        preemptive_generation={
            "enabled": True,
            "preemptive_tts": True,  # TTS starts before transcript is final
            "max_speech_duration": 8.0,
            "max_retries": 2,
        },
    )


    # --------------------------------------------------------------------------
    # Rime Coda TTS
    #
    # Celeste = female base voice
    # hi = Hindi
    # bySentence = cleaner sentence-level synthesis
    # NOTE: for Rime, speed_alpha LOWER than 1.0 = FASTER speech.
    # time_scale_factor / reduce_latency are ignored by Coda over WebSocket.
    # --------------------------------------------------------------------------

    tts = rime.TTS(
        model="coda",
        speaker="luna",
        lang="eng",
        sample_rate=22050,
        use_websocket=True,
        segment="bySentence",
        speed_alpha=0.95,            # 0.7–0.9 = faster; raise toward 1.0 if too fast
    )


    # --------------------------------------------------------------------------
    # Agent Session
    # --------------------------------------------------------------------------

    session = AgentSession(

        # ----------------------------------------------------------------------
        # Deepgram STT
        # ----------------------------------------------------------------------

        stt=deepgram.STT(
            model="nova-3",
            language="hi",
            interim_results=True,
            smart_format=True,
            endpointing_ms=100,

            keyterm=[
                "UPI",
                "EMI",
                "NEFT",
                "OTP",
                "order",
                "track",
                "refund",
                "delivery",
                "return",
                "payment",
                "account",
            ],
        ),


        # ----------------------------------------------------------------------
        # Groq LLM
        # ----------------------------------------------------------------------

        llm=openai.LLM(
            model="openai/gpt-oss-20b",
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
            temperature=0.2,
            max_completion_tokens=60,
            top_p=0.9,
            reasoning_effort="low",
        ),


        # ----------------------------------------------------------------------
        # Rime TTS
        # ----------------------------------------------------------------------

        tts=tts,

        vad=vad,

        turn_handling=turn_handling,
    )


    # --------------------------------------------------------------------------
    # Deepgram transcript logger
    # --------------------------------------------------------------------------

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(
        event: UserInputTranscribedEvent
    ):

        logger.info(
            f"🎤 USER TRANSCRIPT: "
            f"{event.transcript} "
            f"(final={event.is_final}, "
            f"language={event.language})"
        )


    # --------------------------------------------------------------------------
    # Start Agent Session
    # --------------------------------------------------------------------------

    await session.start(

        room=ctx.room,

        agent=HinglishSupportAgent(),

        room_input_options=RoomInputOptions(),
    )


    # --------------------------------------------------------------------------
    # Initial greeting (energetic)
    # --------------------------------------------------------------------------

    await session.generate_reply(
        instructions=(
            "Say exactly: "
            "'नमस्ते! मैं sporthi हूँ! बताइए, "
            "आज कैसे help करूँ?'"
        )
    )


# ------------------------------------------------------------------------------
# Run worker
# ------------------------------------------------------------------------------

if __name__ == "__main__":

    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint
        )
    )