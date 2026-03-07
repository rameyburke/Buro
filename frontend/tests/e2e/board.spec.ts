import { test, expect } from '@playwright/test'
import { loginAsDemoUser } from './utils/auth'

async function selectSampleProject(page) {
  await page.goto('/projects')
  const projectHeading = page.getByRole('heading', { name: /Sample Project/i }).first()
  await expect(projectHeading).toBeVisible({ timeout: 15_000 })
  await projectHeading.click()
  await expect(page.getByRole('button', { name: /Sample Project/i })).toBeVisible({
    timeout: 5_000
  })
}

async function goToBoardPage(page) {
  await selectSampleProject(page)
  await page.getByRole('link', { name: /Kanban Board/i }).click()
  await expect(page).toHaveURL(/\/board/)
  await expect(page.getByRole('heading', { name: /Board$/i })).toBeVisible({ timeout: 15_000 })
}

test.describe('Board view', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDemoUser(page)
  })

  test('opens issue view modal when clicking card title', async ({ page }) => {
    await goToBoardPage(page)

    const titleButton = page.locator('[data-testid="issue-card-title"]').first()
    const titleText = (await titleButton.textContent())?.trim()
    await expect(titleButton).toBeVisible({ timeout: 10_000 })
    await titleButton.click()

    const modalHeading = page.getByRole('heading', { name: /Issue Details/i })
    await expect(modalHeading).toBeVisible()

    if (titleText) {
      await expect(page.locator('.view-issue-title')).toContainText(titleText)
    }

    await page.getByRole('button', { name: /^Close$/ }).click()
    await expect(page.locator('.modal-overlay')).toBeHidden()
  })
})
