export interface ChatRequestEntity {
  message: string;
  sessionId?: string;
  model?: "baseline" | "agent";
}
