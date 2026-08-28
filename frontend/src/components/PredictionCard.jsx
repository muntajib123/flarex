function PredictionCard({ records, status }) {
  const firstDate = records[0]?.forecast_date
  const lastDate = records.at(-1)?.forecast_date

  return (
    <article className="data-card">
      <div className="data-card-header">
        <h2>Model predictions</h2>
        <span>{records.length} records</span>
      </div>
      {status?.status === 'unavailable' ? (
        <p>{status.message ?? 'AI predictions are unavailable because required model features are missing.'}</p>
      ) : records.length > 0 ? (
        <dl className="data-preview data-summary">
          <div>
            <dt>Prediction range</dt>
            <dd>{formatDateRange(firstDate, lastDate)}</dd>
          </div>
          <div>
            <dt>Available records</dt>
            <dd>{records.length}</dd>
          </div>
        </dl>
      ) : (
        <p>No prediction records are available.</p>
      )}
    </article>
  )
}

function formatDateRange(firstDate, lastDate) {
  if (!firstDate || !lastDate) return 'Unavailable'
  return firstDate === lastDate ? firstDate : `${firstDate} to ${lastDate}`
}

export default PredictionCard
