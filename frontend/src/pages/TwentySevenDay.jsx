import ForecastTable from '../components/ForecastTable'
import ForecastGraphs from '../components/ForecastGraphs'
import HistoricalData from '../components/HistoricalData'
import LoadingSpinner from '../components/LoadingSpinner'
import useForecastData from '../hooks/useForecastData'
import {
  getTwentySevenDayCurrent,
  getTwentySevenDayHistory,
  refreshTwentySevenDayCurrent,
} from '../services/api'

function TwentySevenDay() {
  const {
    current,
    predictions,
    isLoading,
    error,
    refresh,
  } = useForecastData(
    getTwentySevenDayCurrent,
    refreshTwentySevenDayCurrent,
  )

  return (
    <main className="forecast-page">
      <section className="forecast-hero">
        <div className="forecast-title-area">
          <div className="forecast-eyebrow">
            EXTENDED SPACE WEATHER
          </div>

          <h1>27-Day Forecast</h1>

          <p>
            Long-range solar and geomagnetic
            activity outlook.
          </p>

          <button
            type="button"
            className="forecast-refresh"
            onClick={refresh}
            disabled={isLoading}
          >
            <span>↻</span>
            Refresh data
          </button>
        </div>

        <div
          className="forecast-orbit-visual forecast-orbit-long"
          aria-hidden="true"
        >
          <div className="forecast-orbit-ring ring-one" />
          <div className="forecast-orbit-ring ring-two" />
          <div className="forecast-orbit-ring ring-three" />

          <div className="forecast-core">
            <span />
            <span />
            <span />
            <span />
          </div>

          <div className="forecast-orbit-dot dot-one" />
          <div className="forecast-orbit-dot dot-two" />
          <div className="forecast-orbit-dot dot-three" />
        </div>
      </section>

      {isLoading && <LoadingSpinner />}

      {error && (
        <p className="error-message">
          {error}
        </p>
      )}

      {!isLoading && !error && (
        <>
          <div className="forecast-tables">
            <ForecastTable
              title="Current Forecast"
              records={current}
            />

            <ForecastTable
              title="FlareX AI Predictions"
              records={predictions}
            />
          </div>

          <ForecastGraphs
            current={current}
            predictions={predictions}
            type="twenty-seven-day"
          />
        </>
      )}

      <HistoricalData
        title="27-Day Historical Data"
        fetchHistory={getTwentySevenDayHistory}
        type="twenty-seven-day"
      />
    </main>
  )
}

export default TwentySevenDay