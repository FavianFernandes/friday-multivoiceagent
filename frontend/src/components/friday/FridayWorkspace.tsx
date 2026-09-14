import React, { useEffect, useMemo, useRef, useState } from 'react';
import './FridayWorkspace.css';

export type FridayWorkspaceTab =
  | 'workspace'
  | 'overview'
  | 'understanding'
  | 'workflow'
  | 'demo'
  | 'evaluation'
  | 'rime'
  | 'architecture'
  | 'privacy';

type ConceptId = 'track' | 'travel' | 'qa' | 'accessibility' | 'productivity';

interface Concept {
  id: ConceptId;
  title: string;
  caseId: string;
  description: string;
  step1: { title: string; detail: string };
  step2: { title: string; detail: string };
  step3: { title: string; detail: string };
  userQuote: string;
  agentSpeech: string;
  progress: number;
  progressCaption: string;
}

export interface FridayWorkspaceProps {
  voiceState: string;
  isMicActive: boolean;
  measuredTtfa?: number;
  statusMessage?: string;
  activeSpeakerName: string;
  onToggleMic: () => void | Promise<void>;
  onInterrupt: () => void;
  onNavigate: (tab: FridayWorkspaceTab) => void;
  onOpenHistory: () => void;
  onRunScenario?: (input: string) => void;
}

const CONCEPTS: Record<ConceptId, Concept> = {
  track: {
    id: 'track',
    title: 'Checking Order',
    caseId: '#98765',
    description: 'Check delivery status',
    step1: { title: 'Order found', detail: 'Verified in BlueDart Hub Delhi' },
    step2: { title: 'Customer verified', detail: 'OTP & Voiceprint matched (+91 98*** 12345)' },
    step3: { title: 'Checking delivery status', detail: 'Querying live courier GPS location' },
    userQuote: 'ORD98765 ka live tracking batao bhai...',
    agentSpeech: 'Samajh gaya! Aapka order abhi out for delivery hai. By 4:30 PM deliver ho jayega. Anything else?',
    progress: 78,
    progressCaption: 'HANG TIGHT, ALMOST THERE...',
  },
  travel: {
    id: 'travel',
    title: 'Booking IRCTC Train',
    caseId: '#TK-4029',
    description: 'Trains, flights, buses',
    step1: { title: 'Route locked: NDLS → MMCT', detail: 'Rajdhani Express (12952) departing 16:55' },
    step2: { title: 'AC 2-Tier Berth confirmed', detail: 'Preference: Lower Berth & veg meals noted' },
    step3: { title: 'Confirming PNR & Tatkal quota', detail: 'Gateway pinging IRCTC booking servers' },
    userQuote: 'Bhai, mujhe Delhi se Mumbai ka AC 2-tier ticket chahiye...',
    agentSpeech: 'Ticket allocate ho gaya hai! Rajdhani Express me Coach A1, Berth 34 confirm hai. PNR ABC1234 generate ho gaya.',
    progress: 68,
    progressCaption: 'CONNECTING TO RAILWAY SERVERS...',
  },
  qa: {
    id: 'qa',
    title: 'Return & Refund Policy',
    caseId: '#RET-7712',
    description: 'General queries',
    step1: { title: 'Product identified', detail: 'Noise ColorFit Pulse 5 Smartwatch (Black)' },
    step2: { title: '7-Day Return window valid', detail: 'Eligible for 100% full refund to UPI' },
    step3: { title: 'Scheduling doorstep pickup', detail: 'Assigning nearest Ekart logistics partner' },
    userQuote: 'Yeh watch return ho sakti hai kya? Fit nahi baith raha...',
    agentSpeech: 'Haanji bilkul! 7 din ki easy replacement policy hai. Kal morning 11:00 AM home pickup schedule kar diya hai.',
    progress: 84,
    progressCaption: 'SCHEDULING PICKUP AGENT...',
  },
  accessibility: {
    id: 'accessibility',
    title: 'Hands-Free Voice Mode',
    caseId: '#HF-VOICE',
    description: 'Hands-free assistance',
    step1: { title: 'Ambient noise filter active', detail: '60dB road traffic & kitchen noise suppressed' },
    step2: { title: 'Bilingual sensitivity locked', detail: 'Debounce buffer: 2-3 words active' },
    step3: { title: 'Full-duplex listening active', detail: 'LiveKit armed for instant barge-in interrupt' },
    userQuote: 'Bhai thoda slow bolo aur cart open karo bina screen chuhe...',
    agentSpeech: 'Zaroor, tempo adjust kar diya hai. Aapka shopping cart screen par open hai jisme 3 items hain. Bolte hi checkout start ho jayega.',
    progress: 92,
    progressCaption: 'LIVEKIT FULL-DUPLEX LISTENING ACTIVE...',
  },
  productivity: {
    id: 'productivity',
    title: 'Voice Cart & Reminders',
    caseId: '#PRD-1052',
    description: 'Notes, emails, reminders',
    step1: { title: 'Voice memo captured', detail: 'Diwali festive gifting dry fruits & sweets' },
    step2: { title: 'Price comparison completed', detail: 'Found ₹240 lower price on Amazon Pantry' },
    step3: { title: 'Setting midnight price alert', detail: 'Synchronizing reminder with Google Calendar' },
    userQuote: 'Woh wala add to cart aur kal subah remind kar dena...',
    agentSpeech: 'Done! Kaju katli aur California Almonds cart me save ho gaye hain. Kal subah 10:00 AM reminder trigger hoga.',
    progress: 88,
    progressCaption: 'SYNCING CLOUD REMINDERS...',
  },
};

