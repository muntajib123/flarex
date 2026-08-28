function Navbar({ onNavigate }) {
  const handleNavigation = (event, path) => {
    event.preventDefault()
    onNavigate(path)
  }

  return (
    <header className="navbar">
      <nav aria-label="Main navigation">
        <a href="/" onClick={(event) => handleNavigation(event, '/')}>
          FlareX
        </a>
        <div className="navbar-links">
          <a
            href="/three-day"
            onClick={(event) => handleNavigation(event, '/three-day')}
          >
            3-Day
          </a>
          <a
            href="/twenty-seven-day"
            onClick={(event) => handleNavigation(event, '/twenty-seven-day')}
          >
            27-Day
          </a>
        </div>
      </nav>
    </header>
  )
}

export default Navbar
