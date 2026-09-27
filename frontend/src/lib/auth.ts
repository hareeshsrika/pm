export type AuthUser = {
  authenticated: true;
  username: string;
};

const getErrorMessage = async (response: Response) => {
  try {
    const data = await response.json();
    return data.detail ?? "Authentication request failed";
  } catch {
    return "Authentication request failed";
  }
};

export const getCurrentUser = async (): Promise<AuthUser | null> => {
  const response = await fetch("/api/auth/me", { credentials: "include" });
  if (response.status === 401) {
    return null;
  }
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return response.json();
};

export const login = async (
  username: string,
  password: string
): Promise<AuthUser> => {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return response.json();
};

export const logout = async () => {
  const response = await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
};
