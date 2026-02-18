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
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { AlertCircle, Info } from "lucide-react";
import type { ExecutorWithUI } from "@/lib/executorUiMapper";
import { enrichExecutorsWithUI } from "@/lib/executorUiMapper";
import type { ExecutorSetting } from "@/types/components";
import { getExecutors } from "@/lib/api/executorsApi";
import { StepListEditor, StepDefinition } from "@/components/pipeline/StepListEditor";

interface ExecutorConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  executor: ExecutorWithUI | null;
  initialConfig?: any;
  onSave: (config: any) => void;
  availablePipelines?: any[];
}

export const ExecutorConfigDialog = ({
  open,
  onOpenChange,
  executor,
  initialConfig,
  onSave,
  availablePipelines = [],
}: ExecutorConfigDialogProps) => {
  
  const [config, setConfig] = useState<Record<string, any>>({
    name: "",
    description: "",
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [steps, setSteps] = useState<StepDefinition[]>([]);
  const [availableExecutorsForSteps, setAvailableExecutorsForSteps] = useState<ExecutorWithUI[]>([]);

  useEffect(() => {
    if (executor) {
      const initialValues: Record<string, any> = {
        name: initialConfig?.name || executor.name,
        description: initialConfig?.description || executor?.description || "",
      };

      // Add sub-pipeline specific field
      if (executor.category === "pipeline") {
        initialValues.selectedPipelineId = initialConfig?.selectedPipelineId || "";
        initialValues.selectedPipelineName = initialConfig?.selectedPipelineName || "";
      }

      // Initialize steps for for_each_content executors
      const isForEachContent = executor.category === "control_flow" || executor.id === "for_each_content";
      if (isForEachContent) {
        const initialSteps = initialConfig?.settings?.steps || [];
        setSteps(initialSteps);
      } else {
        setSteps([]);
      }

      // Load values from settings schema
      if (executor.settings_schema) {
        Object.entries(executor.settings_schema).forEach(([key, schema]) => {
          // Skip 'steps' — handled by StepListEditor
          if (key === "steps") return;
          const setting = schema as ExecutorSetting;
          if (initialConfig?.settings?.[key] !== undefined) {
            initialValues[key] = initialConfig.settings[key];
          } else if (setting.default !== undefined && setting.default !== null) {
            initialValues[key] = setting.default;
          } else {
            // Set appropriate default based on type
            switch (setting.type) {
              case "boolean":
                initialValues[key] = false;
                break;
              case "integer":
              case "number":
                initialValues[key] = setting.min || 0;
                break;
              case "string":
                initialValues[key] = "";
                break;
              default:
                initialValues[key] = "";
            }
          }
        });
      }

      setConfig(initialValues);
      setErrors({});
    }
  }, [executor, initialConfig]);

  // Load available executors for step palette when editing a for_each_content executor
  useEffect(() => {
    const isForEachContent = executor?.category === "control_flow" || executor?.id === "for_each_content";
    if (isForEachContent && open && availableExecutorsForSteps.length === 0) {
      getExecutors()
        .then((execs) => setAvailableExecutorsForSteps(enrichExecutorsWithUI(execs)))
        .catch((err) => console.error("Failed to load executors for step editor:", err));
    }
  }, [executor, open]);

  const validateField = (key: string, value: any, setting: ExecutorSetting): string | null => {
    if (setting.required && (value === null || value === undefined || value === "")) {
      return `${setting.title} is required`;
    }

    if (setting.type === "integer" || setting.type === "number") {
      const numValue = Number(value);
      if (isNaN(numValue)) {
        return `${setting.title} must be a valid number`;
      }
      if (setting.min !== null && setting.min !== undefined && numValue < setting.min) {
        return `${setting.title} must be at least ${setting.min}`;
      }
      if (setting.max !== null && setting.max !== undefined && numValue > setting.max) {
        return `${setting.title} must be at most ${setting.max}`;
      }
    }

    return null;
  };

  const validateAll = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!config.name || config.name.trim() === "") {
      newErrors.name = "Name is required";
    }

    if (executor?.category === "pipeline" && !config.selectedPipelineId) {
      newErrors.selectedPipelineId = "Please select a pipeline";
    }

    if (executor?.settings_schema) {
      Object.entries(executor.settings_schema).forEach(([key, schema]) => {
        // Skip 'steps' — validated separately
        if (key === "steps") return;
        const setting = schema as ExecutorSetting;
        const error = validateField(key, config[key], setting);
        if (error) {
          newErrors[key] = error;
        }
      });
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (!validateAll()) {
      return;
    }

    // Separate base config from settings
    const { name, description, selectedPipelineId, selectedPipelineName, ...settings } = config;
    
    // Merge steps back into settings for for_each_content executors
    const isForEachContent = executor?.category === "control_flow" || executor?.id === "for_each_content";
    if (isForEachContent) {
      settings.steps = steps;
    }

    const savedConfig = {
      name,
      description,
      ...(selectedPipelineId && { selectedPipelineId }),
      ...(selectedPipelineName && { selectedPipelineName }),
      settings,
    };

    onSave(savedConfig);
  };

  const handleFieldChange = (key: string, value: any) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
    
    // Clear error for this field when changed
    if (errors[key]) {
      setErrors((prev) => ({ ...prev, [key]: "" }));
    }
  };

  if (!executor) return null;

  const isSubPipeline = executor.category === "pipeline";
  const isForEachContent = executor.category === "control_flow" || executor.id === "for_each_content";
  
  const renderField = (key: string, setting: ExecutorSetting) => {
    const value = config[key];
    const error = errors[key];
    const fieldId = `field-${key}`;
    
    // Determine if field should span full width
    const isFullWidth = setting.ui_component === "textarea" || 
                        (setting.description && setting.description.length > 80);

    switch (setting.ui_component) {
      case "checkbox":
        return (
          <div key={key} className={`flex items-center space-x-2 ${isFullWidth ? 'col-span-2' : ''}`}>
            <Checkbox
              id={fieldId}
              checked={value === true}
              onCheckedChange={(checked) => handleFieldChange(key, checked)}
            />
            <Label
              htmlFor={fieldId}
              className="text-sm cursor-pointer flex-1"
            >
              <span className="inline-flex items-center gap-1">
                {setting.title}
                {setting.required && <span className="text-red-500 ml-1">*</span>}
                {setting.description && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Info className="h-3 w-3 text-muted-foreground cursor-help inline" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="max-w-xs">{setting.description}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </span>
            </Label>
          </div>
        );

      case "select":
        return (
          <div key={key} className={`space-y-0.5 ${isFullWidth ? 'col-span-2' : ''}`}>
            <Label htmlFor={fieldId} className="text-xs inline-flex items-center gap-1">
              {setting.title}
              {setting.required && <span className="text-red-500 ml-1">*</span>}
              {setting.description && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs">{setting.description}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <Select
              value={value?.toString() || ""}
              onValueChange={(val) => handleFieldChange(key, val)}
            >
              <SelectTrigger id={fieldId} className={error ? "border-red-500 h-8 text-sm" : "h-8 text-sm"}>
                <SelectValue placeholder={setting.placeholder || setting.description || "Select..."} />
              </SelectTrigger>
              <SelectContent>
                {setting.options?.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {error && <p className="text-xs text-red-500 mt-0.5">{error}</p>}
          </div>
        );

      case "number":
        return (
          <div key={key} className={`space-y-0.5 ${isFullWidth ? 'col-span-2' : ''}`}>
            <Label htmlFor={fieldId} className="text-xs inline-flex items-center gap-1">
              {setting.title}
              {setting.required && <span className="text-red-500 ml-1">*</span>}
              {setting.description && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs">{setting.description}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <Input
              id={fieldId}
              type="number"
              value={value || ""}
              onChange={(e) => handleFieldChange(key, e.target.value ? Number(e.target.value.trim()) : "")}
              min={setting.min}
              max={setting.max ? setting.max : undefined}
              step={setting.increment ? setting.increment : undefined}
              placeholder={setting.placeholder || setting.description}
              className={error ? "border-red-500 h-8 text-sm" : "h-8 text-sm"}
            />
            {error && <p className="text-xs text-red-500 mt-0.5">{error}</p>}
          </div>
        );

      case "textarea":
        return (
          <div key={key} className="space-y-0.5 col-span-2">
            <Label htmlFor={fieldId} className="text-xs inline-flex items-center gap-1">
              {setting.title}
              {setting.required && <span className="text-red-500 ml-1">*</span>}
              {setting.description && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs">{setting.description}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <Textarea
              id={fieldId}
              value={value || ""}
              onChange={(e) => handleFieldChange(key, e.target.value)}
              placeholder={setting.placeholder || setting.description}
              rows={2}
              className={error ? "border-red-500 text-sm" : "text-sm"}
            />
            {error && <p className="text-xs text-red-500 mt-0.5">{error}</p>}
          </div>
        );

      case "input":
      default:
        return (
          <div key={key} className={`space-y-0.5 ${isFullWidth ? 'col-span-2' : ''}`}>
            <Label htmlFor={fieldId} className="text-xs inline-flex items-center gap-1">
              {setting.title}
              {setting.required && <span className="text-red-500 ml-1">*</span>}
              {setting.description && (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="max-w-xs">{setting.description}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </Label>
            <Input
              id={fieldId}
              value={value || ""}
              onChange={(e) => handleFieldChange(key, e.target.value)}
              placeholder={setting.placeholder || setting.description}
              className={error ? "border-red-500 h-8 text-sm" : "h-8 text-sm"}
            />
            {error && <p className="text-xs text-red-500 mt-0.5">{error}</p>}
          </div>
        );
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <div className={`${executor.color} text-white p-2 rounded-lg`}>
              {executor.icon}
            </div>
            Configure {executor.name}
          </DialogTitle>
          <DialogDescription>
            {isSubPipeline
              ? "Select a saved pipeline to use as a sub-pipeline"
              : isForEachContent
                ? "Configure the inline per-item processing chain and concurrency settings"
                : "Set up parameters and options for this executor"}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-3 px-1 max-h-[60vh] overflow-y-auto">
          {Object.keys(errors).length > 0 && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                Please fix the validation errors before saving.
              </AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="name">
              Name<span className="text-red-500 ml-1">*</span>
            </Label>
            <Input
              id="name"
              value={config.name || ""}
              onChange={(e) => handleFieldChange("name", e.target.value)}
              placeholder="Enter executor name"
              className={errors.name ? "border-red-500" : ""}
            />
            {errors.name && <p className="text-xs text-red-500">{errors.name}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={config.description || ""}
              onChange={(e) => handleFieldChange("description", e.target.value)}
              placeholder="Describe what this executor does..."
              rows={3}
            />
          </div>

          {isSubPipeline && (
            <div className="space-y-2">
              <Label htmlFor="pipeline">
                Select Pipeline<span className="text-red-500 ml-1">*</span>
              </Label>
              <Select
                value={config.selectedPipelineId || ""}
                onValueChange={(value) => {
                  handleFieldChange("selectedPipelineId", value);
                  const selected = availablePipelines.find((p) => p.id === value);
                  handleFieldChange("selectedPipelineName", selected?.name || "");
                }}
              >
                <SelectTrigger id="pipeline" className={errors.selectedPipelineId ? "border-red-500" : ""}>
                  <SelectValue placeholder="Choose a saved pipeline..." />
                </SelectTrigger>
                <SelectContent>
                  {availablePipelines.length === 0 ? (
                    <SelectItem value="__none__" disabled>No saved pipelines available</SelectItem>
                  ) : (
                    availablePipelines.map((pipeline) => (
                      <SelectItem key={pipeline.id} value={pipeline.id}>
                        {pipeline.name} ({pipeline.nodes?.length || 0} executors)
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
              {errors.selectedPipelineId && (
                <p className="text-xs text-red-500">{errors.selectedPipelineId}</p>
              )}
              {config.selectedPipelineId && (
                <p className="text-xs text-muted-foreground">
                  {availablePipelines.find(p => p.id === config.selectedPipelineId)?.description || ""}
                </p>
              )}
            </div>
          )}

          {executor.settings_schema && Object.keys(executor.settings_schema).length > 0 && (
            <>
              <div className="border-t pt-3 mt-3">
                <h4 className="text-sm font-semibold mb-2 px-1">
                  {isForEachContent ? "Loop Settings" : "Executor Settings"}
                </h4>
                <div className="grid grid-cols-2 gap-x-3 gap-y-2 px-1">
                  {Object.entries(executor.settings_schema)
                    .filter(([key]) => key !== "steps")
                    .map(([key, schema]) =>
                      renderField(key, schema as ExecutorSetting)
                    )}
                </div>
              </div>
            </>
          )}

          {/* StepListEditor for for_each_content executors */}
          {isForEachContent && (
            <div className="border-t pt-3 mt-3">
              <StepListEditor
                steps={steps}
                onChange={setSteps}
                availableExecutors={availableExecutorsForSteps}
              />
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