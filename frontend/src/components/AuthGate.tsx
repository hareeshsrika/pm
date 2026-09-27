"use client";

import { useEffect, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";
import { LoginForm } from "@/components/LoginForm";
import { getCurrentUser, logout, type AuthUser } from "@/lib/auth";

type AuthStatus = "loading" | "signed-out" | "signed-in";

export const AuthGate = () => {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    let isMounted = true;

    getCurrentUser()
      .then((currentUser) => {
        if (!isMounted) return;
        setUser(currentUser);
        setStatus(currentUser ? "signed-in" : "signed-out");
      })
      .catch(() => {
        if (!isMounted) return;
        setUser(null);
        setStatus("signed-out");
      });

    return () => {
      isMounted = false;
    };
  }, []);

  if (status === "loading") {
    return (
      <main className="grid min-h-screen place-items-center bg-[var(--surface)] px-6">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--gray-text)]">
          Checking your session...
        </p>
      </main>
    );
  }

  if (status === "signed-out") {
    return (
      <LoginForm
        onSuccess={(signedInUser) => {
          setUser(signedInUser);
          setStatus("signed-in");
        }}
      />
    );
  }

  return (
    <KanbanBoard
      username={user?.username}
      onLogout={async () => {
        await logout();
        setUser(null);
        setStatus("signed-out");
      }}
    />
  );
};
