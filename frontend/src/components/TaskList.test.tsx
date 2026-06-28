import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import TaskList from './TaskList'
import type { Task } from '../types/task'

const tasks: Task[] = [
  {
    id: 'task-1',
    title: 'Replace HVAC filter',
    description: 'Use the filter stored in the utility closet.',
    status: 'pending',
    endGoalDate: '2026-07-01',
  },
  {
    id: 'task-2',
    title: 'Clean bathrooms',
    description: 'Scrub sinks and mirrors.',
    status: 'completed',
    endGoalDate: '2026-07-03',
  },
]

describe('TaskList', () => {
  it('renders one list item for each task passed in', () => {
    render(<TaskList tasks={tasks} />)

    expect(screen.getByRole('region', { name: /tasks/i })).toBeInTheDocument()
    expect(screen.getAllByRole('listitem')).toHaveLength(tasks.length)
    expect(
      screen.getByRole('heading', { name: /replace hvac filter/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: /clean bathrooms/i }),
    ).toBeInTheDocument()
  })

  it('renders an empty state when there are no tasks', () => {
    render(<TaskList tasks={[]} />)

    expect(screen.getByText(/no tasks yet/i)).toBeInTheDocument()
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })
})
