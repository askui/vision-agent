"use client";

import { useState, useRef, useCallback } from "react";
import { Send, Plus, X, Paperclip, Square } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useChatStore } from "@/lib/store";
import { apiClient } from "@/lib/api";
import { Event } from "@/lib/types";

interface AttachedFile {
  id: string;
  file: File;
  preview: string;
  type: "image";
}

let buffer = "";

const SseSplitterStream = (): TransformStream<string, string> =>
  new TransformStream<string, string>({
    start() {},
    transform(chunk, controller) {
      buffer += chunk;
      const parts = buffer.split("\n\n");
      buffer = parts.pop()!; // Keep the last partial event in buffer

      for (const part of parts) {
        controller.enqueue(part);
      }
    },
    flush(controller) {},
  });

function parseSseMessage(message: string): Event {
  const lines = message.split("\n");
  let type = "message";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      type = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }

  if (dataLines.length === 0) {
    throw new Error("No data field in SSE message");
  }

  const rawData = dataLines.join("\n");

  try {
    switch (type) {
      case "thread.run.created":
      case "thread.run.queued":
      case "thread.run.in_progress":
      case "thread.run.completed":
      case "thread.run.cancelling":
      case "thread.run.cancelled":
      case "thread.run.failed":
      case "thread.run.expired":
        return { type, data: JSON.parse(rawData) };
      case "thread.message.created":
        return { type, data: JSON.parse(rawData) };
      case "error":
        return { type, data: JSON.parse(rawData) };
      case "done":
        return { type, data: "[DONE]" };
      default:
        throw new Error(`Unknown event type: ${type}`);
    }
  } catch (e) {
    throw new Error(
      `Failed to parse SSE data of event "${type}": ${
        e instanceof Error ? e.message : String(e)
      }: ${rawData}`
    );
  }
}

