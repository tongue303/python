import React from "react";
import { Download, CheckCircle } from "lucide-react";
import type { ExperimentConfig } from "./SetupView";

interface ResultViewProps {
  cfg: ExperimentConfig;
  phase1Threshold: number;
  phase2Results: { itdUs: number; finalThreshold: number }[];
}

export const ResultView: React.FC<ResultViewProps> = ({ cfg, phase1Threshold, phase2Results }) => {
  const handleDownload = () => {
    const header = "Subject_ID,Phase1_Threshold_dB,Masker_ITD_us,Test_ITD_us,Final_Threshold_dBFS\n";
    const rows = phase2Results.map(r => 
      `${cfg.subjectId},${phase1Threshold.toFixed(2)},${cfg.maskerItdUs},${r.itdUs},${r.finalThreshold.toFixed(2)}`
    ).join("\n");
    
    const csvContent = header + rows;
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `pulsation_threshold_${cfg.subjectId}_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="glass-panel fade-in" style={{ maxWidth: "800px", margin: "0 auto", width: "100%", textAlign: "center" }}>
      <div className="header-container" style={{ marginBottom: "2rem" }}>
        <CheckCircle size={48} color="var(--success)" style={{ marginBottom: "1rem" }} />
        <h2>Experiment Finished</h2>
        <p>Thank you for participating.</p>
      </div>

      <div style={{ textAlign: "left", background: "rgba(0,0,0,0.2)", padding: "1.5rem", borderRadius: "8px", marginBottom: "2rem" }}>
        <h3 style={{ borderBottom: "1px solid var(--panel-border)", paddingBottom: "0.5rem", marginBottom: "1rem" }}>Summary</h3>
        <p><strong>Subject ID:</strong> {cfg.subjectId}</p>
        <p><strong>Phase 1 Threshold:</strong> {phase1Threshold.toFixed(2)} dB FS</p>
        <p><strong>Test Freq:</strong> {cfg.testFreq} Hz</p>
        <p><strong>Modulation:</strong> {cfg.modType} ({cfg.modFreq} Hz)</p>
      </div>

      <div style={{ background: "rgba(0,0,0,0.2)", borderRadius: "8px", overflow: "hidden", marginBottom: "2rem" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead style={{ background: "rgba(255,255,255,0.05)" }}>
            <tr>
              <th style={{ padding: "1rem", textAlign: "left" }}>ITD (µs)</th>
              <th style={{ padding: "1rem", textAlign: "right" }}>Threshold (dB FS)</th>
            </tr>
          </thead>
          <tbody>
            {phase2Results.sort((a, b) => a.itdUs - b.itdUs).map(r => (
              <tr key={r.itdUs} style={{ borderTop: "1px solid var(--panel-border)" }}>
                <td style={{ padding: "1rem", textAlign: "left" }}>{r.itdUs}</td>
                <td style={{ padding: "1rem", textAlign: "right" }}>{r.finalThreshold.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div>
        <button className="btn btn-primary" onClick={handleDownload}>
          <Download size={18} /> Download CSV
        </button>
      </div>
    </div>
  );
};
