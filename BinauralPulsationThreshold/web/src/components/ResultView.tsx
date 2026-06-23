import React, { useRef } from "react";
import { Download, CheckCircle, Image as ImageIcon } from "lucide-react";
import type { ExperimentConfig } from "./SetupView";
import type { Phase2ResultData } from "../App";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface ResultViewProps {
  cfg: ExperimentConfig;
  phase1Threshold: number;
  phase2Results: Phase2ResultData[];
}

export const ResultView: React.FC<ResultViewProps> = ({ cfg, phase1Threshold, phase2Results }) => {
  const chartRefs = useRef<{ [key: number]: ChartJS | null }>({});

  const handleDownloadCSV = () => {
    // Long Format CSV
    const header = "subject_id,sl_reference_db,masker_itd_us,test_itd_us,trial_no,level_db,response,is_reversal,reversal_count,step_size,threshold_db\n";
    
    let rows = "";
    phase2Results.forEach(r => {
      r.history.forEach(h => {
        rows += `${cfg.subjectId},${phase1Threshold.toFixed(2)},${cfg.maskerItdUs},${r.itdUs},${h.trialGlobal},${h.levelDb.toFixed(2)},${h.response},${h.isReversal},${h.reversalCount},${h.stepSize},${r.finalThreshold.toFixed(2)}\n`;
      });
    });
    
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

  const handleDownloadImage = (itdUs: number) => {
    const chart = chartRefs.current[itdUs];
    if (chart) {
      const url = chart.toBase64Image();
      const link = document.createElement("a");
      link.download = `staircase_ITD${itdUs}_${cfg.subjectId}.png`;
      link.href = url;
      link.click();
    }
  };

  const renderChart = (result: Phase2ResultData) => {
    const labels = result.history.map(h => h.trialGlobal.toString());
    const dataPoints = result.history.map(h => h.levelDb);
    
    // Background colors for points based on response
    const pointBgColors = result.history.map(h => 
      h.response === "continuous" ? "#3b82f6" : "#ef4444" // blue for continuous, red for interrupted
    );
    // Point styles based on reversal
    const pointStyles = result.history.map(h => h.isReversal ? "rectRot" : "circle");
    const pointRadii = result.history.map(h => h.isReversal ? 8 : 5);

    const data = {
      labels,
      datasets: [
        {
          label: 'Target Level (dB FS)',
          data: dataPoints,
          borderColor: 'rgba(255, 255, 255, 0.5)',
          backgroundColor: pointBgColors,
          pointBackgroundColor: pointBgColors,
          pointStyle: pointStyles,
          pointRadius: pointRadii,
          pointHoverRadius: 10,
          borderWidth: 2,
          stepped: true as const, // Render as a step chart
        }
      ]
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: `Staircase ITD: ${result.itdUs} µs`,
          color: 'rgba(255, 255, 255, 0.8)'
        },
        tooltip: {
          callbacks: {
            label: function(context: any) {
              const hist = result.history[context.dataIndex];
              return `Level: ${hist.levelDb.toFixed(1)} dB (${hist.response})${hist.isReversal ? ' [Reversal]' : ''}`;
            }
          }
        }
      },
      scales: {
        y: {
          title: { display: true, text: 'Level (dB FS)', color: 'rgba(255, 255, 255, 0.6)' },
          grid: { color: 'rgba(255, 255, 255, 0.1)' },
          ticks: { color: 'rgba(255, 255, 255, 0.6)' }
        },
        x: {
          title: { display: true, text: 'Trial Number', color: 'rgba(255, 255, 255, 0.6)' },
          grid: { color: 'rgba(255, 255, 255, 0.1)' },
          ticks: { color: 'rgba(255, 255, 255, 0.6)' }
        }
      }
    };

    return (
      <div key={result.itdUs} style={{ background: "rgba(0,0,0,0.3)", borderRadius: "8px", padding: "1rem", marginBottom: "2rem", position: "relative" }}>
        <div style={{ height: "300px" }}>
          <Line 
            ref={(ref: any) => chartRefs.current[result.itdUs] = ref} 
            data={data} 
            options={options} 
          />
        </div>
        <div style={{ textAlign: "right", marginTop: "1rem" }}>
          <button className="btn btn-secondary" onClick={() => handleDownloadImage(result.itdUs)} style={{ fontSize: "0.8rem", padding: "0.5rem 1rem" }}>
            <ImageIcon size={14} style={{ marginRight: "0.5rem", verticalAlign: "middle" }} />
            Save Plot PNG
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="glass-panel fade-in" style={{ maxWidth: "800px", margin: "0 auto", width: "100%" }}>
      <div className="header-container" style={{ marginBottom: "2rem", textAlign: "center" }}>
        <CheckCircle size={48} color="var(--success)" style={{ marginBottom: "1rem" }} />
        <h2>Experiment Finished</h2>
        <p>Thank you for participating.</p>
      </div>

      <div style={{ background: "rgba(0,0,0,0.2)", padding: "1.5rem", borderRadius: "8px", marginBottom: "2rem" }}>
        <h3 style={{ borderBottom: "1px solid var(--panel-border)", paddingBottom: "0.5rem", marginBottom: "1rem" }}>Summary</h3>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "2rem" }}>
          <div>
            <p><strong>Subject ID:</strong> {cfg.subjectId}</p>
            <p><strong>Phase 1 Threshold:</strong> {phase1Threshold.toFixed(2)} dB FS</p>
          </div>
          <div>
            <p><strong>Test Freq:</strong> {cfg.testFreq} Hz</p>
            <p><strong>Modulation:</strong> {cfg.modType} ({cfg.modFreq} Hz)</p>
          </div>
        </div>
      </div>

      <div style={{ background: "rgba(0,0,0,0.2)", borderRadius: "8px", overflow: "hidden", marginBottom: "2rem" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead style={{ background: "rgba(255,255,255,0.05)" }}>
            <tr>
              <th style={{ padding: "1rem", textAlign: "left" }}>ITD (µs)</th>
              <th style={{ padding: "1rem", textAlign: "right" }}>Final Threshold (dB FS)</th>
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

      <div style={{ marginBottom: "2rem", textAlign: "center" }}>
        <button className="btn btn-primary" onClick={handleDownloadCSV}>
          <Download size={18} /> Download Detailed Data (CSV)
        </button>
      </div>

      <h3 style={{ borderBottom: "1px solid var(--panel-border)", paddingBottom: "0.5rem", marginBottom: "1rem" }}>Staircase Plots</h3>
      <div style={{ marginBottom: "2rem", fontSize: "0.9rem", color: "var(--text-muted)" }}>
        <span style={{ display: "inline-block", marginRight: "1rem" }}><span style={{ color: "#3b82f6" }}>●</span> Continuous (UP)</span>
        <span style={{ display: "inline-block", marginRight: "1rem" }}><span style={{ color: "#ef4444" }}>●</span> Interrupted (DOWN)</span>
        <span style={{ display: "inline-block" }}>◆ Reversal Point</span>
      </div>

      {phase2Results.sort((a, b) => a.itdUs - b.itdUs).map(renderChart)}
    </div>
  );
};
