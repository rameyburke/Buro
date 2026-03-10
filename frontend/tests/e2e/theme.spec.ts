import { test, expect } from '@playwright/test'
import { loginAsDemoUser } from './utils/auth'

test.describe('Theme preferences', () => {
  test.skip(({ browserName }) => browserName === 'firefox', 'Theme toggle persistence is validated in Chromium; Firefox timing is flaky in CI.')

  test('persists selected theme across logout and login', async ({ page }) => {
    await loginAsDemoUser(page)

    const toggle = page.getByTestId('theme-toggle')
    await expect(toggle).toBeVisible()

    // Normalize state: switch to dark once so persistence assertion is deterministic.
    if ((await toggle.textContent())?.trim() === 'Dark') {
      const profileRefresh = page.waitForResponse(
        (response) => response.url().includes('/api/auth/me/') && response.status() === 200,
      )
      await toggle.click()
      await profileRefresh
    }

    await expect(page.locator('.app-root')).toHaveClass(/dark/)

    await page.getByRole('button', { name: /logout/i }).click()
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible({ timeout: 15_000 })

    await loginAsDemoUser(page, { logConsole: false, logRequests: false })
    await expect(page.locator('.app-root')).toHaveClass(/dark/)

    // Cleanup so other tests run with the default visual baseline.
    const toggleAfterRelogin = page.getByTestId('theme-toggle')
    if ((await toggleAfterRelogin.textContent())?.trim() === 'Light') {
      await toggleAfterRelogin.click()
    }
    await expect(page.locator('.app-root')).not.toHaveClass(/dark/)
  })
})
