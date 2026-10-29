import { useState, useEffect } from "react";
import ChatWindow from "./components/ChatWindow.jsx";
import StageIndicator from "./components/StageIndicator.jsx";
import {
  createSession,
  sendChat,
  finalizeIdea,
  finalizeFeasibility,
  finalizePlan,
  getDocument,
  exportDocx,
} from "./api.js";

const EMPTY_MESSAGES = { ideation: [], feasibility: [], planning: [], documentation: [] };

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [stage, setStage] = useState("ideation");
  const [viewingStage, setViewingStage] = useState("ideation");
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
      if (res.auto_message) {
        appendMessage(res.stage, { role: "assistant", content: res.auto_message });
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleFinalizeFeasibility() {
    setLoading(true);
    setError(null);
    try {
      const res = await finalizeFeasibility(sessionId);
      setStage(res.stage);
      setViewingStage(res.stage);
      appendMessage(res.stage, {
        role: "assistant",
        content: `**Feasibility approved — moving to Planning.**`,
      });
    } catch (e) {
      setError(e.message); // e.g. "not approved yet" — shown inline, stage doesn't change
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

  const placeholders = {
    ideation: "Tell the Ideation Agent what domain or rough idea you're interested in.",
    feasibility:
      "Discuss the verdict above — propose a twist or push back. You'll unlock Planning once you see [APPROVED].",
    planning:
      "Discuss timeline and tech stack. Paste your grading rubric here if you have one, so word counts can be allocated per section.",
    documentation: "Ask the Documentation Agent to revise any section of your report.",
  };

  return (
    <div className="app">
      <header>
        <h1>Multi-Agent Academic Project Mentor</h1>
        <p className="subtitle">Ideation → Feasibility → Planning → Documentation</p>
      </header>

      <StageIndicator currentStage={stage} viewingStage={viewingStage} onSelect={setViewingStage} />

      {error && <div className="error-banner">{error}</div>}

      {!isViewingActiveStage && (
        <div className="readonly-banner">
          Viewing a completed stage — read only. Switch back to <strong>{stage}</strong> to
          continue working.
        </div>
      )}

      <ChatWindow
        messages={currentMessages}
        onSend={handleSend}
        disabled={loading || !sessionId || !isViewingActiveStage}
        placeholder={placeholders[viewingStage]}
      />

      {isViewingActiveStage && (
        <div className="actions">
          {stage === "ideation" && (
            <button onClick={handleFinalizeIdea} disabled={loading || currentMessages.length === 0}>
              Finalize Idea → Check Feasibility
            </button>
          )}
          {stage === "feasibility" && (
            <button onClick={handleFinalizeFeasibility} disabled={loading}>
              Finalize Feasibility → Move to Planning
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
