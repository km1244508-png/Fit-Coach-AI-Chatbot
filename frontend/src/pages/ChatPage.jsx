import { useCallback, useState } from "react";
import { useMatch, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { useConversations } from "../hooks/useConversations.js";
import { useChatSession } from "../hooks/useChatSession.js";
import { useNow } from "../hooks/useNow.js";
import Sidebar from "../components/sidebar/Sidebar.jsx";
import ChatHeader from "../components/chat/ChatHeader.jsx";
import MessageList from "../components/chat/MessageList.jsx";
import Composer from "../components/chat/Composer.jsx";
import ConfirmDialog from "../components/ui/ConfirmDialog.jsx";
import Alert from "../components/ui/Alert.jsx";

export default function ChatPage() {
  const match = useMatch("/chat/:conversationId");
  const conversationId = match?.params.conversationId ?? null;
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const now = useNow();

  const convs = useConversations();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [notice, setNotice] = useState(null);
  const [toDelete, setToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState(null);

  const chat = useChatSession({
    conversationId,
    createConversation: convs.create,
    onConversationUpdate: convs.upsert,
    onNavigate: (id) => navigate(`/chat/${id}`, { replace: true }),
  });

  const activeConv = convs.items.find((c) => c.id === conversationId);

  const openConversation = useCallback((id) => {
    setDrawerOpen(false);
    navigate(`/chat/${id}`);
  }, [navigate]);

  async function newChat() {
    if (creating) return;
    setCreating(true);
    setNotice(null);
    try {
      const conv = await convs.create();
      openConversation(conv.id);
    } catch (e) {
      setNotice(e.message);
    } finally {
      setCreating(false);
    }
  }

  async function renameConversation(id, title) {
    try {
      await convs.rename(id, title);
    } catch (e) {
      setNotice(e.message);
      throw e;
    }
  }

  async function confirmDelete() {
    if (!toDelete) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await convs.remove(toDelete.id);
      if (toDelete.id === conversationId) navigate("/chat", { replace: true });
      setToDelete(null);
    } catch (e) {
      setDeleteError(e.message);
    } finally {
      setDeleting(false);
    }
  }

  const handleSend = (text) => chat.send(text);
  const handleRetry = (message) => chat.send(message.content, message);

  return (
    <div className="relative flex h-dvh overflow-hidden bg-slate-950 text-slate-200">
      <div className="pointer-events-none absolute -right-40 -top-40 h-96 w-96 rounded-full bg-emerald-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 left-1/3 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl" />

      <Sidebar
        user={user}
        conversations={convs.items}
        total={convs.total}
        loading={convs.loading}
        loadingMore={convs.loadingMore}
        error={convs.error}
        activeId={conversationId}
        now={now}
        creating={creating}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onNewChat={newChat}
        onOpen={openConversation}
        onRename={renameConversation}
        onDelete={(c) => { setDeleteError(null); setToDelete(c); }}
        onLoadMore={convs.loadMore}
        onReload={convs.reload}
        onLogout={logout}
      />

      <section className="relative flex min-w-0 flex-1 flex-col">
        <ChatHeader title={activeConv?.title || (conversationId ? "Conversation" : "New conversation")} onOpenSidebar={() => setDrawerOpen(true)} />
        {notice && (
          <div className="px-4 pt-3 sm:px-6"><div className="mx-auto max-w-3xl"><Alert type="error" onClose={() => setNotice(null)}>{notice}</Alert></div></div>
        )}
        <MessageList
          conversationId={conversationId}
          messages={chat.messages}
          loading={chat.loading}
          loadError={chat.loadError}
          hasMore={chat.hasMore}
          loadingOlder={chat.loadingOlder}
          awaitingReply={chat.awaitingReply}
          sending={chat.sending}
          onLoadOlder={chat.loadOlder}
          onRetry={handleRetry}
          onReload={chat.reload}
          onSuggestion={handleSend}
          onNewChat={() => navigate("/chat", { replace: true })}
        />
        <Composer onSend={handleSend} sending={chat.sending} />
      </section>

      <ConfirmDialog
        open={Boolean(toDelete)}
        title="Delete this conversation?"
        message={toDelete ? `"${toDelete.title}" and all of its messages will be permanently deleted. This can't be undone.` : ""}
        loading={deleting}
        error={deleteError}
        onConfirm={confirmDelete}
        onCancel={() => setToDelete(null)}
      />
    </div>
  );
}
