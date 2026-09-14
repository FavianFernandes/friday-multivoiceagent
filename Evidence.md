Rime Voice Robustness Evidence
1. Evidence Claim
Hard-voice / noisy-environment claim:
The voice agent was tested with loud background noise and traffic noise while handling multilingual and code-switched customer-support conversations. In the acceptance test, the agent continued to work correctly under the tested loud-noise conditions.
This evidence focuses on the voice pipeline's ability to operate in difficult acoustic conditions while processing Romanized Hinglish and Devanagari code-switched speech.
Important: This is an acceptance-test result from the scenarios actually tested. It is not a claim of guaranteed performance for every possible noise level, microphone, accent, device, or environment.
2. Acceptance Test
A. Cross-Language Customer & Technical Support
Test A1 — Romanized Hinglish
Input
"Mera account login nahi ho raha hai. Maine password reset link try kiya par OTP email par deliver hi nahi ho raha. Can you please check if my account is blocked?"
Expected behavior
Understand Romanized Hinglish with English technical terms.
Preserve the conversational meaning.
Respond as a customer-support agent.
Produce a clear spoken response.
Test A2 — Devanagari Code-Switched
Input
"मैंने yesterday app update किया था, उसके बाद से biometric authentication work नहीं कर रहा है। बार-बार 'Session Expired' show होता है।"
Expected behavior
Handle Devanagari Hindi mixed with English technical vocabulary.
Correctly understand the authentication/session issue.
Respond conversationally and clearly.
B. Public Services & Citizen Utilities
Test B1 — Ration Card / Documentation
Input
"Mera ration card update karwana tha. Kya address change ke liye electricity bill aur Aadhaar card scan upload karna mandatory hai, ya physically submit karna hoga?"
Expected behavior
Understand Romanized Hinglish.
Handle government-service terminology and English document names.
Provide a relevant conversational response.
Test B2 — Public Scheme / Subsidy
Input
"PM Awas Yojana का subsidy status check करना है। क्या verification team direct site visit करेगी या online approval मिलेगा?"
Expected behavior
Handle Devanagari Hindi with English terms.
Understand the user's question about verification and approval.
Respond naturally.
C. Additional Conversational Tests
Test C1 — Civic Complaint
Input
"Pichhle do hafte se hamare ward me water pipeline repair work pending hai. Complaint status 'in progress' dikha raha hai par site par koi worker nahi hai."
Test C2 — UPI Payment Failure
Input
"Payment UPI se deduct ho gaya aur bank statement me debit dikha raha hai, lekin order confirmation page par 'Transaction Failed' aa raha hai. Refund initiate kab hoga?"
Expected behavior for C1/C2
Understand multi-clause conversational input.
Identify the actual user issue.
Respond as a support agent rather than merely repeating keywords.
Maintain natural code-switched speech.
3. Noise Acceptance Procedure
Test Environment
The acceptance test was performed while introducing:
Loud background noise
Traffic noise
The purpose was to evaluate whether the voice interaction remained usable under difficult real-world acoustic conditions.
Procedure
For each scenario:
Start the voice agent.
Enable the microphone.
Introduce the specified loud/traffic background noise.
Speak the complete test input naturally.
Allow the agent to process the utterance.
Listen to the generated response.
Record whether the agent successfully completed the interaction.
Repeat with the remaining scenarios.
Pass condition
A scenario is considered a pass when the agent remains operational under the tested noise condition and produces a usable response to the spoken request.
4. Result
Acceptance Result
Result: PASS for the tested loud-background-noise and traffic-noise conditions.
During the acceptance test:
The agent continued functioning in loud background noise.
The agent continued functioning in traffic noise.
Romanized Hinglish scenarios were tested.
Devanagari code-switched scenarios were tested.
Customer/technical-support scenarios were tested.
Public-service/civic scenarios were tested.
Commerce/payment-support input was tested.
The tested conversations demonstrated that the system could continue the voice interaction despite difficult background acoustic conditions.
5. Rime / Voice Pipeline Evidence
Rime is used as the TTS component of the voice pipeline.
The relevant voice path is:
User Speech
    ↓
Microphone
    ↓
LiveKit
    ↓
Noise Cancellation / VAD
    ↓
Deepgram STT
    ↓
LLM
    ↓
Rime TTS
    ↓
LiveKit Audio
    ↓
User
The noise acceptance result therefore evaluates the end-to-end voice interaction, rather than Rime TTS in isolation.
The tested result supports the claim that the complete voice pipeline remained usable under the tested loud-noise and traffic-noise conditions.
6. Reproducible Test Fixture
The following fixture can be used for future acceptance runs.
TEST_ENVIRONMENT:
  background_noise:
    - loud_background_noise
    - traffic_noise

LANGUAGES:
  - Romanized Hinglish
  - Devanagari Hindi + English code-switching

DOMAINS:
  - customer_support
  - technical_support
  - public_services
  - civic_complaints
  - payments

SCENARIOS:
  A1 = account login / OTP delivery
  A2 = biometric authentication / session expired
  B1 = ration card / address change
  B2 = PM Awas Yojana / subsidy verification
  C1 = water pipeline repair complaint
  C2 = UPI payment / refund
Manual Acceptance Run
Run the voice agent and speak each fixture exactly once under the selected noise condition.
Record:
Scenario | Noise Condition | Speech Understood | Agent Responded | Pass/Fail
Example:
A1 | Loud background noise | Yes | Yes | PASS
A2 | Traffic noise         | Yes | Yes | PASS
B1 | Loud background noise | Yes | Yes | PASS
B2 | Traffic noise         | Yes | Yes | PASS
C1 | Loud background noise | Yes | Yes | PASS
C2 | Traffic noise         | Yes | Yes | PASS
7. Limitations
The acceptance test does not establish performance for:
Every possible background-noise level.
Every microphone or headset.
Every phone, browser, or audio device.
All Indian accents and dialects.
Extremely distorted or clipped audio.
Multiple simultaneous speakers.
Music or speech directly overlapping the user's voice.
Very long paragraph-length user input.
Long paragraph-style agent responses.
Known conversational limitation
The current system performs better with short, conversational turns. When the user speaks a long paragraph containing many sentences or multiple requests, the agent may not process the complete input correctly.
The agent also currently performs better when its response is concise rather than a long paragraph. This is a known limitation of the current conversational voice implementation and should be considered during evaluation.
8. Acceptance Scope
This evidence should be interpreted as:
Tested and passed: end-to-end voice interaction under the loud background and traffic-noise conditions used during the acceptance test.
It should not be interpreted as:
Guaranteed noise immunity under all real-world acoustic conditions.
Further quantitative testing should measure:
First-audio latency
Barge-in recovery latency
STT/TTS word error rate
Task completion rate
Feminine grammatical accuracy
Prosody and naturalness
