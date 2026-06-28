import React, { useState, useEffect, useRef } from "react";
import { Activity } from "lucide-react";
import * as config from "../config";
import { Phase1ThresholdTrack } from "../AdaptiveTrack";
import { generateTestSignal } from "../audio";

interface Phase1ViewProps {
  onComplete: (thresholdDb: number) => void;
}

export const Phase1View: React.FC<Phase1ViewProps> = ({ onComplete }) => {
  const [track] = useState(() => new Phase1ThresholdTrack());
  const [status, setStatus] = useState<"idle" | "playing" | "waiting_response" | "completed">("idle");
  const audioCtxRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    // コンポーネントマウント時にAudioContextを準備
    audioCtxRef.current = new window.AudioContext();
    return () => {
      audioCtxRef.current?.close();
    };
  }, []);

  const playStimulus = async () => {
    if (!audioCtxRef.current || track.isFinished()) return;
    setStatus("playing");
    
    // User interaction has occurred, safe to resume
    if (audioCtxRef.current.state === "suspended") {
      await audioCtxRef.current.resume();
    }

    const levelDb = track.getCurrentLevel();
    const stereoData = generateTestSignal(levelDb, 0, config.PHASE1_DURATION, config.PHASE1_FREQ);
    
    const buffer = audioCtxRef.current.createBuffer(2, stereoData[0].length, config.SAMPLE_RATE);
    buffer.copyToChannel(stereoData[0] as any, 0);
    buffer.copyToChannel(stereoData[1] as any, 1);

    const source = audioCtxRef.current.createBufferSource();
    source.buffer = buffer;
    source.connect(audioCtxRef.current.destination);
    
    source.onended = () => {
      setStatus("waiting_response");
    };
    source.start();
  };

  const handleResponse = (responded: boolean) => {
    track.recordResponse(responded);
    if (track.isFinished()) {
      setStatus("completed");
    } else {
      setStatus("idle");
      setTimeout(playStimulus, 300); // 0.3秒待って次の音
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (status === "waiting_response") {
        const key = e.key.toLowerCase();
        if (key === config.KEY_PHASE1_YES || key === config.KEY_PHASE1_NO) {
          e.preventDefault();
          handleResponse(key === config.KEY_PHASE1_YES);
        }
      } else if (status === "idle" && track.trialNo === 0) {
        // Spaceキーで最初の試行を開始
        if (e.code === "Space") {
          e.preventDefault();
          playStimulus();
        }
      } else if (status === "completed") {
        if (e.code === "Space") {
          e.preventDefault();
          onComplete(track.getThreshold());
        }
      }
    };
    
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [status, track, onComplete]);

  return (
    <div className="glass-panel fade-in" style={{ maxWidth: "800px", margin: "0 auto", width: "100%", textAlign: "center" }}>
      <div className="header-container" style={{ marginBottom: "3rem" }}>
        <Activity size={48} color="var(--accent)" style={{ marginBottom: "1rem" }} />
        <h2>Phase 1: 1kHz Threshold</h2>
      </div>

      <div className="test-prompt">
        {status === "idle" && track.trialNo === 0 && (
          <div className="fade-in" style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem" }}>
            <button className="btn btn-primary" onClick={playStimulus} style={{ fontSize: "1.2rem", padding: "1rem 2rem", width: "100%", maxWidth: "300px" }}>
              Start Experiment
            </button>
            <span style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
              or press <kbd className="kbd">Space</kbd>
            </span>
          </div>
        )}
        {status === "playing" && (
          <span className="fade-in" style={{ color: "var(--accent)" }}>
            Listening...
          </span>
        )}
        {status === "waiting_response" && (
          <span className="fade-in">Did you hear the tone?</span>
        )}
      </div>

      {status === "waiting_response" && (
        <div className="fade-in" style={{ display: "flex", justifyContent: "center", gap: "1rem", marginTop: "2rem", flexWrap: "wrap" }}>
          <button 
            className="btn btn-secondary" 
            onClick={() => handleResponse(true)}
            style={{ fontSize: "1.2rem", padding: "1.5rem 2rem", flex: "1 1 200px", maxWidth: "300px", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}
          >
            <span>Yes</span>
            <kbd className="kbd" style={{ fontSize: "0.8rem", background: "rgba(255,255,255,0.1)" }}>{config.KEY_PHASE1_YES.toUpperCase()}</kbd>
          </button>
          <button 
            className="btn btn-secondary" 
            onClick={() => handleResponse(false)}
            style={{ fontSize: "1.2rem", padding: "1.5rem 2rem", flex: "1 1 200px", maxWidth: "300px", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}
          >
            <span>No</span>
            <kbd className="kbd" style={{ fontSize: "0.8rem", background: "rgba(255,255,255,0.1)" }}>{config.KEY_PHASE1_NO.toUpperCase()}</kbd>
          </button>
        </div>
      )}
      {status === "completed" && (
        <div className="fade-in" style={{ textAlign: "center", marginTop: "2rem" }}>
          <h3 style={{ fontSize: "2rem", color: "var(--accent)", marginBottom: "0.5rem" }}>Phase 1 Complete</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "1.1rem" }}>Please record this value if necessary.</p>
          <div style={{ margin: "2rem auto", padding: "2rem", background: "rgba(255,255,255,0.05)", borderRadius: "12px", maxWidth: "400px" }}>
            <span style={{ fontSize: "1.2rem", color: "var(--text-muted)" }}>Your 1kHz Threshold</span>
            <br/>
            <strong style={{ fontSize: "3.5rem", color: "var(--text-light)", display: "block", marginTop: "0.5rem" }}>
              {track.getThreshold().toFixed(1)} <span style={{ fontSize: "1.5rem", color: "var(--text-muted)", fontWeight: "normal" }}>dB FS</span>
            </strong>
          </div>
          <button 
            className="btn btn-primary" 
            style={{ fontSize: "1.2rem", padding: "1rem 2rem", width: "100%", maxWidth: "300px" }}
            onClick={() => onComplete(track.getThreshold())}
          >
            Proceed to Phase 2
          </button>
          <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginTop: "1rem" }}>
            or press <kbd className="kbd">Space</kbd>
          </div>
        </div>
      )}
      
    </div>
  );
};
