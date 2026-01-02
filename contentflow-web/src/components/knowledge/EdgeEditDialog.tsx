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
import type { Edge as FlowEdge } from "reactflow";

interface EdgeData {
  label?: string;
  description?: string;
  type?: string;
  strength?: number;
}

interface EdgeEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  edge: FlowEdge<EdgeData> | null;
  onSave: (edge: FlowEdge<EdgeData>) => void;
  onDelete?: (edgeId: string) => void;
}

export const EdgeEditDialog = ({
  open,
  onOpenChange,
  edge,
  onSave,
  onDelete,
}: EdgeEditDialogProps) => {
  const [editedEdge, setEditedEdge] = useState<FlowEdge<EdgeData> | null>(null);

  useEffect(() => {
    if (edge) {
      setEditedEdge(edge);
    }
  }, [edge]);

  const handleSave = () => {
    if (editedEdge) {
      onSave(editedEdge);
      onOpenChange(false);
    }
  };

  const handleDelete = () => {
    if (editedEdge && onDelete) {
      onDelete(editedEdge.id);
      onOpenChange(false);
    }
  };

  const updateEdgeData = (updates: Partial<EdgeData>) => {
    if (editedEdge) {
      setEditedEdge({
        ...editedEdge,
        data: { ...editedEdge.data, ...updates },
        label: updates.label !== undefined ? updates.label : editedEdge.label,
      });
    }
  };

  if (!editedEdge) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Edit Relationship</DialogTitle>
          <DialogDescription>
            Update the relationship between nodes
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>From</Label>
              <Input value={editedEdge.source} disabled className="bg-muted" />
            </div>
            <div className="space-y-2">
              <Label>To</Label>
              <Input value={editedEdge.target} disabled className="bg-muted" />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="label">Relationship Label</Label>
            <Input
              id="label"
              value={editedEdge.data?.label || (typeof editedEdge.label === 'string' ? editedEdge.label : "") || ""}
              onChange={(e) => updateEdgeData({ label: e.target.value })}
              placeholder="e.g., includes, relates to, depends on"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="type">Relationship Type</Label>
            <Select
              value={editedEdge.data?.type || "relates-to"}
              onValueChange={(value: any) => updateEdgeData({ type: value })}
            >
              <SelectTrigger id="type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="includes">Includes</SelectItem>
                <SelectItem value="utilizes">Utilizes</SelectItem>
                <SelectItem value="documented-in">Documented In</SelectItem>
                <SelectItem value="developed-by">Developed By</SelectItem>
                <SelectItem value="researched-by">Researched By</SelectItem>
                <SelectItem value="relates-to">Relates To</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={editedEdge.data?.description || ""}
              onChange={(e) => updateEdgeData({ description: e.target.value })}
              placeholder="Describe this relationship..."
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="strength">Relationship Strength ({editedEdge.data?.strength || 5}/10)</Label>
            <input
              id="strength"
              type="range"
              min="1"
              max="10"
              value={editedEdge.data?.strength || 5}
              onChange={(e) => updateEdgeData({ strength: parseInt(e.target.value) })}
              className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
            />
          </div>
        </div>

        <DialogFooter className="gap-2">
          {onDelete && (
            <Button variant="destructive" onClick={handleDelete} className="mr-auto">
              Delete Relationship
            </Button>
          )}
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
