import type { Task } from '../types/task'

export const placeholderUserTasks: Task[] = [
  {
    id: 'clean-kitchen-counters',
    title: 'Clean kitchen counters',
    description: 'Wipe counters, stovetop, and the small appliance area.',
    status: 'pending',
    endGoalDate: '2026-07-03',
  },
  {
    id: 'replace-hvac-filter',
    title: 'Replace HVAC filter',
    description: 'Use the 20x25x1 filter from the garage shelf.',
    status: 'completed',
    endGoalDate: '2026-07-01',
  },
]
