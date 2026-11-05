import ReactMarkdown from "react-markdown";
import ObjectionResponse from "./ObjectionResponse";
import LeadScoreCard from "./LeadScoreCard";

const MessageResponse = ({ message }) => {
  return (
    <div
      className={`message-content${
        message.query_type === "objection"
          ? " message-content--objection"
          : ""
      }`}
    >
      {message.error ? (
        <p role="alert">{message.error}</p>
      ) : message.query_type === "objection" ? (
        <ObjectionResponse message={message} />
      ) : message.query_type === "lead_qualification" ? (
        <LeadScoreCard message={message} />
      ) : (
        <ReactMarkdown>{message.content}</ReactMarkdown>
      )}
    </div>
  );
};

export default MessageResponse;