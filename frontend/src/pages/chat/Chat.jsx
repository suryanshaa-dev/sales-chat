
import { act, useState } from "react";
import "./chat.css";
import Sidebar from "./Sidebar";
import Composer from "./Composer";

import MessageResponse from "./MessageResponse";
const initialChats = [
  { id: 1, title: "Building my AI assistant" },
  { id: 2, title: "Python learning roadmap" },
  { id: 3, title: "Marketing strategy" },
];

function Chat() {
  const [chats, setChats] = useState(initialChats);
  const [activeChat, setActiveChat] = useState(1);
  const [messages, setMessages] = useState({});
  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [messageProcessing, setMessageProcessing] = useState(false);
  const [selectedModel, setSelectedModel] = useState("gpt-5.4-nano");

  const currentMessages = messages[activeChat] || [];

  function newChat() {
    const id = Date.now();
    setChats((prev) => [{ id, title: "New chat" }, ...prev]);
    setActiveChat(id);
    setInput("");
  }

  async function sendMessage(e) {
    e.preventDefault();
    const text = input.trim();

    setMessageProcessing(true);
 

    
   

    if (!text) return;

    const currentChat = chats.find((chat) => chat.id === activeChat);

    setChats((prev) =>
      prev.map((chat) =>
        chat.id === activeChat && chat.title === "New chat"
          ? { ...chat, title: text.slice(0, 30) }
          : chat
      )
    );

    setMessages((prev) => ({
      ...prev,
      [activeChat]: [
        ...(prev[activeChat] || []),
        { role: "user", content: text, id: crypto.randomUUID() },
      ],
    }));

    setInput("");
    let assistantMessageId = null;
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/auth/chat",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({ user_query:text, selected_model:selectedModel }),
        }
      );
      console.log("HERE MY REP:")
      console.log(response)
      if (!response.ok) {
        throw new Error(`Chat request failed: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      const unique_id = crypto.randomUUID();
      assistantMessageId = unique_id;

      setMessages((prev) => ({
        ...prev,
        [activeChat]: [
          ...(prev[activeChat] || []),
          {
            role: "assistant",
            content: "",
            data: null,
            query_type: null,
            isStreaming: true,
            id: unique_id,
          },
        ],
      }));

      const handleSseFrame = (frame) => {
        let eventName = "message";
        const dataLines = [];

        for (const line of frame.split(/\r?\n/)) {
          if (line.startsWith("event:")) eventName = line.slice(6).trim();
          if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
        }

        if (dataLines.length === 0) return;
        const payload = JSON.parse(dataLines.join("\n"));

        setMessages((prev) => ({
          ...prev,
          [activeChat]: (prev[activeChat] || []).map((msg) => {
            if (msg.id !== unique_id) return msg;

            if (eventName === "metadata") {
              return { ...msg, query_type: payload.query_type };
            }
            if (eventName === "delta") {
              return { ...msg, content: msg.content + payload.content };
            }
            if (eventName === "complete") {
              return { ...msg, data: payload.response };
            }
            if (eventName === "sources") {
              return { ...msg, sources: payload.documents || [] };
            }
            if (eventName === "error") {
              return { ...msg, error: payload.message, isStreaming: false };
            }
            if (eventName === "done") {
              return { ...msg, isStreaming: false };
            }
            return msg;
          }),
        }));
      };

      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

        const frames = buffer.split(/\r?\n\r?\n/);
        buffer = frames.pop() || "";
        for (const frame of frames) handleSseFrame(frame);

        if (done) {
          if (buffer.trim()) handleSseFrame(buffer);
          break;
        }
      }
      // Navigate to your dashboard here.
    } catch (err) {
      console.log(err);
      if (assistantMessageId) {
        setMessages((prev) => ({
          ...prev,
          [activeChat]: (prev[activeChat] || []).map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, error: err.message, isStreaming: false }
              : msg
          ),
        }));
      }
    } finally {
     setMessageProcessing(false)
    }


  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(e);
    }
  }

  return (
    <div className="app">
       
       <Sidebar chats={chats} activeChat={activeChat} newChat={newChat} />

      <main className="main">
        <header className="topbar">
          <div className="topbar-left">
            {!sidebarOpen && (
              <button
                className="icon-button"
                onClick={() => setSidebarOpen(true)}
                aria-label="Open sidebar"
              >
                ☰
              </button>
            )}
            <label className="model-picker">
              <span className="model-picker-label">Model</span>
              <select
                className="model-selector"
                value={selectedModel}
                onChange={(event) => setSelectedModel(event.target.value)}
                aria-label="Select AI model"
              >
                <option value="gpt-5.4-nano">gpt-5.4-nano</option>
                <option value="gpt-5.4">gpt-5.4</option>
              </select>
            </label>
          </div>

          <button className="profile-button" title="Your profile">
            S
          </button>
        </header>

        <section className="conversation">
          {currentMessages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-mark">✳</div>
              <h1>What can I help with?</h1>
              <p>
                Think it through. Build something. Make it happen.
              </p>

              <div className="suggestions">
                <button
                  onClick={() =>
                    setInput("Prospect said let me think about it")
                  }
                >
                  <span>⌘</span>
                  Prospect said let me think about it
                </button>
                <button
                  onClick={() =>
                    setInput("Explain a complex topic simply")
                  }
                >
                  <span>◉</span>
                  Learn something new
                </button>
                <button
                  onClick={() =>
                    setInput("Help me brainstorm business ideas")
                  }
                >
                  <span>✧</span>
                  Brainstorm ideas
                </button>
                <button
                  onClick={() =>
                    setInput("Help me debug my code")
                  }
                >
                  <span>{"</>"}</span>
                  Write or debug code
                </button>
              </div>
            </div>
          ) : (
            <div className="messages">
              {currentMessages.map((message, index) => (
                <div
                  key={index}
                  className={`message ${
                    message.role === "assistant" ? "assistant-message" : ""
                  } ${
                    message.role === "user" ? "user-message" : ""
                  }`}
                >
                  {message.role === "assistant" && (
                    <div className="assistant-avatar">✳</div>
                  )}
             

                    <MessageResponse message={message}></MessageResponse>
        
                </div>
              ))}
            </div>
          )}
        </section>

        <Composer messageProcessing={messageProcessing} sendMessage={sendMessage} 
        handleKeyDown={handleKeyDown} 
        input={input} 
        setInput={setInput} 
        />

        
      </main>
    </div>
  );
}

export default Chat;
