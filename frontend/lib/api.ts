const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ChatMessage {
  role: "user" | "agent";
  content: string;
}

export interface ChatResponse {
  reply: string;
  conversation_id: string;
  tokens_used: number;
  turn_number: number;
}

export interface HealthResponse {
  status: string;
  version: string;
}

export async function sendMessage(
  message: string,
  conversationId?: string
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail ?? `HTTP ${res.status}`);
  }

  return res.json();
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error("Agent offline");
  return res.json();
}
