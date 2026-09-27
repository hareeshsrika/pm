import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import * as boardApi from "@/lib/boardApi";
import { initialData, type BoardData } from "@/lib/kanban";
import { ChatSidebar } from "@/components/ChatSidebar";

vi.mock("@/lib/boardApi", () => ({
  sendChat: vi.fn(),
}));

describe("ChatSidebar", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("sends a message and applies the returned board", async () => {
    const updatedBoard: BoardData = {
      ...initialData,
      columns: initialData.columns.map((column) =>
        column.id === "col-review" ? { ...column, title: "Approval" } : column
      ),
    };
    vi.mocked(boardApi.sendChat).mockResolvedValue({
      reply: "I renamed Review to Approval.",
      operations: [],
      board: updatedBoard,
    });
    const onBoardUpdated = vi.fn();

    render(<ChatSidebar onBoardUpdated={onBoardUpdated} />);
    await userEvent.type(
      screen.getByLabelText("Message for the board assistant"),
      "Rename Review"
    );
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("I renamed Review to Approval.")).toBeInTheDocument();
    expect(boardApi.sendChat).toHaveBeenCalledWith("Rename Review", []);
    expect(onBoardUpdated).toHaveBeenCalledWith(updatedBoard);
  });

  it("shows an assistant error", async () => {
    vi.mocked(boardApi.sendChat).mockRejectedValue(
      new Error("Assistant request failed")
    );

    render(<ChatSidebar onBoardUpdated={vi.fn()} />);
    await userEvent.type(
      screen.getByLabelText("Message for the board assistant"),
      "Help"
    );
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Assistant request failed"
    );
  });
});
