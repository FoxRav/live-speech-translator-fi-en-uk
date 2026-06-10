import type { ClientCommand, ServerMessage } from "./types";

const WS_URL = import.meta.env.DEV
  ? `ws://${window.location.hostname}:8000/ws`
  : `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws`;

export type MessageHandler = (message: ServerMessage) => void;
export type ConnectionHandler = (connected: boolean) => void;

export class TranslatorWebSocket {
  private socket: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private onMessage: MessageHandler;
  private onConnectionChange: ConnectionHandler;

  constructor(onMessage: MessageHandler, onConnectionChange: ConnectionHandler) {
    this.onMessage = onMessage;
    this.onConnectionChange = onConnectionChange;
  }

  connect(): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return;
    }

    this.socket = new WebSocket(WS_URL);

    this.socket.onopen = () => {
      this.onConnectionChange(true);
      if (this.reconnectTimer !== null) {
        window.clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };

    this.socket.onclose = () => {
      this.onConnectionChange(false);
      this.scheduleReconnect();
    };

    this.socket.onerror = () => {
      this.onConnectionChange(false);
    };

    this.socket.onmessage = (event: MessageEvent<string>) => {
      try {
        const data = JSON.parse(event.data) as ServerMessage;
        this.onMessage(data);
      } catch {
        this.onMessage({ type: "error", message: "Invalid server message" });
      }
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer !== null) {
      return;
    }
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 2000);
  }

  send(command: ClientCommand): void {
    if (this.socket?.readyState !== WebSocket.OPEN) {
      return;
    }
    this.socket.send(JSON.stringify({ command }));
  }

  disconnect(): void {
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.socket?.close();
    this.socket = null;
  }
}
