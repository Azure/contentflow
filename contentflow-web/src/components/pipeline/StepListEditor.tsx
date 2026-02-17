import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import {
  ChevronDown,
  ChevronRight,
  ChevronUp,
  ArrowDown,
  ArrowUp,
  X,
  Plus,
  GripVertical,
  Info,
  Settings,
} from "lucide-react";
import type { ExecutorCatalogDefinition, ExecutorSetting } from "@/types/components";
import type { ExecutorWithUI } from "@/lib/executorUiMapper";

export interface StepDefinition {
  id: string;
  type: string;
  settings?: Record<string, any>;
}

interface StepListEditorProps {
  steps: StepDefinition[];
  onChange: (steps: StepDefinition[]) => void;
  availableExecutors: ExecutorWithUI[];
}

interface StepCardProps {
  step: StepDefinition;
  index: number;
  total: number;
  executorDef: ExecutorWithUI | undefined;
  onUpdate: (index: number, step: StepDefinition) => void;
  onRemove: (index: number) => void;
  onMoveUp: (index: number) => void;
  onMoveDown: (index: number) => void;
}

/**
 * Renders a single setting field for a step, reusing the same pattern
 * as ExecutorConfigDialog's renderField.
 */
function StepSettingField({
  settingKey,
  setting,
  value,
  onChange,
}: {
  settingKey: string;
  setting: ExecutorSetting;
  value: any;
  onChange: (key: string, value: any) => void;
}) {
  const fieldId = `step-field-${settingKey}`;

  const labelEl = (
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
  );

  switch (setting.ui_component) {
    case "checkbox":
      return (
        <div className="flex items-center space-x-2">
          <Checkbox
            id={fieldId}
            checked={value === true}
            onCheckedChange={(checked) => onChange(settingKey, checked)}
          />
          {labelEl}
        </div>
      );

    case "select":
      return (
        <div className="space-y-0.5">
          {labelEl}
          <Select
            value={value?.toString() || ""}
            onValueChange={(val) => onChange(settingKey, val)}
          >
            <SelectTrigger className="h-8 text-sm">
              <SelectValue placeholder={setting.placeholder || "Select..."} />
            </SelectTrigger>
            <SelectContent>
              {setting.options?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      );

    case "number":
      return (
        <div className="space-y-0.5">
          {labelEl}
          <Input
            id={fieldId}
            type="number"
            value={value ?? ""}
            onChange={(e) =>
              onChange(settingKey, e.target.value ? Number(e.target.value) : "")
            }
            min={setting.min}
            max={setting.max ?? undefined}
            step={setting.increment ?? undefined}
            placeholder={setting.placeholder || setting.description}
            className="h-8 text-sm"
          />
        </div>
      );

    case "textarea":
      return (
        <div className="space-y-0.5 col-span-2">
          {labelEl}
          <Textarea
            id={fieldId}
            value={value || ""}
            onChange={(e) => onChange(settingKey, e.target.value)}
            placeholder={setting.placeholder || setting.description}
            rows={2}
            className="text-sm"
          />
        </div>
      );

    case "input":
    default:
      return (
        <div className="space-y-0.5">
          {labelEl}
          <Input
            id={fieldId}
            value={value || ""}
            onChange={(e) => onChange(settingKey, e.target.value)}
            placeholder={setting.placeholder || setting.description}
            className="h-8 text-sm"
          />
        </div>
      );
  }
}

/**
 * A single expandable step card with reorder and delete controls.
 */
function StepCard({
  step,
  index,
  total,
  executorDef,
  onUpdate,
  onRemove,
  onMoveUp,
  onMoveDown,
}: StepCardProps) {
  const [expanded, setExpanded] = useState(false);
  const settingsSchema = executorDef?.settings_schema;
  const hasSettings = settingsSchema && Object.keys(settingsSchema).length > 0;

  const handleSettingChange = (key: string, value: any) => {
    const newSettings = { ...step.settings, [key]: value };
    onUpdate(index, { ...step, settings: newSettings });
  };

  const handleIdChange = (newId: string) => {
    onUpdate(index, { ...step, id: newId });
  };

  return (
    <Card className="border border-border">
      <Collapsible open={expanded} onOpenChange={setExpanded}>
        <div className="flex items-center gap-2 p-3">
          {/* Grip / index */}
          <div className="flex-shrink-0 text-muted-foreground">
            <GripVertical className="w-4 h-4" />
          </div>

          {/* Step number */}
          <Badge variant="outline" className="text-xs font-mono flex-shrink-0">
            {index + 1}
          </Badge>

          {/* Icon from executor */}
          {executorDef && (
            <div
              className={`${executorDef.color} text-white p-1 rounded flex-shrink-0`}
            >
              {executorDef.icon}
            </div>
          )}

          {/* Step ID + type */}
          <div className="flex-1 min-w-0">
            <div className="font-medium text-sm truncate">{step.id}</div>
            <div className="text-xs text-muted-foreground truncate">
              {executorDef?.name || step.type}
            </div>
          </div>

          {/* Reorder buttons */}
          <div className="flex items-center gap-0.5 flex-shrink-0">
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              disabled={index === 0}
              onClick={(e) => {
                e.stopPropagation();
                onMoveUp(index);
              }}
            >
              <ArrowUp className="h-3 w-3" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              disabled={index === total - 1}
              onClick={(e) => {
                e.stopPropagation();
                onMoveDown(index);
              }}
            >
              <ArrowDown className="h-3 w-3" />
            </Button>
          </div>

          {/* Delete */}
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 text-destructive hover:text-destructive flex-shrink-0"
            onClick={(e) => {
              e.stopPropagation();
              onRemove(index);
            }}
          >
            <X className="h-3 w-3" />
          </Button>

          {/* Expand toggle */}
          <CollapsibleTrigger asChild>
            <Button variant="ghost" size="icon" className="h-6 w-6 flex-shrink-0">
              {expanded ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
            </Button>
          </CollapsibleTrigger>
        </div>

        <CollapsibleContent>
          <div className="px-3 pb-3 pt-1 space-y-3 border-t border-border">
            {/* Step ID field */}
            <div className="space-y-0.5">
              <Label className="text-xs">Step ID</Label>
              <Input
                value={step.id}
                onChange={(e) => handleIdChange(e.target.value)}
                placeholder="Unique step identifier"
                className="h-8 text-sm"
              />
            </div>

            {/* Step type (read-only since it's chosen from the palette) */}
            <div className="space-y-0.5">
              <Label className="text-xs">Executor Type</Label>
              <div className="flex items-center gap-2 h-8 px-3 bg-muted rounded-md text-sm text-muted-foreground">
                {executorDef && (
                  <div
                    className={`${executorDef.color} text-white p-0.5 rounded`}
                  >
                    {executorDef.icon}
                  </div>
                )}
                <span className="truncate">{executorDef?.name || step.type}</span>
                <Badge variant="outline" className="text-[10px] ml-auto">
                  {step.type}
                </Badge>
              </div>
            </div>

            {/* Schema-driven settings */}
            {hasSettings ? (
              <div className="space-y-1">
                <div className="flex items-center gap-1 text-xs font-semibold text-muted-foreground">
                  <Settings className="w-3 h-3" />
                  Settings
                </div>
                <div className="grid grid-cols-2 gap-x-3 gap-y-2">
                  {Object.entries(settingsSchema).map(([key, schema]) => {
                    const setting = schema as ExecutorSetting;
                    const isFullWidth =
                      setting.ui_component === "textarea" ||
                      (setting.description && setting.description.length > 80);
                    return (
                      <div
                        key={key}
                        className={isFullWidth ? "col-span-2" : ""}
                      >
                        <StepSettingField
                          settingKey={key}
                          setting={setting}
                          value={step.settings?.[key] ?? setting.default ?? ""}
                          onChange={handleSettingChange}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground italic">
                No configurable settings for this executor type.
              </p>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}

/**
 * Add Step Palette — lets the user pick an executor type to add as a new step.
 */
function AddStepPalette({
  executors,
  onAdd,
  onCancel,
}: {
  executors: ExecutorWithUI[];
  onAdd: (executor: ExecutorWithUI) => void;
  onCancel: () => void;
}) {
  const [search, setSearch] = useState("");

  // Filter out control_flow and pipeline categories to avoid nesting issues
  const filteredExecutors = executors.filter((ex) => {
    const cat = ex.category.toLowerCase();
    if (cat === "pipeline" || cat === "control_flow") return false;
    if (!search) return true;
    return (
      ex.name.toLowerCase().includes(search.toLowerCase()) ||
      ex.id.toLowerCase().includes(search.toLowerCase()) ||
      ex.category.toLowerCase().includes(search.toLowerCase())
    );
  });

  // Group by category
  const grouped = filteredExecutors.reduce((acc, ex) => {
    const cat = ex.category.toLowerCase();
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(ex);
    return acc;
  }, {} as Record<string, ExecutorWithUI[]>);

  return (
    <Card className="border-2 border-dashed border-amber-400/50 p-3">
      <div className="flex items-center justify-between mb-2">
        <h5 className="text-xs font-semibold">Select Executor Type</h5>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onCancel}>
          <X className="h-3 w-3" />
        </Button>
      </div>
      <Input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search executors..."
        className="h-8 text-sm mb-2"
        autoFocus
      />
      <div className="max-h-[200px] overflow-y-auto space-y-2">
        {Object.entries(grouped).map(([category, execs]) => (
          <div key={category}>
            <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">
              {category}
            </div>
            <div className="space-y-0.5">
              {execs.map((ex) => (
                <Button
                  key={ex.id}
                  variant="ghost"
                  className="w-full justify-start gap-2 h-auto py-1.5 px-2 text-left"
                  onClick={() => onAdd(ex)}
                >
                  <div className={`${ex.color} text-white p-0.5 rounded flex-shrink-0`}>
                    {ex.icon}
                  </div>
                  <span className="text-xs flex-1 truncate">{ex.name}</span>
                </Button>
              ))}
            </div>
          </div>
        ))}
        {Object.keys(grouped).length === 0 && (
          <p className="text-xs text-muted-foreground text-center py-4">
            No executors found
          </p>
        )}
      </div>
    </Card>
  );
}

/**
 * StepListEditor — Phase 2 visual step editor for ForEachContentExecutor.
 *
 * Renders an ordered list of step cards, each expandable to edit settings
 * using schema-driven forms. Supports reordering, deletion, and adding
 * new steps from an executor palette.
 */
export function StepListEditor({
  steps,
  onChange,
  availableExecutors,
}: StepListEditorProps) {
  const [showPalette, setShowPalette] = useState(false);

  const handleAddStep = (executor: ExecutorWithUI) => {
    const newStepId = `${executor.id.replace(/_/g, "_")}_${steps.length + 1}`;
    const newStep: StepDefinition = {
      id: newStepId,
      type: executor.id,
      settings: {},
    };

    // Pre-populate defaults from schema
    if (executor.settings_schema) {
      Object.entries(executor.settings_schema).forEach(([key, schema]) => {
        const setting = schema as ExecutorSetting;
        if (setting.default !== undefined && setting.default !== null) {
          newStep.settings![key] = setting.default;
        }
      });
    }

    onChange([...steps, newStep]);
    setShowPalette(false);
  };

  const handleUpdateStep = (index: number, updatedStep: StepDefinition) => {
    const newSteps = [...steps];
    newSteps[index] = updatedStep;
    onChange(newSteps);
  };

  const handleRemoveStep = (index: number) => {
    onChange(steps.filter((_, i) => i !== index));
  };

  const handleMoveUp = (index: number) => {
    if (index <= 0) return;
    const newSteps = [...steps];
    [newSteps[index - 1], newSteps[index]] = [newSteps[index], newSteps[index - 1]];
    onChange(newSteps);
  };

  const handleMoveDown = (index: number) => {
    if (index >= steps.length - 1) return;
    const newSteps = [...steps];
    [newSteps[index], newSteps[index + 1]] = [newSteps[index + 1], newSteps[index]];
    onChange(newSteps);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label className="text-xs font-semibold">
          Steps ({steps.length})
        </Label>
      </div>

      {/* Step cards */}
      {steps.length > 0 ? (
        <div className="space-y-2">
          {steps.map((step, index) => {
            const executorDef = availableExecutors.find(
              (ex) => ex.id === step.type
            );
            return (
              <div key={index}>
                <StepCard
                  step={step}
                  index={index}
                  total={steps.length}
                  executorDef={executorDef}
                  onUpdate={handleUpdateStep}
                  onRemove={handleRemoveStep}
                  onMoveUp={handleMoveUp}
                  onMoveDown={handleMoveDown}
                />
                {/* Arrow connector between steps */}
                {index < steps.length - 1 && (
                  <div className="flex justify-center py-1">
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="border border-dashed border-border rounded-lg p-6 text-center">
          <Settings className="w-6 h-6 text-muted-foreground mx-auto mb-2" />
          <p className="text-xs text-muted-foreground">No steps defined yet</p>
          <p className="text-[10px] text-muted-foreground mt-1">
            Add steps to define the per-item processing chain
          </p>
        </div>
      )}

      {/* Add Step */}
      {showPalette ? (
        <AddStepPalette
          executors={availableExecutors}
          onAdd={handleAddStep}
          onCancel={() => setShowPalette(false)}
        />
      ) : (
        <Button
          variant="outline"
          className="w-full gap-2 border-dashed"
          onClick={() => setShowPalette(true)}
        >
          <Plus className="w-4 h-4" />
          Add Step
        </Button>
      )}
    </div>
  );
}
