import axios from 'axios'

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 35_000,
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      throw new Error('Forecast request timed out. Please try again shortly.')
    }

    const detail = error.response?.data?.detail
    throw new Error(detail || 'Unable to load forecast data from the backend.')
  },
)

export async function getThreeDayCurrent() {
  const response = await api.get('/api/3day/current')
  return response.data
}

export async function refreshThreeDayCurrent() {
  const response = await api.post('/api/3day/current/refresh')
  return response.data
}

export async function getTwentySevenDayCurrent() {
  const response = await api.get('/api/27day/current')
  return response.data
}

export async function refreshTwentySevenDayCurrent() {
  const response = await api.post('/api/27day/current/refresh')
  return response.data
}

export async function getThreeDayHistory(skip = 0, limit = 20) {
  const response = await api.get('/api/history/3day', {
    params: {
      skip,
      limit,
    },
  })

  return response.data
}

export async function getTwentySevenDayHistory(skip = 0, limit = 20) {
  const response = await api.get('/api/history/27day', {
    params: {
      skip,
      limit,
    },
  })

  return response.data
}

export default api