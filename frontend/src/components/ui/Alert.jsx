import { AlertCircle, CheckCircle2, X } from "lucide-react";

const STYLES = {
  error: "border-rose-500/30 bg-rose-500/10 text-rose-200",
  success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
};

export default function Alert({ type = "error", children, onClose }) {
  const Icon = type === "success" ? CheckCircle2 : AlertCircle;
  return (
    <div role={type === "error" ? "alert" : "status"} className={`flex items-start gap-2.5 rounded-xl border px-3.5 py-2.5 text-sm ${STYLES[type]}`}>
      <Icon size={17} className="mt-0.5 shrink-0" />
      <div className="min-w-0 flex-1 wrap-anywhere">{children}</div>
      {onClose && (
        <button type="button" onClick={onClose} aria-label="Dismiss" className="shrink-0 rounded p-0.5 opacity-70 hover:opacity-100">
          <X size={15} />
        </button>
      )}
    </div>
  );
}
