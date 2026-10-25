import { useEffect, useRef, useState } from "react";
import { Check, MessageSquare, Pencil, Trash2, X } from "lucide-react";
import { formatItemTime } from "../../utils/dateGroups.js";

export default function ConversationItem({ conversation, active, now, onOpen, onRename, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(conversation.title);
  const [saving, setSaving] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    if (editing) inputRef.current?.select();
  }, [editing]);

  function startEdit(e) {
    e.stopPropagation();
    setDraft(conversation.title);
    setEditing(true);
  }

  async function save() {
    const title = draft.trim().replace(/\s+/g, " ");
    if (!title || title === conversation.title) return setEditing(false);
    setSaving(true);
    try {
      await onRename(conversation.id, title);
      setEditing(false);
    } catch {
      /* parent shows the error; keep the editor open so the user can retry */
    } finally {
      setSaving(false);
    }
  }

  function onKeyDown(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      save();
    } else if (e.key === "Escape") setEditing(false);
  }

  if (editing) {
    return (
      <li className="flex items-center gap-1.5 rounded-xl bg-white/8 px-2 py-1.5">
        <input
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          maxLength={100}
          disabled={saving}
          aria-label="Conversation title"
          className="min-w-0 flex-1 rounded-lg border border-emerald-400/40 bg-slate-950/70 px-2.5 py-1.5 text-sm text-white outline-none focus:ring-2 focus:ring-emerald-400/30"
        />
        <button type="button" onClick={save} disabled={saving} aria-label="Save title" className="rounded-lg p-1.5 text-emerald-300 hover:bg-white/10"><Check size={16} /></button>
        <button type="button" onClick={() => setEditing(false)} disabled={saving} aria-label="Cancel rename" className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10"><X size={16} /></button>
      </li>
    );
  }

  return (
    <li className="group relative">
      <button
        type="button"
        onClick={() => onOpen(conversation.id)}
        aria-current={active ? "page" : undefined}
        className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition ${
          active ? "bg-linear-to-r from-emerald-400/15 to-cyan-400/10 ring-1 ring-emerald-400/30" : "hover:bg-white/5"
        }`}
      >
        <MessageSquare size={16} className={`shrink-0 ${active ? "text-emerald-300" : "text-slate-500"}`} />
        <span className="min-w-0 flex-1">
          <span className={`block truncate text-sm ${active ? "font-semibold text-white" : "text-slate-300"}`}>{conversation.title}</span>
          <span className="block text-[11px] text-slate-500">{formatItemTime(conversation.last_message_at, now)}</span>
        </span>
      </button>
      <div className="absolute right-1.5 top-1/2 flex -translate-y-1/2 gap-0.5 rounded-lg bg-slate-900/90 p-0.5 opacity-100 backdrop-blur md:opacity-0 md:group-focus-within:opacity-100 md:group-hover:opacity-100">
        <button type="button" onClick={startEdit} aria-label={`Rename ${conversation.title}`} className="rounded-md p-1.5 text-slate-400 transition hover:bg-white/10 hover:text-white"><Pencil size={14} /></button>
        <button type="button" onClick={(e) => { e.stopPropagation(); onDelete(conversation); }} aria-label={`Delete ${conversation.title}`} className="rounded-md p-1.5 text-slate-400 transition hover:bg-rose-500/15 hover:text-rose-300"><Trash2 size={14} /></button>
      </div>
    </li>
  );
}
