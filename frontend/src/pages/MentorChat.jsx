import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import BotAvatar from "../components/BotAvatar";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal";
import ChatMessage from "../components/mentor/ChatMessage";
import Composer from "../components/mentor/Composer";
import ChatSidebar from "../components/mentor/ChatSidebar";
import MentorHome, { SUGGESTIONS } from "../components/mentor/MentorHome";
import {
  deleteConversation as deleteSavedConversation,
  getConversation,
  listConversations,
  makeTitle,
  newId,
  renameConversation as renameSavedConversation,
  saveConversation,
} from "../services/chats";
import { streamMentorReply } from "../services/mentorChat";

// Earlier messages sent with each new one. The backend keeps only the newest
// CHAT_HISTORY_LIMIT of them; this just keeps the request small.
const MAX_HISTORY_SENT = 50;
const MAX_HISTORY_TEXT = 20000; // backend limit per earlier message

// Earlier messages of a conversation in the format the backend expects.
// Only real messages are sent: failed replies without any text are left out.
function toHistory(messages) {
  return messages
    .filter((m) => m.content.trim() || m.attachments?.length)
    .slice(-MAX_HISTORY_SENT)
    .map(({ role, content, attachments }) => ({
      role,
      content: content.slice(0, MAX_HISTORY_TEXT),
      attachments: (attachments ?? []).map((a) => a.id),
    }));
}

