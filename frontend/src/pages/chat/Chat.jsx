
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import "./chat.css";
import Sidebar from "./Sidebar";
import Composer from "./Composer";

import MessageResponse from "./MessageResponse";
import { API_BASE_URL } from "../../api";
function Chat() {
  const navigate = useNavigate();
  const [chats, setChats] = useState([]);
  const [activeChat, setActiveChat] = useState(null);
  const [messages, setMessages] = useState({});
  const [input, setInput] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [messageProcessing, setMessageProcessing] = useState(false);
  const [selectedModel, setSelectedModel] = useState("gpt-5.4-nano");
  const [user, setUser] = useState(null);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  const currentMessages = messages[activeChat] || [];
  const activeChatRecord = chats.find((chat) => chat.id === activeChat);
  const isEmptyNewChat = activeChatRecord?.title === "New chat" && currentMessages.length === 0;

  useEffect(() => {
    fetch(`${API_BASE_URL}/auth/me`, { credentials: "include" })
      .then((response) => {
        if (response.status === 401) {
          navigate("/login", { replace: true });
          return null;
        }
        if (!response.ok) throw new Error("Could not load profile");
        return response.json();
      })
      .then((profile) => { if (profile) setUser(profile); })
      .catch(() => {});
  }, [navigate]);

  useEffect(() => {
    fetch(`${API_BASE_URL}/auth/chats`, { credentials: "include" })
      .then((response) => {
        if (response.status === 401) {
          navigate("/login", { replace: true });
          return [];
        }
        if (!response.ok) throw new Error("Could not load chats");
        return response.json();
      })
      .then((savedChats) => {
        setChats(savedChats);
        if (savedChats.length) setActiveChat(savedChats[0].id);
        else {
          const id = crypto.randomUUID();
          setChats([{ id, title: "New chat" }]);
          setActiveChat(id);
        }
      })
      .catch(() => {
        const id = crypto.randomUUID();
        setChats([{ id, title: "New chat" }]);
        setActiveChat(id);
      });
  }, [navigate]);

  useEffect(() => {
    if (!activeChat) return;
    fetch(`${API_BASE_URL}/auth/chats/${activeChat}/messages`, { credentials: "include" })
      .then((response) => {
        if (response.status === 401) {
          navigate("/login", { replace: true });
          return [];
        }
        if (!response.ok) throw new Error("Could not load messages");
        return response.json();
      })
      .then((savedMessages) => setMessages((previous) => ({ ...previous, [activeChat]: savedMessages })))
      .catch(() => {});
  }, [activeChat, navigate]);

  function newChat() {
    if (isEmptyNewChat) return;
    const id = crypto.randomUUID();
    setChats((prev) => [{ id, title: "New chat" }, ...prev]);
    setActiveChat(id);
    setInput("");
  }

  async function logout() {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch {
      // Leave the page even if the network is unavailable.
    } finally {
      navigate("/login", { replace: true });
    }
  }

  async function sendMessage(e) {
    e.preventDefault();
    const text = input.trim();

    if (!text || !activeChat) return;
    setMessageProcessing(true);
 

    
   

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
        `${API_BASE_URL}/auth/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({
            user_query: text,
            selected_model: selectedModel,
            thread_id: activeChat,
          }),
        }
      );
      
      if (!response.ok) {
        if (response.status === 401) {
          navigate("/login", { replace: true });
          return;
        }
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
       
       {sidebarOpen && <Sidebar chats={chats} activeChat={activeChat} setActiveChat={setActiveChat} newChat={newChat} setSidebarOpen={setSidebarOpen} canCreateChat={!isEmptyNewChat} />}

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

          <div className="profile-menu-wrap">
            <button
              className="profile-button"
              title="Your profile"
              aria-label="Open profile menu"
              aria-expanded={profileMenuOpen}
              onClick={() => setProfileMenuOpen((open) => !open)}
            >
              {(user?.first_name || user?.email || "U").charAt(0).toUpperCase()}
            </button>
            {profileMenuOpen && (
              <div className="profile-menu">
                <div className="profile-name">{user?.first_name || "Account"}</div>
                {user?.email && <div className="profile-email">{user.email}</div>}
                <button className="logout-button" onClick={logout}>Log out</button>
              </div>
            )}
          </div>
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
