import ForecastTable from '../components/ForecastTable'
import ForecastGraphs from '../components/ForecastGraphs'
import HistoricalData from '../components/HistoricalData'
import LoadingSpinner from '../components/LoadingSpinner'
import useForecastData from '../hooks/useForecastData'
import {
  getThreeDayCurrent,
  getThreeDayHistory,
  refreshThreeDayCurrent,
} from '../services/api'

function ThreeDay() {
  const {
    current,
    predictions,
    isLoading,
    error,
    refresh,
  } = useForecastData(
    getThreeDayCurrent,
    refreshThreeDayCurrent,
  )

  return (
    <main className="forecast-page">
      <h1>3-Day Forecast</h1>

      <section
        className="forecast-metadata"
        aria-live="polite"
      >
        <button
          type="button"
          onClick={refresh}
          disabled={isLoading}
        >
          Refresh
        </button>
      </section>

      {isLoading && (
        <LoadingSpinner />
      )}

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
            type="three-day"
          />
        </>
      )}

      <HistoricalData
        title="3-Day Historical Data"
        fetchHistory={
          getThreeDayHistory
        }
        type="three-day"
      />
    </main>
  )
}

export default ThreeDay