function WaveCanvas({ active }: { active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let raf = 0;
    let phase = 0;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const draw = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      ctx.clearRect(0, 0, w, h);

      const intensity = active ? 1.8 : 0.75;
      const centerY = h * 0.52;

      for (let line = 0; line < 3; line++) {
        ctx.beginPath();
        for (let x = 0; x <= w; x += 8) {
          const envelope = Math.exp(-Math.pow((x - w * 0.5) / (w * 0.38), 2));
          const y =
            centerY +
            Math.sin(x * 0.012 + phase + line * 0.7) *
              10 *
              intensity *
              envelope;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.strokeStyle =
          line === 0
            ? 'rgba(255,42,133,0.13)'
            : line === 1
              ? 'rgba(255,123,0,0.09)'
              : 'rgba(0,229,255,0.06)';
        ctx.lineWidth = line === 0 ? 1.5 : 1;
        ctx.stroke();
      }

      phase += active ? 0.045 : 0.018;
      raf = requestAnimationFrame(draw);
    };

    resize();
    window.addEventListener('resize', resize);
    draw();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
    };
  }, [active]);

  return <canvas ref={canvasRef} className="friday-wave-canvas" aria-hidden="true" />;
}

const Icon = ({ type }: { type: ConceptId | 'mic' | 'user' | 'menu' | 'package' }) => {
  if (type === 'menu') {
    return (
      <svg viewBox="0 0 22 18" fill="none">
        <path d="M1 2h20M1 9h15M1 16h20" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
      </svg>
    );
  }

  if (type === 'user') {
    return (
      <svg viewBox="0 0 24 24" fill="none">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" strokeWidth="2" />
        <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" />
      </svg>
    );
  }

  if (type === 'mic') {
    return (
      <svg viewBox="0 0 36 36" fill="none">
        <rect x="13" y="5" width="10" height="17" rx="5" fill="url(#fridayMicGrad)" />
        <path d="M8 17c0 5.523 4.477 10 10 10s10-4.477 10-10" stroke="url(#fridayMicGrad)" strokeWidth="2.8" strokeLinecap="round" />
        <path d="M18 27v6M13 33h10" stroke="url(#fridayMicGrad)" strokeWidth="2.8" strokeLinecap="round" />
        <defs>
          <linearGradient id="fridayMicGrad" x1="13" y1="5" x2="25" y2="33">
            <stop stopColor="#FF5C8A" />
            <stop offset=".5" stopColor="#FFAA5B" />
            <stop offset="1" stopColor="#FFD166" />
          </linearGradient>
        </defs>
      </svg>
    );
  }

  if (type === 'package') {
    return (
      <svg viewBox="0 0 24 24" fill="none">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4Z" stroke="currentColor" strokeWidth="1.8" />
        <path d="m3.27 6.96 8.73 5.05 8.73-5.05M12 22.08V12" stroke="currentColor" strokeWidth="1.8" />
      </svg>
    );
  }

  const common = <></>;
  void common;

  if (type === 'travel') {
    return (
      <svg viewBox="0 0 24 24" fill="none">
        <rect x="4" y="3" width="16" height="16" rx="2" stroke="currentColor" strokeWidth="1.8" />
        <path d="M4 11h16M12 3v8m-4 8-2 3m10-3 2 3" stroke="currentColor" strokeWidth="1.8" />
        <circle cx="8" cy="15" r="1" fill="currentColor" />
        <circle cx="16" cy="15" r="1" fill="currentColor" />
      </svg>
    );
  }

  if (type === 'qa') {
    return (
      <svg viewBox="0 0 24 24" fill="none">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" stroke="currentColor" strokeWidth="1.8" />
        <path d="M14 2v6h6M16 13H8m8 4H8m2-8H8" stroke="currentColor" strokeWidth="1.8" />
      </svg>
    );
  }

  if (type === 'accessibility') {
    return (
      <svg viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="1.8" />
        <path d="M5 21v-2a7 7 0 0 1 14 0v2" stroke="currentColor" strokeWidth="1.8" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" fill="none">
      <rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.8" />
      <path d="M8 9h8m-8 4h8m-8 4h5" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
};

export const FridayWorkspace: React.FC<FridayWorkspaceProps> = ({
  voiceState,
  isMicActive,
  measuredTtfa = 64,
  
  onToggleMic,
  onInterrupt,
  onNavigate,
  onOpenHistory,
  onRunScenario,
}) => {
  const [selected, setSelected] = useState<ConceptId>('track');
  const [menuOpen, setMenuOpen] = useState(false);
  const [architectureOpen, setArchitectureOpen] = useState(false);

  const concept = CONCEPTS[selected];

  const listening =
    isMicActive ||
    voiceState === 'listening' ||
    voiceState === 'understanding' ||
    voiceState === 'checking';

  const speaking = voiceState === 'speaking';
  const statusLabel = speaking ? 'Rime Speaking' : listening ? 'Listening' : 'Rime Connected';

  const selectConcept = (id: ConceptId) => {
    setSelected(id);
    onRunScenario?.(CONCEPTS[id].userQuote);
  };

  const navItems = useMemo(
    () => [
      ['workspace', 'Workspace'],
      ['understanding', 'Understanding'],
      ['workflow', 'Workflow Pipeline'],
      ['demo', 'Guided Demo'],
      ['evaluation', 'Evaluation Lab'],
      ['rime', 'Rime Engine'],
      ['architecture', 'Architecture'],
      ['privacy', 'Privacy'],
    ] as const,
    []
  );

  return (
    <div className="friday-shell">
      <div className="friday-glow friday-glow-tl" />
      <div className="friday-glow friday-glow-center" />
      <div className="friday-glow friday-glow-br" />
      <div className="friday-glow friday-glow-left" />
      <WaveCanvas active={listening || speaking} />

      <div className="friday-container">
        <header className="friday-nav">
          <div className="friday-nav-left">
            <button
              className="friday-icon-btn"
              aria-label="Open navigation"
              onClick={() => setMenuOpen((v) => !v)}
            >
              <Icon type="menu" />
            </button>

            <div className="friday-brand">
              <div className="friday-eq" aria-hidden="true">
                {[12, 22, 16, 24, 10].map((h, i) => (
                  <span key={i} style={{ height: h }} />
                ))}
              </div>
              <div>
                <div className="friday-logo">Friday!</div>
                <div className="friday-logo-sub">SPEAK AND YOUR WORK IS DONE.</div>
              </div>
            </div>
          </div>

          <div className="friday-nav-center">
            <span>MADE FOR INDIA</span>
            <small>REAL CONVERSATIONS. REAL POSSIBILITIES.</small>
          </div>

          <div className="friday-nav-right">
            <button className="friday-profile" onClick={onOpenHistory}>
              <span className="friday-avatar"><Icon type="user" /></span>
              <span>Profile</span>
            </button>

            <button className="friday-status" onClick={() => setArchitectureOpen(true)}>
              <span className="friday-status-dot" />
              <span>{statusLabel}</span>
              <strong>{Math.round(measuredTtfa)} ms</strong>
              <span>›</span>
            </button>
          </div>

          {menuOpen && (
            <div className="friday-menu">
              {navItems.map(([tab, label]) => (
                <button
                  key={tab}
                  onClick={() => {
                    setMenuOpen(false);
                    onNavigate(tab);
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          )}
        </header>

        <main className="friday-main">
          <section className="friday-hero-left">
            <div>
              <h1>Voice assisted<br /><span>site!</span></h1>
              <p>JUST SAY IT.<br />WE’LL BE THERE FOR YOU.</p>
            </div>

            <div className="friday-bags" aria-hidden="true">
              <div className="friday-bag friday-bag-back"><span /></div>
              <div className="friday-bag friday-bag-front"><span /><i /></div>
              <div className="friday-bag-shadow" />
            </div>
          </section>

          <section className="friday-voice-center">
            <div className="friday-center-header">
              <h2>Friday!</h2>
              <p>YOUR VOICE ASSISTANT</p>
            </div>

            <div className="friday-voice-stage">
              <div className={`friday-orb-glow ${listening ? 'active' : ''}`} />
              <div className="friday-radar" />
              <div className="friday-radar delay" />

              <button
                className={`friday-orb ${listening ? 'listening' : ''}`}
                onClick={speaking ? onInterrupt : onToggleMic}
                aria-label={speaking ? 'Interrupt assistant' : 'Tap to speak'}
              >
                <span className="friday-orb-ring" />
                <span className="friday-orb-core">
                  <Icon type="mic" />
                </span>
              </button>
            </div>

            <div className="friday-orb-label">
              <strong>{speaking ? 'TAP TO INTERRUPT' : listening ? 'LISTENING (HINGLISH)...' : 'TAP TO SPEAK'}</strong>
              <span>ASSISTANCE. IN HINGLISH. NATURALLY.</span>
            </div>

            <div className="friday-ribbon">
              <strong>User:</strong>
              <span>“{concept.userQuote}”</span>
            </div>

            {isMicActive && (
              <div className="friday-status-message">
                {voiceState === 'error' ? 'Microphone unavailable' : 'Live microphone active'}
              </div>
            )}
          </section>

          <section className="friday-action-wrap">
            <div className="friday-action-card">
              <div className="friday-action-header">
                <span>CURRENT ACTION</span>
                <b><i /> ACTIVE</b>
              </div>

              <div className="friday-subject">
                <div className={`friday-subject-icon ${selected}`}>
                  <Icon type={selected} />
                </div>
                <div>
                  <h3>{concept.title}</h3>
                  <span>{concept.caseId}</span>
                </div>
              </div>

              <div className="friday-stepper">
                {[concept.step1, concept.step2].map((step) => (
                  <React.Fragment key={step.title}>
                    <div className="friday-step completed">
                      <span>✓</span>
                      <div><strong>{step.title}</strong><small>{step.detail}</small></div>
                    </div>
                    <div className="friday-step-line completed" />
                  </React.Fragment>
                ))}

                <div className="friday-step current">
                  <span className="pulse" />
                  <div><strong>{concept.step3.title}</strong><small>{concept.step3.detail}</small></div>
                </div>
              </div>

              <div className="friday-dialogue">
                <div className="friday-dialogue-head">
                  <span>R</span>
                  <div>
                    <strong>Rime Arcana V3</strong>
                    <small>Voice: Seraphina (Bilingual)</small>
                  </div>
                </div>
                <p>“{concept.agentSpeech}”</p>
              </div>

              <div className="friday-progress">
                <div><span style={{ width: `${concept.progress}%` }} /></div>
                <small>{concept.progressCaption}</small>
              </div>
            </div>
          </section>
        </main>

        <nav className="friday-concepts" aria-label="Action concepts">
          {(Object.keys(CONCEPTS) as ConceptId[]).map((id) => (
            <button
              key={id}
              className={`friday-concept ${selected === id ? 'active' : ''}`}
              onClick={() => selectConcept(id)}
            >
              <span className={`friday-concept-icon ${id}`}><Icon type={id} /></span>
              <strong>{id === 'track' ? 'Track a Package' : CONCEPTS[id].title}</strong>
              <small>{CONCEPTS[id].description}</small>
            </button>
          ))}
        </nav>

        <footer className="friday-footer">
          <span>VOICE FIRST</span><i>|</i><span>MADE FOR REAL PEOPLE</span>
        </footer>
      </div>

      {architectureOpen && (
        <div className="friday-modal-backdrop" onClick={() => setArchitectureOpen(false)}>
          <div className="friday-modal" onClick={(e) => e.stopPropagation()}>
            <button className="friday-modal-close" onClick={() => setArchitectureOpen(false)}>×</button>
            <div className="friday-hackathon">DATAFORGE × RIME HACKATHON</div>
            <h2>Why Every Voice Assistant Sounds Stupid In Hinglish</h2>
            <p className="friday-modal-sub">Architecture & Live Telemetry Inspector</p>

            <div className="friday-pipeline">
              {[
                ['RUNNER 1', 'The Ears (STT)', 'Deepgram Nova-3'],
                ['RUNNER 2', 'The Brain (LLM)', 'GPT-4o Stream'],
                ['RUNNER 3', 'The Mouth (TTS)', 'Rime Arcana V3'],
                ['RUNNER 4', 'The Referee', 'LiveKit Agents'],
              ].map(([num, title, model], i) => (
                <React.Fragment key={num}>
                  <div className={`friday-pipeline-step ${i === 2 ? 'highlight' : ''}`}>
                    <small>{num}</small>
                    <h3>{title}</h3>
                    <b>{model}</b>
                    <span>{i === 2 ? `Voice: Seraphina | ${Math.round(measuredTtfa)}ms` : i === 0 ? 'WER < 10%' : i === 1 ? 'Streaming: Active' : 'Duplex Latency: 650ms'}</span>
                  </div>
                  {i < 3 && <em>→</em>}
                </React.Fragment>
              ))}
            </div>

            <div className="friday-problems">
              <div><b>1. Language Debouncing</b><p>Waits for enough target-language context before switching.</p></div>
              <div><b>2. Consistent Voice Identity</b><p>One bilingual voice keeps the assistant personality consistent.</p></div>
              <div><b>3. Sub-800ms Latency</b><p>STT, LLM and TTS stream continuously instead of waiting for full sentences.</p></div>
              <div><b>4. Real Interruption Handling</b><p>LiveKit detects barge-in and stops queued speech.</p></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FridayWorkspace;
