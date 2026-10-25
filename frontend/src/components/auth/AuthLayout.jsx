import { Apple, BrainCircuit, Dumbbell, ShieldCheck } from "lucide-react";
import Logo from "../ui/Logo.jsx";

const FEATURES = [
  { icon: Dumbbell, title: "Personalized workouts", text: "Plans built around your goals, equipment and schedule." },
  { icon: Apple, title: "Smart nutrition", text: "Simple meal ideas that fit your tastes and targets." },
  { icon: BrainCircuit, title: "Evidence-based answers", text: "Grounded in a trusted fitness & nutrition knowledge base." },
  { icon: ShieldCheck, title: "Private & saved", text: "Every conversation is stored securely in your account." },
];

export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="relative min-h-dvh overflow-hidden bg-slate-950 text-slate-200">
      {/* decorative glows */}
      <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 animate-float rounded-full bg-emerald-500/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 right-0 h-112 w-md animate-float rounded-full bg-cyan-500/15 blur-3xl [animation-delay:2s]" />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_1px_1px,rgba(255,255,255,0.05)_1px,transparent_0)] bg-size-[28px_28px]" />

      <div className="relative mx-auto grid min-h-dvh max-w-6xl items-center gap-10 px-5 py-10 lg:grid-cols-2 lg:gap-16">
        <section className="hidden lg:block">
          <Logo size="lg" />
          <h1 className="mt-10 text-5xl font-extrabold leading-[1.08] tracking-tight text-white">
            Your <span className="bg-linear-to-r from-emerald-300 via-teal-300 to-cyan-300 bg-clip-text text-transparent">hyper-personalized</span> health &amp; fitness coach.
          </h1>
          <p className="mt-5 max-w-md text-lg text-slate-400">Ask anything about training, nutrition and healthy habits - and get safe, structured guidance in your own language.</p>
          <ul className="mt-10 grid max-w-xl gap-4 sm:grid-cols-2">
            {FEATURES.map(({ icon: Icon, title: t, text }) => (
              <li key={t} className="rounded-2xl border border-white/10 bg-white/3 p-4 backdrop-blur-sm">
                <div className="mb-2.5 grid h-9 w-9 place-items-center rounded-lg bg-emerald-400/15 text-emerald-300">
                  <Icon size={18} />
                </div>
                <div className="text-sm font-semibold text-white">{t}</div>
                <div className="mt-0.5 text-xs leading-relaxed text-slate-400">{text}</div>
              </li>
            ))}
          </ul>
        </section>

        <main className="mx-auto w-full max-w-md animate-fade-up">
          <div className="mb-8 flex justify-center lg:hidden">
            <Logo size="lg" />
          </div>
          <div className="rounded-3xl border border-white/10 bg-slate-900/70 p-7 shadow-2xl shadow-black/40 backdrop-blur-xl sm:p-9">
            <h2 className="text-2xl font-bold tracking-tight text-white">{title}</h2>
            <p className="mt-1.5 text-sm text-slate-400">{subtitle}</p>
            <div className="mt-7">{children}</div>
          </div>
          <p className="mt-6 text-center text-sm text-slate-400">{footer}</p>
        </main>
      </div>
    </div>
  );
}
