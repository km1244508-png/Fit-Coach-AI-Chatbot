import ConversationItem from "./ConversationItem.jsx";

export default function ConversationGroup({ label, items, activeId, now, onOpen, onRename, onDelete }) {
  return (
    <section aria-label={label} className="mb-4">
      <h3 className="px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">{label}</h3>
      <ul className="space-y-0.5">
        {items.map((c) => (
          <ConversationItem key={c.id} conversation={c} active={c.id === activeId} now={now} onOpen={onOpen} onRename={onRename} onDelete={onDelete} />
        ))}
      </ul>
    </section>
  );
}
