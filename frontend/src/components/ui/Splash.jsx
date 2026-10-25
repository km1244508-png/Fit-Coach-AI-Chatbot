import Logo from "./Logo.jsx";
import Spinner from "./Spinner.jsx";

export default function Splash() {
  return (
    <div className="grid h-dvh place-items-center bg-slate-950">
      <div className="flex flex-col items-center gap-6">
        <Logo size="lg" />
        <Spinner size={22} className="text-emerald-400" />
      </div>
    </div>
  );
}
