"use client";

import { useState, type FormEvent } from "react";
import { login, type AuthUser } from "@/lib/auth";

type LoginFormProps = {
  onSuccess: (user: AuthUser) => void;
};

export const LoginForm = ({ onSuccess }: LoginFormProps) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const user = await login(username, password);
      onSuccess(user);
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Unable to sign in"
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="relative grid min-h-screen place-items-center overflow-hidden px-6 py-12">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <section className="relative w-full max-w-md rounded-[32px] border border-[var(--stroke)] bg-white/90 p-8 shadow-[var(--shadow)] backdrop-blur">
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
          Single Board Kanban
        </p>
        <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
          Sign in to Kanban Studio
        </h1>
        <p className="mt-3 text-sm leading-6 text-[var(--gray-text)]">
          Sign in to access your project board.
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          <div>
            <label
              htmlFor="username"
              className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
            >
              Username
            </label>
            <input
              id="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              required
              className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
            />
          </div>
          <div>
            <label
              htmlFor="password"
              className="text-xs font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
              className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
            />
          </div>
          {error && (
            <p role="alert" className="text-sm font-semibold text-[var(--secondary-purple)]">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-full bg-[var(--secondary-purple)] px-4 py-3 text-xs font-semibold uppercase tracking-wide text-white transition hover:brightness-110 disabled:cursor-wait disabled:opacity-60"
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
};
