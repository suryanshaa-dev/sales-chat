
import { act, useState } from "react";
import "./chat.css";
import Sidebar from "./Sidebar";
import Composer from "./Composer";
import ReactMarkdown from "react-markdown";
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
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/auth/chat",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({ user_query:text }),
        }
      );

     

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
 
      const unique_id =crypto.randomUUID();

  setMessages((prev) => ({
  ...prev,
  [activeChat]: [
    ...prev[activeChat],
    {
      role: "assistant",
      content: "",
      id: unique_id

    }
  ]
}));
   while (true) {
  const { value, done } = await reader.read();

  if (done) break;

  const chunk = decoder.decode(value, { stream: true });

 setMessages((prev) => ({
  ...prev,

  [activeChat]: prev[activeChat].map((msg) =>
    msg.id === unique_id
      ? { ...msg, content: msg.content + chunk }
      : msg
  )
}));
 

   
}

   
 
 
 
      // Navigate to your dashboard here.
    } catch (err) {
      console.log(err)
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
            <button className="model-selector">
              SalesGPT <span className="model-badge">AI</span>
              
            </button>
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
                    setInput("Help me build an AI-powered application")
                  }
                >
                  <span>⌘</span>
                  Build an application
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
               <div className="message-content">
                   <ReactMarkdown >
  {message.content}
</ReactMarkdown>
               </div>
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
