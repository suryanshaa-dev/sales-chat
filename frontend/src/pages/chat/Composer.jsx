const Composer = ({sendMessage, handleKeyDown, input, setInput, messageProcessing}) => {
    return ( <div className="composer-area">
          <form className="composer" onSubmit={sendMessage}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message ChatGPT..."
              rows={1}
              aria-label="Message"
            />

            <div className="composer-footer">
              <div className="composer-tools">
                <button
                  type="button"
                  className="tool-button"
                  title="Add attachment (demo)"
                  onClick={() =>
                    alert("Connect a file upload component here.")
                  }
                >
                  ＋
                </button>
                <button
                  type="button"
                  className="tool-button tool-label"
                  onClick={() =>
                    setInput((prev) => prev + "Please think carefully.")
                  }
                >
                  ✧ Think
                </button>
              </div>

              <div className="composer-actions">
                <button
                  type="button"
                  className="tool-button voice-button"
                  title="Voice (demo)"
                  onClick={() => alert("Voice input is not configured yet.")}
                >
                  ♩
                </button>
                {!messageProcessing ?   <button
                  type="submit"
                  className="send-button"
                  disabled={!input.trim()}
                  aria-label="Send message"
                >
                  ↑
                </button>
                
                : 
                      <button
      className="pause-button"
      
      aria-label="Stop generating"
    >
      <span></span>
      <span></span>
    </button>
                
                
                }
              
      
  
              </div>
            </div>
          </form>

     
        </div> );
}
 
export default Composer;