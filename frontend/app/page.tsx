"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Citation,
  DocumentRow,
  chat,
  deleteDocument,
  listDocuments,
  uploadDocument,
} from "./api";

type Message =
  | { role: "user"; text: string }
  | { role: "assistant"; text: string; citations: Citation[] };

export default function Home() {
  const [docs, setDocs] = useState<DocumentRow[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [chatError, setChatError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      setDocs(await listDocuments());
    } catch (err) {
      setUploadError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      await uploadDocument(file);
      if (fileRef.current) fileRef.current.value = "";
      await refresh();
    } catch (err) {
      setUploadError((err as Error).message);
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteDocument(id);
      await refresh();
    } catch (err) {
      setUploadError((err as Error).message);
    }
  }

  async function handleAsk() {
    const q = question.trim();
    if (!q || pending) return;
    setPending(true);
    setChatError(null);
    setMessages((m) => [...m, { role: "user", text: q }]);
    setQuestion("");
    try {
      const res = await chat(q);
      setMessages((m) => [
        ...m,
        { role: "assistant", text: res.answer, citations: res.citations },
      ]);
    } catch (err) {
      setChatError((err as Error).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="container">
      <div className="header">
        <h1>docuchat</h1>
        <span className="sub">Chat with your documents — answers with citations.</span>
      </div>

      <div className="grid">
        <div className="panel">
          <h2>Documents</h2>

          <form className="upload" onSubmit={handleUpload}>
            <input ref={fileRef} type="file" accept=".pdf,.csv,.txt,.md" />
            <button type="submit" disabled={uploading}>
              {uploading ? "Uploading…" : "Upload"}
            </button>
          </form>
          {uploadError && <div className="error">{uploadError}</div>}

          {docs.length === 0 ? (
            <div className="empty">No documents yet. Upload a PDF, CSV, or text file.</div>
          ) : (
            docs.map((d) => (
              <div key={d.id} className="doc">
                <div className="name">{d.filename}</div>
                <div className="meta">
                  {d.num_chunks} chunks · {new Date(d.created_at).toLocaleString()}{" "}
                  <a
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      handleDelete(d.id);
                    }}
                  >
                    delete
                  </a>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="panel chat">
          <h2>Chat</h2>
          <div className="messages">
            {messages.length === 0 && (
              <div className="empty">
                Ask a question about your uploaded documents. Citations will link back to the
                exact source passages.
              </div>
            )}
            {messages.map((m, i) =>
              m.role === "user" ? (
                <div key={i} className="msg user">{m.text}</div>
              ) : (
                <div key={i} className="msg assistant">
                  {m.text}
                  {m.citations.length > 0 && (
                    <div className="citations">
                      {m.citations.map((c) => (
                        <div className="citation" key={c.chunk_id}>
                          <span className="marker">[{c.marker}]</span>
                          {c.filename}
                          {c.page ? `, p.${c.page}` : ""} · score {c.score.toFixed(3)} —{" "}
                          {c.snippet}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            )}
          </div>

          <div className="composer">
            <textarea
              placeholder="Ask a question…"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                  e.preventDefault();
                  handleAsk();
                }
              }}
            />
            <button onClick={handleAsk} disabled={pending}>
              {pending ? "Thinking…" : "Ask"}
            </button>
          </div>
          {chatError && <div className="error">{chatError}</div>}
        </div>
      </div>
    </div>
  );
}
