"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Thread } from "@/lib/types";
import { apiClient } from "@/lib/api";

interface RenameThreadDialogProps {
  thread: Thread;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function RenameThreadDialog({
  thread,
  open,
  onOpenChange,
}: RenameThreadDialogProps) {
  const [name, setName] = useState(thread.name || "");
  const queryClient = useQueryClient();

  const renameThreadMutation = useMutation({
    mutationFn: (newName: string) =>
      apiClient.modifyThread(thread.id, { name: newName }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["threads"] });
      toast.success("Thread renamed");
      onOpenChange(false);
    },
    onError: () => {
      toast.error("Failed to rename thread");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      renameThreadMutation.mutate(name.trim());
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Rename Conversation</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter new name..."
                autoFocus
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!name.trim() || renameThreadMutation.isPending}
            >
              {renameThreadMutation.isPending ? "Renaming..." : "Rename"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
