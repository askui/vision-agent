import { Assistant, Thread, Message, Run, ListResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class APIClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    if (options.method === "DELETE") {
      return undefined as T;
    }

    return response.json();
  }

  // Assistants
  async listAssistants(params?: {
    limit?: number;
    after?: string;
    before?: string;
    order?: "asc" | "desc";
  }): Promise<ListResponse<Assistant>> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.after) searchParams.set("after", params.after);
    if (params?.before) searchParams.set("before", params.before);
    if (params?.order) searchParams.set("order", params.order);

    return this.request(`/v1/assistants?${searchParams}`);
  }

  async retrieveAssistant(assistantId: string): Promise<Assistant> {
    return this.request(`/v1/assistants/${assistantId}`);
  }

  // Threads
  async listThreads(params?: {
    limit?: number;
    after?: string;
    before?: string;
    order?: "asc" | "desc";
  }): Promise<ListResponse<Thread>> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.after) searchParams.set("after", params.after);
    if (params?.before) searchParams.set("before", params.before);
    if (params?.order) searchParams.set("order", params.order);

    return this.request(`/v1/threads?${searchParams}`);
  }

  async createThread(data: {
    name?: string;
    messages?: any[];
  }): Promise<Thread> {
    return this.request("/v1/threads", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async retrieveThread(threadId: string): Promise<Thread> {
    return this.request(`/v1/threads/${threadId}`);
  }

  async modifyThread(
    threadId: string,
    data: { name?: string }
  ): Promise<Thread> {
    return this.request(`/v1/threads/${threadId}`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async deleteThread(threadId: string): Promise<void> {
    await this.request(`/v1/threads/${threadId}`, {
      method: "DELETE",
    });
  }

  // Messages
  async listMessages(
    threadId: string,
    params?: {
      limit?: number;
      after?: string;
      before?: string;
      order?: "asc" | "desc";
    }
  ): Promise<ListResponse<Message>> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set("limit", params.limit.toString());
    if (params?.after) searchParams.set("after", params.after);
    if (params?.before) searchParams.set("before", params.before);
    if (params?.order) searchParams.set("order", params.order);

    return this.request(`/v1/threads/${threadId}/messages?${searchParams}`);
  }

  async createMessage(
    threadId: string,
    data: {
      role: "user" | "assistant";
      content: string | any[];
    }
  ): Promise<Message> {
    return this.request(`/v1/threads/${threadId}/messages`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async deleteMessage(threadId: string, messageId: string): Promise<void> {
    await this.request(`/v1/threads/${threadId}/messages/${messageId}`, {
      method: "DELETE",
    });
  }

  // Runs
  async createRun(
    threadId: string,
    data: {
      assistant_id: string;
      stream?: boolean;
    }
  ): Promise<EventSource> {
    const url = `${API_BASE_URL}/v1/threads/${threadId}/runs`;
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Failed to create run: ${response.status}`);
    }

    if (data.stream) {
      return new EventSource(url, {
        withCredentials: false,
      });
    }

    return response.json();
  }

  async cancelRun(threadId: string, runId: string): Promise<Run> {
    return this.request(`/v1/threads/${threadId}/runs/${runId}/cancel`, {
      method: "POST",
    });
  }

  async retrieveRun(threadId: string, runId: string): Promise<Run> {
    return this.request(`/v1/threads/${threadId}/runs/${runId}`);
  }
}

export const apiClient = new APIClient();
