 const Sidebar = ({newChat, chats, activeChat}) => {
    return ( <aside className="sidebar">
          <div className="sidebar-top">
            <button
              className="icon-button"
              onClick={() => setSidebarOpen(false)}
              aria-label="Close sidebar"
            >
              ◧
            </button>

            <button
              className="icon-button"
              onClick={newChat}
              aria-label="New chat"
            >
              ✎
            </button>
          </div>

          <button className="new-chat" onClick={newChat}>
            <span>＋</span> New chat
          </button>

          <div className="history-label">Your conversations</div>

          <div className="chat-list">
            {chats.map((chat) => (
              <button
                key={chat.id}
                className={`chat-item ${
                  activeChat === chat.id ? "active" : ""
                }`}
                onClick={() => setActiveChat(chat.id)}
              >
                <span className="chat-symbol">◌</span>
                <span className="chat-title">{chat.title}</span>
              </button>
            ))}
          </div>

          <div className="sidebar-bottom">
            <div className="upgrade-icon">✦</div>
            <div>
              <div className="upgrade-title">Explore AI</div>
              <div className="upgrade-subtitle">
                Your ideas, amplified.
              </div>
            </div>
          </div>
        </aside> );
 }
  
 export default Sidebar;