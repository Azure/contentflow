import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
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
import { Search, Trash2, FolderOpen, Calendar } from "lucide-react";
import type { Pipeline } from "@/types/components";

interface LoadPipelinesDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  pipelines: Pipeline[];
  onLoad: (pipeline: Pipeline) => void;
  onDelete: (pipelineId: string) => void;
}

export const LoadPipelinesDialog = ({
  open,
  onOpenChange,
  pipelines,
  onLoad,
  onDelete,
}: LoadPipelinesDialogProps) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const filteredPipelines = pipelines.filter(
    (pipeline) =>
      pipeline.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      pipeline.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleLoad = (pipeline: Pipeline) => {
    onLoad(pipeline);
    onOpenChange(false);
  };

  const handleDeleteConfirm = () => {
    if (deleteConfirmId) {
      onDelete(deleteConfirmId);
      setDeleteConfirmId(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
    });
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-[700px] max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Saved Pipelines</DialogTitle>
            <DialogDescription>
              Load a previously saved pipeline to continue working on it.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {/* Search */}
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search pipelines..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Pipeline List */}
            <ScrollArea className="h-[400px] pr-4">
              {filteredPipelines.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <FolderOpen className="w-12 h-12 text-muted-foreground mb-3" />
                  <p className="text-muted-foreground">
                    {searchQuery ? "No pipelines found" : "No saved pipelines yet"}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {searchQuery
                      ? "Try a different search term"
                      : "Create and save your first pipeline"}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredPipelines.map((pipeline) => (
                    <Card
                      key={pipeline.id}
                      className="p-4 hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => handleLoad(pipeline)}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-foreground mb-1 truncate">
                            {pipeline.name.length > 50
                              ? pipeline.name.slice(0, 50) + "..."
                              : pipeline.name}
                          </h4>
                          {pipeline.description && (
                            <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                              {pipeline.description?.length > 100
                                ? pipeline.description.slice(0, 100) + "..."
                                : pipeline.description}
                            </p>
                          )}
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            {pipeline.updated_at && (
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {formatDate(pipeline.updated_at)}
                              </span>
                            )}
                            {pipeline.nodes && (
                              <span>
                                {pipeline.nodes.length} node{pipeline.nodes.length !== 1 ? "s" : ""}
                              </span>
                            )}
                            {pipeline.edges && (
                              <span>
                                {pipeline.edges.length} connection{pipeline.edges.length !== 1 ? "s" : ""}
                              </span>
                            )}
                          </div>
                        </div>

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteConfirmId(pipeline.id);
                          }}
                          className="text-destructive hover:text-destructive hover:bg-destructive/10"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteConfirmId !== null} onOpenChange={(open) => !open && setDeleteConfirmId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Pipeline</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this pipeline? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
