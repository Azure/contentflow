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
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { HelpCircle } from "lucide-react";
import { toast } from "sonner";
import type { Vault, Pipeline, UpdateVaultRequest } from "@/types/components";

interface UpdateVaultDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  vault: Vault | null;
  onUpdateVault: (vaultId: string, data: UpdateVaultRequest) => void;
  isLoading?: boolean;
}

export const UpdateVaultDialog = ({
  open,
  onOpenChange,
  vault,
  onUpdateVault,
  isLoading = false,
}: UpdateVaultDialogProps) => {
  const [formData, setFormData] = useState<UpdateVaultRequest>({
    name: "",
    description: "",
    save_execution_output: false,
    enabled: true,
    tags: [],
  });
  const [tagInput, setTagInput] = useState("");

  // Update form when vault changes
  useEffect(() => {
    if (vault) {
      setFormData({
        name: vault.name,
        description: vault.description || "",
        save_execution_output: vault.save_execution_output || false,
        enabled: vault.enabled !== false,
        tags: vault.tags || [],
      });
      setTagInput("");
    }
  }, [vault, open]);

  const handleSubmit = () => {
    if (!formData.name.trim()) {
      toast.error("Please enter a vault name");
      return;
    }
    
    if (vault) {
      onUpdateVault(vault.id, formData);
    }
  };

  const addTag = () => {
    if (tagInput.trim() && !(formData.tags || []).includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...(formData.tags || []), tagInput.trim()],
      });
      setTagInput("");
    }
  };

  const removeTag = (tag: string) => {
    setFormData({
      ...formData,
      tags: (formData.tags || []).filter((t) => t !== tag),
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Update Vault</DialogTitle>
          <DialogDescription>
            Update the vault details and settings
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Vault Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., AI Research Vault"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe the purpose of this vault..."
              rows={3}
            />
          </div>

          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="enabled"
                checked={formData.enabled}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, enabled: checked === true })
                }
              />
              <Label htmlFor="enabled" className="cursor-pointer flex items-center gap-2">
                Enabled
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-4 h-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>When enabled, this vault will be active and available for use</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </Label>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="save_execution_output"
                checked={formData.save_execution_output}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, save_execution_output: checked === true })
                }
              />
              <Label htmlFor="save_execution_output" className="cursor-pointer flex items-center gap-2">
                Save Execution Output
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <HelpCircle className="w-4 h-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>When enabled, pipeline execution output will be saved to Cosmos DB</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </Label>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="tags">Tags</Label>
            <div className="flex gap-2">
              <Input
                id="tags"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && (e.preventDefault(), addTag())}
                placeholder="Add tags..."
              />
              <Button type="button" variant="outline" onClick={addTag}>
                Add
              </Button>
            </div>
            {(formData.tags && formData.tags.length > 0) && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.tags.map((tag) => (
                  <div
                    key={tag}
                    className="bg-secondary text-secondary-foreground px-3 py-1 rounded-full text-sm flex items-center gap-2"
                  >
                    {tag}
                    <button
                      onClick={() => removeTag(tag)}
                      className="hover:text-destructive"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} className="bg-gradient-secondary" disabled={isLoading}>
            {isLoading ? "Updating..." : "Update Vault"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
