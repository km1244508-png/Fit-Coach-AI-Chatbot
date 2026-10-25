import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Bot, RotateCw, TriangleAlert } from "lucide-react";
import { formatMessageTime } from "../../utils/dateGroups.js";

const mdComponents = {
  a: ({ node, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer nofollow" />,
};

function MessageBubble({ message, onRetry, retryDisabled }) {
  const isUser = message.role === "user";
  const failed = message.localStatus === "failed";
  const sending = message.localStatus === "sending";

  if (isUser) {
    return (
      <div className="flex flex-col items-end gap-1.5 animate-fade-up">
        <div className={`max-w-[88%] whitespace-pre-wrap rounded-2xl rounded-br-md px-4 py-2.5 text-[15px] leading-relaxed wrap-anywhere sm:max-w-[75%] ${
          failed ? "border border-rose-500/40 bg-rose-500/10 text-rose-100" : "bg-linear-to-br from-emerald-500 to-teal-600 text-white shadow-lg shadow-emerald-900/30"
        } ${sending ? "opacity-70" : ""}`}>
          {message.content}
        </div>
        {failed ? (
          <div className="flex max-w-[88%] flex-wrap items-center justify-end gap-x-3 gap-y-1 text-xs text-rose-300 sm:max-w-[75%]">
            <span className="inline-flex items-center gap-1.5"><TriangleAlert size={13} /> {message.errorMessage || "Couldn't get a reply."}</span>
            <button type="button" onClick={() => onRetry(message)} disabled={retryDisabled} className="inline-flex items-center gap-1.5 rounded-lg bg-rose-500/15 px-2.5 py-1 font-semibold text-rose-200 transition hover:bg-rose-500/25 disabled:opacity-50">
              <RotateCw size={12} /> Retry
            </button>
          </div>
        ) : (
          <span className="px-1 text-[11px] text-slate-500">{sending ? "Sending..." : formatMessageTime(message.created_at)}</span>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 animate-fade-up">
      <div className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-linear-to-br from-emerald-400 to-cyan-500 text-slate-950"><Bot size={17} /></div>
      <div className="min-w-0 max-w-[92%] sm:max-w-[80%]">
        <div className="rounded-2xl rounded-tl-md border border-white/10 bg-white/5 px-4 py-3 text-[15px] text-slate-200 backdrop-blur-sm">
          <div className="md"><ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>{message.content}</ReactMarkdown></div>
        </div>
        <span className="mt-1 block px-1 text-[11px] text-slate-500">{formatMessageTime(message.created_at)}</span>
      </div>
    </div>
  );
}

export default memo(MessageBubble);
