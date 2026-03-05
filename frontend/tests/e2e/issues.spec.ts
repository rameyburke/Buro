import { test, expect } from '@playwright/test'
import { loginAsDemoUser } from './utils/auth'

async function selectSampleProject(page) {
  await page.goto('/projects')
  const projectHeading = page.getByRole('heading', { name: /Sample Project/i }).first()
  await expect(projectHeading).toBeVisible({ timeout: 15_000 })
  await projectHeading.click()
  await expect(page.getByRole('button', { name: /Sample Project/i })).toBeVisible({ timeout: 5_000 })
}

async function goToIssuesPage(page) {
  await selectSampleProject(page)
  await page.getByRole('link', { name: /^Issues$/ }).click()
  await expect(page).toHaveURL(/\/issues/)
  await expect(page.getByRole('heading', { name: /^Issues$/ })).toBeVisible({ timeout: 15_000 })
}

async function openCreateIssueModal(page) {
  await page.getByRole('button', { name: /\+ New Issue/i }).click()
  await expect(page.getByRole('heading', { name: /Create New Issue/i })).toBeVisible()
  const modal = page.locator('.modal-overlay')
  await expect(modal).toBeVisible()
  return modal
}

function issueTitleInput(page) {
  return page.getByPlaceholder('Brief description of the issue...')
}

function issueDescriptionInput(page) {
  return page.getByPlaceholder('Detailed issue description...')
}

function typeSelect(page) {
  return page.locator('label', { hasText: 'Type' }).locator('..').getByRole('combobox')
}

function prioritySelect(page) {
  return page.locator('label', { hasText: 'Priority' }).locator('..').getByRole('combobox')
}

function assigneeSearchInput(page) {
  return page.getByPlaceholder('Search team members')
}

function assigneeSelect(page) {
  return page.locator('label', { hasText: 'Assignee (Optional)' }).locator('..').getByRole('combobox')
}

test.describe('Issues management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDemoUser(page)
  })

  test('opens edit issue modal from issues table', async ({ page }) => {
    await goToIssuesPage(page)

    const editButton = page.getByRole('button', { name: /^Edit$/ }).first()
    await expect(editButton).toBeVisible()
    await editButton.click()

    await expect(page.getByRole('heading', { name: /Edit Issue/i })).toBeVisible()
    await page.getByRole('button', { name: /^Cancel$/ }).click()
  })

  test('opens view modal and launches edit from it', async ({ page }) => {
    await goToIssuesPage(page)

    const viewButton = page.getByRole('button', { name: /^View$/ }).first()
    await expect(viewButton).toBeVisible()
    await viewButton.click()

    const viewHeading = page.getByRole('heading', { name: /Issue Details/i })
    await expect(viewHeading).toBeVisible()
    const viewModal = page.locator('.modal-card').filter({ has: viewHeading })
    await viewModal.getByRole('button', { name: /^Edit$/ }).click()

    const editHeading = page.getByRole('heading', { name: /Edit Issue/i })
    await expect(editHeading).toBeVisible()
    const editModal = page.locator('.modal-card').filter({ has: editHeading })
    await expect(editModal.locator('input[type="text"]').first()).toBeFocused()
    await page.getByRole('button', { name: /^Cancel$/ }).click()
  })
})

test.describe('Issue creation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsDemoUser(page)
    await goToIssuesPage(page)
  })

  test('opens create issue modal', async ({ page }) => {
    const modal = await openCreateIssueModal(page)
    await expect(modal.locator('form')).toBeVisible()
  })

  test('disables submit until title is provided', async ({ page }) => {
    await openCreateIssueModal(page)

    const createButton = page.getByRole('button', { name: /^Create Issue$/ })
    await expect(createButton).toBeDisabled()

    await issueTitleInput(page).fill('   ')
    await expect(createButton).toBeDisabled()

    await issueTitleInput(page).fill(`E2E issue ${Date.now()}`)
    await expect(createButton).toBeEnabled()
  })

  test('creates issue with minimal fields', async ({ page }) => {
    const modal = await openCreateIssueModal(page)
    const title = `E2E minimal ${Date.now()}`

    await issueTitleInput(page).fill(title)
    await page.getByRole('button', { name: /^Create Issue$/ }).click()

    await expect(modal).toBeHidden()
    const createdRow = page.locator('.issues-table tbody tr', { hasText: title }).first()
    await expect(createdRow).toBeVisible()
  })

  test('creates issue with full details and assignee', async ({ page }) => {
    const modal = await openCreateIssueModal(page)
    const title = `E2E full ${Date.now()}`

    await issueTitleInput(page).fill(title)
    await issueDescriptionInput(page).fill('Created from Playwright test')
    await typeSelect(page).selectOption('bug')
    await prioritySelect(page).selectOption('high')

    await assigneeSearchInput(page).fill('System')
    await expect(assigneeSelect(page)).toBeEnabled()
    await expect(assigneeSelect(page).locator('option')).toHaveCount(2, { timeout: 10_000 })
    const assigneeValue = await assigneeSelect(page)
      .locator('option', { hasText: 'System Admin' })
      .first()
      .getAttribute('value')
    if (assigneeValue) {
      await assigneeSelect(page).selectOption(assigneeValue)
    }

    await page.getByRole('button', { name: /^Create Issue$/ }).click()

    await expect(modal).toBeHidden()
    const createdRow = page.locator('.issues-table tbody tr', { hasText: title }).first()
    await expect(createdRow).toBeVisible()
    await expect(createdRow).toContainText(/bug/i)
    await expect(createdRow).toContainText(/high/i)
    await expect(createdRow).toContainText(/System Admin/i)
  })

  test('cancel closes and resets form', async ({ page }) => {
    let modal = await openCreateIssueModal(page)

    await issueTitleInput(page).fill('Temporary issue')
    await page.getByRole('button', { name: /^Cancel$/ }).click()
    await expect(modal).toBeHidden()

    modal = await openCreateIssueModal(page)
    await expect(issueTitleInput(page)).toHaveValue('')
    await expect(page.getByRole('button', { name: /^Create Issue$/ })).toBeDisabled()
  })

  test('shows error when create fails', async ({ page }) => {
    await page.route('**/api/issues/', async (route) => {
      await route.fulfill({
        status: 500,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ detail: 'Failed to create issue' })
      })
    })

    await openCreateIssueModal(page)
    await issueTitleInput(page).fill(`E2E failure ${Date.now()}`)
    await page.getByRole('button', { name: /^Create Issue$/ }).click()

    await expect(page.getByText(/Failed to create issue/i)).toBeVisible()
    await expect(page.locator('.modal-overlay')).toBeVisible()
  })
})
