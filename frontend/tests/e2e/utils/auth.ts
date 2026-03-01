import { Page, expect } from '@playwright/test'

export async function loginAsDemoUser(page: Page) {
  page.on('console', msg => console.log('BROWSER LOG:', msg.text()))
  page.on('requestfailed', req => console.log('FAILED REQUEST:', req.url(), req.failure()?.errorText))
  page.on('response', res => {
    if (res.url().includes('/api/')) {
      console.log('API RESPONSE:', res.url(), res.status())
    }
  })
  
  await page.goto('/login')
  await page.waitForLoadState('networkidle')
  console.log('Page loaded, filling credentials...')
  await page.getByLabel('Email address').fill('admin@buro.dev')
  await page.getByLabel('Password').fill('admin123')
  console.log('Clicking sign in button...')
  await page.getByRole('button', { name: /sign in/i }).click()
  
  try {
    await page.waitForResponse(res => res.url().includes('/api/auth/login') && res.status() === 200, { timeout: 10000 })
    console.log('Login response received')
  } catch (e) {
    console.log('Login response wait failed, checking current URL:', page.url())
    const content = await page.content()
    console.log('Page content preview:', content.substring(0, 500))
    throw e
  }
  
  console.log('Waiting for board URL...')
  await page.waitForURL('**/board', { timeout: 15000 })
  await expect(page.getByRole('button', { name: /logout/i })).toBeVisible({ timeout: 10_000 })
}
