"use client";

import { useCallback, useEffect, useState } from "react";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";

export default function ChatConsole() {
  const [token, setToken] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const t = localStorage.getItem("bfsi_token");
    if (t) setToken(t);
  }, []);

  const login = async () => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "customer@demo.com", password: "demo1234" }),
    });
    const data = await res.json();
    localStorage.setItem("bfsi_token", data.access_token);
    setToken(data.access_token);
  };

  const send = useCallback(async () => {
    if (!input.trim()) return;
    setMessages((m) => [...m, { role: "user", content: input }]);
    setInput("");
    setBusy(true);
    try {
      const res = await fetch(`${API_BASE}/chats`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: input }),
      });
      const data = await res.json();
      setMessages((m) => [...m, { role: "assistant", content: data.reply }]);
    } finally {
      setBusy(false);
    }
  }, [input, token]);

  return (
    <main style={{ maxWidth: 800, margin: "0 auto", padding: 24 }}>
      <h1>BFSI AI Agent — Demo Console</h1>
      {!token ? (
        <button onClick={login}>Login (demo customer)</button>
      ) : (
        <>
          <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, minHeight: 300 }}>
            {messages.map((m, i) => (
              <p key={i} style={{ textAlign: m.role === "user" ? "right" : "left" }}>
                <strong>{m.role === "user" ? "You" : "Agent"}:</strong> {m.content}
              </p>
            ))}
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <input
              style={{ flex: 1, padding: 8 }}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Ask about your loan eligibility..."
            />
            <button onClick={send} disabled={busy}>
              Send
            </button>
          </div>
        </>
      )}
    </main>
  );
}