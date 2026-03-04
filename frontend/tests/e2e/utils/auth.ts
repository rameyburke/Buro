import { Page, expect } from '@playwright/test'

export async function loginAsDemoUser(page: Page) {
  page.on('console', msg => console.log('BROWSER LOG:', msg.text()))
  page.on('requestfailed', req => {
    const errorText = req.failure()?.errorText ?? ''
    if (errorText.includes('ERR_ABORTED') || errorText.includes('NS_BINDING_ABORTED')) {
      return
    }
    console.log('FAILED REQUEST:', req.url(), errorText)
  })
  page.on('response', res => console.log('API RESPONSE:', res.url(), res.status()))
  
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible({ timeout: 10_000 })
  
  await page.getByLabel('Email address').fill('admin@buro.dev')
  await page.getByLabel('Password').fill('admin123')
  const loginResponse = page.waitForResponse(
    res => res.url().includes('/api/auth/login') && res.status() === 200,
    { timeout: 15_000 }
  )
  await page.getByRole('button', { name: /sign in/i }).click()
  
  try {
    await loginResponse
  } catch (e) {
    console.log('Login response wait failed. Checking page state...')
    const errorText = await page
      .locator('.text-red-600, .text-red-500, [class*="error"]')
      .first()
      .textContent()
      .catch(() => 'no error text found')
    console.log('Error text:', errorText)
  }
  
  await page.waitForURL('**/board', { timeout: 15_000 })
  await expect(page.getByRole('button', { name: /logout/i })).toBeVisible({ timeout: 10_000 })
}
