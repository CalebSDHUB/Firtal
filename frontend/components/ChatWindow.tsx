"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import { sendMessage, type ChatMessage } from "@/lib/api";
import MessageBubble from "./MessageBubble";

export default function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [meta, setMeta] = useState<{ tokens: number; turn: number } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const res = await sendMessage(text, conversationId);
      setConversationId(res.conversation_id);
      setMeta({ tokens: res.tokens_used, turn: res.turn_number });
      setMessages((prev) => [...prev, { role: "agent", content: res.reply }]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setMessages([]);
    setConversationId(undefined);
    setMeta(null);
    setError(null);
  }

  return (
    <div className="flex flex-col h-full">
      {/* Message area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-3">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-3 text-zinc-500">
            <span className="text-4xl">💬</span>
            <p className="text-sm">Ask anything about Firetal&apos;s internal systems.</p>
            <div className="flex flex-wrap gap-2 mt-2 justify-center">
              {[
                "How do I deploy a new app?",
                "Where are secrets stored?",
                "What is rate limiting?",
              ].map((s) => (
                <button
                  key={s}
                  onClick={() => setInput(s)}
                  className="rounded-full border border-zinc-700 px-3 py-1 text-xs text-zinc-400 hover:border-indigo-500 hover:text-indigo-400 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-sm bg-zinc-800 px-4 py-3">
              <span className="flex gap-1">
                <span className="h-2 w-2 rounded-full bg-zinc-500 animate-bounce [animation-delay:0ms]" />
                <span className="h-2 w-2 rounded-full bg-zinc-500 animate-bounce [animation-delay:150ms]" />
                <span className="h-2 w-2 rounded-full bg-zinc-500 animate-bounce [animation-delay:300ms]" />
              </span>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg bg-red-950 border border-red-800 px-4 py-2.5 text-sm text-red-300">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Footer meta */}
      {meta && (
        <div className="px-4 pb-1 flex gap-4 text-xs text-zinc-600">
          <span>Turn {meta.turn} / 10</span>
          <span>{meta.tokens} tokens used</span>
          {meta.turn >= 8 && (
            <span className="text-yellow-600">
              ⚠ {10 - meta.turn} turn{10 - meta.turn !== 1 ? "s" : ""} left
            </span>
          )}
        </div>
      )}

      {/* Input bar */}
      <form
        onSubmit={handleSubmit}
        className="flex gap-2 border-t border-zinc-800 px-4 py-3"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about internal systems…"
          disabled={loading}
          className="flex-1 rounded-xl bg-zinc-800 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 outline-none focus:ring-2 focus:ring-indigo-600 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
        {messages.length > 0 && (
          <button
            type="button"
            onClick={handleReset}
            className="rounded-xl border border-zinc-700 px-3 py-2.5 text-sm text-zinc-400 hover:text-zinc-200 transition-colors"
            title="New conversation"
          >
            ↺
          </button>
        )}
      </form>
    </div>
  );
}
