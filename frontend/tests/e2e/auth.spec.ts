import { test, expect } from '@playwright/test'
import { loginAsDemoUser } from './utils/auth'

test.describe('Authentication', () => {
  test('logs in with demo credentials and shows Kanban board', async ({ page }) => {
    await loginAsDemoUser(page)

    await expect(page.getByRole('button', { name: /logout/i })).toBeVisible()
    await expect(page.getByText(/Track and manage your team's work/i)).toBeVisible()
  })
})
