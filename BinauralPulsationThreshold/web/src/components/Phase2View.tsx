import React, { useState, useEffect, useRef } from "react";
import { Headphones } from "lucide-react";
import * as config from "../config";
import { AdaptiveTrack1Up1Down } from "../AdaptiveTrack";
import { buildAlternatingStimulus } from "../audio";
import type { ExperimentConfig } from "./SetupView";
import type { Phase2ResultData } from "../App";

interface Phase2ViewProps {
  cfg: ExperimentConfig;
  maskerSpectrumLevelDb: number;
  onComplete: (results: Phase2ResultData[]) => void;
}

export const Phase2View: React.FC<Phase2ViewProps> = ({ cfg, maskerSpectrumLevelDb, onComplete }) => {
  const [itdOrder, setItdOrder] = useState<number[]>([]);
  const [currentConditionIndex, setCurrentConditionIndex] = useState(0);
  const [track, setTrack] = useState<AdaptiveTrack1Up1Down | null>(null);
  const [status, setStatus] = useState<"idle" | "playing" | "waiting_response" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [results, setResults] = useState<Phase2ResultData[]>([]);
  
  const audioCtxRef = useRef<AudioContext | null>(null);

  // 初回マウント時にITDリストをシャッフル
  useEffect(() => {
    const order = [...cfg.itdListUs];
    for (let i = order.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [order[i], order[j]] = [order[j], order[i]];
    }
    setItdOrder(order);
    setTrack(new AdaptiveTrack1Up1Down(maskerSpectrumLevelDb));
    
    audioCtxRef.current = new window.AudioContext();
    return () => {
      audioCtxRef.current?.close();
    };
  }, [cfg, maskerSpectrumLevelDb]);

  const playStimulus = async () => {
    if (!audioCtxRef.current || !track || track.isFinished()) return;
    setStatus("playing");
    
    if (audioCtxRef.current.state === "suspended") {
      await audioCtxRef.current.resume();
    }

    const itdUs = itdOrder[currentConditionIndex];
    const itdSec = itdUs * 1e-6;
    const maskerItdSec = cfg.maskerItdUs * 1e-6;
    const levelDb = track.getCurrentLevel();

    try {
      const audioBuffer = await buildAlternatingStimulus(
        maskerSpectrumLevelDb,
        levelDb,
        itdSec,
        cfg.testFreq,
        cfg.modFreq,
        cfg.modType,
        maskerItdSec
      );

      const source = audioCtxRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioCtxRef.current.destination);
      
      source.onended = () => {
        setStatus("waiting_response");
      };
      source.start();
    } catch (e: any) {
      console.error(e);
      setErrorMsg(e.message || "An unknown error occurred during audio generation.");
      setStatus("error");
    }
  };

  const handleResponse = (isContinuous: boolean) => {
    if (!track) return;
    track.recordResponse(isContinuous, track.trialNo);

    if (track.isFinished()) {
      // 現在の条件が終了
      const currentItdUs = itdOrder[currentConditionIndex];
      const newResults = [...results, { itdUs: currentItdUs, finalThreshold: track.getThreshold(), history: track.history }];
      setResults(newResults);

      if (currentConditionIndex + 1 < itdOrder.length) {
        // 次の条件へ
        setCurrentConditionIndex(idx => idx + 1);
        setTrack(new AdaptiveTrack1Up1Down(maskerSpectrumLevelDb));
        setStatus("idle");
      } else {
        // 全条件終了
        onComplete(newResults);
      }
    } else {
      setStatus("idle");
      setTimeout(playStimulus, 300);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (status === "waiting_response" && track) {
        const key = e.key.toLowerCase();
        if (key === config.KEY_CONTINUOUS || key === config.KEY_INTERRUPTED) {
          e.preventDefault();
          handleResponse(key === config.KEY_CONTINUOUS);
        }
      } else if (status === "idle" && track?.trialNo === 0) {
        if (e.code === "Space") {
          e.preventDefault();
          playStimulus();
        }
      }
    };
    
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [status, track, currentConditionIndex, itdOrder, results, onComplete]);

  if (itdOrder.length === 0 || !track) return null;

  return (
    <div className="glass-panel fade-in" style={{ maxWidth: "800px", margin: "0 auto", width: "100%", textAlign: "center" }}>
      <div className="header-container" style={{ marginBottom: "3rem" }}>
        <Headphones size={48} color="var(--accent)" style={{ marginBottom: "1rem" }} />
        <h2>Phase 2: Pulsation Threshold</h2>
        <p>Condition {currentConditionIndex + 1} of {itdOrder.length}</p>
      </div>

      <div className="test-prompt">
        {status === "error" && (
          <div className="fade-in" style={{ color: "var(--danger)", background: "rgba(239, 68, 68, 0.1)", padding: "1.5rem", borderRadius: "8px", textAlign: "left" }}>
            <h3 style={{ marginTop: 0 }}>Audio Clip Error</h3>
            <p style={{ whiteSpace: "pre-wrap", margin: 0, color: "var(--danger)" }}>{errorMsg}</p>
            <div style={{ marginTop: "1rem", textAlign: "center" }}>
              <button className="btn btn-primary" onClick={() => window.location.reload()}>
                Reload Setup
              </button>
            </div>
          </div>
        )}
        {status === "idle" && track?.trialNo === 0 && (
          <div className="fade-in" style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem" }}>
            <span style={{ color: "var(--text-muted)", fontSize: "1.2rem", marginBottom: "0.5rem" }}>ITD = {itdOrder[currentConditionIndex]} µs</span>
            <button className="btn btn-primary" onClick={playStimulus} style={{ fontSize: "1.2rem", padding: "1rem 2rem", width: "100%", maxWidth: "300px" }}>
              Start Trial
            </button>
            <span style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
              or press <kbd className="kbd">Space</kbd>
            </span>
          </div>
        )}
        {status === "idle" && track?.trialNo !== 0 && (
          <span className="fade-in" style={{ color: "var(--text-muted)", fontSize: "1.2rem" }}>
            ITD = {itdOrder[currentConditionIndex]} µs <br/>
            Preparing...
          </span>
        )}
        {status === "playing" && (
          <span className="fade-in" style={{ color: "var(--accent)" }}>
            Listening...
          </span>
        )}
        {status === "waiting_response" && (
          <span className="fade-in">Was the test tone continuous?</span>
        )}
      </div>

      {status === "waiting_response" && (
        <div className="fade-in" style={{ display: "flex", justifyContent: "center", gap: "1rem", marginTop: "2rem", flexWrap: "wrap" }}>
          <button 
            className="btn btn-secondary" 
            onClick={() => handleResponse(true)}
            style={{ fontSize: "1.2rem", padding: "1.5rem 2rem", flex: "1 1 200px", maxWidth: "300px", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}
          >
            <span>Continuous</span>
            <kbd className="kbd" style={{ fontSize: "0.8rem", background: "rgba(255,255,255,0.1)" }}>{config.KEY_CONTINUOUS.toUpperCase()}</kbd>
          </button>
          <button 
            className="btn btn-secondary" 
            onClick={() => handleResponse(false)}
            style={{ fontSize: "1.2rem", padding: "1.5rem 2rem", flex: "1 1 200px", maxWidth: "300px", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem" }}
          >
            <span>Interrupted</span>
            <kbd className="kbd" style={{ fontSize: "0.8rem", background: "rgba(255,255,255,0.1)" }}>{config.KEY_INTERRUPTED.toUpperCase()}</kbd>
          </button>
        </div>
      )}
      
    </div>
  );
};
