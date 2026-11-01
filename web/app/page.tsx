"use client";

import { useState } from "react";
import type { AskResponse } from "./types";

const MAX_CHARS = 500;
const EXAMPLES = [
  "How much food grain does a priority ration card household get?",
  "आयुष्मान भारत में प्रति परिवार कितना कवरेज मिलता है?",
];

export default function Home() {
  const [q, setQ] = useState("");
  const [res, setRes] = useState<AskResponse | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [rated, setRated] = useState(false);

  async function ask() {
    setBusy(true); setErr(""); setRes(null); setRated(false);
    try {
      const r = await fetch("/api/ask", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ question: q, k: 5 }) });
      if (r.status === 429) throw new Error("Too many requests. Please wait a minute.");
      if (r.status === 503) throw new Error("The demo is currently unavailable.");
      if (!r.ok) throw new Error(`Request failed (${r.status}).`);
      setRes((await r.json()) as AskResponse);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Something went wrong.");
    } finally { setBusy(false); }
  }

  async function rate(rating: 1 | -1) {
    await fetch("/api/feedback", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ question: q, rating, reason: "" }) });
    setRated(true);
  }

  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: "24px 16px" }}>
      <h1 style={{ marginBottom: 4 }}>IndicRAG</h1>
      <p style={{ marginTop: 0, color: "#444" }}>Ask about Indian government schemes and services in English, हिन्दी or ಕನ್ನಡ. Answers cite their sources.</p>
      <p role="note" style={{ background: "#fff4d6", padding: 8, borderRadius: 6, fontSize: 14 }}>
        Do not enter Aadhaar, phone, PAN, bank or other personal details. Research demo: not legal or financial advice.
      </p>
      <form onSubmit={(e) => { e.preventDefault(); if (q.trim().length >= 3) void ask(); }}>
        <label htmlFor="q" style={{ display: "block", fontWeight: 600 }}>Your question</label>
        <textarea id="q" value={q} maxLength={MAX_CHARS} rows={3} onChange={(e) => setQ(e.target.value)}
          style={{ width: "100%", padding: 8, fontSize: 16, boxSizing: "border-box" }} />
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "#555" }}>
          <span>Try: {EXAMPLES.map((x) => (<button type="button" key={x} onClick={() => setQ(x)} style={{ marginRight: 6, fontSize: 12 }}>{x.slice(0, 28)}…</button>))}</span>
          <span>{q.length}/{MAX_CHARS}</span>
        </div>
        <button type="submit" disabled={busy || q.trim().length < 3} style={{ marginTop: 8, padding: "8px 16px", fontSize: 16 }}>
          {busy ? "Searching…" : "Ask"}
        </button>
      </form>

      {err && <p role="alert" style={{ color: "#b00020" }}>{err}</p>}

      {res && (
        <section aria-live="polite" style={{ marginTop: 20 }}>
          {res.answer ? <p style={{ fontSize: 18, lineHeight: 1.5 }}>{res.answer}</p>
            : <p style={{ fontSize: 16 }}><strong>{res.reason === "budget_exhausted" ? "Answer generation is paused." : res.reason === "pii_in_question" ? "Please remove personal details and ask again." : "No reliable answer found."}</strong> {res.note ?? ""}</p>}
          {res.sources.length > 0 && (
            <>
              <h2 style={{ fontSize: 16 }}>Sources</h2>
              <ol style={{ paddingLeft: 20 }}>
                {res.sources.map((s) => (
                  <li key={s.id} style={{ marginBottom: 6, opacity: s.cited || res.answer === null ? 1 : 0.6 }}>
                    <strong>[{s.id}]</strong> <a href={s.url} target="_blank" rel="noopener noreferrer">{s.title || s.doc_id}</a>
                    {s.cited ? " (cited)" : ""} <small style={{ color: "#555" }}>fetched {s.fetched_at.slice(0, 10)}</small>
                    {s.excerpt && <blockquote style={{ margin: "4px 0", color: "#333" }}>{s.excerpt}</blockquote>}
                  </li>
                ))}
              </ol>
            </>
          )}
          <p style={{ fontSize: 13, color: "#555" }}>Information valid as of {res.valid_as_of}. {res.disclaimer}</p>
          {!rated ? (
            <p>Was this helpful? <button onClick={() => void rate(1)}>Yes</button> <button onClick={() => void rate(-1)}>No</button></p>
          ) : <p>Thanks for the feedback.</p>}
        </section>
      )}
    </main>
  );
}
