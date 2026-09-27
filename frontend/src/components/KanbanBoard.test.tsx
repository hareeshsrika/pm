import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import * as boardApi from "@/lib/boardApi";
import { initialData, type BoardData } from "@/lib/kanban";
import { KanbanBoard } from "@/components/KanbanBoard";

vi.mock("@/lib/boardApi", () => ({
  createCard: vi.fn(),
  deleteCard: vi.fn(),
  getBoard: vi.fn(),
  moveCard: vi.fn(),
  renameColumn: vi.fn(),
  sendChat: vi.fn(),
  updateCard: vi.fn(),
}));

const cloneBoard = (): BoardData => JSON.parse(JSON.stringify(initialData));
let mockBoard: BoardData;
const cloneCurrentBoard = (): BoardData => JSON.parse(JSON.stringify(mockBoard));

describe("KanbanBoard", () => {
  beforeEach(() => {
    mockBoard = cloneBoard();
    vi.mocked(boardApi.getBoard).mockResolvedValue(cloneCurrentBoard());
    vi.mocked(boardApi.renameColumn).mockImplementation(async (columnId, title) => {
      mockBoard.columns = mockBoard.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      );
      return cloneCurrentBoard();
    });
    vi.mocked(boardApi.createCard).mockImplementation(async (columnId, title, details) => {
      const id = "card-new";
      mockBoard.cards[id] = { id, title, details };
      mockBoard.columns = mockBoard.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column
      );
      return cloneCurrentBoard();
    });
    vi.mocked(boardApi.deleteCard).mockImplementation(async (cardId) => {
      delete mockBoard.cards[cardId];
      mockBoard.columns = mockBoard.columns.map((column) => ({
        ...column,
        cardIds: column.cardIds.filter((id) => id !== cardId),
      }));
      return cloneCurrentBoard();
    });
  });

  it("renders five columns from the API", async () => {
    render(<KanbanBoard />);
    expect(await screen.findAllByTestId(/column-/i)).toHaveLength(5);
    expect(boardApi.getBoard).toHaveBeenCalledOnce();
  });

  it("renames a column", async () => {
    render(<KanbanBoard />);
    const columns = await screen.findAllByTestId(/column-/i);
    const input = within(columns[0]).getByLabelText("Column title");
    await userEvent.clear(input);
    await userEvent.type(input, "New Name");
    expect(input).toHaveValue("New Name");
    await userEvent.tab();
    expect(boardApi.renameColumn).toHaveBeenCalledWith("col-backlog", "New Name");
  });

  it("adds and removes a card through the API", async () => {
    render(<KanbanBoard />);
    const columns = await screen.findAllByTestId(/column-/i);
    const column = columns[0];
    await userEvent.click(within(column).getByRole("button", { name: /add a card/i }));

    await userEvent.type(within(column).getByPlaceholderText(/card title/i), "New card");
    await userEvent.type(within(column).getByPlaceholderText(/details/i), "Notes");
    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(await within(column).findByText("New card")).toBeInTheDocument();
    expect(boardApi.createCard).toHaveBeenCalledWith("col-backlog", "New card", "Notes");

    await userEvent.click(
      within(column).getByRole("button", { name: /delete new card/i })
    );
    expect(boardApi.deleteCard).toHaveBeenCalledWith("card-new");
    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });
});
