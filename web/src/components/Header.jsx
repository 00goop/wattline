const fmt = (n) => (n == null ? '—' : n.toLocaleString('en-US'))

export default function Header({ stats, mock, exposure, onHome }) {
  // Live count at the scrubbed hour once the series is loaded; the static
  // /api/stats number is the pre-load fallback.
  const npusCritical = exposure
    ? exposure.npus.filter((n) => n.tier === 'critical').length
    : stats?.npus_critical
  return (
    <header className="header">
      <div className="brand">
        <button className="brand-home" onClick={onHome} aria-label="Back to Wattline overview"><h1>
          WATT<span className="line">LINE</span>
        </h1></button>
        <span className="tagline">Atlanta · Outage Exposure</span>
        {mock && <span className="mock-chip">mock data</span>}
      </div>
      <div className="stats">
        <div className="stat">
          <div className="num">{fmt(stats?.georgia_total)}</div>
          <div className="label">electricity-dependent in GA</div>
        </div>
        <div className="stat">
          <div className="num">{fmt(stats?.metro_atlanta_total)}</div>
          <div className="label">metro Atlanta</div>
        </div>
        <div className="stat">
          <div className="num critical">{fmt(npusCritical)}</div>
          <div className="label">NPUs critical</div>
        </div>
      </div>
    </header>
  )
}
