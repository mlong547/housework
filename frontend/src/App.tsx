import { useState } from 'react'

import LandingPage from './components/LandingPage'
import TaskList from './components/TaskList'
import { placeholderUserTasks } from './data/placeholderTasks'

function App() {
  const [hasPlaceholderSession, setHasPlaceholderSession] = useState(false)

  function handleGoogleSignInPlaceholder() {
    setHasPlaceholderSession(true)
  }

  if (!hasPlaceholderSession) {
    return <LandingPage onSignIn={handleGoogleSignInPlaceholder} />
  }

  return (
    <main className="app-shell" aria-labelledby="app-title">
      <header className="app-shell__header">
        <p className="app-shell__eyebrow">Housework</p>
        <h1 id="app-title">Your chores</h1>
      </header>
      <TaskList tasks={placeholderUserTasks} />
    </main>
  )
}

export default App
