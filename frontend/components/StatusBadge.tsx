"use client";

import { useEffect, useState } from "react";
import { checkHealth } from "@/lib/api";

export default function StatusBadge() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");
  const [version, setVersion] = useState("");

  useEffect(() => {
    checkHealth()
      .then((h) => {
        setStatus("online");
        setVersion(h.version);
      })
      .catch(() => setStatus("offline"));
  }, []);

  const colour =
    status === "online"
      ? "bg-emerald-500"
      : status === "offline"
      ? "bg-red-500"
      : "bg-yellow-400 animate-pulse";

  const label =
    status === "online"
      ? `Online${version ? ` · v${version}` : ""}`
      : status === "offline"
      ? "Offline"
      : "Checking…";

  return (
    <span className="flex items-center gap-1.5 text-xs text-zinc-400">
      <span className={`inline-block h-2 w-2 rounded-full ${colour}`} />
      {label}
    </span>
  );
}
