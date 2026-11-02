const ObjectionResponse = ({message}) => {
  const response = message.data;

  if (!response) {
    return <p>{message.isStreaming ? "Preparing objection response…" : "No structured response was returned."}</p>;
  }

  return (
    <section className="objection-response">
      <h2>{response.objection_name}</h2>
      <div>
        <h3>Suggested response</h3>
        <p>{response.script}</p>
      </div>
      <div>
        <h3>Why it works</h3>
        <p>{response.psychology}</p>
      </div>
    </section>
  );
}

export default ObjectionResponse;
