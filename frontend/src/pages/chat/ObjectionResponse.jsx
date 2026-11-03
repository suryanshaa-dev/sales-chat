const parseScript = (script = "") => {
  const turns = [];
  const marker = /\b(You|Prospect):\s*/g;
  const matches = [...script.matchAll(marker)];

  matches.forEach((match, index) => {
    const contentStart = match.index + match[0].length;
    const contentEnd = matches[index + 1]?.index ?? script.length;
    const text = script.slice(contentStart, contentEnd).trim();

    if (text) turns.push({ speaker: match[1], text });
  });

  return turns;
};

const getPsychologyPoints = (psychology) => {
  if (Array.isArray(psychology)) return psychology;
  if (typeof psychology !== "string") return [];

  return psychology
    .split(/(?<=[.!?])\s+(?=[A-Z“])/)
    .map((point) => point.trim())
    .filter(Boolean);
};

const ObjectionResponse = ({ message }) => {
  const response = message.data;

  const psychologyPoints = getPsychologyPoints(response?.psychology);

  if (!response) {
    return <p>{message.isStreaming ? "Preparing objection response…" : "No structured response was returned."}</p>;
  }

  return (
    <section className="objection-response">
      <header className="objection-heading">
        <span className="objection-eyebrow">OBJECTION:</span>
        <h2>{response.objection_name}</h2>
      </header>

      <div className="objection-section">
        <h3>Suggested response</h3>
        <div className="objection-dialogue">
          {parseScript(response.script).map((turn, index) => {
            const isYou = turn.speaker === "You";
            return (
              <div
                className={`dialogue-turn ${isYou ? "dialogue-turn--you" : "dialogue-turn--prospect"}`}
                key={`${turn.speaker}-${index}`}
              >
                <span className="dialogue-speaker">
                  <span className="dialogue-speaker-dot" />
                  {isYou ? "Suggested line" : "Prospect"}
                </span>
                <p>{turn.text}</p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="objection-psychology">
       
        <h3>Why it works</h3>
        <ul>
          {psychologyPoints.map((point, index) => (
            <li key={index}>{point}</li>
          ))}
        </ul>
      </div>
      <div className="source">
        <h4>Sources</h4>
        {message.sources?.length ? (
          <ul>
            {message.sources.map((source, index) => (
              <li key={`${source.source}-${source.page}-${index}`}>
                {source.source || "Unknown source"}
                {source.page != null ? ` (page ${source.page})` : ""}
              </li>
            ))}
          </ul>
        ) : (
          <p>No source documents were returned.</p>
        )}
      </div>
    </section>
  );
}

export default ObjectionResponse;
