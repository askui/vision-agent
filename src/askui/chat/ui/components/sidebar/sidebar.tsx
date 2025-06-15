"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useChatStore } from "@/lib/store";
import { ThreadList } from "./thread-list";
import { apiClient } from "@/lib/api";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export function Sidebar() {
  const { isCollapsed, setIsCollapsed, setSelectedThread } = useChatStore();
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
    <TooltipProvider>
      <motion.div
        initial={false}
        animate={{ width: isCollapsed ? 64 : 320 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="relative h-full bg-background border-r border-border flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <AnimatePresence mode="wait">
            {!isCollapsed && (
              <motion.h2
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.2 }}
                className="text-lg font-semibold"
              >
                Chat
              </motion.h2>
            )}
          </AnimatePresence>

          <div className="flex items-center gap-2">
            {!isCollapsed && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleCreateThread}
                    disabled={createThreadMutation.isPending}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>New Thread</TooltipContent>
              </Tooltip>
            )}

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setIsCollapsed(!isCollapsed)}
                >
                  {isCollapsed ? (
                    <ChevronRight className="h-4 w-4" />
                  ) : (
                    <ChevronLeft className="h-4 w-4" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
              </TooltipContent>
            </Tooltip>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          <AnimatePresence>
            {!isCollapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="h-full flex flex-col"
              >
                <ThreadList />
              </motion.div>
            )}
          </AnimatePresence>

          {isCollapsed && (
            <div className="p-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={handleCreateThread}
                    disabled={createThreadMutation.isPending}
                    className="w-full"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="right">New Thread</TooltipContent>
              </Tooltip>
            </div>
          )}
        </div>
      </motion.div>
    </TooltipProvider>
  );
}
