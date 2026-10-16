// Saves the mentor conversations in this browser (localStorage), so the chat
// list survives a page reload. Nothing is stored on the server.
//
// A conversation: { id, title, updatedAt, messages: [{ id, role, content, error?, stopped? }] }

const STORAGE_KEY = "mentora.conversations.v1";
const MAX_CONVERSATIONS = 50; // oldest ones are dropped beyond this

/** All saved conversations, newest first. Returns [] if nothing is saved or storage fails. */
export function loadConversations() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    return Array.isArray(saved) ? saved : [];
  } catch {
    return []; // storage blocked (e.g. private mode) or corrupted
  }
}

/** Save the conversations (they should be newest first). Fails silently. */
export function saveConversations(conversations) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations.slice(0, MAX_CONVERSATIONS)));
  } catch {
    // Storage full or blocked: the chat still works, it just isn't saved
  }
}

/** A short title from the first message, like "How do I learn React?" */
export function makeTitle(text) {
  const oneLine = text.replace(/\s+/g, " ").trim();
  return oneLine.length > 40 ? `${oneLine.slice(0, 40)}…` : oneLine;
}

/** A unique id (crypto.randomUUID needs a secure context, so keep a fallback) */
export function newId() {
  return globalThis.crypto?.randomUUID?.() ?? `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

/** Which sidebar group a conversation belongs to, like ChatGPT: Today, Yesterday, ... */
export function dateGroup(timestamp, now = new Date()) {
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const day = 24 * 60 * 60 * 1000;
  if (timestamp >= startOfToday) return "Today";
  if (timestamp >= startOfToday - day) return "Yesterday";
  if (timestamp >= startOfToday - 7 * day) return "Previous 7 days";
  if (timestamp >= startOfToday - 30 * day) return "Previous 30 days";
  return "Older";
}
