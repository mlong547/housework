interface LandingPageProps {
  onSignIn: () => void
}

function LandingPage({ onSignIn }: LandingPageProps) {
  return (
    <main className="landing-page" aria-labelledby="landing-page-title">
      <section className="landing-page__content">
        <h1 id="landing-page-title">Housework</h1>
        <p className="landing-page__description">
          and app for managing your chores
        </p>
        <button
          className="landing-page__sign-in"
          type="button"
          onClick={onSignIn}
        >
          sign in with Google
        </button>
      </section>
    </main>
  )
}

export default LandingPage
