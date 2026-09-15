const STAGES = [
  { key: "ideation", label: "1. Ideation" },
  { key: "feasibility", label: "2. Feasibility" },
  { key: "planning", label: "3. Planning" },
  { key: "documentation", label: "4. Documentation" },
];

export default function StageIndicator({ currentStage, viewingStage, onSelect }) {
  const currentIndex = STAGES.findIndex((s) => s.key === currentStage);

  return (
    <div className="stage-bar">
      {STAGES.map((s, i) => {
        const unlocked = i <= currentIndex;
        const isViewing = s.key === viewingStage;
        return (
          <button
            key={s.key}
            className={
              "stage-pill " +
              (isViewing ? "active" : i < currentIndex ? "done" : "") +
              (unlocked ? "" : " locked")
            }
            disabled={!unlocked}
            onClick={() => unlocked && onSelect(s.key)}
          >
            {s.label}
          </button>
        );
      })}
    </div>
  );
}
