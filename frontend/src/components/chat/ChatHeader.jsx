import { Menu } from "lucide-react";

export default function ChatHeader({ title, onOpenSidebar }) {
  return (
    <header className="flex items-center gap-3 border-b border-white/10 bg-slate-950/60 px-4 py-3 backdrop-blur-xl sm:px-6">
      <button type="button" onClick={onOpenSidebar} aria-label="Open chat history" className="rounded-lg p-2 text-slate-300 transition hover:bg-white/10 md:hidden"><Menu size={20} /></button>
      <div className="min-w-0">
        <h1 className="truncate text-sm font-bold text-white sm:text-base">{title}</h1>
        <p className="flex items-center gap-1.5 text-[11px] text-slate-500"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> AI Health, Nutrition &amp; Fitness Coach</p>
      </div>
    </header>
  );
}
