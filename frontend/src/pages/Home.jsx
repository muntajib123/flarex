function Home({ onNavigate }) {
  return (
    <main className="home-page">
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="status-dot" />
            LIVE SPACE WEATHER INTELLIGENCE
          </div>

          <p className="eyebrow">
            Solar activity monitoring
          </p>

          <h1>
            Forecast solar
            <br />
            activity with
            <br />
            confidence.
          </h1>

          <p className="hero-description">
            Observe solar activity, analyze emerging
            patterns and explore intelligent forecasts
            across multiple time horizons.
          </p>

          <div className="hero-stats">
            <div className="hero-stat">
              <span className="hero-stat-value">
                3
              </span>
              <span className="hero-stat-label">
                Day Outlook
              </span>
            </div>

            <div className="hero-stat-divider" />

            <div className="hero-stat">
              <span className="hero-stat-value">
                27
              </span>
              <span className="hero-stat-label">
                Day Outlook
              </span>
            </div>

            <div className="hero-stat-divider" />

            <div className="hero-stat">
              <span className="hero-stat-value">
                AI
              </span>
              <span className="hero-stat-label">
                Predictions
              </span>
            </div>
          </div>
        </div>

        <div
          className="solar-visual"
          aria-hidden="true"
        >
          <div className="solar-glow" />

          <div className="solar-orbit solar-orbit-one">
            <span className="orbit-particle" />
          </div>

          <div className="solar-orbit solar-orbit-two">
            <span className="orbit-particle" />
          </div>

          <div className="solar-orbit solar-orbit-three">
            <span className="orbit-particle" />
          </div>

          <div className="sun">
            <div className="sun-core" />

            <div className="sun-flare sun-flare-one" />
            <div className="sun-flare sun-flare-two" />
            <div className="sun-flare sun-flare-three" />
          </div>

          <span className="solar-particle particle-one" />
          <span className="solar-particle particle-two" />
          <span className="solar-particle particle-three" />
          <span className="solar-particle particle-four" />
          <span className="solar-particle particle-five" />
          <span className="solar-particle particle-six" />
          <span className="solar-particle particle-seven" />
          <span className="solar-particle particle-eight" />

          <div className="solar-scan-line" />
        </div>
      </section>

      <section
        className="forecast-grid"
        aria-label="Forecast types"
      >
        <button
          className="forecast-link-card"
          type="button"
          onClick={() =>
            onNavigate('/three-day')
          }
        >
          <div className="forecast-card-icon">
            <div className="forecast-icon three-day-icon">
              <span />
              <span />
              <span />
            </div>
          </div>

          <h2>3-Day Forecast</h2>

          <div className="forecast-card-corner">
            ↗
          </div>
        </button>

        <button
          className="forecast-link-card"
          type="button"
          onClick={() =>
            onNavigate('/twenty-seven-day')
          }
        >
          <div className="forecast-card-icon">
            <div className="forecast-icon twenty-seven-day-icon">
              <span />
              <span />
              <span />
              <span />
            </div>
          </div>

          <h2>27-Day Forecast</h2>

          <div className="forecast-card-corner">
            ↗
          </div>
        </button>
      </section>

      <section className="home-footer-strip">
        <div className="footer-signal">
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>

        <div className="footer-message">
          <span>FLAREX</span>
          <p>
            Observe · Predict · Understand
          </p>
        </div>

        <div className="footer-coordinate">
          <span>SOLAR ACTIVITY</span>
          <span>DATA + AI</span>
        </div>
      </section>
    </main>
  )
}

export default Home