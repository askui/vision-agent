"use client";

import { MessageSquare, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useChatStore } from "@/lib/store";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";

export function EmptyState() {
  const { setSelectedThread } = useChatStore();
  const queryClient = useQueryClient();

  const createThreadMutation = useMutation({
    mutationFn: () => apiClient.createThread({ name: null }),
    onSuccess: (thread) => {
      setSelectedThread(thread);
      queryClient.invalidateQueries({ queryKey: ["threads"] });
      toast.success("New thread created");
    },
    onError: () => {
      toast.error("Failed to create thread");
    },
  });

  const handleCreateThread = () => {
    createThreadMutation.mutate();
  };

  return (
    <div className="flex flex-col items-center justify-center h-full max-w-2xl mx-auto p-8 text-center">
      <div className="mb-8">
        <div className="relative">
          <MessageSquare className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <Sparkles className="h-6 w-6 text-primary absolute -top-2 -right-2" />
        </div>
        <h1 className="text-3xl font-bold mb-2">Welcome to AskUI Chat</h1>
        <p className="text-lg text-muted-foreground mb-8">
          Start a conversation with AI Computer Agent to automate robotic
          processes on your computer.
        </p>
      </div>

      <div className="space-y-4 w-full max-w-md">
        <Button
          onClick={handleCreateThread}
          disabled={createThreadMutation.isPending}
          size="lg"
          className="w-full"
        >
          {createThreadMutation.isPending
            ? "Creating..."
            : "Start New Conversation"}
        </Button>

        <div className="text-sm text-muted-foreground">
          Or select an existing conversation from the sidebar
        </div>
      </div>
    </div>
  );
}
