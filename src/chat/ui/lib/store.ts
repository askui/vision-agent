import { create } from "zustand";
import { persist } from "zustand/middleware";
import { ChatState } from "./types";
import { DEFAULT_ASSISTANT } from "./constants";

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      selectedAssistant: DEFAULT_ASSISTANT,
      selectedThread: null,
      isCollapsed: false,
      currentRun: null,
      messages: [],
      setSelectedAssistant: (assistant) =>
        set({ selectedAssistant: assistant }),
      setSelectedThread: (thread) =>
        set({ selectedThread: thread, messages: [] }),
      setIsCollapsed: (collapsed) => set({ isCollapsed: collapsed }),
      setCurrentRun: (run) => set({ currentRun: run }),
      appendMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),
      clearMessages: () => set({ messages: [] }),
    }),
    {
      name: "chat-store",
      partialize: (state) => ({
        selectedAssistant: state.selectedAssistant ?? DEFAULT_ASSISTANT,
        isCollapsed: state.isCollapsed ?? false,
      }),
    }
  )
);
