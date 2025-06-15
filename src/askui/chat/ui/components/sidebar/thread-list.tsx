"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { format, formatDistanceToNow } from "date-fns";
import { MoreHorizontal, MessageSquare } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api";
import { useChatStore } from "@/lib/store";
import { Thread } from "@/lib/types";
import { ThreadItemMenu } from "./thread-item-menu";

export function ThreadList() {
  const { selectedThread, setSelectedThread } = useChatStore();

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    error,
    refetch,
  } = useInfiniteQuery({
    queryKey: ["threads"],
    queryFn: ({ pageParam }) =>
      apiClient.listThreads({
        limit: 20,
        after: pageParam,
        order: "desc",
      }),
    getNextPageParam: (lastPage) =>
      lastPage.has_more ? lastPage.last_id : undefined,
    initialPageParam: undefined as string | undefined,
  });

  const threads = data?.pages.flatMap((page) => page.data) ?? [];

  const handleThreadSelect = (thread: Thread) => {
    setSelectedThread(thread);
  };

  const handleLoadMore = () => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 p-4 space-y-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex-1 p-4 text-center">
        <p className="text-sm text-muted-foreground mb-2">
          Failed to load threads
        </p>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          Retry
        </Button>
      </div>
    );
  }

  if (threads.length === 0) {
    return (
      <div className="flex-1 p-4 flex flex-col items-center justify-center min-h-[200px] text-center">
        <MessageSquare className="h-12 w-12 mb-4 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          No threads yet. Create your first thread to get started.
        </p>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1">
      <div className="p-2 space-y-1">
        <AnimatePresence>
          {threads.map((thread) => (
            <motion.div
              key={thread.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
              className={`group relative p-3 rounded-lg cursor-pointer transition-colors ${
                selectedThread?.id === thread.id
                  ? "bg-accent text-accent-foreground"
                  : "hover:bg-accent/50"
              }`}
              onClick={() => handleThreadSelect(thread)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0 max-w-[180px]">
                  <h3
                    className="font-medium text-sm truncate"
                    title={thread.name ?? "New Thread"}
                  >
                    {thread.name ?? "New Thread"}
                  </h3>
                  <p
                    className="text-xs text-muted-foreground mt-1 truncate"
                    title={format(new Date(thread.created_at * 1000), "PPpp")}
                  >
                    {formatDistanceToNow(new Date(thread.created_at * 1000), {
                      addSuffix: true,
                    })}
                  </p>
                </div>

                <ThreadItemMenu
                  thread={thread}
                  trigger={
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  }
                />
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Load More */}
        {hasNextPage && (
          <div className="p-2 text-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLoadMore}
              disabled={isFetchingNextPage}
            >
              {isFetchingNextPage ? "Loading..." : "Load More"}
            </Button>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
