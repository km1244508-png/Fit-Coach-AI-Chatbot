import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";
import Spinner from "./Spinner.jsx";

export default function ConfirmDialog({ open, title, message, confirmLabel = "Delete", loading = false, error = null, onConfirm, onCancel }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && !loading && onCancel();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, loading, onCancel]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
      <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={() => !loading && onCancel()} />
      <div className="relative w-full max-w-sm animate-fade-up rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl">
        <div className="mb-4 grid h-11 w-11 place-items-center rounded-xl bg-rose-500/15 text-rose-400">
          <AlertTriangle size={22} />
        </div>
        <h2 id="confirm-title" className="text-lg font-bold text-white">{title}</h2>
        <p className="mt-1.5 text-sm leading-relaxed text-slate-400">{message}</p>
        {error && <p className="mt-3 rounded-lg bg-rose-500/10 px-3 py-2 text-sm text-rose-300">{error}</p>}
        <div className="mt-6 flex justify-end gap-3">
          <button type="button" onClick={onCancel} disabled={loading} className="rounded-xl border border-white/10 px-4 py-2 text-sm font-semibold text-slate-300 transition hover:bg-white/5 disabled:opacity-50">
            Cancel
          </button>
          <button type="button" onClick={onConfirm} disabled={loading} autoFocus className="flex items-center gap-2 rounded-xl bg-rose-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-400 disabled:opacity-60">
            {loading && <Spinner size={15} />} {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
