import { expect, test, type Page } from "@playwright/test";

type MockBoard = {
  columns: { id: string; title: string; cardIds: string[] }[];
  cards: Record<string, { id: string; title: string; details: string }>;
};

const createMockBoard = (): MockBoard => ({
  columns: [
    { id: "col-backlog", title: "Backlog", cardIds: ["card-1", "card-2"] },
    { id: "col-discovery", title: "Discovery", cardIds: ["card-3"] },
    { id: "col-progress", title: "In Progress", cardIds: ["card-4", "card-5"] },
    { id: "col-review", title: "Review", cardIds: ["card-6"] },
    { id: "col-done", title: "Done", cardIds: ["card-7", "card-8"] },
  ],
  cards: {
    "card-1": { id: "card-1", title: "Align roadmap themes", details: "Draft quarterly themes." },
    "card-2": { id: "card-2", title: "Gather customer signals", details: "Review customer feedback." },
    "card-3": { id: "card-3", title: "Prototype analytics view", details: "Sketch the dashboard." },
    "card-4": { id: "card-4", title: "Refine status language", details: "Standardize column labels." },
    "card-5": { id: "card-5", title: "Design card layout", details: "Add hierarchy and spacing." },
    "card-6": { id: "card-6", title: "QA micro-interactions", details: "Verify interaction states." },
    "card-7": { id: "card-7", title: "Ship marketing page", details: "Deliver the approved page." },
    "card-8": { id: "card-8", title: "Close onboarding sprint", details: "Document release notes." },
  },
});

const mockBoardApi = async (page: Page, emptyReview = false) => {
  const board = createMockBoard();
  if (emptyReview) {
    board.columns[3].cardIds = [];
    delete board.cards["card-6"];
  }
  await page.route("**/api/board**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const json = () =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(board),
      });

    if (request.method() === "GET" && path === "/api/board") {
      await json();
      return;
    }

    if (request.method() === "PATCH" && path.startsWith("/api/board/columns/")) {
      const columnId = path.split("/").pop();
      const body = request.postDataJSON();
      const column = board.columns.find((item) => item.id === columnId);
      if (column) column.title = body.title;
      await json();
      return;
    }

    if (request.method() === "POST" && path === "/api/board/cards") {
      const body = request.postDataJSON();
      const id = "card-playwright";
      board.cards[id] = { id, title: body.title, details: body.details };
      board.columns
        .find((column) => column.id === body.column_id)
        ?.cardIds.push(id);
      await json();
      return;
    }

    if (request.method() === "PATCH" && path.startsWith("/api/board/cards/")) {
      const cardId = path.split("/").pop() ?? "";
      const body = request.postDataJSON();
      if (board.cards[cardId]) {
        board.cards[cardId].title = body.title;
        board.cards[cardId].details = body.details;
      }
      await json();
      return;
    }

    if (request.method() === "DELETE" && path.startsWith("/api/board/cards/")) {
      const cardId = path.split("/").pop() ?? "";
      delete board.cards[cardId];
      board.columns.forEach((column) => {
        column.cardIds = column.cardIds.filter((id) => id !== cardId);
      });
      await json();
      return;
    }

    if (request.method() === "POST" && path.endsWith("/move")) {
      const cardId = path.split("/").slice(-2, -1)[0];
      const body = request.postDataJSON();
      const source = board.columns.find((column) => column.cardIds.includes(cardId));
      const target = board.columns.find((column) => column.id === body.column_id);
      if (source && target) {
        source.cardIds = source.cardIds.filter((id) => id !== cardId);
        target.cardIds.splice(Math.min(body.position, target.cardIds.length), 0, cardId);
      }
      await json();
      return;
    }

    await route.continue();
  });
};

const mockSignedOutAuth = async (page: Page, emptyReview = false) => {
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({ status: 401, body: JSON.stringify({ detail: "Not authenticated" }) })
  );
  await page.route("**/api/auth/login", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: true, username: "user" }),
    })
  );
  await page.route("**/api/auth/logout", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ authenticated: false }),
    })
  );
  await mockBoardApi(page, emptyReview);
  await page.route("**/api/ai/chat", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        reply: "There are two cards in progress.",
        operations: [],
        board: createMockBoard(),
      }),
    });
  });
};

const signIn = async (page: Page, emptyReview = false) => {
  await mockSignedOutAuth(page, emptyReview);
  await page.goto("/");
  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
};

test("requires sign in", async ({ page }) => {
  await mockSignedOutAuth(page);
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /sign in to kanban studio/i })
  ).toBeVisible();
  await expect(page.getByTestId("column-col-backlog")).not.toBeVisible();
});

test("signs in and logs out", async ({ page }) => {
  await signIn(page);
  await page.getByRole("button", { name: "Log out" }).click();
  await expect(
    page.getByRole("heading", { name: /sign in to kanban studio/i })
  ).toBeVisible();
});

test("loads the kanban board", async ({ page }) => {
  await signIn(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await signIn(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("uses the assistant sidebar", async ({ page }) => {
  await signIn(page);
  await page
    .getByLabel("Message for the board assistant")
    .fill("What is currently in progress?");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("There are two cards in progress.")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await signIn(page);
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

const dragCardToColumn = async (page: Page, columnId: string) => {
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId(`column-${columnId}`);
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 160,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
};

test("moves a Backlog card into In Progress", async ({ page }) => {
  await signIn(page);
  await dragCardToColumn(page, "col-progress");
});

test("moves a Backlog card into Done", async ({ page }) => {
  await signIn(page);
  await dragCardToColumn(page, "col-done");
});

test("moves a card into an empty column", async ({ page }) => {
  await signIn(page, true);
  const card = page.getByTestId("card-card-4");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 160,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-4")).toBeVisible();
});
