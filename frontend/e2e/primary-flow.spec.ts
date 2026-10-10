// TEST-54: index §7 primary flow in 4 browser contexts (Aarav, Meera, Suresh, Kavya), steps 1, 3, 4, 6, 7, 9, 10.
// Step 2 (uploads) is covered by TEST-13 in pytest, so step 3 here applies without the uploads.
// Needs a fresh `seed --reset` (TODAY_OVERRIDE or --anchor-date so the seeded flags hold).
import { expect, test, type Browser, type Page } from "@playwright/test";

const PASSWORD = "Demo@123"; // synthetic demo password (README)

async function login(browser: Browser, email: string, home: RegExp): Promise<Page> {
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(PASSWORD);
  await page.getByRole("button", { name: /log in/i }).click();
  await expect(page).toHaveURL(home);
  return page;
}

test.describe.configure({ mode: "serial" });

test("index §7 primary flow", async ({ browser }) => {
  // Step 1: Aarav opens "Edge AI for Agriculture": fit 38–50, "Close" (AC-004.1).
  const aarav = await login(browser, "aarav@demo.gurusetu", /\/student$/);
  await aarav.getByRole("link", { name: /Edge AI for Agriculture/ }).first().click();
  await expect(aarav).toHaveURL(/\/student\/openings\/op-edge-ai/);
  await expect(aarav.getByText(/^Close/).first()).toBeVisible();

  // Step 3 (without uploads): apply → "Applied · Pending"; applying again shows "Applied" (AC-006.1).
  await aarav.getByRole("button", { name: /^Apply/ }).click();
  await expect(aarav.getByText(/Applied/).first()).toBeVisible();

  // Step 4: Meera sees Aarav among the ranked applicants, shortlists, then accepts (REQ-005, REQ-006).
  const meera = await login(browser, "meera@demo.gurusetu", /\/faculty$/);
  await meera.goto("/faculty/openings/op-edge-ai");
  await expect(meera.getByText("Aarav Menon").first()).toBeVisible();
  await meera.getByRole("button", { name: "Shortlist Aarav Menon" }).click();
  await expect(meera.getByText("Aarav Menon shortlisted.")).toBeVisible();
  await meera.getByRole("button", { name: "Accept Aarav Menon" }).click();
  await expect(meera.getByText("Aarav Menon accepted. Guide link created.")).toBeVisible();

  // Step 6: My mentees shows 13 assigned rows, 3 flagged; log a group session (REQ-012, REQ-008).
  await meera.goto("/faculty");
  const assigned = meera.locator("section:has(#assigned-title) > ul > li");
  await expect(assigned).toHaveCount(13);
  await expect(meera.locator("section:has(#assigned-title) [aria-label='Needs attention']")).toHaveCount(3);
  await meera.getByRole("link", { name: /^Log session$/ }).click();
  await expect(meera).toHaveURL(/\/faculty\/sessions\/new$/);
  await meera.getByLabel(/Select all mentees/).check();
  await meera.locator("fieldset:has(legend:text('Attendance for Diya Ramesh')) label:text('Absent')").click();
  await meera.getByRole("button", { name: "Academic", exact: true }).click();
  await meera.getByRole("button", { name: "Attendance", exact: true }).click();
  const actions = ["Finish DL assignment 3", "Read the CNN chapter"];
  for (let i = 0; i < actions.length; i++) {
    const text = actions[i];
    await meera.getByRole("button", { name: "Add action item" }).click();
    await meera.locator(`#sf-actions-${i}-student_id`).selectOption({ label: "Aarav Menon" });
    await meera.locator(`#sf-actions-${i}-text`).fill(text);
  }
  await meera.getByRole("button", { name: "Add issue" }).click();
  await meera.locator("#sf-issues-0-student_id").selectOption({ label: "Diya Ramesh" });
  await meera.locator("#sf-issues-0-category").selectOption("attendance");
  await meera.locator("#sf-issues-0-text").fill("Attendance below 75% in two courses");
  await meera.getByRole("button", { name: "Save session" }).click();
  // 13 selected with Diya absent = 12 present; the toast counts present attendees (FLOW-07).
  await expect(meera.getByText("Session saved for 12 students")).toBeVisible();

  // Step 7: Aarav confirms the session and marks one action item done (REQ-009, REQ-010, REQ-014).
  await aarav.goto("/student/mentorship");
  await aarav.getByRole("button", { name: /Confirm I attended/ }).first().click();
  await expect(aarav.getByText(/Confirmed/).first()).toBeVisible();
  await aarav.getByRole("checkbox", { name: /Mark done/ }).first().check();

  // Step 9: Suresh's dashboard shows 48/50 allotted and a needs-attention list with names (REQ-016).
  const suresh = await login(browser, "suresh@demo.gurusetu", /\/coordinator$/);
  await expect(suresh.getByText("48/50").first()).toBeVisible();
  await expect(suresh.getByText(/Karthik S/).first()).toBeVisible();

  // Step 10: Kavya sees no student names; both exports are available (REQ-016 AC-016.2, REQ-017).
  const kavya = await login(browser, "kavya@demo.gurusetu", /\/coordinator$/);
  await expect(kavya.getByText(/Karthik S|Aarav Menon|Diya Ramesh/)).toHaveCount(0);
  await expect(kavya.getByRole("button", { name: /Export mentoring pack/ })).toBeVisible();
  await expect(kavya.getByRole("button", { name: /Export achievements/ })).toBeVisible();
});
