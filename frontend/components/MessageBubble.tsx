import type { ChatMessage } from "@/lib/api";

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "rounded-br-sm bg-indigo-600 text-white"
            : "rounded-bl-sm bg-zinc-800 text-zinc-100"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}
