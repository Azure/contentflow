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
import { Switch } from "@/components/ui/switch";
import { Pipeline } from "@/types/components";

export interface PipelineSaveDialogDataProps {
  name: string;
  description: string;
  tags?: string[];
  version?: string;
  enabled?: boolean;
  retry_delay?: number;
  timeout?: number;
  retries?: number;
}

interface PipelineSaveDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (data: PipelineSaveDialogDataProps) => void;
  pipeline?: Pipeline;
}

export const PipelineSaveDialog = ({
  open,
  onOpenChange,
  onSave,
  pipeline,
}: PipelineSaveDialogProps) => {
  const [name, setName] = useState(pipeline?.name || "");
  const [description, setDescription] = useState(pipeline?.description || "");
  const [tags, setTags] = useState<string>((pipeline?.tags || []).join(", "));
  const [version, setVersion] = useState(pipeline?.version || "");
  const [enabled, setEnabled] = useState(pipeline?.enabled ?? true);
  const [retryDelay, setRetryDelay] = useState((pipeline?.retry_delay ?? 0).toString());
  const [timeout, setTimeout] = useState((pipeline?.timeout ?? 300).toString());
  const [retries, setRetries] = useState((pipeline?.retries ?? 0).toString());

  // Track previous open state to detect when dialog opens
  const [prevOpen, setPrevOpen] = useState(open);

  useEffect(() => {
    // Only reset form when dialog transitions from closed to open
    if (open && !prevOpen) {
      setName(pipeline?.name || "");
      setDescription(pipeline?.description || "");
      setTags((pipeline?.tags || []).join(", "));
      setVersion(pipeline?.version || "");
      setEnabled(pipeline?.enabled ?? true);
      setRetryDelay((pipeline?.retry_delay ?? 0).toString());
      setTimeout((pipeline?.timeout ?? 300).toString());
      setRetries((pipeline?.retries ?? 0).toString());
    }
    setPrevOpen(open);
  }, [open, pipeline]);

  const handleSave = () => {
    if (name.trim()) {
      const tagsArray = tags
        .split(",")
        .map((tag) => tag.trim())
        .filter((tag) => tag.length > 0);

      onSave({
        name: name.trim(),
        description: description.trim(),
        tags: tagsArray.length > 0 ? tagsArray : undefined,
        version: version.trim() || undefined,
        enabled,
        retry_delay: retryDelay ? parseInt(retryDelay, 10) : undefined,
        timeout: timeout ? parseInt(timeout, 10) : undefined,
        retries: retries ? parseInt(retries, 10) : undefined,
      });
      onOpenChange(false);
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
              rows={3}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="pipeline-tags">Tags</Label>
            <Input
              id="pipeline-tags"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="e.g., extraction, pdf, ai (comma-separated)"
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="pipeline-version">Version</Label>
            <Input
              id="pipeline-version"
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              placeholder="e.g., 1.0.0"
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="pipeline-enabled">Enabled</Label>
              <div className="text-sm text-muted-foreground">
                Enable this pipeline for execution
              </div>
            </div>
            <Switch
              id="pipeline-enabled"
              checked={enabled}
              onCheckedChange={setEnabled}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="pipeline-retries">Retries</Label>
              <Input
                id="pipeline-retries"
                type="number"
                min="0"
                value={retries}
                onChange={(e) => setRetries(e.target.value)}
                placeholder="0"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="pipeline-retry-delay">Retry Delay (s)</Label>
              <Input
                id="pipeline-retry-delay"
                type="number"
                min="0"
                value={retryDelay}
                onChange={(e) => setRetryDelay(e.target.value)}
                placeholder="0"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="pipeline-timeout">Timeout (s)</Label>
              <Input
                id="pipeline-timeout"
                type="number"
                min="0"
                value={timeout}
                onChange={(e) => setTimeout(e.target.value)}
                placeholder="300"
              />
            </div>
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
