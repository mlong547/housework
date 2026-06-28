import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('App', () => {
  it('renders the accessible skeleton shell', () => {
    render(<App />)

    expect(
      screen.getByRole('main', { name: /frontend foundation/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/react, typescript, test, lint, and design-token setup/i),
    ).toBeInTheDocument()
  })
})
