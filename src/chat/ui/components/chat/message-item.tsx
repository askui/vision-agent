"use client";

import { useState, forwardRef } from "react";
import { format } from "date-fns";
import { User, Bot, MoreHorizontal, Trash2, Edit2, Copy } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Message } from "@/lib/types";
import { apiClient } from "@/lib/api";
import { useChatStore } from "@/lib/store";
import { MessageContentBlock } from "./message-content-block";

interface MessageItemProps {
  message: Message;
  isFirst: boolean;
  isLast: boolean;
}

export const MessageItem = forwardRef<HTMLDivElement, MessageItemProps>(
  function MessageItem({ message, isFirst, isLast }, ref) {
    const [isHovered, setIsHovered] = useState(false);
    const [isActionsOpen, setIsActionsOpen] = useState(false);
    const queryClient = useQueryClient();
    const { selectedThread } = useChatStore();

    // Fetch assistant info if message is from assistant
    const { data: assistant } = useQuery({
      queryKey: ["assistant", message.assistant_id],
      queryFn: () => apiClient.retrieveAssistant(message.assistant_id!),
      enabled: !!message.assistant_id && message.role === "assistant",
    });

    const deleteMessageMutation = useMutation({
      mutationFn: () => apiClient.deleteMessage(message.thread_id, message.id),
      onSuccess: () => {
        queryClient.invalidateQueries({
          queryKey: ["messages", selectedThread?.id],
        });
        toast.success("Message deleted");
      },
      onError: () => {
        toast.error("Failed to delete message");
      },
    });

    const handleDelete = () => {
      deleteMessageMutation.mutate();
    };

    const handleCopy = () => {
      const content =
        typeof message.content === "string"
          ? message.content
          : message.content
              .map((c) => {
                switch (c.type) {
                  case "text":
                    return c.text;
                  case "image":
                    return "[Image]";
                  case "tool_result":
                    return typeof c.content === "string"
                      ? c.content
                      : c.content
                          .map((subContent) =>
                            subContent.type === "text"
                              ? subContent.text
                              : "[Image]"
                          )
                          .join("\n");
                  case "tool_use":
                    return `[Tool: ${c.name}]`;
                  default:
                    return "[Unknown content type]";
                }
              })
              .join("\n");

      navigator.clipboard.writeText(content);
      toast.success("Message copied to clipboard");
    };

    const isUser = message.role === "user";
    const displayName = isUser ? "You" : assistant?.name || "Assistant";
    const timestamp = format(
      new Date(message.created_at * 1000),
      "MMM d, yyyy • h:mm a"
    );

    return (
      <div
        ref={ref}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className="pb-4"
      >
        <TooltipProvider>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="group relative"
          >
            <div className="flex gap-4">
              {/* Avatar */}
              <Avatar className="h-8 w-8 mt-1">
                <AvatarImage src={isUser ? "" : assistant?.avatar || ""} />
                <AvatarFallback>
                  {isUser ? (
                    <User className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4" />
                  )}
                </AvatarFallback>
              </Avatar>

              {/* Content */}
              <div className="flex-1 min-w-0">
                {/* Header */}
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm">{displayName}</span>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span className="text-xs text-muted-foreground cursor-help">
                        {format(new Date(message.created_at * 1000), "h:mm a")}
                      </span>
                    </TooltipTrigger>
                    <TooltipContent>{timestamp}</TooltipContent>
                  </Tooltip>
                </div>

                {/* Message Content */}
                <div className="text-sm leading-relaxed">
                  <MessageContentBlock content={message.content} />
                </div>
              </div>

              {/* Actions */}
              <AnimatePresence>
                {(isHovered || isActionsOpen) && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ duration: 0.15 }}
                    className="absolute top-0 right-0"
                  >
                    <DropdownMenu onOpenChange={setIsActionsOpen}>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={handleCopy}>
                          <Copy className="h-4 w-4 mr-2" />
                          Copy
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={handleDelete}>
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </TooltipProvider>
      </div>
    );
  }
);
