import { useEffect, useRef, useState } from "react";
import { ArrowUp } from "lucide-react";
import Spinner from "../ui/Spinner.jsx";

const MAX_LENGTH = 4000; // keep in sync with MAX_MESSAGE_LENGTH on the server

export default function Composer({ onSend, sending }) {
  const [value, setValue] = useState("");
  const ref = useRef(null);
  const wasSending = useRef(false);

  // Auto-grow up to ~8 lines.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  // Return focus to the box when a reply finishes.
  useEffect(() => {
    if (wasSending.current && !sending) ref.current?.focus();
    wasSending.current = sending;
  }, [sending]);

  const trimmed = value.trim();
  const canSend = trimmed.length > 0 && trimmed.length <= MAX_LENGTH && !sending;

  function submit() {
    if (!canSend) return;
    onSend(trimmed);
    setValue("");
  }

  function onKeyDown(e) {
    // Enter = send, Shift+Enter = new line. Ignore Enter while an IME is composing.
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="border-t border-white/10 bg-slate-950/60 px-4 pb-4 pt-3 backdrop-blur-xl sm:px-6">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-slate-900/80 p-2 shadow-xl shadow-black/30 transition focus-within:border-emerald-400/50 focus-within:ring-2 focus-within:ring-emerald-400/15">
          <textarea
            ref={ref}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKeyDown}
            rows={1}
            maxLength={MAX_LENGTH}
            disabled={sending}
            placeholder={sending ? "Coach is replying..." : "Message your coach..."}
            aria-label="Message"
            className="max-h-50 min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-[15px] text-white outline-none placeholder:text-slate-500 disabled:opacity-60"
          />
          <button
            type="button"
            onClick={submit}
            disabled={!canSend}
            aria-label="Send message"
            className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-linear-to-br from-emerald-400 to-cyan-400 text-slate-950 shadow-lg shadow-emerald-500/25 transition enabled:hover:brightness-110 disabled:cursor-not-allowed disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-400 disabled:shadow-none"
          >
            {sending ? <Spinner size={18} /> : <ArrowUp size={20} strokeWidth={2.6} />}
          </button>
        </div>
        <div className="mt-2 flex items-center justify-between gap-3 px-1 text-[11px] text-slate-500">
          <span>Enter to send &middot; Shift+Enter for a new line</span>
          {value.length > MAX_LENGTH * 0.8 && <span className={value.length >= MAX_LENGTH ? "text-rose-400" : ""}>{value.length}/{MAX_LENGTH}</span>}
        </div>
        <p className="mt-1 text-center text-[11px] text-slate-600">AI coaching is not medical advice. For pain, injury or emergencies, consult a medical professional.</p>
      </div>
    </div>
  );
}
