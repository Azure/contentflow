import { memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { X, BanIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

export const ExecutorNode = memo(({ data }: NodeProps) => {
  const { label, executor, config, onDelete } = data;
  const description = config?.description || executor.description;
  const disabled = config?.settings?.enabled === false;

  return (
    <Card className={`w-[220px] shadow-lg hover:shadow-xl transition-all duration-300 group relative ${disabled ? 'bg-gray-100 opacity-70' : ''}`}>
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
      
      <div className="p-4">
        <div className="flex items-start gap-3 mb-3">
          <div className={`${executor.color} text-white p-2.5 rounded-xl group-hover:scale-110 transition-transform`}>
            {executor.icon}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1">
              <h4 className="font-semibold text-foreground text-sm truncate">{label}</h4>
              {disabled && (
                <BanIcon className="h-3.5 w-3.5 text-gray-500 flex-shrink-0" />
              )}
            </div>
            <Badge variant="outline" className="text-xs mt-1 capitalize">
              {executor.category}
            </Badge>
          </div>
        </div>
        
        <div className="text-xs text-muted-foreground space-y-1 border-t border-border pt-2">
            {description && (
              <p className="truncate" title={description}>{description}</p>
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

ExecutorNode.displayName = "ExecutorNode";
