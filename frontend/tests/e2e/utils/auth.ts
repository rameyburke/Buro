import { Page, expect } from '@playwright/test'

export async function loginAsDemoUser(page: Page) {
  page.on('console', msg => console.log('BROWSER LOG:', msg.text()))
  page.on('requestfailed', req => console.log('FAILED REQUEST:', req.url(), req.failure()?.errorText))
  page.on('response', res => console.log('API RESPONSE:', res.url(), res.status()))
  
  await page.goto('/login')
  await page.waitForLoadState('networkidle')
  
  await page.getByLabel('Email address').fill('admin@buro.dev')
  await page.getByLabel('Password').fill('admin123')
  await page.getByRole('button', { name: /sign in/i }).click()
  
  try {
    await page.waitForResponse(res => res.url().includes('/api/auth/login') && res.status() === 200, { timeout: 10000 })
  } catch (e) {
    console.log('Login failed. Checking page state...')
    const errorText = await page.locator('.text-red-600, .text-red-500, [class*="error"]').first().textContent().catch(() => 'no error text found')
    console.log('Error text:', errorText)
    throw e
  }
  
  await page.waitForURL('**/board', { timeout: 15000 })
  await expect(page.getByRole('button', { name: /logout/i })).toBeVisible({ timeout: 10_000 })
}
