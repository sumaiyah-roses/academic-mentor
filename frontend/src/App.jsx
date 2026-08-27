import { useState, useEffect } from "react";
import ChatWindow from "./components/ChatWindow.jsx";
import StageIndicator from "./components/StageIndicator.jsx";
import {
  createSession,
  sendChat,
  finalizeIdea,
  finalizePlan,
  getDocument,
  exportDocx,
} from "./api.js";

const EMPTY_MESSAGES = { ideation: [], planning: [], documentation: [] };

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [stage, setStage] = useState("ideation");       // furthest unlocked stage
  const [viewingStage, setViewingStage] = useState("ideation"); // which tab is on screen
  const [messagesByStage, setMessagesByStage] = useState(EMPTY_MESSAGES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [docContent, setDocContent] = useState("");

  useEffect(() => {
    createSession()
      .then((res) => setSessionId(res.session_id))
      .catch((e) => setError(e.message));
  }, []);

  function appendMessage(stageKey, message) {
    setMessagesByStage((prev) => ({
      ...prev,
      [stageKey]: [...prev[stageKey], message],
    }));
  }

  async function handleSend(text) {
    if (!sessionId) return;
    appendMessage(stage, { role: "user", content: text });
    setLoading(true);
    setError(null);
    try {
      const res = await sendChat(sessionId, text);
      appendMessage(stage, { role: "assistant", content: res.reply });
      if (stage === "documentation") setDocContent(res.reply);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleFinalizeIdea() {
    setLoading(true);
    setError(null);
    try {
      const res = await finalizeIdea(sessionId);
      setStage(res.stage);
      setViewingStage(res.stage);
      appendMessage(res.stage, {
        role: "assistant",
        content: `**Idea locked in:**\n\n${res.brief}`,
      });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleFinalizePlan() {
    setLoading(true);
    setError(null);
    try {
      const res = await finalizePlan(sessionId);
      setStage(res.stage);
      setViewingStage(res.stage);
      appendMessage(res.stage, {
        role: "assistant",
        content: `**Plan locked in:**\n\n${res.brief}`,
      });
      // Documentation draft was already generated server-side by finalize-plan.
      const docRes = await getDocument(sessionId);
      setDocContent(docRes.content);
      appendMessage(res.stage, { role: "assistant", content: docRes.content });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const isViewingActiveStage = viewingStage === stage;
  const currentMessages = messagesByStage[viewingStage];

  return (
    <div className="app">
      <header>
        <h1>Multi-Agent Academic Project Mentor</h1>
        <p className="subtitle">Ideation → Planning → Documentation</p>
      </header>

      <StageIndicator
        currentStage={stage}
        viewingStage={viewingStage}
        onSelect={setViewingStage}
      />

      {error && <div className="error-banner">{error}</div>}

      {!isViewingActiveStage && (
        <div className="readonly-banner">
          Viewing a completed stage — read only. Switch back to{" "}
          <strong>{stage}</strong> to continue working.
        </div>
      )}

      <ChatWindow
        messages={currentMessages}
        onSend={handleSend}
        disabled={loading || !sessionId || !isViewingActiveStage}
        placeholder={
          viewingStage === "ideation"
            ? "Tell the Ideation Agent what domain or rough idea you're interested in."
            : viewingStage === "planning"
            ? "Discuss timeline, tech stack, and team roles with the Planning Agent."
            : "Ask the Documentation Agent to revise any section of your report."
        }
      />

      {isViewingActiveStage && (
        <div className="actions">
          {stage === "ideation" && (
            <button
              onClick={handleFinalizeIdea}
              disabled={loading || currentMessages.length === 0}
            >
              Finalize Idea → Move to Planning
            </button>
          )}
          {stage === "planning" && (
            <button
              onClick={handleFinalizePlan}
              disabled={loading || currentMessages.length === 0}
            >
              Finalize Plan → Generate Documentation
            </button>
          )}
          {stage === "documentation" && (
            <button onClick={() => exportDocx(sessionId)} disabled={!docContent}>
              Export as .docx
            </button>
          )}
        </div>
      )}

      {loading && <div className="loading-hint">Agent is thinking…</div>}
    </div>
  );
}
