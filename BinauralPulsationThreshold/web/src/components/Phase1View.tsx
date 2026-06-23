import React, { useState, useEffect, useRef } from "react";
import { Activity, Play } from "lucide-react";
import * as config from "../config";
import { Phase1ThresholdTrack } from "../AdaptiveTrack";
import { generateTestSignal } from "../audio";

interface Phase1ViewProps {
  onComplete: (thresholdDb: number) => void;
}

export const Phase1View: React.FC<Phase1ViewProps> = ({ onComplete }) => {
  const [track] = useState(() => new Phase1ThresholdTrack());
  const [status, setStatus] = useState<"idle" | "playing" | "waiting_response">("idle");
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
    buffer.copyToChannel(stereoData[0], 0);
    buffer.copyToChannel(stereoData[1], 1);

    const source = audioCtxRef.current.createBufferSource();
    source.buffer = buffer;
    source.connect(audioCtxRef.current.destination);
    
    source.onended = () => {
      setStatus("waiting_response");
    };
    source.start();
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (status === "waiting_response") {
        const key = e.key.toLowerCase();
        if (key === config.KEY_PHASE1_YES || key === config.KEY_PHASE1_NO) {
          e.preventDefault();
          const responded = key === config.KEY_PHASE1_YES;
          track.recordResponse(responded);

          if (track.isFinished()) {
            onComplete(track.getThreshold());
          } else {
            setStatus("idle");
            setTimeout(playStimulus, 300); // 0.3秒待って次の音
          }
        }
      } else if (status === "idle" && track.trialNo === 0) {
        // Spaceキーで最初の試行を開始
        if (e.code === "Space") {
          e.preventDefault();
          playStimulus();
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
        {status === "idle" && (
          <span className="fade-in" style={{ color: "var(--text-muted)", fontSize: "1.2rem" }}>
            Press <kbd className="kbd">Space</kbd> to start the first trial.
          </span>
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
        <div className="key-instruction fade-in">
          <div className="key-badge">
            <kbd className="kbd">{config.KEY_PHASE1_YES.toUpperCase()}</kbd>
            <span>Yes</span>
          </div>
          <div className="key-badge">
            <kbd className="kbd">{config.KEY_PHASE1_NO.toUpperCase()}</kbd>
            <span>No</span>
          </div>
        </div>
      )}
      
      <div style={{ marginTop: "3rem", fontSize: "0.9rem", color: "var(--text-muted)" }}>
        Current level: {track.getCurrentLevel().toFixed(1)} dB (Debug info)
      </div>
    </div>
  );
};
