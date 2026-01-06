import { useEffect, useRef, useState } from "react";

export default function ChatWidget({ apiBase }) {
  const [open, setOpen] = useState(false);

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loadingText, setLoadingText] = useState(false);

  const [isVoiceOn, setIsVoiceOn] = useState(false);
  const [liveUserTranscript, setLiveUserTranscript] = useState("");

  const pcRef = useRef(null);
  const dcRef = useRef(null);
  const localStreamRef = useRef(null);

  const remoteAudioElRef = useRef(null);
  const ttsAudioElRef = useRef(null);

  const endRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [open, messages, liveUserTranscript, loadingText]);

  const speakTTS = async (text, voice) => {
    try {
      const r = await fetch(`${apiBase}/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice }),
      });
      if (!r.ok) throw new Error(await r.text());

      const blob = await r.blob();
      const url = URL.createObjectURL(blob);

      const el = ttsAudioElRef.current;
      if (el) {
        el.src = url;
        await el.play().catch(() => {});
      }

      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch {
      // ignore tts failures
    }
  };

  const voiceByIntent = {
    sales: "ash",
    marketing: "sage",
    technical_support: "ash",
    order_logistics: "sage",
  };

  const sendTextMessage = async () => {
    // If the user is typing/sending, don't keep voice capture running.
    if (isVoiceOn) {
      try {
        await stopRealtimeVoice();
      } catch {
        // ignore
      }
    }

    const text = input.trim();
    if (!text || loadingText) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setLoadingText(true);

    try {
      const res = await fetch(`${apiBase}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "ai", text: data.response, intent: data.intent },
      ]);

      const voice = voiceByIntent[data.intent] || undefined;
      await speakTTS(data.response, voice);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: `Error: ${e?.message || String(e)}` },
      ]);
    } finally {
      setLoadingText(false);
    }
  };

  const startRealtimeVoice = async () => {
    if (isVoiceOn) return;

    const pc = new RTCPeerConnection();
    pcRef.current = pc;

    const dc = pc.createDataChannel("oai-events");
    dcRef.current = dc;

    pc.ontrack = (event) => {
      const [remoteStream] = event.streams;
      if (remoteAudioElRef.current && remoteStream) {
        remoteAudioElRef.current.srcObject = remoteStream;
      }
    };

    const localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    localStreamRef.current = localStream;
    localStream.getTracks().forEach((t) => pc.addTrack(t, localStream));

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    const sdpRes = await fetch(`${apiBase}/realtime/call`, {
      method: "POST",
      headers: { "Content-Type": "application/sdp" },
      body: offer.sdp,
    });

    if (!sdpRes.ok) throw new Error(await sdpRes.text());
    const answerSdp = await sdpRes.text();
    await pc.setRemoteDescription({ type: "answer", sdp: answerSdp });

    const handleAgentTurn = async (transcript) => {
      const text = (transcript || "").trim();
      if (!text) return;

      setLiveUserTranscript("");
      setMessages((prev) => [...prev, { role: "user", text }]);

      try {
        const res = await fetch(`${apiBase}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text }),
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();

        setMessages((prev) => [
          ...prev,
          { role: "ai", text: data.response, intent: data.intent },
        ]);

        const voice = voiceByIntent[data.intent] || undefined;
        await speakTTS(data.response, voice);
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          { role: "ai", text: `Voice routed-chat error: ${err?.message || String(err)}` },
        ]);
      }
    };

    dc.onmessage = (e) => {
      let msg;
      try {
        msg = JSON.parse(e.data);
      } catch {
        return;
      }

      if (
        (msg.type === "conversation.item.input_audio_transcription.delta" ||
          msg.type === "conversation.item.input_audio_transcription.partial") &&
        typeof msg.delta === "string"
      ) {
        setLiveUserTranscript((prev) => prev + msg.delta);
      }

      if (
        msg.type === "conversation.item.input_audio_transcription.completed" &&
        typeof msg.transcript === "string"
      ) {
        handleAgentTurn(msg.transcript);
      }
    };

    dc.onopen = () => {
      setIsVoiceOn(true);

      // Reinforce settings on the client side too.
      dc.send(
        JSON.stringify({
          type: "session.update",
          session: {
            modalities: ["text", "audio"],
            input_audio_transcription: { model: "whisper-1" },
            turn_detection: { type: "server_vad" },
          },
        })
      );
    };
  };

  const stopRealtimeVoice = async () => {
    setIsVoiceOn(false);

    try {
      dcRef.current?.close();
    } catch {
      // ignore
    }
    dcRef.current = null;

    try {
      pcRef.current?.close();
    } catch {
      // ignore
    }
    pcRef.current = null;

    try {
      localStreamRef.current?.getTracks().forEach((t) => t.stop());
    } catch {
      // ignore
    }
    localStreamRef.current = null;

    if (remoteAudioElRef.current) remoteAudioElRef.current.srcObject = null;
    setLiveUserTranscript("");
  };

  const onVoiceClick = async () => {
    try {
      if (isVoiceOn) await stopRealtimeVoice();
      else await startRealtimeVoice();
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: `Voice error: ${err?.message || String(err)}` },
      ]);
      await stopRealtimeVoice();
    }
  };

  useEffect(() => {
    return () => {
      stopRealtimeVoice();
    };
  }, []);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        style={styles.launcher}
        aria-label={open ? "Close chat" : "Open chat"}
        title={open ? "Close chat" : "Chat"}
      >
        {open ? "×" : <ChatIcon />}
      </button>

      {open ? (
        <div style={styles.panel}>
          <div style={styles.panelHeader}>
            <div>
              <div style={styles.panelTitle}>ElectroMart AI</div>
              <div style={styles.panelSub}>
                {isVoiceOn ? "Voice: On" : "Voice: Off"}
              </div>
            </div>
            <button type="button" onClick={() => setOpen(false)} style={styles.closeBtn}>
              ×
            </button>
          </div>

          <div style={styles.chat}>
            {liveUserTranscript ? (
              <div style={{ ...styles.row, justifyContent: "flex-end", opacity: 0.85 }}>
                <div style={{ ...styles.bubble, background: "#334155" }}>{liveUserTranscript}</div>
              </div>
            ) : null}

            {messages.map((m, i) => (
              <div
                key={i}
                style={{
                  ...styles.row,
                  justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                }}
              >
                <div
                  style={{
                    ...styles.bubble,
                    background: m.role === "user" ? "#4f46e5" : "#1f2937",
                  }}
                >
                  {m.role === "ai" && m.intent ? (
                    <div style={styles.intentPill}>{m.intent}</div>
                  ) : null}
                  {m.text}
                </div>
              </div>
            ))}

            {loadingText ? <div style={styles.loading}>Thinking…</div> : null}
            <div ref={endRef} />
          </div>

          <div style={styles.inputRow}>
            <button
              type="button"
              onClick={onVoiceClick}
              style={{
                ...styles.iconBtn,
                ...(isVoiceOn ? styles.iconBtnActive : null),
              }}
              title={isVoiceOn ? "Stop voice" : "Start voice"}
              aria-label="Voice"
              disabled={loadingText}
            >
              <MicIcon />
            </button>

            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onFocus={() => {
                if (isVoiceOn) stopRealtimeVoice();
              }}
              placeholder="Ask something…"
              style={styles.input}
              onKeyDown={(e) => e.key === "Enter" && sendTextMessage()}
              disabled={loadingText}
            />

            <button
              onClick={sendTextMessage}
              style={styles.send}
              disabled={loadingText || !input.trim()}
            >
              Send
            </button>
          </div>

          <audio ref={remoteAudioElRef} autoPlay />
          <audio ref={ttsAudioElRef} autoPlay />
        </div>
      ) : null}
    </>
  );
}

function ChatIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M21 12a8 8 0 0 1-8 8H7l-4 3V12a8 8 0 1 1 18 0Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function MicIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3Z"
        stroke="currentColor"
        strokeWidth="2"
      />
      <path
        d="M19 11a7 7 0 0 1-14 0"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path d="M12 18v3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M8 21h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

const styles = {
  launcher: {
    position: "fixed",
    right: 18,
    bottom: 18,
    width: 54,
    height: 54,
    borderRadius: 999,
    border: "1px solid rgba(255,255,255,0.14)",
    background:
      "linear-gradient(180deg, rgba(79,70,229,0.95), rgba(67,56,202,0.95))",
    color: "white",
    cursor: "pointer",
    display: "grid",
    placeItems: "center",
    boxShadow: "0 18px 50px rgba(0,0,0,0.40)",
    zIndex: 9999,
    fontSize: 26,
    lineHeight: 1,
  },
  panel: {
    position: "fixed",
    right: 18,
    bottom: 86,
    width: "min(380px, calc(100vw - 36px))",
    height: "min(560px, calc(100vh - 120px))",
    borderRadius: 16,
    border: "1px solid rgba(255,255,255,0.10)",
    background: "rgba(15, 23, 42, 0.96)",
    boxShadow: "0 20px 60px rgba(0,0,0,0.50)",
    overflow: "hidden",
    zIndex: 9999,
    display: "flex",
    flexDirection: "column",
    color: "white",
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
  },
  panelHeader: {
    padding: "12px 12px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    borderBottom: "1px solid rgba(255,255,255,0.08)",
  },
  panelTitle: { fontWeight: 700, fontSize: 14 },
  panelSub: { fontSize: 12, opacity: 0.75, marginTop: 2 },
  closeBtn: {
    width: 34,
    height: 34,
    borderRadius: 10,
    border: "1px solid rgba(255,255,255,0.12)",
    background: "rgba(0,0,0,0.25)",
    color: "white",
    cursor: "pointer",
    fontSize: 22,
    lineHeight: 1,
  },
  chat: {
    flex: 1,
    overflowY: "auto",
    padding: 12,
    display: "flex",
    flexDirection: "column",
    gap: 10,
    background: "rgba(0,0,0,0.15)",
  },
  row: { display: "flex", width: "100%" },
  bubble: {
    maxWidth: "82%",
    padding: "10px 12px",
    borderRadius: 12,
    border: "1px solid rgba(255,255,255,0.08)",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    fontSize: 13,
  },
  intentPill: {
    display: "inline-block",
    fontSize: 11,
    padding: "2px 8px",
    borderRadius: 999,
    marginBottom: 6,
    border: "1px solid rgba(255,255,255,0.18)",
    opacity: 0.9,
    textTransform: "capitalize",
  },
  loading: { opacity: 0.75, fontStyle: "italic", fontSize: 13 },
  inputRow: {
    padding: 10,
    display: "flex",
    gap: 8,
    alignItems: "center",
    borderTop: "1px solid rgba(255,255,255,0.08)",
    background: "rgba(15, 23, 42, 0.98)",
  },
  iconBtn: {
    width: 40,
    height: 40,
    borderRadius: 10,
    border: "1px solid rgba(255,255,255,0.12)",
    background: "rgba(0,0,0,0.25)",
    color: "white",
    cursor: "pointer",
    display: "grid",
    placeItems: "center",
  },
  iconBtnActive: {
    border: "1px solid rgba(239, 68, 68, 0.6)",
    background: "rgba(239, 68, 68, 0.18)",
  },
  input: {
    flex: 1,
    padding: "10px 10px",
    borderRadius: 10,
    border: "1px solid rgba(255,255,255,0.12)",
    background: "rgba(0,0,0,0.25)",
    color: "white",
    outline: "none",
  },
  send: {
    padding: "10px 12px",
    borderRadius: 10,
    border: "none",
    background: "#22c55e",
    color: "#06110b",
    cursor: "pointer",
    fontWeight: 700,
  },
};
