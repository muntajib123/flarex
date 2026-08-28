import { useEffect, useState } from 'react'
import LoadingSpinner from './LoadingSpinner'

const PAGE_SIZE = 20

const THREE_DAY_COLUMNS = [
  ['forecast_date', 'Forecast Date'],
  ['max_Kp', 'Max Kp'],
  ['G_scale', 'G Scale'],
  ['S1_prob', 'S1 Probability'],
  ['R1_R2_prob', 'R1-R2 Probability'],
  ['R3_prob', 'R3 Probability'],
]

const TWENTY_SEVEN_DAY_COLUMNS = [
  ['forecast_date', 'Forecast Date'],
  ['radio_flux_10.7cm', 'Radio Flux 10.7 cm'],
  ['planetary_A_index', 'Planetary A Index'],
  ['largest_Kp_index', 'Largest Kp Index'],
]

function HistoricalData({
  title,
  fetchHistory,
  type,
}) {
  const [records, setRecords] = useState([])
  const [skip, setSkip] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isActive = true

    async function loadHistory() {
      setIsLoading(true)
      setError('')

      try {
        const data = await fetchHistory(
          skip,
          PAGE_SIZE,
        )

        if (!isActive) {
          return
        }

        setRecords(
          Array.isArray(data) ? data : [],
        )
      } catch (requestError) {
        if (!isActive) {
          return
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : 'Unable to load historical data.',
        )
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    loadHistory()

    return () => {
      isActive = false
    }
  }, [fetchHistory, skip])

  const columns =
    type === 'three-day'
      ? THREE_DAY_COLUMNS
      : TWENTY_SEVEN_DAY_COLUMNS

  const canGoPrevious = skip > 0
  const canGoNext =
    records.length === PAGE_SIZE

  function handlePrevious() {
    setSkip((currentSkip) =>
      Math.max(
        0,
        currentSkip - PAGE_SIZE,
      ),
    )
  }

  function handleNext() {
    if (canGoNext) {
      setSkip(
        (currentSkip) =>
          currentSkip + PAGE_SIZE,
      )
    }
  }

  return (
    <section className="historical-data">
      <h2>{title}</h2>

      {isLoading && <LoadingSpinner />}

      {error && (
        <p className="error-message">
          {error}
        </p>
      )}

      {!isLoading &&
        !error &&
        records.length === 0 && (
          <p>
            No historical records are available.
          </p>
        )}

      {!isLoading &&
        !error &&
        records.length > 0 && (
          <>
            <div className="forecast-tables">
              <div
                className="table-wrapper"
                tabIndex="0"
              >
                <table>
                  <thead>
                    <tr>
                      {columns.map(
                        ([key, label]) => (
                          <th
                            key={key}
                            scope="col"
                          >
                            {label}
                          </th>
                        ),
                      )}
                    </tr>
                  </thead>

                  <tbody>
                    {records.map(
                      (record, index) => (
                        <tr
                          key={`${record.forecast_date ?? 'record'}-${index}`}
                        >
                          {columns.map(
                            ([key]) => (
                              <td key={key}>
                                {formatValue(
                                  record[key],
                                  key,
                                )}
                              </td>
                            ),
                          )}
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="historical-pagination">
              <button
                type="button"
                onClick={handlePrevious}
                disabled={
                  !canGoPrevious ||
                  isLoading
                }
              >
                Previous
              </button>

              <span>
                Records {skip + 1}–
                {skip + records.length}
              </span>

              <button
                type="button"
                onClick={handleNext}
                disabled={
                  !canGoNext ||
                  isLoading
                }
              >
                Next
              </button>
            </div>
          </>
        )}
    </section>
  )
}

function formatValue(value, key) {
  if (
    value === null ||
    value === undefined
  ) {
    return '—'
  }

  if (key === 'forecast_date') {
    const date = new Date(value)

    if (!Number.isNaN(date.getTime())) {
      return new Intl.DateTimeFormat(
        'en-GB',
        {
          dateStyle: 'medium',
          timeZone: 'UTC',
        },
      ).format(date)
    }
  }

  if (typeof value === 'number') {
    return Number.isInteger(value)
      ? value
      : value.toFixed(2)
  }

  return String(value)
}

export default HistoricalData