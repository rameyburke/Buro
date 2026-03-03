import { test, expect } from '@playwright/test'
import { loginAsDemoUser } from './utils/auth'

test.describe('Authentication', () => {
  test('logs in with demo credentials and shows Kanban board', async ({ page }) => {
    await loginAsDemoUser(page)

    // Wait for logout button to confirm login
    await expect(page.getByRole('button', { name: /logout/i })).toBeVisible()

    // Wait for kanban board to load with extended timeout
    await expect(page.getByText(/Track and manage your team's work/i)).toBeVisible({ timeout: 30000 })

    // Also verify we're on the right page
    await expect(page).toHaveURL('/board')
  })
})
