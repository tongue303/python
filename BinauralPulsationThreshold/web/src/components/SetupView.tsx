import React, { useState } from "react";
import { Settings, Play } from "lucide-react";
import * as config from "../config";

export interface ExperimentConfig {
  subjectId: string;
  itdListUs: number[];
  slReferenceDb: number | null;
  testFreq: number;
  modFreq: number;
  modType: "None" | "SAM" | "Transposed";
  maskerItdUs: number;
}

interface SetupViewProps {
  onStart: (cfg: ExperimentConfig) => void;
}

export const SetupView: React.FC<SetupViewProps> = ({ onStart }) => {
  const [subjectId, setSubjectId] = useState("P01");
  const [rawItds, setRawItds] = useState("0, 200, 400");
  const [rawSl, setRawSl] = useState("");
  const [testFreq, setTestFreq] = useState(config.TEST_FREQ.toString());
  const [modFreq, setModFreq] = useState(config.MOD_FREQ.toString());
  const [modType, setModType] = useState<"None" | "SAM" | "Transposed">(config.MOD_TYPE);
  const [maskerItd, setMaskerItd] = useState(config.MASKER_ITD_US.toString());
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // ITDのパース
    const itdTokens = rawItds.split(",").map(t => t.trim()).filter(t => t !== "");
    const itdListUs: number[] = [];
    for (const token of itdTokens) {
      const num = parseInt(token, 10);
      if (isNaN(num)) {
        setError(`Invalid ITD list: '${rawItds}'`);
        return;
      }
      itdListUs.push(num);
    }
    if (itdListUs.length === 0) {
      setError("Please enter a valid ITD list.");
      return;
    }

    // SLのパース
    let slReferenceDb: number | null = null;
    if (rawSl.trim() !== "") {
      slReferenceDb = parseFloat(rawSl);
      if (isNaN(slReferenceDb)) {
        setError("SL reference must be a number.");
        return;
      }
    }

    onStart({
      subjectId,
      itdListUs,
      slReferenceDb,
      testFreq: parseFloat(testFreq),
      modFreq: parseFloat(modFreq),
      modType,
      maskerItdUs: parseInt(maskerItd, 10),
    });
  };

  return (
    <div className="glass-panel fade-in" style={{ maxWidth: "600px", margin: "0 auto", width: "100%" }}>
      <div className="header-container" style={{ marginBottom: "1.5rem" }}>
        <Settings size={48} color="var(--accent)" style={{ marginBottom: "1rem" }} />
        <h2>Experiment Setup</h2>
        <p>Configure the parameters for the Pulsation Threshold measurement.</p>
      </div>

      {error && (
        <div style={{ padding: "1rem", backgroundColor: "rgba(239, 68, 68, 0.2)", color: "var(--danger)", borderRadius: "8px", marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Subject ID</label>
          <input className="form-input" value={subjectId} onChange={e => setSubjectId(e.target.value)} required />
        </div>

        <div className="form-group">
          <label className="form-label">ITD list (µs, comma-separated)</label>
          <input className="form-input" value={rawItds} onChange={e => setRawItds(e.target.value)} required />
        </div>

        <div className="form-group">
          <label className="form-label">SL reference (dB FS, blank = run Phase 1)</label>
          <input className="form-input" value={rawSl} onChange={e => setRawSl(e.target.value)} placeholder="e.g. -45.5" />
        </div>

        <div style={{ display: "flex", gap: "1rem" }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label">Test Frequency (Hz)</label>
            <input className="form-input" type="number" value={testFreq} onChange={e => setTestFreq(e.target.value)} required />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label">Modulation Freq (Hz)</label>
            <input className="form-input" type="number" value={modFreq} onChange={e => setModFreq(e.target.value)} required />
          </div>
        </div>

        <div style={{ display: "flex", gap: "1rem" }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label">Modulation Type</label>
            <select className="form-select" value={modType} onChange={e => setModType(e.target.value as any)}>
              <option value="None">None</option>
              <option value="SAM">SAM</option>
              <option value="Transposed">Transposed</option>
            </select>
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label className="form-label">Masker ITD (µs)</label>
            <input className="form-input" type="number" value={maskerItd} onChange={e => setMaskerItd(e.target.value)} required />
          </div>
        </div>

        <div style={{ textAlign: "right", marginTop: "2rem" }}>
          <button type="submit" className="btn btn-primary">
            <Play size={18} /> Proceed
          </button>
        </div>
      </form>
    </div>
  );
};
