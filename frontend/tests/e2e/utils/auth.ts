import { Page, expect } from '@playwright/test'

type LoginOptions = {
  logConsole?: boolean
  logRequests?: boolean
}

export async function loginAsDemoUser(page: Page, options: LoginOptions = {}) {
  const { logConsole = true, logRequests = true } = options

  if (logConsole) {
    page.on('console', msg => console.log('BROWSER LOG:', msg.text()))
  }
  if (logRequests) {
    page.on('requestfailed', req => {
    const errorText = req.failure()?.errorText ?? ''
    if (errorText.includes('ERR_ABORTED') || errorText.includes('NS_BINDING_ABORTED')) {
      return
    }
    console.log('FAILED REQUEST:', req.url(), errorText)
    })
    page.on('response', res => console.log('API RESPONSE:', res.url(), res.status()))
  }
  
  await page.goto('/login')
  const signInHeading = page.getByRole('heading', { name: /sign in/i })
  const logoutButton = page.getByRole('button', { name: /logout/i })

  await Promise.race([
    signInHeading.waitFor({ state: 'visible' }),
    logoutButton.waitFor({ state: 'visible' }),
    page.waitForURL('**/board')
  ]).catch(() => undefined)

  if (!(await signInHeading.isVisible().catch(() => false))) {
    await expect(logoutButton).toBeVisible({ timeout: 10_000 })
    return
  }
  
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
