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
import { Slider } from "@/components/ui/slider";

interface ExecutorConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  executor: any;
  initialConfig?: any;
  onSave: (config: any) => void;
}

export const ExecutorConfigDialog = ({
  open,
  onOpenChange,
  executor,
  initialConfig,
  onSave,
}: ExecutorConfigDialogProps) => {
  const [config, setConfig] = useState({
    name: "",
    description: "",
    model: "default",
    temperature: 0.7,
    maxTokens: 1000,
    steps: 3,
  });

  useEffect(() => {
    if (executor) {
      setConfig({
        name: initialConfig?.name || executor.name,
        description: initialConfig?.description || "",
        model: initialConfig?.model || "default",
        temperature: initialConfig?.temperature || 0.7,
        maxTokens: initialConfig?.maxTokens || 1000,
        steps: initialConfig?.steps || 3,
      });
    }
  }, [executor, initialConfig]);

  const handleSave = () => {
    onSave(config);
  };

  if (!executor) return null;

  const isSubWorkflow = executor.category === "workflow";
  const isAIExecutor = executor.category === "analyze";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <div className={`${executor.color} text-white p-2 rounded-lg`}>
              {executor.icon}
            </div>
            Configure {executor.name}
          </DialogTitle>
          <DialogDescription>
            {isSubWorkflow 
              ? "Configure the sub-workflow settings and nested pipeline"
              : "Set up parameters and options for this executor"}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={config.name}
              onChange={(e) => setConfig({ ...config, name: e.target.value })}
              placeholder="Enter executor name"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={config.description}
              onChange={(e) => setConfig({ ...config, description: e.target.value })}
              placeholder="Describe what this executor does..."
              rows={3}
            />
          </div>

          {isSubWorkflow && (
            <div className="space-y-2">
              <Label htmlFor="steps">Number of Nested Steps</Label>
              <div className="flex items-center gap-4">
                <Slider
                  id="steps"
                  min={1}
                  max={10}
                  step={1}
                  value={[config.steps]}
                  onValueChange={(value) => setConfig({ ...config, steps: value[0] })}
                  className="flex-1"
                />
                <span className="font-medium text-foreground w-8 text-center">{config.steps}</span>
              </div>
            </div>
          )}

          {isAIExecutor && (
            <>
              <div className="space-y-2">
                <Label htmlFor="model">AI Model</Label>
                <Select
                  value={config.model}
                  onValueChange={(value) => setConfig({ ...config, model: value })}
                >
                  <SelectTrigger id="model">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="default">Default Model</SelectItem>
                    <SelectItem value="gpt-4">GPT-4</SelectItem>
                    <SelectItem value="claude">Claude</SelectItem>
                    <SelectItem value="gemini">Gemini Pro</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="temperature">Temperature: {config.temperature}</Label>
                  <Slider
                    id="temperature"
                    min={0}
                    max={1}
                    step={0.1}
                    value={[config.temperature]}
                    onValueChange={(value) => setConfig({ ...config, temperature: value[0] })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="maxTokens">Max Tokens</Label>
                  <Input
                    id="maxTokens"
                    type="number"
                    value={config.maxTokens}
                    onChange={(e) => setConfig({ ...config, maxTokens: parseInt(e.target.value) })}
                    min={100}
                    max={4000}
                  />
                </div>
              </div>
            </>
          )}

          {executor.category === "extract" && (
            <div className="space-y-2">
              <Label htmlFor="format">Output Format</Label>
              <Select defaultValue="json">
                <SelectTrigger id="format">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="json">JSON</SelectItem>
                  <SelectItem value="xml">XML</SelectItem>
                  <SelectItem value="markdown">Markdown</SelectItem>
                  <SelectItem value="plain">Plain Text</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} className="bg-gradient-secondary">
            Save Configuration
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};