import { Apple, Dumbbell, FlaskConical, HeartPulse } from "lucide-react";

const SUGGESTIONS = [
  { icon: Dumbbell, text: "Mujhe ghar par karne ke liye 3-day beginner workout plan chahiye" },
  { icon: Apple, text: "Weight loss ke liye ek healthy desi meal plan banao" },
  { icon: FlaskConical, text: "How much protein do I need per day to build muscle?" },
  { icon: HeartPulse, text: "Squat karte waqt sahi form kaisa hota hai?" },
];

export default function EmptyState({ onPick, disabled, isNew }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center overflow-y-auto px-5 py-10">
      <div className="relative mb-6">
        <div className="absolute inset-0 animate-float rounded-full bg-emerald-400/30 blur-2xl" />
        <div className="relative grid h-20 w-20 place-items-center rounded-3xl bg-linear-to-br from-emerald-400 to-cyan-500 text-slate-950 shadow-2xl shadow-emerald-500/30"><Dumbbell size={38} strokeWidth={2.4} /></div>
      </div>
      <h2 className="text-center text-2xl font-extrabold tracking-tight text-white sm:text-3xl">
        {isNew ? "New chat - what's your goal?" : "How can I help you today?"}
      </h2>
      <p className="mt-2 max-w-md text-center text-sm text-slate-400">Ask about workouts, nutrition or healthy habits. Tell me your goal, equipment and schedule for a plan made just for you.</p>
      <div className="mt-8 grid w-full max-w-2xl gap-3 sm:grid-cols-2">
        {SUGGESTIONS.map(({ icon: Icon, text }) => (
          <button key={text} type="button" disabled={disabled} onClick={() => onPick(text)} className="group flex items-start gap-3 rounded-2xl border border-white/10 bg-white/3 p-4 text-left transition hover:border-emerald-400/40 hover:bg-emerald-400/5 disabled:opacity-50">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-emerald-400/10 text-emerald-300 transition group-hover:bg-emerald-400/20"><Icon size={18} /></span>
            <span className="text-sm leading-snug text-slate-300">{text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