export function ChatInput() {
  const [message, setMessage] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const {
    selectedThread,
    selectedAssistant,
    currentRun,
    setCurrentRun,
    appendMessage,
    clearMessages,
  } = useChatStore();

  const createMessageMutation = useMutation({
    mutationFn: async (data: { content: any; role: "user" }) => {
      if (!selectedThread) throw new Error("No thread selected");
      return apiClient.createMessage(selectedThread.id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["messages", selectedThread?.id],
      });
    },
  });

  const createRunMutation = useMutation({
    mutationFn: async () => {
      if (!selectedThread || !selectedAssistant) {
        throw new Error("Thread and assistant required");
      }

      const response = await fetch(
        `${
          process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        }/v1/threads/${selectedThread.id}/runs`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            assistant_id: selectedAssistant.id,
            stream: true,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error("No response body");
      }

      const reader = response.body
        .pipeThrough(new TextDecoderStream())
        .pipeThrough(SseSplitterStream())
        .getReader();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const event: Event = parseSseMessage(value);
        switch (event.type) {
          case "thread.run.created":
          case "thread.run.queued":
          case "thread.run.in_progress":
          case "thread.run.completed":
          case "thread.run.cancelling":
          case "thread.run.cancelled":
          case "thread.run.failed":
          case "thread.run.expired":
            setCurrentRun(event.data);
            break;
          case "thread.message.created":
            appendMessage(event.data);
            break;
          case "error":
            throw new Error(event.data.error.message);
          case "done":
            setCurrentRun(null);
            break;
        }
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["messages", selectedThread?.id],
      });
      setCurrentRun(null);
      clearMessages();
    },
    onError: (error) => {
      toast.error(`Run failed: ${error.message}`);
      queryClient.invalidateQueries({
        queryKey: ["messages", selectedThread?.id],
      });
      setCurrentRun(null);
      clearMessages();
    },
  });

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;

    Array.from(files).forEach((file) => {
      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => {
          const newFile: AttachedFile = {
            id: Math.random().toString(36).substr(2, 9),
            file,
            preview: e.target?.result as string,
            type: "image",
          };
          setAttachedFiles((prev) => [...prev, newFile]);
        };
        reader.readAsDataURL(file);
      } else {
        toast.error("Only image files are supported");
      }
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedThread || !selectedAssistant) {
      toast.error("Please select a thread and assistant");
      return;
    }

    if (!message.trim() && attachedFiles.length === 0) {
      return;
    }

    const content: any[] = [];

    if (message.trim()) {
      content.push({
        type: "text",
        text: message.trim(),
      });
    }

    attachedFiles.forEach((file) => {
      const base64Data = file.preview.split(",")[1];
      content.push({
        type: "image",
        source: {
          type: "base64",
          media_type: file.file.type,
          data: base64Data,
        },
      });
    });

    try {
      await createMessageMutation.mutateAsync({
        content:
          content.length === 1 && content[0].type === "text"
            ? content[0].text
            : content,
        role: "user",
      });

      // Start the run
      await createRunMutation.mutateAsync();

      // Clear input
      setMessage("");
      setAttachedFiles([]);
    } catch (error) {
      console.error("Error sending message:", error);
    }
  };

  const handleCancel = () => {
    if (currentRun) {
      // Cancel the run
      apiClient
        .cancelRun(currentRun.thread_id, currentRun.id)
        .then(() => {
          toast.success("Send request to cancel run");
        })
        .catch(() => {
          toast.error("Failed to send request to cancel run");
        });
    }
  };

  const removeFile = (fileId: string) => {
    setAttachedFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  }, []);

  const isLoading =
    createMessageMutation.isPending || createRunMutation.isPending;
  const isRunning = !!currentRun;

  return (
    <TooltipProvider>
      <div className="p-4 border-t border-border">
        <form onSubmit={handleSubmit} className="space-y-3">
          {/* File Attachments */}
          <AnimatePresence>
            {attachedFiles.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="flex gap-2 flex-wrap"
              >
                {attachedFiles.map((file) => (
                  <div
                    key={file.id}
                    className="relative group rounded-lg overflow-hidden border border-border"
                  >
                    <img
                      src={file.preview}
                      alt={file.file.name}
                      className="w-16 h-16 object-cover"
                    />
                    <Button
                      type="button"
                      variant="destructive"
                      size="icon"
                      className="absolute top-1 right-1 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={() => removeFile(file.id)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Input Area */}
          <div
            className={`relative rounded-lg border ${
              isDragOver ? "border-primary border-2" : "border-border"
            } transition-colors duration-200`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={
                !selectedAssistant
                  ? "Please select an assistant first..."
                  : "Type your message here..."
              }
              autoFocus
              disabled={isLoading || !selectedAssistant}
              className="min-h-[60px] max-h-[200px] resize-none border-0 focus-visible:ring-0 pr-20"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />

            <div className="absolute bottom-2 right-2 flex items-center gap-1">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                className="hidden"
                onChange={(e) => handleFileSelect(e.target.files)}
              />

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isLoading}
                  >
                    <Paperclip className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Attach Image</TooltipContent>
              </Tooltip>

              {isRunning ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      type="button"
                      variant="destructive"
                      size="icon"
                      className="h-8 w-8"
                      onClick={handleCancel}
                    >
                      <Square className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Cancel</TooltipContent>
                </Tooltip>
              ) : (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      type="submit"
                      size="icon"
                      className="h-8 w-8"
                      disabled={
                        isLoading ||
                        (!message.trim() && attachedFiles.length === 0) ||
                        !selectedAssistant
                      }
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Send Message</TooltipContent>
                </Tooltip>
              )}
            </div>
          </div>

          {/* Drag overlay */}
          <AnimatePresence>
            {isDragOver && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-primary/10 border-2 border-primary border-dashed rounded-lg flex items-center justify-center pointer-events-none"
              >
                <div className="text-center">
                  <Plus className="h-8 w-8 mx-auto mb-2 text-primary" />
                  <p className="text-sm font-medium text-primary">
                    Drop images here to attach
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </form>
      </div>
    </TooltipProvider>
  );
}
