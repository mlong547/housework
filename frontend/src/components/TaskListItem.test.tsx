import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import TaskListItem from './TaskListItem'
import type { Task } from '../types/task'

const baseTask: Task = {
  id: 'task-1',
  title: 'Replace HVAC filter',
  description: 'Use the filter stored in the utility closet.',
  status: 'pending',
  endGoalDate: '2026-07-01',
}

describe('TaskListItem', () => {
  it('shows the task name, end goal date, and description', () => {
    render(<TaskListItem task={baseTask} />)

    expect(
      screen.getByRole('heading', { name: /replace hvac filter/i }),
    ).toBeInTheDocument()
    expect(screen.getByText('Jul 1, 2026')).toBeInTheDocument()
    expect(
      screen.getByText(/use the filter stored in the utility closet/i),
    ).toBeInTheDocument()
    expect(
      screen.getByLabelText('End goal date: Jul 1, 2026'),
    ).toBeInTheDocument()
    expect(screen.getByText('Pending')).toBeInTheDocument()
  })

  it('shortens long descriptions with an ellipsis', () => {
    const longDescription =
      'Wipe down the counters, cabinet fronts, sink, fixtures, backsplash, stovetop, and the appliance handles before putting the cleaning supplies away.'

    render(
      <TaskListItem
        task={{
          ...baseTask,
          description: longDescription,
        }}
      />,
    )

    const item = screen.getByRole('listitem')
    const descriptionPreview = within(item).getByText(/\.\.\.$/)

    expect(descriptionPreview).toBeInTheDocument()
    expect(descriptionPreview).toHaveAttribute('title', longDescription)
    expect(descriptionPreview).toHaveAccessibleName(longDescription)
    expect(screen.queryByText(longDescription)).not.toBeInTheDocument()
  })

  it('styles completed tasks with a completed state', () => {
    render(
      <TaskListItem
        task={{
          ...baseTask,
          status: 'completed',
        }}
      />,
    )

    expect(screen.getByRole('listitem')).toHaveClass('task-list-item--completed')
    expect(
      screen.getByRole('heading', { name: /replace hvac filter/i }),
    ).toHaveClass('task-list-item__text--completed')
    expect(screen.getByText('Jul 1, 2026')).toHaveClass(
      'task-list-item__text--completed',
    )
    expect(screen.getByText('Completed')).toBeInTheDocument()
  })
})
