import { useEffect, useRef } from "react";
import { AlertCircle, ChevronUp, RefreshCw } from "lucide-react";
import MessageBubble from "./MessageBubble.jsx";
import TypingIndicator from "./TypingIndicator.jsx";
import EmptyState from "./EmptyState.jsx";
import Spinner from "../ui/Spinner.jsx";

export default function MessageList({
  conversationId, messages, loading, loadError, hasMore, loadingOlder, awaitingReply, sending,
  onLoadOlder, onRetry, onReload, onSuggestion, onNewChat,
}) {
  const bottomRef = useRef(null);
  const lastId = messages[messages.length - 1]?.id;

  // Scroll to the newest message when it changes, or when the typing indicator appears.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [lastId, awaitingReply, messages.length === 0]);

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center" aria-busy="true">
        <div className="flex items-center gap-3 text-sm text-slate-400"><Spinner size={20} className="text-emerald-400" /> Loading conversation...</div>
      </div>
    );
  }

  if (loadError) {
    const notFound = loadError.status === 404;
    return (
      <div className="flex flex-1 items-center justify-center px-6">
        <div className="max-w-sm text-center">
          <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-2xl bg-rose-500/10 text-rose-400"><AlertCircle size={24} /></div>
          <p className="font-semibold text-white">{notFound ? "This conversation doesn't exist" : "Couldn't load this conversation"}</p>
          <p className="mt-1 text-sm text-slate-400">{notFound ? "It may have been deleted." : loadError.message}</p>
          <button type="button" onClick={notFound ? onNewChat : onReload} className="mt-5 inline-flex items-center gap-2 rounded-xl bg-white/10 px-4 py-2 text-sm font-semibold text-white hover:bg-white/15">
            {notFound ? "Start a new chat" : <><RefreshCw size={15} /> Try again</>}
          </button>
        </div>
      </div>
    );
  }

  if (messages.length === 0 && !awaitingReply) {
    return <EmptyState onPick={onSuggestion} disabled={sending} isNew={Boolean(conversationId)} />;
  }

  return (
    <div className="min-h-0 flex-1 overflow-y-auto" role="log" aria-live="polite" aria-label="Conversation">
      <div className="mx-auto flex max-w-3xl flex-col gap-5 px-4 py-6 sm:px-6">
        {hasMore && (
          <button type="button" onClick={onLoadOlder} disabled={loadingOlder} className="mx-auto inline-flex items-center gap-2 rounded-full border border-white/10 px-4 py-1.5 text-xs font-semibold text-slate-300 hover:bg-white/5">
            {loadingOlder ? <Spinner size={13} /> : <ChevronUp size={14} />} Load earlier messages
          </button>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} onRetry={onRetry} retryDisabled={sending} />
        ))}
        {awaitingReply && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
