// API Types based on OpenAPI schema
export interface Assistant {
  id: string;
  created_at: number;
  name: string | null;
  description: string | null;
  object: "assistant";
  avatar: string | null;
}

export interface Thread {
  id: string;
  created_at: number;
  name: string | null;
  object: "thread";
}

export interface MessageContentText {
  type: "text";
  text: string;
}

export interface MessageContentImageSourceBase64 {
  type: "base64";
  data: string;
  media_type: "image/jpeg" | "image/png" | "image/gif" | "image/webp";
}

export interface MessageContentImageSourceUrl {
  type: "url";
  url: string;
}

export type MessageContentImageSource =
  | MessageContentImageSourceBase64
  | MessageContentImageSourceUrl;

export interface MessageContentImage {
  type: "image";
  source: MessageContentImageSource;
}

export interface MessageContentToolResult {
  type: "tool_result";
  tool_use_id: string;
  content: string | (MessageContentText | MessageContentImage)[];
  is_error: boolean;
}

export interface MessageContentToolUse {
  type: "tool_use";
  id: string;
  input: object;
  name: string;
}

export type MessageContent =
  | MessageContentText
  | MessageContentImage
  | MessageContentToolResult
  | MessageContentToolUse;

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string | MessageContent[];
  assistant_id: string | null;
  thread_id: string;
  created_at: number;
  object: "thread.message";
  run_id: string | null;
}

export interface Run {
  id: string;
  assistant_id: string;
  thread_id: string;
  status:
    | "queued"
    | "in_progress"
    | "completed"
    | "cancelling"
    | "cancelled"
    | "failed"
    | "expired";
  created_at: number;
  started_at: number | null;
  completed_at: number | null;
  cancelled_at: number | null;
  failed_at: number | null;
  expires_at: number;
  tried_cancelling_at: number | null;
  last_error: RunError | null;
  object: "thread.run";
}

export interface RunError {
  message: string;
  code: "server_error" | "rate_limit_exceeded" | "invalid_prompt";
}

export interface ListResponse<T> {
  object: "list";
  data: T[];
  first_id: string | null;
  last_id: string | null;
  has_more: boolean;
}

// UI State Types
export interface ChatState {
  selectedAssistant: Assistant | null;
  selectedThread: Thread | null;
  isCollapsed: boolean;
  currentRun: Run | null;
  messages: Message[];
  setSelectedAssistant: (assistant: Assistant | null) => void;
  setSelectedThread: (thread: Thread | null) => void;
  setIsCollapsed: (collapsed: boolean) => void;
  setCurrentRun: (run: Run | null) => void;
  appendMessage: (message: Message) => void;
  clearMessages: () => void;
}

export interface ThreadFilters {
  search?: string;
  order: "asc" | "desc";
  sortBy: "created_at" | "name";
}

interface RunEvent {
  type:
    | "thread.run.created"
    | "thread.run.queued"
    | "thread.run.in_progress"
    | "thread.run.completed"
    | "thread.run.cancelling"
    | "thread.run.cancelled"
    | "thread.run.failed"
    | "thread.run.expired";
  data: Run;
}

interface MessageEvent {
  type: "thread.message.created";
  data: Message;
}

interface ErrorEventDataError {
  message: string;
}

interface ErrorEventData {
  error: ErrorEventDataError;
}

interface ErrorEvent {
  type: "error";
  data: ErrorEventData;
}

interface DoneEvent {
  type: "done";
  data: "[DONE]";
}

export type Event = RunEvent | MessageEvent | ErrorEvent | DoneEvent;
