export type PipelineStatus = "idle" | "listening" | "processing" | "error";

export interface TranslationEntry {
  timestamp: string;
  fi: string;
  en: string;
  uk: string;
  latency_ms: number;
}

export interface StatusMessage {
  type: "status";
  status: PipelineStatus;
  message: string;
}

export interface PartialMessage {
  type: "partial";
  fi_partial: string;
}

export interface TranslationMessage {
  type: "translation";
  timestamp: string;
  fi: string;
  en: string;
  uk: string;
  latency_ms: number;
}

export interface ErrorMessage {
  type: "error";
  message: string;
}

export interface ClearedMessage {
  type: "cleared";
}

export interface LogSavedMessage {
  type: "log_saved";
  jsonl_path: string;
  markdown_path: string;
}

export interface PongMessage {
  type: "pong";
}

export type ServerMessage =
  | StatusMessage
  | PartialMessage
  | TranslationMessage
  | ErrorMessage
  | ClearedMessage
  | LogSavedMessage
  | PongMessage;

export type ClientCommand = "start" | "stop" | "clear" | "ping" | "save_log";

export interface UiSettings {
  maxHistoryItems: number;
  fontScale: number;
  showFi: boolean;
  showEn: boolean;
  showUk: boolean;
}
