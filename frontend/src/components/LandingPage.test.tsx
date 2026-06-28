import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import LandingPage from './LandingPage'

describe('LandingPage', () => {
  it('renders the unauthenticated landing page content', () => {
    render(<LandingPage onSignIn={() => undefined} />)

    expect(
      screen.getByRole('main', { name: 'Housework' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { level: 1, name: 'Housework' }),
    ).toBeInTheDocument()
    expect(
      screen.getByText('and app for managing your chores'),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'sign in with Google' }),
    ).toBeInTheDocument()
  })

  it('calls the sign-in handler from the Google button', async () => {
    const user = userEvent.setup()
    const handleSignIn = vi.fn()

    render(<LandingPage onSignIn={handleSignIn} />)

    await user.click(screen.getByRole('button', { name: 'sign in with Google' }))

    expect(handleSignIn).toHaveBeenCalledTimes(1)
  })
})
