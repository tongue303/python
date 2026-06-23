import { useState } from 'react';
import { SetupView } from './components/SetupView';
import type { ExperimentConfig } from './components/SetupView';
import { InstructionView } from './components/InstructionView';
import { Phase1View } from './components/Phase1View';
import { Phase2View } from './components/Phase2View';
import { ResultView } from './components/ResultView';
import type { TrackHistoryRecord } from './AdaptiveTrack';
import * as config from './config';

type AppState = "SETUP" | "INSTRUCTION" | "PHASE1" | "PHASE2" | "RESULT";

export type Phase2ResultData = { itdUs: number; finalThreshold: number; history: TrackHistoryRecord[] };

function App() {
  const [appState, setAppState] = useState<AppState>("SETUP");
  const [cfg, setCfg] = useState<ExperimentConfig | null>(null);
  const [phase1Threshold, setPhase1Threshold] = useState<number | null>(null);
  const [phase2Results, setPhase2Results] = useState<Phase2ResultData[]>([]);

  const handleStartSetup = (c: ExperimentConfig) => {
    setCfg(c);
    setAppState("INSTRUCTION");
  };

  const handleInstructionNext = () => {
    if (!cfg) return;
    if (cfg.slReferenceDb !== null) {
      setPhase1Threshold(cfg.slReferenceDb);
      setAppState("PHASE2");
    } else {
      setAppState("PHASE1");
    }
  };

  const handlePhase1Complete = (threshold: number) => {
    setPhase1Threshold(threshold);
    setAppState("PHASE2");
  };

  const handlePhase2Complete = (results: Phase2ResultData[]) => {
    setPhase2Results(results);
    setAppState("RESULT");
  };

  const maskerSpectrumLevelDb = (phase1Threshold ?? 0) + config.TARGET_SL;

  return (
    <div className="container">
      {appState === "SETUP" && <SetupView onStart={handleStartSetup} />}
      {appState === "INSTRUCTION" && <InstructionView onNext={handleInstructionNext} />}
      {appState === "PHASE1" && <Phase1View onComplete={handlePhase1Complete} />}
      {appState === "PHASE2" && cfg && (
        <Phase2View 
          cfg={cfg} 
          maskerSpectrumLevelDb={maskerSpectrumLevelDb} 
          onComplete={handlePhase2Complete} 
        />
      )}
      {appState === "RESULT" && cfg && phase1Threshold !== null && (
        <ResultView 
          cfg={cfg} 
          phase1Threshold={phase1Threshold} 
          phase2Results={phase2Results} 
        />
      )}
    </div>
  );
}

export default App;
