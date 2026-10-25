import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client.js";

const byActivity = (a, b) => Date.parse(b.last_message_at) - Date.parse(a.last_message_at);
const PAGE = 100;

export function useConversations() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listConversations({ limit: PAGE, skip: 0 });
      setItems(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const loadMore = useCallback(async () => {
    setLoadingMore(true);
    try {
      const res = await api.listConversations({ limit: PAGE, skip: items.length });
      setItems((prev) => {
        const seen = new Set(prev.map((c) => c.id));
        return [...prev, ...res.items.filter((c) => !seen.has(c.id))].sort(byActivity);
      });
      setTotal(res.total);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoadingMore(false);
    }
  }, [items.length]);

  // Insert or update one conversation (new chat, new activity, rename) and keep newest-activity-first.
  const upsert = useCallback((conv) => {
    setItems((prev) => [conv, ...prev.filter((c) => c.id !== conv.id)].sort(byActivity));
  }, []);

  const create = useCallback(async () => {
    const conv = await api.createConversation();
    upsert(conv);
    setTotal((t) => t + 1);
    return conv;
  }, [upsert]);

  const rename = useCallback(
    async (id, title) => {
      const conv = await api.renameConversation(id, title);
      upsert(conv);
      return conv;
    },
    [upsert]
  );

  const remove = useCallback(async (id) => {
    await api.deleteConversation(id);
    setItems((prev) => prev.filter((c) => c.id !== id));
    setTotal((t) => Math.max(0, t - 1));
  }, []);

  return { items, total, loading, loadingMore, error, reload: load, loadMore, upsert, create, rename, remove };
}
