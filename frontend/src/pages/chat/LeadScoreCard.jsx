const FACTORS = [
  { key: "need", label: "Need" },
  { key: "budget", label: "Budget" },
  { key: "authority", label: "Authority" },
  { key: "timeline", label: "Timeline" },
];

const valueClass = (value) => {
  const normalized = String(value || "").toLowerCase();
  if (normalized === "high") return "pq-strong";
  if (normalized === "moderate") return "pq-moderate";
  if (normalized === "low" || normalized === "unconfirmed") return "pq-unconfirmed";
  return "pq-unconfirmed";
};

const LeadScoreCard = ({ message }) => {
  const response = typeof message.data === "string"
    ? (() => {
        try {
          return JSON.parse(message.data);
        } catch {
          return null;
        }
      })()
    : message.data;

  if (!response || typeof response !== "object") {
    return <p>{message.isStreaming ? "Qualifying prospect…" : "No qualification data available."}</p>;
  }

  const score = Math.max(0, Math.min(100, Number(response.qualification_score) || 0));
  const missing = FACTORS.filter(({ key }) =>
    !response[key] || String(response[key]).toLowerCase() === "unconfirmed"
  );
  const status = missing.length === 0 ? "Qualified" : "Partially Qualified";
  const statusClass = missing.length === 0 ? "" : " pq-status-badge--partial";
  const summary = missing.length === 0
    ? `All qualification factors are confirmed. The prospect’s overall qualification score is ${score}/100.`
    : `More information is needed about ${missing.map(({ label }) => label.toLowerCase()).join(", ")}. The current qualification score is ${score}/100.`;

  return (
    <div className="pq-qualification-widget">
      <section className="pq-qualification-card">
        <div className="pq-card-header">
          <div>
            <p className="pq-eyebrow">PROSPECT QUALIFICATION</p>
            <h2 className="pq-card-title">Lead qualification</h2>
          </div>
          <span className={`pq-status-badge${statusClass}`}>{status}</span>
        </div>

        <div className="pq-score-section">
          <div className="pq-score-info">
            <div className="pq-score-value">{score}<span>/100</span></div>
            <div className="pq-score-label">Lead qualification score</div>
          </div>
          <div
            className="pq-score-circle"
            style={{ "--pq-score": `${score}%` }}
            role="img"
            aria-label={`${score} percent qualification score`}
          >
            <span className="pq-score-circle-value">{score}%</span>
          </div>
        </div>

        <div className="pq-divider" />

        <div className="pq-factors-section">
          <h3 className="pq-factors-title">Qualification factors</h3>
          <div className="pq-factor-table" role="table" aria-label="Qualification factors">
            <div className="pq-factor-table-header" role="row">
              <span role="columnheader">Factor</span>
              <span role="columnheader">Status</span>
              <span role="columnheader">Evidence</span>
            </div>
            {FACTORS.map(({ key, label }) => (
              <div className="pq-factor-table-row" role="row" key={key}>
                <span className="pq-factor-name" role="cell">{label}</span>
                <span className={`pq-factor-value ${valueClass(response[key])}`} role="cell">
                  {response[key] || "Unconfirmed"}
                </span>
                <span className="pq-factor-evidence" role="cell">
                  {response[`${key}_reasoning`] || "No evidence provided."}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {missing.length > 0 && (
        <section className="pq-detail-card">
          <h3 className="pq-detail-title">Missing information</h3>
          <ul className="pq-missing-list">
            {missing.map(({ label }) => <li key={label}>{label}</li>)}
          </ul>
        </section>
      )}

      <section className="pq-detail-card pq-summary-card">
        <h3 className="pq-detail-title">Qualification summary</h3>
        <p>{summary}</p>
      </section>
    </div>
  );
};

export default LeadScoreCard;
