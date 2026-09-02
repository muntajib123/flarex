const dateFormatter = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
})

function ForecastTable({ title, records }) {
  /*
   * These fields are intentionally hidden from the forecast tables.
   *
   * issued_date:
   * Not needed in the user-facing forecast table.
   *
   * rationale_keywords:
   * Internal/model metadata. We do not expose it in the forecast UI.
   */
  const HIDDEN_COLUMNS = [
    'issued_date',
    'rationale_keywords',
  ]

  const columns = [
    ...new Set(
      records.flatMap((record) =>
        Object.keys(record),
      ),
    ),
  ].filter(
    (column) =>
      !HIDDEN_COLUMNS.includes(column),
  )

  return (
    <section className="forecast-table-section">
      <div className="table-heading">
        <h2>{title}</h2>

        <span>
          {records.length} records
        </span>
      </div>

      {records.length === 0 ? (
        <p className="empty-table-message">
          No records are available.
        </p>
      ) : (
        <div
          className="table-scroll"
          tabIndex="0"
        >
          <table>
            <thead>
              <tr>
                {columns.map((column) => (
                  <th
                    key={column}
                    scope="col"
                  >
                    {formatColumnName(column)}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {records.map(
                (record, index) => (
                  <tr
                    key={`${
                      record.forecast_date ??
                      'record'
                    }-${index}`}
                  >
                    {columns.map(
                      (column) => (
                        <td key={column}>
                          {formatValue(
                            column,
                            record[column],
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
      )}
    </section>
  )
}

function formatColumnName(column) {
  return column
    .replaceAll('_', ' ')
    .replaceAll('.', ' ')
}

function formatValue(column, value) {
  if (
    value === null ||
    value === undefined
  ) {
    return '—'
  }

  /*
   * Forecast dates are returned by the API as ISO strings such as:
   *   2026-09-02T00:00:00
   *
   * Extract the calendar date directly so JavaScript does not
   * apply the user's local timezone and shift the date backward.
   */
  if (
    column.endsWith('date') &&
    typeof value === 'string'
  ) {
    const match = value.match(
      /^(\d{4})-(\d{2})-(\d{2})/,
    )

    if (!match) {
      return value
    }

    const [, year, month, day] = match

    const date = new Date(
      Date.UTC(
        Number(year),
        Number(month) - 1,
        Number(day),
      ),
    )

    return Number.isNaN(date.getTime())
      ? value
      : dateFormatter.format(date)
  }

  if (
    typeof value === 'number' &&
    !Number.isInteger(value)
  ) {
    return value.toFixed(2)
  }

  return String(value)
}

export default ForecastTable
