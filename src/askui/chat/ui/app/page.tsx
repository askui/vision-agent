"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";
import { Sidebar } from "@/components/sidebar/sidebar";
import { ChatContainer } from "@/components/chat/chat-container";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

function ChatApp() {
  return (
    <div className="h-screen flex">
      <Sidebar />
      <ChatContainer />
    </div>
  );
}

export default function Home() {
  return (
    <QueryClientProvider client={queryClient}>
      <ChatApp />
      <Toaster position="bottom-right" richColors />
    </QueryClientProvider>
  );
}
