import { useEffect, useState } from 'react'

const POLL_INTERVAL_MS = 30 * 60 * 1000

function useForecastData(fetchCurrent, refreshCurrent) {
  const [current, setCurrent] = useState([])
  const [predictions, setPredictions] = useState([])
  const [metadata, setMetadata] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isActive = true

    async function loadForecastData() {
      setIsLoading(true)
      setError('')

      try {
        const forecast = await fetchCurrent()
        if (!isActive) return

        setCurrent(forecast.forecast ?? [])
        setPredictions(forecast.ai_predictions ?? [])
        setMetadata(forecast)
      } catch (requestError) {
        if (!isActive) return

        setError(
          requestError instanceof Error
            ? requestError.message
            : 'Unable to load forecast data.',
        )
      } finally {
        if (isActive) setIsLoading(false)
      }
    }

    loadForecastData()
    const intervalId = window.setInterval(loadForecastData, POLL_INTERVAL_MS)
    return () => {
      isActive = false
      window.clearInterval(intervalId)
    }
  }, [fetchCurrent])

  async function refresh() {
    setIsLoading(true)
    setError('')
    try {
      const forecast = await refreshCurrent()
      setCurrent(forecast.forecast ?? [])
      setPredictions(forecast.ai_predictions ?? [])
      setMetadata(forecast)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Unable to refresh forecast data.',
      )
    } finally {
      setIsLoading(false)
    }
  }

  return { current, predictions, metadata, isLoading, error, refresh }
}

export default useForecastData
