"use client";

import { useState } from "react";
import { Edit2, Trash2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Thread } from "@/lib/types";
import { apiClient } from "@/lib/api";
import { useChatStore } from "@/lib/store";
import { RenameThreadDialog } from "./rename-thread-dialog";

interface ThreadItemMenuProps {
  thread: Thread;
  trigger: React.ReactNode;
}

export function ThreadItemMenu({ thread, trigger }: ThreadItemMenuProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showRenameDialog, setShowRenameDialog] = useState(false);
  const queryClient = useQueryClient();
  const { selectedThread, setSelectedThread } = useChatStore();

  const deleteThreadMutation = useMutation({
    mutationFn: () => apiClient.deleteThread(thread.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["threads"] });
      if (selectedThread?.id === thread.id) {
        setSelectedThread(null);
      }
      toast.success("Thread deleted");
    },
    onError: (error) => {
      console.error(error);
      toast.error("Failed to delete thread");
    },
  });

  const handleDelete = () => {
    deleteThreadMutation.mutate();
    setShowDeleteDialog(false);
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>{trigger}</DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => setShowRenameDialog(true)}>
            <Edit2 className="h-4 w-4 mr-2" />
            Rename
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => setShowDeleteDialog(true)}
            className="text-destructive focus:text-destructive"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Thread</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this thread? This action cannot be
              undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <RenameThreadDialog
        thread={thread}
        open={showRenameDialog}
        onOpenChange={setShowRenameDialog}
      />
    </>
  );
}
