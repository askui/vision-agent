"use client";

import { useChatStore } from "@/lib/store";
import { EmptyState } from "./empty-state";
import { ChatHeader } from "./chat-header";
import { MessageList } from "./message-list";
import { ChatInput } from "./chat-input";

export function ChatContainer() {
  const { selectedThread } = useChatStore();

  if (!selectedThread) {
    return <EmptyState />;
  }

  return (
    <div className="flex flex-col h-full w-full">
      <ChatHeader />
      <MessageList />
      <ChatInput />
    </div>
  );
}
