// Mentor conversations, saved in the database through /api/conversations.
//
// In the page a conversation is { id, title, updatedAt (ms), messages }, where
// `messages` is undefined until the chat is opened (the list comes without them).
// A message: { id, role, content, attachments?, error?, stopped?, edited? }

import { api } from "./api";

const fromApi = (c) => ({ id: c.id, title: c.title, updatedAt: Date.parse(c.updated_at) });

/** All saved conversations, newest first, without their messages. */
export async function listConversations() {
  return (await api.get("/api/conversations")).map(fromApi);
}

/** One conversation with its messages. */
export async function getConversation(id) {
  const data = await api.get(`/api/conversations/${encodeURIComponent(id)}`);
  return { ...fromApi(data), messages: data.messages };
}

/** Create the conversation, or replace its title and all its messages. */
export function saveConversation({ id, title, updatedAt, messages }) {
  return api.put(`/api/conversations/${encodeURIComponent(id)}`, {
    title,
    updated_at: new Date(updatedAt).toISOString(),
    messages: messages.map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      attachments: m.attachments ?? [],
      error: m.error ?? null,
      stopped: !!m.stopped,
      edited: !!m.edited,
    })),
  });
}

export function renameConversation(id, title) {
  return api.patch(`/api/conversations/${encodeURIComponent(id)}`, { title });
}

export function deleteConversation(id) {
  return api.delete(`/api/conversations/${encodeURIComponent(id)}`);
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
