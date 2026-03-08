import { test, expect } from '@playwright/test'
import { loginAsDemoUser } from './utils/auth'

test.describe('User maintenance', () => {
  test('admin can add user and reveal temp password', async ({ page }) => {
    await loginAsDemoUser(page)
    await page.getByRole('link', { name: /^Users$/ }).click()
    await expect(page).toHaveURL(/\/users/)

    const email = `playwright-user-${Date.now()}@example.com`
    await page.getByRole('button', { name: /add user/i }).click()
    await page.getByLabel('Full name').fill('Playwright User')
    await page.getByLabel('Email').fill(email)
    await page.getByRole('combobox').selectOption('developer')
    await page.getByRole('button', { name: /create user/i }).click()

    await expect(page.getByText('Temporary password:')).toBeVisible({ timeout: 10_000 })
  })

  test('inactive users only appear when filter is enabled', async ({ page }) => {
    await loginAsDemoUser(page)
    await page.getByRole('link', { name: /^Users$/ }).click()

    const email = `inactive-user-${Date.now()}@example.com`
    await page.getByRole('button', { name: /add user/i }).click()
    await page.getByLabel('Full name').fill('Inactive Candidate')
    await page.getByLabel('Email').fill(email)
    await page.getByRole('button', { name: /create user/i }).click()
    await expect(page.locator('.users-table')).toContainText(email)

    const row = page.locator('tr', { hasText: email })
    await row.getByRole('button', { name: /delete/i }).click()
    await page.getByRole('button', { name: /deactivate/i }).click()

    await expect(page.locator('.users-table')).not.toContainText(email)

    await page.getByLabel(/show inactive users/i).check()
    await expect(page.locator('.users-table')).toContainText(email)
    await expect(page.locator('tr', { hasText: email })).toContainText('Inactive')
  })

  test('non-admin cannot access users page', async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel('Email address').fill('manager@buro.dev')
    await page.getByLabel('Password').fill('manager123')
    await page.getByRole('button', { name: /sign in/i }).click()
    await page.waitForURL('**/board', { timeout: 15_000 })

    await page.goto('/users')
    await expect(page).toHaveURL(/\/board/)
    await expect(page.getByRole('heading', { name: /Board$/i })).toBeVisible()
  })
})
