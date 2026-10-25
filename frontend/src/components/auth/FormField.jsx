import { forwardRef, useId } from "react";

const FormField = forwardRef(function FormField({ label, icon: Icon, error, hint, right, ...inputProps }, ref) {
  const id = useId();
  const describedBy = error ? `${id}-err` : hint ? `${id}-hint` : undefined;
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium text-slate-300">{label}</label>
      <div className="relative">
        {Icon && <Icon size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />}
        <input
          id={id}
          ref={ref}
          aria-invalid={Boolean(error)}
          aria-describedby={describedBy}
          className={`w-full rounded-xl border bg-slate-950/60 py-3 text-sm text-white placeholder:text-slate-600 outline-none transition focus:ring-2 ${Icon ? "pl-10" : "pl-4"} ${right ? "pr-11" : "pr-4"} ${
            error ? "border-rose-500/60 focus:ring-rose-500/30" : "border-white/10 focus:border-emerald-400/60 focus:ring-emerald-400/20"
          }`}
          {...inputProps}
        />
        {right && <div className="absolute right-2 top-1/2 -translate-y-1/2">{right}</div>}
      </div>
      {error ? (
        <p id={`${id}-err`} className="mt-1.5 text-xs text-rose-400">{error}</p>
      ) : hint ? (
        <p id={`${id}-hint`} className="mt-1.5 text-xs text-slate-500">{hint}</p>
      ) : null}
    </div>
  );
});

export default FormField;
