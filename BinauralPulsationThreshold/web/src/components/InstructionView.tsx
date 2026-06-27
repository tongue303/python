import React, { useEffect } from "react";
import { Info } from "lucide-react";
import * as config from "../config";

interface InstructionViewProps {
  onNext: () => void;
}

export const InstructionView: React.FC<InstructionViewProps> = ({ onNext }) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === "Space") {
        e.preventDefault();
        onNext();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onNext]);

  return (
    <div className="glass-panel fade-in" style={{ maxWidth: "700px", margin: "0 auto", width: "100%" }}>
      <div className="header-container">
        <Info size={48} color="var(--accent)" style={{ marginBottom: "1rem" }} />
        <h2>Instructions</h2>
      </div>

      <div style={{ background: "rgba(0,0,0,0.2)", padding: "1.5rem", borderRadius: "8px", whiteSpace: "pre-wrap", fontSize: "1.1rem" }}>
        {config.INSTRUCTION_TEXT}
      </div>

      <div style={{ textAlign: "center", marginTop: "2rem", display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem" }}>
        <button 
          className="btn btn-primary" 
          onClick={onNext}
          style={{ fontSize: "1.2rem", padding: "1rem 2rem", width: "100%", maxWidth: "300px" }}
        >
          Start Experiment
        </button>
        <span style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
          or press <kbd className="kbd">Space</kbd>
        </span>
      </div>
    </div>
  );
};
