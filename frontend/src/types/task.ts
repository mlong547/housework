export type TaskStatus = 'pending' | 'completed'

export interface Task {
  id: string
  title: string
  description?: string | null
  status: TaskStatus
  endGoalDate: string
}
