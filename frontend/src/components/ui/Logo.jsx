import { Dumbbell } from "lucide-react";

export default function Logo({ size = "md", showText = true }) {
  const box = size === "lg" ? "h-12 w-12 rounded-2xl" : "h-9 w-9 rounded-xl";
  const icon = size === "lg" ? 26 : 19;
  return (
    <div className="flex items-center gap-3">
      <div className={`${box} grid shrink-0 place-items-center bg-linear-to-br from-emerald-400 to-cyan-500 text-slate-950 shadow-lg shadow-emerald-500/30`}>
        <Dumbbell size={icon} strokeWidth={2.5} />
      </div>
      {showText && (
        <div className="leading-tight">
          <div className={`${size === "lg" ? "text-xl" : "text-base"} font-extrabold tracking-tight text-white`}>
            FitCoach<span className="bg-linear-to-r from-emerald-300 to-cyan-300 bg-clip-text text-transparent"> AI</span>
          </div>
          <div className="text-[11px] font-medium text-slate-400">Health &amp; Fitness Coach</div>
        </div>
      )}
    </div>
  );
}
