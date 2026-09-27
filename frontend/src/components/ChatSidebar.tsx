"use client";

import { useState, type FormEvent } from "react";
import { sendChat, type ChatMessage } from "@/lib/boardApi";
import type { BoardData } from "@/lib/kanban";

type ChatSidebarProps = {
  onBoardUpdated: (board: BoardData) => void;
};

export const ChatSidebar = ({ onBoardUpdated }: ChatSidebarProps) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [message, setMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextMessage = message.trim();
    if (!nextMessage || isSending) return;

    setError(null);
    setMessage("");
    setMessages((current) => [
      ...current,
      { role: "user", content: nextMessage },
    ]);
    setIsSending(true);

    try {
      const response = await sendChat(nextMessage, messages);
      onBoardUpdated(response.board);
      setMessages((current) => [
        ...current,
        { role: "assistant", content: response.reply },
      ]);
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Unable to contact the assistant"
      );
    } finally {
      setIsSending(false);
    }
  };

  return (
    <aside
      aria-label="AI assistant"
      className="flex min-h-[520px] flex-col rounded-3xl border border-[var(--stroke)] bg-white/85 p-5 shadow-[var(--shadow)]"
    >
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
          Board assistant
        </p>
        <h2 className="mt-2 font-display text-xl font-semibold text-[var(--navy-dark)]">
          Ask about your work
        </h2>
        <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
          Ask a question or request a safe board update.
        </p>
      </div>

      <div className="mt-5 flex-1 space-y-3 overflow-y-auto" aria-live="polite">
        {messages.length === 0 && (
          <p className="rounded-2xl border border-dashed border-[var(--stroke)] p-4 text-sm leading-6 text-[var(--gray-text)]">
            Try asking: “What is currently in progress?”
          </p>
        )}
        {messages.map((item, index) => (
          <div
            key={`${item.role}-${index}`}
            className={
                item.role === "user"
                ? "ml-5 whitespace-pre-line rounded-2xl bg-[var(--navy-dark)] p-3 text-sm leading-6 text-white"
                : "mr-5 whitespace-pre-line rounded-2xl bg-[var(--surface)] p-3 text-sm leading-6 text-[var(--navy-dark)]"
            }
          >
            {item.content}
          </div>
        ))}
        {isSending && (
          <p className="text-sm text-[var(--gray-text)]" role="status">
            Thinking...
          </p>
        )}
      </div>

      {error && (
        <p role="alert" className="mb-3 text-sm font-semibold text-[var(--secondary-purple)]">
          {error}
        </p>
      )}

      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <label htmlFor="chat-message" className="sr-only">
          Message for the board assistant
        </label>
        <textarea
          id="chat-message"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ask about your board..."
          rows={3}
          disabled={isSending}
          className="w-full resize-none rounded-2xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)] disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={isSending || !message.trim()}
          className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-3 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSending ? "Sending..." : "Send"}
        </button>
      </form>
    </aside>
  );
};
