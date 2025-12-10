import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface PipelineSaveDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (name: string, description: string) => void;
  initialName?: string;
  initialDescription?: string;
}

export const PipelineSaveDialog = ({
  open,
  onOpenChange,
  onSave,
  initialName = "",
  initialDescription = "",
}: PipelineSaveDialogProps) => {
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription);

  useEffect(() => {
    if (open) {
      setName(initialName);
      setDescription(initialDescription);
    }
  }, [open, initialName, initialDescription]);

  const handleSave = () => {
    if (name.trim()) {
      onSave(name.trim(), description.trim());
      onOpenChange(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && e.metaKey) {
      handleSave();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Save Pipeline</DialogTitle>
          <DialogDescription>
            Give your pipeline a name and description to save it for later use.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="pipeline-name">Pipeline Name*</Label>
            <Input
              id="pipeline-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g., Video Transcription Pipeline"
              autoFocus
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="pipeline-description">Description</Label>
            <Textarea
              id="pipeline-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this pipeline does..."
              rows={4}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!name.trim()}>
            Save Pipeline
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
