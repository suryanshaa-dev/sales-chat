import ReactMarkdown from "react-markdown";
import ObjectionResponse from "./ObjectionResponse";
const MessageResponse = ({message}) => {
  return (
    <div className="message-content">
      {message.error ? (
        <p role="alert">{message.error}</p>
      ) : message.query_type === "objection" ? (
        <ObjectionResponse message={message} />
      ) : (
        <ReactMarkdown>{message.content}</ReactMarkdown>
      )}
    </div>
  );
}
export default MessageResponse;
