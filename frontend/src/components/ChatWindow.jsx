import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// Markdown links must open in a new tab. target="_blank" alone can get
// ignored in some setups, so force it explicitly: stop the default
// same-tab navigation and open the URL with window.open instead. Without
// this, clicking a paper/repo link navigates the whole React app away in
// the same tab, wiping all in-memory session state.
const markdownComponents = {
  a: ({ node, href, children, ...props }) => (
    <a
      {...props}
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => {
        e.preventDefault();
        window.open(href, "_blank", "noopener,noreferrer");
      }}
    >
      {children}
    </a>
  ),
};

export default function ChatWindow({ messages, onSend, disabled, placeholder }) {
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
  }

  return (
    <div className="chat-window">
      <div className="messages">
        {messages.length === 0 && <div className="empty-hint">{placeholder}</div>}
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            <div className="bubble-role">{m.role === "user" ? "You" : "Agent"}</div>
            <div className="bubble-text">
              <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                {m.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={disabled}
        />
        <button type="submit" disabled={disabled || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
