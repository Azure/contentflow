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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Plus, X } from "lucide-react";

interface NodeData {
  label: string;
  type: "person" | "organization" | "concept" | "document" | "technology" | "event";
  description?: string;
  metadata?: Record<string, string>;
}

interface Node {
  id: string;
  data: NodeData;
  position?: { x: number; y: number };
}

interface NodeEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  node: Node | null;
  onSave: (nodeData: NodeData) => void;
}

export const NodeEditDialog = ({
  open,
  onOpenChange,
  node,
  onSave,
}: NodeEditDialogProps) => {
  const [editedData, setEditedData] = useState<NodeData | null>(null);
  const [metadata, setMetadata] = useState<Record<string, string>>({});
  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("");

  useEffect(() => {
    if (node?.data) {
      setEditedData(node.data);
      setMetadata(node.data.metadata || {});
    }
  }, [node]);

  const handleSave = () => {
    if (editedData) {
      onSave({ ...editedData, metadata });
      onOpenChange(false);
    }
  };

  const addMetadata = () => {
    if (newKey && newValue) {
      setMetadata({ ...metadata, [newKey]: newValue });
      setNewKey("");
      setNewValue("");
    }
  };

  const removeMetadata = (key: string) => {
    const newMetadata = { ...metadata };
    delete newMetadata[key];
    setMetadata(newMetadata);
  };

  if (!editedData) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Knowledge Node</DialogTitle>
          <DialogDescription>
            Update the node properties and metadata
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="label">Label</Label>
            <Input
              id="label"
              value={editedData.label}
              onChange={(e) => setEditedData({ ...editedData, label: e.target.value })}
              placeholder="Enter node label"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="type">Type</Label>
            <Select
              value={editedData.type}
              onValueChange={(value: any) => setEditedData({ ...editedData, type: value })}
            >
              <SelectTrigger id="type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="person">Person</SelectItem>
                <SelectItem value="organization">Organization</SelectItem>
                <SelectItem value="concept">Concept</SelectItem>
                <SelectItem value="document">Document</SelectItem>
                <SelectItem value="technology">Technology</SelectItem>
                <SelectItem value="event">Event</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={editedData.description || ""}
              onChange={(e) => setEditedData({ ...editedData, description: e.target.value })}
              placeholder="Describe this entity..."
              rows={3}
            />
          </div>

          <div className="space-y-3">
            <Label>Metadata</Label>
            
            {Object.entries(metadata).length > 0 && (
              <div className="space-y-2">
                {Object.entries(metadata).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-2 p-2 rounded-lg bg-muted">
                    <Badge variant="outline" className="font-mono text-xs">
                      {key}
                    </Badge>
                    <span className="flex-1 text-sm text-foreground truncate">{value}</span>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-6 w-6"
                      onClick={() => removeMetadata(key)}
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            <div className="flex gap-2">
              <Input
                placeholder="Key"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                className="flex-1"
              />
              <Input
                placeholder="Value"
                value={newValue}
                onChange={(e) => setNewValue(e.target.value)}
                className="flex-1"
              />
              <Button
                size="icon"
                variant="outline"
                onClick={addMetadata}
                disabled={!newKey || !newValue}
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} className="bg-gradient-secondary">
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};