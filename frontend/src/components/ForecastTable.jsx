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

  if (
    column.endsWith('date') &&
    typeof value === 'string'
  ) {
    const date = new Date(value)

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