// Chat with the AI mentor, ChatGPT-style. Opens on a landing screen; "New chat"
// (or a suggestion) opens the chat. Saved chats are listed on the left.
function MentorChat() {
  // Newest first. Saved in the database (see services/chats.js); a chat's
  // `messages` are loaded when it is first opened.
  const [conversations, setConversations] = useState([]);
  const [listError, setListError] = useState("");
  const [saveError, setSaveError] = useState("");
  // "home" = landing screen, "chat" = a conversation is open
  const [view, setView] = useState("home");
  // null = a new chat that has no messages yet (it's saved once you send one)
  const [activeId, setActiveId] = useState(null);
  // "idle" -> "waiting" (sent, no tokens yet) -> "streaming" -> "idle"
  const [phase, setPhase] = useState("idle");
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [dragging, setDragging] = useState(false);

  const abortRef = useRef(null);
  const listEndRef = useRef(null);
  const composerRef = useRef(null);
  const location = useLocation();
  const navigate = useNavigate();
  const handledPrompt = useRef(false);
  const dragDepth = useRef(0); // dragenter/leave fire for every child element
  const latestRef = useRef(conversations);
  latestRef.current = conversations;
  // Ids of conversations changed since they were last saved
  const unsavedRef = useRef(new Set());

  const busy = phase !== "idle";
  const active = conversations.find((c) => c.id === activeId) ?? null;
  const messages = active?.messages ?? [];
  const lastReply = messages.at(-1);
  // An existing chat that was opened but whose messages haven't arrived yet
  const chatLoading = !!active && !active.messages;

  // Load the chat list
  useEffect(() => {
    let current = true;
    listConversations()
      .then((saved) => {
        if (!current) return;
        // Keep a chat started before the list arrived (e.g. a prompt from another page)
        setConversations((now) => {
          const savedIds = new Set(saved.map((c) => c.id));
          const loaded = new Map(now.map((c) => [c.id, c]));
          return [...now.filter((c) => !savedIds.has(c.id)), ...saved.map((c) => loaded.get(c.id) ?? c)];
        });
      })
      .catch((err) => current && setListError(err.message));
    return () => {
      current = false;
    };
  }, []);

  // Save every changed conversation to the database
  const saveChanges = useCallback(() => {
    for (const id of unsavedRef.current) {
      unsavedRef.current.delete(id);
      const conversation = latestRef.current.find((c) => c.id === id);
      if (!conversation?.messages) continue;
      saveConversation(conversation)
        .then(() => setSaveError(""))
        .catch((err) => {
          unsavedRef.current.add(id); // try again with the next change
          setSaveError(`This chat could not be saved: ${err.message}`);
        });
    }
  }, []);

  // Save when a reply is finished (not on every token), and when leaving the page
  useEffect(() => {
    if (phase === "idle") saveChanges();
  }, [conversations, phase, saveChanges]);

  useEffect(
    () => () => {
      abortRef.current?.abort(); // cancel a running stream if the user leaves the page
      saveChanges();
    },
    [saveChanges]
  );

  // Keep the newest message in view as text arrives
  useEffect(() => {
    if (view === "chat") listEndRef.current?.scrollIntoView({ block: "end" });
  }, [messages, phase, view]);

  // Focus the input when another chat opens
  useEffect(() => {
    if (view === "chat") composerRef.current?.focus();
  }, [activeId, view]);

  // Update one message of one conversation (used while its reply streams in)
  const updateMessage = (conversationId, messageId, changes) =>
    setConversations((current) =>
      current.map((c) =>
        c.id !== conversationId
          ? c
          : {
              ...c,
              messages: c.messages.map((m) =>
                m.id === messageId ? { ...m, ...(typeof changes === "function" ? changes(m) : changes) } : m
              ),
            }
      )
    );

  // Send `text` (and uploaded `attachments`) in the open chat, or in a brand-new
  // chat when `fresh` is true
  const sendMessage = async (text, { fresh = false, attachments = [] } = {}) => {
    text = text.trim();
    if ((!text && attachments.length === 0) || busy || (!fresh && chatLoading)) return;

    const history = fresh ? [] : toHistory(messages);
    const conversationId = (!fresh && activeId) || newId();
    unsavedRef.current.add(conversationId);
    const replyId = newId();
    const newMessages = [
      { id: newId(), role: "user", content: text, attachments },
      { id: replyId, role: "assistant", content: "" },
    ];

    // Add the messages and move this conversation to the top of the list
    setConversations((current) => {
      const existing = current.find((c) => c.id === conversationId);
      const updated = existing
        ? { ...existing, messages: [...existing.messages, ...newMessages], updatedAt: Date.now() }
        : { id: conversationId, title: makeTitle(text || attachments[0].filename), messages: newMessages, updatedAt: Date.now() };
      return [updated, ...current.filter((c) => c.id !== conversationId)];
    });
    setActiveId(conversationId);
    setView("chat");
    await streamReply(conversationId, replyId, text, attachments, history);
  };

  // Edit one of your earlier messages: everything after it is removed and the
  // mentor answers the edited message again (like ChatGPT). Its files are kept.
  const editMessage = async (messageId, newText) => {
    const text = newText.trim();
    const index = messages.findIndex((m) => m.id === messageId);
    const original = messages[index];
    if (busy || index < 0 || (!text && !original.attachments?.length)) return;

    const replyId = newId();
    const kept = messages.slice(0, index);
    unsavedRef.current.add(activeId);
    setConversations((current) =>
      current.map((c) =>
        c.id !== activeId
          ? c
          : {
              ...c,
              messages: [...kept, { ...original, content: text, edited: true }, { id: replyId, role: "assistant", content: "" }],
              updatedAt: Date.now(),
            }
      )
    );
    await streamReply(activeId, replyId, text, original.attachments ?? [], toHistory(kept));
  };

  // Stream the mentor's reply into message `replyId` of a conversation
  const streamReply = async (conversationId, replyId, text, attachments, history) => {
    setPhase("waiting");
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await streamMentorReply(text, {
        attachments: attachments.map((a) => a.id),
        history,
        signal: controller.signal,
        onToken: (token) => {
          setPhase("streaming");
          updateMessage(conversationId, replyId, (m) => ({ content: m.content + token }));
        },
      });
    } catch (err) {
      if (err.name === "AbortError") {
        updateMessage(conversationId, replyId, { stopped: true });
      } else {
        updateMessage(conversationId, replyId, { error: err.message });
      }
    } finally {
      abortRef.current = null;
      setPhase("idle");
    }
  };

  // Another page can open the mentor with a question, e.g. Career's "Ask Mentora
  // for a roadmap": navigate("/mentor", { state: { prompt } }). It's sent once in a
  // new chat, then removed from the history entry so a reload doesn't resend it.
  useEffect(() => {
    const prompt = location.state?.prompt;
    if (!prompt || handledPrompt.current) return;
    handledPrompt.current = true;
    navigate(location.pathname, { replace: true, state: null });
    sendMessage(prompt, { fresh: true });
  }, []);

  const goHome = () => {
    setView("home");
    setActiveId(null);
  };

  const startNewChat = () => {
    setActiveId(null);
    setView("chat");
  };

  const setConversation = (id, changes) =>
    setConversations((current) => current.map((c) => (c.id === id ? { ...c, ...changes } : c)));

  // Open a chat, loading its messages the first time
  const openChat = async (id) => {
    setActiveId(id);
    setView("chat");
    const conversation = latestRef.current.find((c) => c.id === id);
    if (!conversation || conversation.messages) return;
    setConversation(id, { loadError: "" });
    try {
      const { messages: saved } = await getConversation(id);
      setConversation(id, { messages: saved });
    } catch (err) {
      setConversation(id, { loadError: err.message });
    }
  };

  const renameConversation = (id, title) => {
    const clean = title.replace(/\s+/g, " ").trim().slice(0, 80);
    if (!clean) return;
    const conversation = latestRef.current.find((c) => c.id === id);
    setConversation(id, { title: clean });
    if (conversation?.messages) {
      // Loaded here (maybe not saved yet): save the whole chat with its new title
      unsavedRef.current.add(id);
    } else {
      renameSavedConversation(id, clean).catch((err) => setSaveError(`The new name could not be saved: ${err.message}`));
    }
  };

  const deleteConversation = (id) => {
    setConversations((current) => current.filter((c) => c.id !== id));
    unsavedRef.current.delete(id);
    if (id === activeId) goHome();
    deleteSavedConversation(id).catch((err) => {
      // 404: it was never saved, so there's nothing to delete
      if (!err.message.includes("not found")) setSaveError(`This chat could not be deleted: ${err.message}`);
    });
  };

  // Drag files anywhere over the open chat to attach them
  const hasFiles = (event) => Array.from(event.dataTransfer?.types ?? []).includes("Files");
  const dropHandlers =
    !busy
      ? {
          onDragEnter: (event) => {
            if (!hasFiles(event)) return;
            dragDepth.current += 1;
            setDragging(true);
          },
          onDragLeave: () => {
            dragDepth.current = Math.max(0, dragDepth.current - 1);
            if (dragDepth.current === 0) setDragging(false);
          },
          onDragOver: (event) => hasFiles(event) && event.preventDefault(),
          onDrop: (event) => {
            if (!hasFiles(event)) return;
            event.preventDefault();
            dragDepth.current = 0;
            setDragging(false);
            composerRef.current?.addFiles(event.dataTransfer.files);
          },
        }
      : {};

  return (
    <div className="d-flex gap-3 chat-page">
      <ChatSidebar
        conversations={conversations}
        activeId={view === "chat" ? activeId : null}
        isHome={view === "home"}
        disabled={busy}
        onHome={goHome}
        onNewChat={startNewChat}
        onSelect={openChat}
        onDelete={setDeleteTarget}
        onRename={renameConversation}
      />

      <section className="d-flex flex-column flex-grow-1 chat-main">
        <div className="d-flex align-items-center gap-2 mb-3">
          {/* Opens the chat list on small screens (on larger ones it's always shown) */}
          <button
            type="button"
            className="btn btn-outline-secondary btn-sm d-md-none text-nowrap"
            data-bs-toggle="offcanvas"
            data-bs-target="#chatHistory"
            aria-controls="chatHistory"
          >
            <i className="bi bi-layout-sidebar me-1" aria-hidden="true" />
            Chats
          </button>
          {view === "chat" && (
            <h2 className="h6 fw-semibold mb-0 text-truncate flex-grow-1">{active ? active.title : "New chat"}</h2>
          )}
          {view === "chat" && (
            <button
              type="button"
              className="btn btn-sm btn-outline-secondary ms-auto"
              onClick={startNewChat}
              disabled={busy || !active}
              title="New chat"
            >
              <i className="bi bi-plus-lg" aria-hidden="true" />
              <span className="d-none d-sm-inline ms-1">New chat</span>
            </button>
          )}
        </div>

        {(listError || saveError) && (
          <div className="alert alert-warning d-flex align-items-center gap-2 py-2 small">
            <i className="bi bi-exclamation-triangle" aria-hidden="true" />
            <span className="flex-grow-1">{listError ? `Could not load your chats: ${listError}` : saveError}</span>
            {saveError && !listError && (
              <button type="button" className="btn-close btn-sm" aria-label="Dismiss" onClick={() => setSaveError("")} />
            )}
          </div>
        )}

        <div className="card chat-card flex-grow-1 overflow-hidden position-relative" {...dropHandlers}>
          {dragging && (
            <div className="drop-overlay" aria-hidden="true">
              <i className="bi bi-cloud-arrow-up display-5" />
              <div className="fw-semibold mt-2">Drop files to attach</div>
              <div className="small text-body-secondary">Images, PDFs or code · max 5</div>
            </div>
          )}
          {view === "home" ? (
            <MentorHome
              lastConversation={conversations[0]}
              onNewChat={startNewChat}
              onOpen={openChat}
              onSuggestion={(prompt) => sendMessage(prompt, { fresh: true })}
            />
          ) : null}
          {view === "home" ? (
            // Type or attach right away: sending starts a new chat
            <Composer
              key="home"
              ref={composerRef}
              busy={busy}
              placeholder="Ask Mentora anything, or add images and files..."
              onSend={(text, attachments) => sendMessage(text, { fresh: true, attachments })}
              onStop={() => abortRef.current?.abort()}
            />
          ) : chatLoading ? (
            <div className="card-body d-flex flex-column align-items-center justify-content-center text-center">
              {active.loadError ? (
                <>
                  <p className="text-danger mb-2">Could not load this chat: {active.loadError}</p>
                  <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => openChat(active.id)}>
                    Try again
                  </button>
                </>
              ) : (
                <div className="text-body-secondary">
                  <span className="spinner-border spinner-border-sm me-2" role="status" /> Loading chat...
                </div>
              )}
            </div>
          ) : (
            <>
              {/* Message list */}
              <div className="card-body overflow-auto chat-scroll" aria-live="polite">
                {messages.length === 0 ? (
                  <EmptyChat onSuggestion={(prompt) => sendMessage(prompt)} />
                ) : (
                  messages.map((message) => (
                    <ChatMessage
                      key={message.id}
                      message={message}
                      canEdit={!busy && message.role === "user"}
                      onEdit={(text) => editMessage(message.id, text)}
                      isWaiting={busy && message === lastReply && message.content === "" && !message.error}
                      isStreaming={phase === "streaming" && message === lastReply}
                    />
                  ))
                )}
                <div ref={listEndRef} />
              </div>

              {/* Input box with attachments */}
              <Composer
                key={activeId ?? "new"}
                ref={composerRef}
                busy={busy}
                onSend={(text, attachments) => sendMessage(text, { attachments })}
                onStop={() => abortRef.current?.abort()}
              />
            </>
          )}
        </div>
      </section>

      {deleteTarget && (
        <ConfirmDeleteModal
          itemLabel={deleteTarget.title}
          onConfirm={() => deleteConversation(deleteTarget.id)}
          onClose={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}

// Shown in a new chat before the first message
function EmptyChat({ onSuggestion }) {
  return (
    <div className="h-100 d-flex flex-column align-items-center justify-content-center text-center py-4">
      <BotAvatar size={72} float sparkles />
      <h3 className="h4 mt-3 mb-1">What's on your mind?</h3>
      <p className="text-body-secondary mb-4">Ask anything about learning, projects or your career.</p>
      <div className="d-flex flex-wrap justify-content-center gap-2">
        {SUGGESTIONS.map((s) => (
          <button key={s.title} type="button" className="btn btn-sm suggestion-chip" onClick={() => onSuggestion(s.prompt)}>
            <i className={`bi ${s.icon} me-1`} aria-hidden="true" />
            {s.title}
          </button>
        ))}
      </div>
    </div>
  );
}

export default MentorChat;
