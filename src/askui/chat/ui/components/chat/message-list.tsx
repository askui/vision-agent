"use client";

import { useEffect, useRef } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { MessageSquare } from "lucide-react";
import { useChatStore } from "@/lib/store";
import { apiClient } from "@/lib/api";
import { MessageItem } from "./message-item";
import { Message } from "@/lib/types";
import { uniqBy } from "lodash-es";
import { MAX_MESSAGES_PER_THREAD } from "@/lib/constants";

export function MessageList() {
  const {
    selectedThread,
    currentRun,
    messages: storeMessages,
  } = useChatStore();
  const lastMessageRef = useRef<HTMLDivElement>(null);
  const prevLastMessageIdRef = useRef<string | undefined>(undefined);

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
    queryKey: ["messages", selectedThread?.id],
    queryFn: ({ pageParam }) =>
      apiClient.listMessages(selectedThread!.id, {
        limit: MAX_MESSAGES_PER_THREAD,
        before: pageParam,
        order: "asc",
      }),
    getNextPageParam: (lastPage) =>
      lastPage.has_more ? lastPage.last_id : undefined,
    initialPageParam: undefined as string | undefined,
    enabled: !!selectedThread,
  });

  const queryMessages = data?.pages.flatMap((page) => page.data) ?? [];

  // Combine query messages with store messages
  const allMessages: Message[] = uniqBy(
    [...queryMessages, ...storeMessages],
    (message) => message.id
  );

  useEffect(() => {
    if (allMessages.length === 0) {
      prevLastMessageIdRef.current = undefined;
      return;
    }
    const lastMessage = allMessages[allMessages.length - 1];
    console.log(
      `prevLastMessageIdRef.current: ${prevLastMessageIdRef.current}`
    );
    console.log(`lastMessage.id:               ${lastMessage.id}`);
    if (
      lastMessage &&
      lastMessage.id !== prevLastMessageIdRef.current &&
      lastMessageRef.current
    ) {
      setTimeout(() => {
        lastMessageRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "end",
        });
      });
    }
    prevLastMessageIdRef.current = lastMessage?.id;
  }, [allMessages]);

  const handleLoadMore = () => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 p-4 space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex gap-3">
            <Skeleton className="h-8 w-8 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-20 w-full" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-muted-foreground mb-2">
            Failed to load messages
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (allMessages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            No messages yet. Start the conversation below.
          </p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1">
      <div className="p-4 space-y-2">
        {/* Load More Button */}
        {hasNextPage && (
          <div className="text-center">
            <Button
              variant="outline"
              size="sm"
              onClick={handleLoadMore}
              disabled={isFetchingNextPage}
            >
              {isFetchingNextPage ? "Loading..." : "Load Earlier Messages"}
            </Button>
          </div>
        )}

        {/* Messages */}
        {allMessages.map((message, index) => (
          <MessageItem
            key={message.id}
            message={message}
            isFirst={index === 0}
            isLast={index === allMessages.length - 1}
            ref={index === allMessages.length - 1 ? lastMessageRef : undefined}
          />
        ))}
      </div>
    </ScrollArea>
  );
}
