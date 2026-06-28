import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('App', () => {
  it('renders the landing page before sign-in', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { level: 1, name: 'Housework' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'sign in with Google' }),
    ).toBeInTheDocument()
  })

  it('renders the task list after sign-in', async () => {
    const user = userEvent.setup()

    render(<App />)

    await user.click(screen.getByRole('button', { name: 'sign in with Google' }))

    expect(
      screen.getByRole('heading', { level: 1, name: 'Your chores' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('region', { name: /tasks/i })).toBeInTheDocument()
    expect(screen.getByText('Clean kitchen counters')).toBeInTheDocument()
  })
})
