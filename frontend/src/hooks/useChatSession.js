import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client.js";

const NEW = "__new__"; // sentinel: a brand-new conversation is being created

// Merge by id (server copy wins) and order by timestamp. Date.parse - not string compare - because
// ISO strings with/without fractional seconds do not sort lexicographically.
function mergeMessages(base, incoming) {
  const out = [];
  const index = new Map();
  for (const m of [...base, ...incoming]) {
    if (index.has(m.id)) out[index.get(m.id)] = m;
    else {
      index.set(m.id, out.length);
      out.push(m);
    }
  }
  return out.sort((a, b) => Date.parse(a.created_at) - Date.parse(b.created_at));
}

/**
 * Messages + send/retry logic for the open conversation.
 * Partial failure policy: if the AI fails, the user's message stays on screen (and on the server)
 * flagged `failed` with a Retry action - it is never silently dropped.
 */
export function useChatSession({ conversationId, createConversation, onConversationUpdate, onNavigate }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [pendingId, setPendingId] = useState(null);

  const activeRef = useRef(conversationId);
  activeRef.current = conversationId;
  const sendingRef = useRef(false);
  const skipLoadRef = useRef(null);
  const loadToken = useRef(0);
  const cb = useRef({});
  cb.current = { createConversation, onConversationUpdate, onNavigate };

  const load = useCallback(async (id) => {
    const token = ++loadToken.current;
    setLoading(true);
    setLoadError(null);
    setMessages([]);
    setHasMore(false);
    try {
      const res = await api.getConversation(id);
      if (token !== loadToken.current) return; // user already switched chats: ignore stale response
      setMessages(res.messages);
      setHasMore(res.has_more);
    } catch (e) {
      if (token === loadToken.current) setLoadError(e);
    } finally {
      if (token === loadToken.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!conversationId) {
      loadToken.current++;
      setMessages([]);
      setHasMore(false);
      setLoadError(null);
      setLoading(false);
      return;
    }
    if (skipLoadRef.current === conversationId) {
      skipLoadRef.current = null; // we just created this chat while sending; state is already correct
      return;
    }
    load(conversationId);
  }, [conversationId, load]);

  const loadOlder = useCallback(async () => {
    const first = messages.find((m) => !String(m.id).startsWith("tmp-"));
    if (!conversationId || !first) return;
    setLoadingOlder(true);
    try {
      const res = await api.getConversation(conversationId, { before: first.id });
      if (activeRef.current !== conversationId) return;
      setMessages((prev) => mergeMessages(res.messages, prev));
      setHasMore(res.has_more);
    } catch (e) {
      setLoadError(e);
    } finally {
      setLoadingOlder(false);
    }
  }, [conversationId, messages]);

  /** Send a new message, or retry `existing` (a failed message object). Returns after the turn completes. */
  const send = useCallback(async (content, existing = null) => {
    if (sendingRef.current) return; // blocks duplicate submissions
    sendingRef.current = true;
    const tempId = existing ? existing.id : `tmp-${Date.now()}`;
    let convId = activeRef.current;
    setPendingId(convId || NEW);

    setMessages((prev) =>
      existing
        ? prev.map((m) => (m.id === existing.id ? { ...m, localStatus: "sending", errorMessage: null } : m))
        : [...prev, { id: tempId, role: "user", content, created_at: new Date().toISOString(), localStatus: "sending", saved: false }]
    );

    try {
      if (!convId) {
        const conv = await cb.current.createConversation();
        convId = conv.id;
        skipLoadRef.current = convId;
        activeRef.current = convId;
        setPendingId(convId);
        cb.current.onNavigate(convId);
      }
      const body = existing?.saved ? { content: existing.content, retry_message_id: existing.id } : { content };
      const res = await api.sendMessage(convId, body);
      cb.current.onConversationUpdate(res.conversation);
      if (activeRef.current === convId) {
        setMessages((prev) => mergeMessages(prev.filter((m) => m.id !== tempId), [res.user_message, res.assistant_message]));
      }
    } catch (err) {
      const saved = err?.data?.user_message; // server kept the user's message
      if (activeRef.current === convId || !convId) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === tempId
              ? { ...(saved || m), localStatus: "failed", saved: Boolean(saved) || Boolean(m.saved), errorMessage: err?.message || "Something went wrong." }
              : m
          )
        );
      }
    } finally {
      sendingRef.current = false;
      setPendingId(null);
    }
  }, []);

  const sending = pendingId !== null;
  const awaitingReply = pendingId !== null && (pendingId === conversationId || (pendingId === NEW && !conversationId));

  return { messages, loading, loadError, hasMore, loadingOlder, sending, awaitingReply, send, loadOlder, reload: () => conversationId && load(conversationId) };
}
