import type { Task } from '../types/task'

const DESCRIPTION_PREVIEW_LENGTH = 140

interface TaskListItemProps {
  task: Task
}

function formatEndGoalDate(value: string) {
  const [year, month, day] = value.split('-').map(Number)

  if (!year || !month || !day) {
    return value
  }

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(Date.UTC(year, month - 1, day)))
}

function getDescriptionPreview(description?: string | null) {
  const trimmedDescription = description?.trim()

  if (!trimmedDescription) {
    return null
  }

  if (trimmedDescription.length <= DESCRIPTION_PREVIEW_LENGTH) {
    return {
      fullDescription: trimmedDescription,
      preview: trimmedDescription,
      isTruncated: false,
    }
  }

  const previewText = trimmedDescription.slice(0, DESCRIPTION_PREVIEW_LENGTH)
  const lastSpaceIndex = previewText.lastIndexOf(' ')
  const wordBoundaryPreview =
    lastSpaceIndex > 0 ? previewText.slice(0, lastSpaceIndex) : previewText

  return {
    fullDescription: trimmedDescription,
    preview: `${wordBoundaryPreview.trimEnd()}...`,
    isTruncated: true,
  }
}

function TaskListItem({ task }: TaskListItemProps) {
  const isCompleted = task.status === 'completed'
  const descriptionPreview = getDescriptionPreview(task.description)
  const formattedEndGoalDate = formatEndGoalDate(task.endGoalDate)
  const completedTextClassName = isCompleted
    ? 'task-list-item__text--completed'
    : undefined
  const statusLabel = isCompleted ? 'Completed' : 'Pending'

  return (
    <li
      className={
        isCompleted
          ? 'task-list-item task-list-item--completed'
          : 'task-list-item'
      }
    >
      <article className="task-list-item__content">
        <span className="visually-hidden">{statusLabel}</span>
        <div className="task-list-item__header">
          <h3 className={`task-list-item__title ${completedTextClassName ?? ''}`}>
            {task.title}
          </h3>
          <time
            aria-label={`End goal date: ${formattedEndGoalDate}`}
            className={`task-list-item__date ${completedTextClassName ?? ''}`}
            dateTime={task.endGoalDate}
          >
            <span className="task-list-item__date-label">Due </span>
            {formattedEndGoalDate}
          </time>
        </div>
        {descriptionPreview ? (
          <p
            aria-label={
              descriptionPreview.isTruncated
                ? descriptionPreview.fullDescription
                : undefined
            }
            className={`task-list-item__description ${completedTextClassName ?? ''}`}
            title={
              descriptionPreview.isTruncated
                ? descriptionPreview.fullDescription
                : undefined
            }
          >
            {descriptionPreview.preview}
          </p>
        ) : null}
      </article>
    </li>
  )
}

export default TaskListItem
