import { create } from "zustand";
import { persist } from "zustand/middleware";
import { ChatState } from "./types";

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      selectedAssistant: null,
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
        selectedAssistant: state.selectedAssistant,
        isCollapsed: state.isCollapsed,
      }),
    }
  )
);
