import { LogOut, MessageSquarePlus, MessagesSquare, RefreshCw, X } from "lucide-react";
import Logo from "../ui/Logo.jsx";
import Spinner from "../ui/Spinner.jsx";
import ConversationGroup from "./ConversationGroup.jsx";
import { groupConversations } from "../../utils/dateGroups.js";

export default function Sidebar({
  user, conversations, total, loading, loadingMore, error, activeId, now, creating, open,
  onClose, onNewChat, onOpen, onRename, onDelete, onLoadMore, onReload, onLogout,
}) {
  const groups = groupConversations(conversations, now);
  const initial = (user?.name || "?").trim().charAt(0).toUpperCase();

  return (
    <>
      {/* mobile backdrop */}
      <div onClick={onClose} className={`fixed inset-0 z-30 bg-slate-950/70 backdrop-blur-sm transition-opacity md:hidden ${open ? "opacity-100" : "pointer-events-none opacity-0"}`} aria-hidden="true" />

      <aside
        aria-label="Conversation history"
        className={`fixed inset-y-0 left-0 z-40 flex w-[19rem] max-w-[85vw] flex-col border-r border-white/10 bg-slate-900/95 backdrop-blur-xl transition-transform duration-300 md:static md:z-auto md:translate-x-0 md:bg-slate-900/60 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between px-4 pb-3 pt-4">
          <Logo />
          <button type="button" onClick={onClose} aria-label="Close history" className="rounded-lg p-2 text-slate-400 hover:bg-white/10 md:hidden"><X size={18} /></button>
        </div>

        <div className="px-4 pb-3">
          <button
            type="button"
            onClick={onNewChat}
            disabled={creating}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-linear-to-r from-emerald-400 to-cyan-400 px-4 py-2.5 text-sm font-bold text-slate-950 shadow-lg shadow-emerald-500/20 transition hover:brightness-110 disabled:opacity-70"
          >
            {creating ? <Spinner size={16} /> : <MessageSquarePlus size={17} />} New Chat
          </button>
        </div>

        <nav className="min-h-0 flex-1 overflow-y-auto px-2 pb-3" aria-label="Chats">
          {loading ? (
            <div className="space-y-2 px-2 pt-2" aria-busy="true" aria-label="Loading conversations">
              {[0, 1, 2, 3, 4].map((i) => <div key={i} className="h-11 animate-pulse rounded-xl bg-white/5" />)}
            </div>
          ) : error ? (
            <div className="px-3 pt-4 text-center text-sm text-slate-400">
              <p className="text-rose-300">{error}</p>
              <button type="button" onClick={onReload} className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-white/5"><RefreshCw size={13} /> Try again</button>
            </div>
          ) : groups.length === 0 ? (
            <div className="px-4 pt-10 text-center">
              <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-white/5 text-slate-500"><MessagesSquare size={22} /></div>
              <p className="text-sm font-medium text-slate-300">No conversations yet</p>
              <p className="mt-1 text-xs text-slate-500">Start a new chat and your history will show up here.</p>
            </div>
          ) : (
            <>
              {groups.map((g) => (
                <ConversationGroup key={g.label} label={g.label} items={g.items} activeId={activeId} now={now} onOpen={onOpen} onRename={onRename} onDelete={onDelete} />
              ))}
              {conversations.length < total && (
                <button type="button" onClick={onLoadMore} disabled={loadingMore} className="mx-auto mb-2 flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-400 hover:bg-white/5 hover:text-white">
                  {loadingMore && <Spinner size={13} />} Load more
                </button>
              )}
            </>
          )}
        </nav>

        <div className="border-t border-white/10 p-3">
          <div className="flex items-center gap-3 rounded-xl bg-white/5 p-2.5">
            <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-linear-to-br from-emerald-400 to-cyan-500 text-sm font-extrabold text-slate-950">{initial}</div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-semibold text-white">{user?.name}</div>
              <div className="truncate text-[11px] text-slate-400">{user?.email}</div>
            </div>
            <button type="button" onClick={onLogout} aria-label="Log out" title="Log out" className="rounded-lg p-2 text-slate-400 transition hover:bg-rose-500/15 hover:text-rose-300"><LogOut size={17} /></button>
          </div>
        </div>
      </aside>
    </>
  );
}
