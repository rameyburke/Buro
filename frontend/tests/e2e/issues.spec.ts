import { test, expect } from '@playwright/test'
import { loginAsDemoUser } from './utils/auth'

async function selectSampleProject(page) {
  await page.goto('/projects')
  const projectHeading = page.getByRole('heading', { name: /Sample Project/i }).first()
  await expect(projectHeading).toBeVisible({ timeout: 15_000 })
  await projectHeading.click()
  await expect(page.getByRole('button', { name: /Sample Project/i })).toBeVisible({ timeout: 5_000 })
}

test.describe('Issues management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDemoUser(page)
  })

  test('opens edit issue modal from issues table', async ({ page }) => {
    await selectSampleProject(page)
    await page.getByRole('link', { name: /^Issues$/ }).click()
    await expect(page).toHaveURL(/\/issues/)
    await expect(page.getByRole('heading', { name: /^Issues$/ })).toBeVisible({ timeout: 15_000 })

    const editButton = page.getByRole('button', { name: /^Edit$/ }).first()
    await expect(editButton).toBeVisible()
    await editButton.click()

    await expect(page.getByRole('heading', { name: /Edit Issue/i })).toBeVisible()
    await page.getByRole('button', { name: /^Cancel$/ }).click()
  })
})
