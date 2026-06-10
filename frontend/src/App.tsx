import { useCallback, useEffect, useState } from "react";
import { TranslatorWebSocket } from "./websocket";
import { TranslationDisplay } from "./TranslationDisplay";
import type {
  PipelineStatus,
  ServerMessage,
  TranslationEntry,
  UiSettings,
} from "./types";

const STATUS_LABELS: Record<PipelineStatus, string> = {
  idle: "PYSÄYTETTY",
  listening: "KUUNTELEE",
  processing: "KÄSITTELEE",
  error: "VIRHE",
};

const DEFAULT_SETTINGS: UiSettings = {
  maxHistoryItems: 4,
  fontScale: 1,
  showFi: true,
  showEn: true,
  showUk: true,
};

function App() {
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState<PipelineStatus>("idle");
  const [statusMessage, setStatusMessage] = useState("Ready");
  const [error, setError] = useState<string | null>(null);
  const [partial, setPartial] = useState("");
  const [entries, setEntries] = useState<TranslationEntry[]>([]);
  const [lastLatency, setLastLatency] = useState<number | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [settings, setSettings] = useState<UiSettings>(DEFAULT_SETTINGS);
  const [showSettings, setShowSettings] = useState(false);
  const [logInfo, setLogInfo] = useState<string | null>(null);

  const handleMessage = useCallback((message: ServerMessage) => {
    switch (message.type) {
      case "status":
        setStatus(message.status);
        setStatusMessage(message.message);
        if (message.status === "listening") {
          setPartial("");
        }
        if (message.status !== "error") {
          setError(null);
        }
        break;
      case "partial":
        setPartial(message.fi_partial);
        break;
      case "translation":
        setPartial("");
        setLastLatency(message.latency_ms);
        setEntries((prev) => [
          ...prev,
          {
            timestamp: message.timestamp,
            fi: message.fi,
            en: message.en,
            uk: message.uk,
            latency_ms: message.latency_ms,
          },
        ]);
        break;
      case "error":
        setError(message.message);
        setStatus("error");
        break;
      case "cleared":
        setEntries([]);
        setPartial("");
        setLastLatency(null);
        setError(null);
        break;
      case "log_saved":
        setLogInfo(
          `Loki tallennettu: ${message.jsonl_path}${message.markdown_path ? ` | MD: ${message.markdown_path}` : ""}`
        );
        break;
      case "pong":
        break;
    }
  }, []);

  const [ws] = useState(
    () => new TranslatorWebSocket(handleMessage, setConnected)
  );

  useEffect(() => {
    ws.connect();
    return () => ws.disconnect();
  }, [ws]);

  useEffect(() => {
    const onFullscreenChange = () => {
      const active = !!document.fullscreenElement;
      setIsFullscreen(active);
      if (active) {
        setShowSettings(false);
      }
    };
    document.addEventListener("fullscreenchange", onFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", onFullscreenChange);
  }, []);

  const isActive = status === "listening" || status === "processing";

  const handleStart = () => {
    setStatus("processing");
    setStatusMessage("Käynnistetään — ladataan malleja...");
    setError(null);
    ws.send("start");
  };

  const toggleFullscreen = async () => {
    if (!document.fullscreenElement) {
      await document.documentElement.requestFullscreen();
    } else {
      await document.exitFullscreen();
    }
  };

  const fontStyle = {
    "--uk-size": `${Math.round(64 * settings.fontScale)}px`,
    "--en-size": `${Math.round(38 * settings.fontScale)}px`,
    "--fi-size": `${Math.round(28 * settings.fontScale)}px`,
  } as React.CSSProperties;

  return (
    <div className={`app ${isFullscreen ? "fullscreen" : ""}`} style={fontStyle}>
      <header className="toolbar">
        <span className={`status-badge ${status}`}>
          {STATUS_LABELS[status]}
        </span>
        <span className="latency latency-slot">
          {lastLatency !== null ? `Latenssi: ${lastLatency} ms` : "\u00A0"}
        </span>
        <button
          className="primary"
          onClick={handleStart}
          disabled={!connected || isActive}
        >
          Käynnistä
        </button>
        <button
          className="danger"
          onClick={() => ws.send("stop")}
          disabled={!connected || !isActive}
        >
          STOP
        </button>
        <button onClick={() => ws.send("clear")} disabled={!connected}>
          Tyhjennä näkymä
        </button>
        <button onClick={toggleFullscreen}>Fullscreen</button>
        <button onClick={() => ws.send("save_log")} disabled={!connected || entries.length === 0}>
          Tallenna loki
        </button>
        <button onClick={() => setShowSettings((v) => !v)}>
          Asetukset
        </button>
        <span className={`connection ${connected ? "connected" : ""}`}>
          {connected ? "Yhdistetty" : "Ei yhteyttä"}
        </span>
      </header>

      <div className="notice-area">
        {error && <div className="error-banner">{error}</div>}
        {statusMessage && status !== "idle" && !error && (
          <div className="status-message">{statusMessage}</div>
        )}
        {logInfo && <div className="latency">{logInfo}</div>}
        {partial && status === "processing" && (
          <div className="partial">Käsitellään...</div>
        )}
      </div>

      <main className="display">
        <TranslationDisplay
          entries={entries}
          settings={settings}
          presentationMode={isFullscreen}
        />
      </main>

      {showSettings && (
        <aside className="settings-panel">
          <label>
            Fonttikoko
            <input
              type="range"
              min="0.7"
              max="1.5"
              step="0.05"
              value={settings.fontScale}
              onChange={(e) =>
                setSettings((s) => ({ ...s, fontScale: parseFloat(e.target.value) }))
              }
            />
            {Math.round(settings.fontScale * 100)}%
          </label>
          <label>
            <input
              type="checkbox"
              checked={settings.showUk}
              onChange={(e) =>
                setSettings((s) => ({ ...s, showUk: e.target.checked }))
              }
            />
            Näytä UKR
          </label>
          <label>
            <input
              type="checkbox"
              checked={settings.showEn}
              onChange={(e) =>
                setSettings((s) => ({ ...s, showEn: e.target.checked }))
              }
            />
            Näytä EN
          </label>
          <label>
            <input
              type="checkbox"
              checked={settings.showFi}
              onChange={(e) =>
                setSettings((s) => ({ ...s, showFi: e.target.checked }))
              }
            />
            Näytä FI
          </label>
        </aside>
      )}

    </div>
  );
}

export default App;
