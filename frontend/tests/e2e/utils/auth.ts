import { Page, expect } from '@playwright/test'

export async function loginAsDemoUser(page: Page) {
  await page.goto('/login')
  await page.getByLabel('Email address').fill('admin@buro.dev')
  await page.getByLabel('Password').fill('admin123')
  await Promise.all([
    page.waitForResponse((res) => res.url().includes('/api/auth/login') && res.status() === 200),
    page.getByRole('button', { name: /sign in/i }).click()
  ])
  await page.waitForURL('**/board', { timeout: 15000 })
  await expect(page.getByRole('button', { name: /logout/i })).toBeVisible({ timeout: 10_000 })
}
