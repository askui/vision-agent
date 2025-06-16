"use client";

import { Bot, Zap } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useChatStore } from "@/lib/store";
import { apiClient } from "@/lib/api";
import { HUMAN_DEMONSTRATION_AGENT_ID } from "@/lib/constants";

export function ChatHeader() {
  const { selectedAssistant, setSelectedAssistant, currentRun } =
    useChatStore();

  const { data: assistantsListResponse, isLoading } = useQuery({
    queryKey: ["assistants"],
    queryFn: () =>
      apiClient.listAssistants().then((response) => {
        return {
          ...response,
          data: response.data.filter(
            (a) => a.id !== HUMAN_DEMONSTRATION_AGENT_ID
          ),
        };
      }),
  });

  const handleAssistantChange = (assistantId: string) => {
    const assistant = assistantsListResponse?.data.find(
      (a) => a.id === assistantId
    );
    if (assistant) {
      setSelectedAssistant(assistant);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-between p-4 border-b border-border">
        <div className="flex items-center gap-3">
          <Skeleton className="h-8 w-8 rounded-full" />
          <Skeleton className="h-4 w-32" />
        </div>
        <Skeleton className="h-6 w-16" />
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between p-4">
      <div className="flex items-center gap-3">
        <Select
          value={selectedAssistant?.id || ""}
          onValueChange={handleAssistantChange}
        >
          <SelectTrigger className="w-auto border-none shadow-none p-0 h-auto">
            <div className="flex items-center gap-3">
              <Avatar className="h-8 w-8">
                <AvatarImage src={selectedAssistant?.avatar || ""} />
                <AvatarFallback>
                  <Bot className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <div className="text-left">
                <div className="font-medium">
                  {selectedAssistant?.name || "Select Assistant"}
                </div>
                {selectedAssistant?.description && (
                  <div className="text-xs text-muted-foreground">
                    {selectedAssistant.description}
                  </div>
                )}
              </div>
            </div>
          </SelectTrigger>
          <SelectContent>
            {assistantsListResponse?.data.map((assistant) => (
              <SelectItem key={assistant.id} value={assistant.id}>
                <div className="flex items-center gap-3">
                  <Avatar className="h-6 w-6">
                    <AvatarImage src={assistant.avatar || ""} />
                    <AvatarFallback>
                      <Bot className="h-3 w-3" />
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="font-medium">{assistant.name}</div>
                    {assistant.description && (
                      <div className="text-xs text-muted-foreground">
                        {assistant.description}
                      </div>
                    )}
                  </div>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {currentRun && (
        <Badge variant="secondary" className="flex items-center gap-1">
          <Zap className="h-3 w-3" />
          {currentRun.status === "in_progress"
            ? "Thinking..."
            : currentRun.status}
        </Badge>
      )}
    </div>
  );
}
