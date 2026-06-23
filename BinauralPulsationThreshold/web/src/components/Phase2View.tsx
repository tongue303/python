import React, { useState, useEffect, useRef } from "react";
import { Headphones } from "lucide-react";
import * as config from "../config";
import { AdaptiveTrack1Up1Down } from "../AdaptiveTrack";
import { buildAlternatingStimulus } from "../audio";
import type { ExperimentConfig } from "./SetupView";

interface Phase2ViewProps {
  cfg: ExperimentConfig;
  maskerSpectrumLevelDb: number;
  onComplete: (results: { itdUs: number; finalThreshold: number }[]) => void;
}

export const Phase2View: React.FC<Phase2ViewProps> = ({ cfg, maskerSpectrumLevelDb, onComplete }) => {
  const [itdOrder, setItdOrder] = useState<number[]>([]);
  const [currentConditionIndex, setCurrentConditionIndex] = useState(0);
  const [track, setTrack] = useState<AdaptiveTrack1Up1Down | null>(null);
  const [status, setStatus] = useState<"idle" | "playing" | "waiting_response">("idle");
  const [results, setResults] = useState<{ itdUs: number; finalThreshold: number }[]>([]);
  
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
    } catch (e) {
      console.error(e);
      // Fallback
      setStatus("waiting_response");
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (status === "waiting_response" && track) {
        const key = e.key.toLowerCase();
        if (key === config.KEY_CONTINUOUS || key === config.KEY_INTERRUPTED) {
          e.preventDefault();
          const isContinuous = key === config.KEY_CONTINUOUS;
          track.recordResponse(isContinuous, track.trialNo);

          if (track.isFinished()) {
            // 現在の条件が終了
            const currentItdUs = itdOrder[currentConditionIndex];
            const newResults = [...results, { itdUs: currentItdUs, finalThreshold: track.getThreshold() }];
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
        {status === "idle" && (
          <span className="fade-in" style={{ color: "var(--text-muted)", fontSize: "1.2rem" }}>
            ITD = {itdOrder[currentConditionIndex]} µs <br/>
            Press <kbd className="kbd">Space</kbd> to start.
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
        <div className="key-instruction fade-in">
          <div className="key-badge">
            <kbd className="kbd">{config.KEY_CONTINUOUS.toUpperCase()}</kbd>
            <span>Continuous</span>
          </div>
          <div className="key-badge">
            <kbd className="kbd">{config.KEY_INTERRUPTED.toUpperCase()}</kbd>
            <span>Interrupted</span>
          </div>
        </div>
      )}
      
    </div>
  );
};
