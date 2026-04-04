"use client";

import { useState, useRef, useEffect, useCallback, type DragEvent, type ChangeEvent } from "react";
import axios from "axios";
import {
  Send,
  Trash2,
  Globe,
  FileText,
  Loader2,
  Bot,
  User,
  PanelLeftClose,
  PanelLeftOpen,
  PlusCircle,
  ExternalLink,
  Upload,
  X,
  Sparkles,
  Database,
  CheckCircle2,
  AlertCircle,
  Info,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

interface Message {
  id: string;
  role: "user" | "bot";
  content: string;
  sources?: string[];
  timestamp: Date;
}

interface Toast {
  id: string;
  type: "success" | "error" | "info";
  message: string;
}

function uid() {
  return Math.random().toString(36).substring(2, 12);
}

function timeStr(d: Date) {
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function Home() {
  /* ── State ── */
  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("vels-chat-history");
      if (saved) {
        try {
          return JSON.parse(saved).map((m: Message) => ({
            ...m,
            timestamp: new Date(m.timestamp),
          }));
        } catch {
          /* ignore */
        }
      }
    }
    return [
      {
        id: uid(),
        role: "bot" as const,
        content:
          "Hello! 👋 I'm the Vels College AI Assistant.\n\nUpload PDFs or paste URLs in the sidebar, process them, and then ask me anything about the content!",
        timestamp: new Date(),
      },
    ];
  });

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [urls, setUrls] = useState(["", "", ""]);
  const [files, setFiles] = useState<File[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);

  const chatEnd = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  /* ── Effects ── */
  useEffect(() => {
    localStorage.setItem("vels-chat-history", JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const toast = useCallback((type: Toast["type"], message: string) => {
    const id = uid();
    setToasts((p) => [...p, { id, type, message }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 4000);
  }, []);

  /* ── Handlers ── */

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const text = input;
    setMessages((p) => [
      ...p,
      { id: uid(), role: "user", content: text, timestamp: new Date() },
    ]);
    setInput("");
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/query`, { query: text });
      setMessages((p) => [
        ...p,
        {
          id: uid(),
          role: "bot",
          content: res.data.answer,
          sources: res.data.sources,
          timestamp: new Date(),
        },
      ]);
    } catch {
      setMessages((p) => [
        ...p,
        {
          id: uid(),
          role: "bot",
          content:
            "Sorry, something went wrong. Make sure you've processed sources and the backend is running.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const processSources = async () => {
    const validUrls = urls.filter((u) => u.trim());
    if (validUrls.length === 0 && files.length === 0) {
      toast("error", "Add at least one URL or upload a PDF first.");
      return;
    }
    setIngesting(true);

    try {
      const pdfPaths: string[] = [];
      for (const f of files) {
        const fd = new FormData();
        fd.append("file", f);
        const res = await axios.post(`${API_BASE}/upload`, fd, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        pdfPaths.push(res.data.path);
      }

      await axios.post(`${API_BASE}/ingest`, {
        urls: validUrls.length > 0 ? validUrls : undefined,
        pdf_paths: pdfPaths.length > 0 ? pdfPaths : undefined,
      });

      toast("success", "Sources are being processed. This may take a minute.");
      setFiles([]);
    } catch {
      toast("error", "Failed to process sources. Check the backend.");
    } finally {
      setIngesting(false);
    }
  };

  const clearDB = async () => {
    if (!confirm("Clear the entire knowledge base?")) return;
    try {
      await axios.delete(`${API_BASE}/clear`);
      setMessages([
        {
          id: uid(),
          role: "bot",
          content: "Knowledge base cleared. Upload new sources to get started!",
          timestamp: new Date(),
        },
      ]);
      toast("success", "Database cleared.");
    } catch {
      toast("error", "Failed to clear database.");
    }
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const pdfs = Array.from(e.dataTransfer.files).filter(
      (f) => f.type === "application/pdf"
    );
    if (pdfs.length === 0) {
      toast("error", "Only PDF files are accepted.");
      return;
    }
    setFiles((p) => [...p, ...pdfs]);
  };

  const onFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const pdfs = Array.from(e.target.files).filter(
      (f) => f.type === "application/pdf"
    );
    setFiles((p) => [...p, ...pdfs]);
  };

  /* ── Toast icon ── */
  const toastIcon = (type: Toast["type"]) => {
    if (type === "success") return <CheckCircle2 size={18} />;
    if (type === "error") return <AlertCircle size={18} />;
    return <Info size={18} />;
  };

  /* ═══════════ RENDER ═══════════ */

  return (
    <div className="app-layout">
      {/* ── Toasts ── */}
      <div className="toast-container">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 50 }}
              className={`toast toast-${t.type}`}
            >
              {toastIcon(t.type)}
              {t.message}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* ── Sidebar Toggle (when closed) ── */}
      {!sidebarOpen && (
        <button className="sidebar-toggle" onClick={() => setSidebarOpen(true)}>
          <PanelLeftOpen size={20} />
        </button>
      )}

      {/* ═══════════ SIDEBAR ═══════════ */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ x: -320, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -320, opacity: 0 }}
            transition={{ type: "spring", damping: 26, stiffness: 220 }}
            className="sidebar"
          >
            {/* Header */}
            <div className="sidebar-header">
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <div
                    style={{
                      background: "var(--gradient-accent)",
                      borderRadius: "12px",
                      width: "38px",
                      height: "38px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Bot size={20} color="white" />
                  </div>
                  <div>
                    <h1>Vels College</h1>
                    <p>AI Knowledge Base</p>
                  </div>
                </div>
                <button
                  onClick={() => setSidebarOpen(false)}
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--text-muted)",
                    cursor: "pointer",
                    padding: "6px",
                  }}
                >
                  <PanelLeftClose size={18} />
                </button>
              </div>
            </div>

            {/* Scrollable Body */}
            <div className="sidebar-body custom-scrollbar">
              {/* URLs Section */}
              <section style={{ marginBottom: "28px" }}>
                <div className="section-title">
                  <Globe size={15} />
                  URLs
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {urls.map((url, i) => (
                    <div key={i}>
                      <label className="sidebar-input-label">URL {i + 1}</label>
                      <input
                        type="text"
                        value={url}
                        onChange={(e) => {
                          const next = [...urls];
                          next[i] = e.target.value;
                          setUrls(next);
                        }}
                        placeholder="https://example.com"
                        className="sidebar-input"
                      />
                    </div>
                  ))}
                </div>
                <button
                  className="btn-link"
                  onClick={() => setUrls([...urls, ""])}
                  style={{ marginTop: "8px" }}
                >
                  <PlusCircle size={15} /> Add another URL
                </button>
              </section>

              {/* PDF Section */}
              <section>
                <div className="section-title">
                  <FileText size={15} />
                  PDF Files
                </div>
                <p style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "12px" }}>
                  Upload PDF documents
                </p>

                <div
                  className={`drop-zone ${dragOver ? "active" : ""}`}
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={(e) => { e.preventDefault(); setDragOver(false); }}
                  onDrop={onDrop}
                  onClick={() => fileRef.current?.click()}
                >
                  <Upload
                    size={28}
                    style={{
                      color: dragOver ? "var(--accent)" : "var(--text-muted)",
                      marginBottom: "10px",
                      transition: "color 0.2s",
                    }}
                  />
                  <div className="drop-zone-text">Drag and drop files here</div>
                  <div className="drop-zone-sub">Limit 200MB per file • PDF</div>
                  <button
                    className="btn-browse"
                    onClick={(e) => {
                      e.stopPropagation();
                      fileRef.current?.click();
                    }}
                  >
                    Browse files
                  </button>
                  <input
                    ref={fileRef}
                    type="file"
                    accept=".pdf"
                    multiple
                    onChange={onFileSelect}
                    style={{ display: "none" }}
                  />
                </div>

                {/* File list */}
                {files.length > 0 && (
                  <div style={{ marginTop: "12px", display: "flex", flexDirection: "column", gap: "8px" }}>
                    {files.map((f, i) => (
                      <motion.div
                        key={`${f.name}-${i}`}
                        initial={{ opacity: 0, y: -8 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="file-chip"
                      >
                        <FileText size={16} style={{ color: "var(--accent)", flexShrink: 0 }} />
                        <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {f.name}
                        </span>
                        <button onClick={() => setFiles((p) => p.filter((_, j) => j !== i))}>
                          <X size={15} />
                        </button>
                      </motion.div>
                    ))}
                  </div>
                )}
              </section>
            </div>

            {/* Footer */}
            <div className="sidebar-footer">
              <button
                className="btn-primary"
                onClick={processSources}
                disabled={ingesting}
              >
                {ingesting ? (
                  <>
                    <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
                    Processing...
                  </>
                ) : (
                  <>
                    <Database size={18} />
                    Process Sources
                  </>
                )}
              </button>
              <button
                className="btn-danger"
                onClick={clearDB}
                style={{ marginTop: "8px" }}
              >
                <Trash2 size={15} />
                Clear Database
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ═══════════ MAIN CHAT AREA ═══════════ */}
      <main className="chat-area">
        {/* Header */}
        <div className="chat-header">
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <Sparkles size={26} style={{ color: "var(--accent)" }} />
            <div>
              <h1>Vels College Chatbot</h1>
              <p>AI-Powered Knowledge Assistant • Ask anything about Vels University</p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="messages-container custom-scrollbar">
          <div className="messages-inner">
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`message-row ${msg.role}`}
                >
                  {/* Avatar */}
                  <div className={`avatar ${msg.role === "bot" ? "avatar-bot" : "avatar-user"}`}>
                    {msg.role === "bot" ? (
                      <Bot size={18} color="white" />
                    ) : (
                      <User size={18} style={{ color: "var(--accent-light)" }} />
                    )}
                  </div>

                  {/* Bubble */}
                  <div className={`bubble ${msg.role === "bot" ? "bubble-bot" : "bubble-user"}`}>
                    <p>{msg.content}</p>

                    {msg.sources && msg.sources.length > 0 && (
                      <div className="sources-row">
                        {[...new Set(msg.sources)].slice(0, 5).map((src, i) => (
                          <a
                            key={i}
                            href={src}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="source-chip"
                          >
                            <ExternalLink size={11} />
                            {src.replace(/https?:\/\//, "").split("/")[0]}
                          </a>
                        ))}
                      </div>
                    )}

                    <div
                      className="bubble-time"
                      style={{ textAlign: msg.role === "user" ? "right" : "left" }}
                    >
                      {timeStr(msg.timestamp)}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Typing Indicator */}
            {loading && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                className="message-row"
              >
                <div className="avatar avatar-bot">
                  <Bot size={18} color="white" />
                </div>
                <div className="bubble bubble-bot typing-dots">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </div>
              </motion.div>
            )}

            <div ref={chatEnd} />
          </div>
        </div>

        {/* ── Input Bar ── */}
        <div className="input-bar-wrapper">
          <div className="input-bar-inner">
            <div className="input-bar">
              <textarea
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="Enter your question"
                onInput={(e) => {
                  const el = e.target as HTMLTextAreaElement;
                  el.style.height = "auto";
                  el.style.height = `${el.scrollHeight}px`;
                }}
              />
              <button
                className="btn-send"
                onClick={sendMessage}
                disabled={loading || !input.trim()}
              >
                <Send size={20} strokeWidth={2.5} />
              </button>
            </div>
            <div className="input-footer">
              Powered by Groq & LangChain • Vels University AI Knowledge Base
            </div>
          </div>
        </div>
      </main>

      {/* Spin keyframe for loader */}
      <style jsx global>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
