import { expect, test } from "@playwright/test";

test("Docker-served frontend uses the real authentication and board API", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /sign in to kanban studio/i })
  ).toBeVisible();

  await page.getByLabel("Username").fill("user");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);

  await page.reload();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);

  await page.getByRole("button", { name: "Log out" }).click();
  await expect(
    page.getByRole("heading", { name: /sign in to kanban studio/i })
  ).toBeVisible();
});
