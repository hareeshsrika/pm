import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthGate } from "@/components/AuthGate";

describe("AuthGate", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows the sign-in form when there is no session", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ status: 401, ok: false })
    );

    render(<AuthGate />);

    expect(
      await screen.findByRole("heading", { name: /sign in to kanban studio/i })
    ).toBeInTheDocument();
  });

  it("shows an error for invalid credentials", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ status: 401, ok: false })
      .mockResolvedValueOnce({
        status: 401,
        ok: false,
        json: async () => ({ detail: "Invalid username or password" }),
      });
    vi.stubGlobal("fetch", fetchMock);

    render(<AuthGate />);
    await screen.findByRole("heading", { name: /sign in to kanban studio/i });

    await userEvent.type(screen.getByLabelText("Username"), "user");
    await userEvent.type(screen.getByLabelText("Password"), "wrong");
    await userEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Invalid username or password"
      )
    );
  });
});
