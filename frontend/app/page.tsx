import ChatWindow from "@/components/ChatWindow";
import StatusBadge from "@/components/StatusBadge";

export default function Home() {
  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-zinc-800 px-6 py-4">
        <div>
          <h1 className="text-base font-semibold tracking-tight">Firetal Assistant</h1>
          <p className="text-xs text-zinc-500 mt-0.5">Internal systems · AI agent PoC</p>
        </div>
        <StatusBadge />
      </header>

      {/* Chat */}
      <main className="flex-1 overflow-hidden">
        <ChatWindow />
      </main>
    </div>
  );
}
