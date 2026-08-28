import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const THREE_DAY_FIELDS = [
  {
    key: 'max_Kp',
    label: 'Max Kp',
  },
  {
    key: 'G_scale',
    label: 'G Scale',
  },
  {
    key: 'S1_prob',
    label: 'S1 Probability',
    percentage: true,
  },
  {
    key: 'R1_R2_prob',
    label: 'R1-R2 Probability',
    percentage: true,
  },
  {
    key: 'R3_prob',
    label: 'R3 Probability',
    percentage: true,
  },
]

const TWENTY_SEVEN_DAY_FIELDS = [
  {
    key: 'radio_flux_10.7cm',
    label: 'Radio Flux 10.7 cm',
  },
  {
    key: 'planetary_A_index',
    label: 'Planetary A Index',
  },
  {
    key: 'largest_Kp_index',
    label: 'Largest Kp Index',
  },
]

function ForecastGraphs({
  current = [],
  predictions = [],
  type = 'three-day',
}) {
  const fields =
    type === 'twenty-seven-day'
      ? TWENTY_SEVEN_DAY_FIELDS
      : THREE_DAY_FIELDS

  return (
    <section className="forecast-graphs">
      <div className="graphs-intro">
        <div>
          <span>ACTIVITY ANALYSIS</span>
          <h2>Forecast Signals</h2>
        </div>

        <div className="graph-legend">
          <span className="legend-item">
            <i className="legend-dot current-dot" />
            Current
          </span>

          <span className="legend-item">
            <i className="legend-dot prediction-dot" />
            AI Prediction
          </span>
        </div>
      </div>

      <GraphGroup
        title="Current Forecast"
        label="CURRENT DATA"
        records={current}
        fields={fields}
        variant="current"
      />

      <GraphGroup
        title="FlareX AI Predictions"
        label="PREDICTED DATA"
        records={predictions}
        fields={fields}
        variant="predicted"
      />
    </section>
  )
}

function GraphGroup({
  title,
  label,
  records,
  fields,
  variant,
}) {
  if (!records || records.length === 0) {
    return null
  }

  return (
    <section
      className={`graph-group graph-group-${variant}`}
    >
      <div className="graph-group-heading">
        <div>
          <span className="graph-group-label">
            {label}
          </span>

          <h3>{title}</h3>
        </div>

        <div
          className={`graph-status graph-status-${variant}`}
        >
          <span />
          {variant === 'current'
            ? 'Observed signal'
            : 'Model projection'}
        </div>
      </div>

      <div className="graphs-grid">
        {fields.map((field) => (
          <FieldGraph
            key={field.key}
            field={field}
            records={records}
            variant={variant}
          />
        ))}
      </div>
    </section>
  )
}

function FieldGraph({
  field,
  records,
  variant,
}) {
  const chartData = records
    .map((record) => ({
      date: formatDate(
        record.forecast_date,
      ),
      value: toNumber(
        record[field.key],
      ),
    }))
    .filter(
      (record) =>
        record.value !== null,
    )

  if (chartData.length === 0) {
    return null
  }

  return (
    <article
      className={`graph-card graph-card-${variant}`}
    >
      <div className="graph-card-header">
        <div>
          <span className="graph-card-kicker">
            {variant === 'current'
              ? 'CURRENT'
              : 'AI MODEL'}
          </span>

          <h4>{field.label}</h4>
        </div>

        <div className="graph-mini-signal">
          <span />
          <span />
          <span />
        </div>
      </div>

      <div className="graph-container">
        <ResponsiveContainer
          width="100%"
          height={280}
        >
          <LineChart
            data={chartData}
            margin={{
              top: 10,
              right: 20,
              left: 0,
              bottom: 10,
            }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--chart-grid)"
            />

            <XAxis
              dataKey="date"
              tick={{
                fontSize: 12,
                fill: 'var(--chart-text)',
              }}
              axisLine={{
                stroke: 'var(--chart-grid)',
              }}
              tickLine={false}
              minTickGap={20}
            />

            <YAxis
              tick={{
                fontSize: 12,
                fill: 'var(--chart-text)',
              }}
              axisLine={false}
              tickLine={false}
              domain={
                field.percentage
                  ? [0, 1]
                  : ['auto', 'auto']
              }
              tickFormatter={(value) =>
                field.percentage
                  ? `${(
                      value * 100
                    ).toFixed(0)}%`
                  : formatNumber(value)
              }
            />

            <Tooltip
              contentStyle={{
                background:
                  'var(--tooltip-bg)',
                border:
                  '1px solid var(--border-strong)',
                borderRadius: '10px',
                color: 'var(--text-heading)',
              }}
              formatter={(value) =>
                field.percentage
                  ? `${(
                      value * 100
                    ).toFixed(1)}%`
                  : formatNumber(value)
              }
              labelFormatter={(label) =>
                `Forecast date: ${label}`
              }
            />

            <Line
              type="monotone"
              dataKey="value"
              name={field.label}
              stroke={
                variant === 'current'
                  ? 'var(--current-line)'
                  : 'var(--prediction-line)'
              }
              strokeWidth={3}
              dot={{
                r: 3,
                fill:
                  variant === 'current'
                    ? 'var(--current-line)'
                    : 'var(--prediction-line)',
              }}
              activeDot={{
                r: 6,
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </article>
  )
}

function toNumber(value) {
  if (
    value === null ||
    value === undefined ||
    value === ''
  ) {
    return null
  }

  const number = Number(value)

  return Number.isFinite(number)
    ? number
    : null
}

function formatNumber(value) {
  if (
    value === null ||
    value === undefined
  ) {
    return '—'
  }

  const number = Number(value)

  if (!Number.isFinite(number)) {
    return '—'
  }

  if (Number.isInteger(number)) {
    return String(number)
  }

  return number.toFixed(2)
}

function formatDate(value) {
  if (!value) {
    return 'Unknown'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return 'Unknown'
  }

  return new Intl.DateTimeFormat(
    'en-GB',
    {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      timeZone: 'UTC',
    },
  ).format(date)
}

export default ForecastGraphs