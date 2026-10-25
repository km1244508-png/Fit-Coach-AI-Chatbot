import { Bot } from "lucide-react";

export default function TypingIndicator() {
  return (
    <div className="flex items-end gap-3 animate-fade-up" role="status" aria-label="Coach is typing">
      <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-linear-to-br from-emerald-400 to-cyan-500 text-slate-950"><Bot size={17} /></div>
      <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-md border border-white/10 bg-white/5 px-4 py-3.5">
        {[0, 1, 2].map((i) => (
          <span key={i} className="h-2 w-2 animate-dot rounded-full bg-emerald-300" style={{ animationDelay: `${i * 0.16}s` }} />
        ))}
        <span className="sr-only">Coach is typing</span>
      </div>
    </div>
  );
}
