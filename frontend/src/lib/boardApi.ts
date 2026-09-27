import type { BoardData } from "@/lib/kanban";

const getErrorMessage = async (
  response: Response,
  fallback = "Board request failed"
) => {
  try {
    const data = await response.json();
    return data.detail ?? fallback;
  } catch {
    return fallback;
  }
};

const requestBoard = async (input: RequestInfo, init?: RequestInit) => {
  const response = await fetch(input, {
    ...init,
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return response.json() as Promise<BoardData>;
};

export const getBoard = () => requestBoard("/api/board");

export const renameColumn = (columnId: string, title: string) =>
  requestBoard(`/api/board/columns/${columnId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });

export const createCard = (
  columnId: string,
  title: string,
  details: string
) =>
  requestBoard("/api/board/cards", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ column_id: columnId, title, details }),
  });

export const updateCard = (cardId: string, title: string, details: string) =>
  requestBoard(`/api/board/cards/${cardId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, details }),
  });

export const deleteCard = (cardId: string) =>
  requestBoard(`/api/board/cards/${cardId}`, {
    method: "DELETE",
  });

export const moveCard = (cardId: string, columnId: string, position: number) =>
  requestBoard(`/api/board/cards/${cardId}/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ column_id: columnId, position }),
  });

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ChatResponse = {
  reply: string;
  operations: Record<string, unknown>[];
  board: BoardData;
};

export const sendChat = async (
  message: string,
  history: ChatMessage[]
): Promise<ChatResponse> => {
  const response = await fetch("/api/ai/chat", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Assistant request failed"));
  }
  return response.json() as Promise<ChatResponse>;
};
