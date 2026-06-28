import TaskListItem from './TaskListItem'
import type { Task } from '../types/task'

interface TaskListProps {
  tasks: Task[]
}

function TaskList({ tasks }: TaskListProps) {
  if (tasks.length === 0) {
    return (
      <section className="task-list" aria-labelledby="task-list-title">
        <h2 id="task-list-title" className="task-list__title">
          Tasks
        </h2>
        <p className="task-list__empty">No tasks yet.</p>
      </section>
    )
  }

  return (
    <section className="task-list" aria-labelledby="task-list-title">
      <h2 id="task-list-title" className="task-list__title">
        Tasks
      </h2>
      <ul className="task-list__items">
        {tasks.map((task) => (
          <TaskListItem key={task.id} task={task} />
        ))}
      </ul>
    </section>
  )
}

export default TaskList
