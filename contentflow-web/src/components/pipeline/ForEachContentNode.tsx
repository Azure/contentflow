import { memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Repeat, X, ChevronRight } from "lucide-react";

export const ForEachContentNode = memo(({ data }: NodeProps) => {
  const { label, config, onDelete, executor } = data;
  const steps = config?.settings?.steps || [];
  const maxConcurrent = config?.settings?.max_concurrent || 5;
  const continueOnError = config?.settings?.continue_on_error;
  const description = config?.description || executor?.description;

  return (
    <Card className="shadow-lg hover:shadow-xl transition-all duration-300 border-2 border-amber-400/40 min-w-[300px] relative group">
      <Handle
        type="target"
        position={Position.Top}
        id="target-top"
        className="w-3 h-3 !bg-secondary"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="target-left"
        className="w-3 h-3 !bg-secondary"
      />

      {/* Delete Button */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute -top-2 -right-2 h-6 w-6 rounded-full bg-destructive/90 hover:bg-destructive text-white opacity-0 group-hover:opacity-100 transition-opacity z-10"
        onClick={(e) => {
          e.stopPropagation();
          onDelete?.();
        }}
      >
        <X className="h-3 w-3" />
      </Button>

      <div className="p-4 bg-gradient-to-br from-amber-500/10 to-transparent">
        {/* Header */}
        <div className="flex items-start gap-3 mb-3">
          <div className="bg-amber-500 text-white p-2.5 rounded-xl group-hover:scale-110 transition-transform">
            <Repeat className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-foreground text-sm truncate">
              {label}
            </h4>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <Badge className="text-xs bg-amber-500/20 text-amber-700 hover:bg-amber-500/30">
                For Each Content
              </Badge>
              <Badge variant="outline" className="text-xs">
                {maxConcurrent} concurrent · {steps.length} step
                {steps.length !== 1 ? "s" : ""}
              </Badge>
              {continueOnError === false && (
                <Badge variant="outline" className="text-xs text-red-600 border-red-300">
                  fail-fast
                </Badge>
              )}
            </div>
          </div>
        </div>

        {description && (
          <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
            {description.length > 60 ? description.slice(0, 60) + "..." : description}
          </p>
        )}

        {/* Inline step chain */}
        <div className="border border-dashed border-amber-400/50 rounded-lg p-3 bg-background/30">
          {steps.length > 0 ? (
            <div className="flex flex-wrap items-center gap-1.5">
              {steps.map((step: any, index: number) => (
                <div key={step.id || index} className="flex items-center gap-1">
                  <Badge
                    variant="secondary"
                    className="text-[10px] px-1.5 py-0.5"
                    title={`${step.type} (${step.id})`}
                  >
                    {step.id}
                  </Badge>
                  {index < steps.length - 1 && (
                    <ChevronRight className="w-3 h-3 text-muted-foreground" />
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-2">
              <Repeat className="w-4 h-4 text-muted-foreground mx-auto mb-1" />
              <p className="text-[10px] text-muted-foreground">
                No steps defined
              </p>
              <p className="text-[9px] text-muted-foreground mt-0.5">
                Double-click to configure
              </p>
            </div>
          )}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        id="source-bottom"
        className="w-3 h-3 !bg-secondary"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="source-right"
        className="w-3 h-3 !bg-secondary"
      />
    </Card>
  );
});

ForEachContentNode.displayName = "ForEachContentNode";
