import { useEffect, useState } from 'react'
import './App.css'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import ThreeDay from './pages/ThreeDay'
import TwentySevenDay from './pages/TwentySevenDay'

const routes = {
  '/three-day': ThreeDay,
  '/twenty-seven-day': TwentySevenDay,
}

const THEME_STORAGE_KEY = 'flarex-theme'

function App() {
  const [pathname, setPathname] = useState(
    window.location.pathname,
  )

  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem(
      THEME_STORAGE_KEY,
    )

    return savedTheme === 'dark'
      ? 'dark'
      : 'light'
  })

  useEffect(() => {
    const handlePopState = () => {
      setPathname(window.location.pathname)
    }

    window.addEventListener(
      'popstate',
      handlePopState,
    )

    return () => {
      window.removeEventListener(
        'popstate',
        handlePopState,
      )
    }
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute(
      'data-theme',
      theme,
    )

    localStorage.setItem(
      THEME_STORAGE_KEY,
      theme,
    )
  }, [theme])

  const navigate = (path) => {
    window.history.pushState({}, '', path)
    setPathname(path)
  }

  const toggleTheme = () => {
    setTheme((currentTheme) =>
      currentTheme === 'light'
        ? 'dark'
        : 'light',
    )
  }

  const Page = routes[pathname] ?? Home

  return (
    <div className="app-shell">
      <Navbar onNavigate={navigate} />

      <div className="theme-controls">
        <button
          type="button"
          className="theme-toggle"
          onClick={toggleTheme}
          aria-label={`Switch to ${
            theme === 'light'
              ? 'dark'
              : 'light'
          } mode`}
          title={`Switch to ${
            theme === 'light'
              ? 'dark'
              : 'light'
          } mode`}
        >
          {theme === 'light' ? '🌙' : '☀️'}

          <span>
            {theme === 'light'
              ? 'Dark'
              : 'Light'}
          </span>
        </button>
      </div>

      <Page onNavigate={navigate} />
    </div>
  )
}

export default App