import { memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const ExecutorNode = memo(({ data }: NodeProps) => {
  const { label, executor, config } = data;
  
  return (
    <Card className="min-w-[220px] shadow-lg hover:shadow-xl transition-all duration-300 group">
      <Handle 
        type="target" 
        position={Position.Top} 
        className="w-3 h-3 !bg-secondary"
      />
      
      <div className="p-4">
        <div className="flex items-start gap-3 mb-3">
          <div className={`${executor.color} text-white p-2.5 rounded-xl group-hover:scale-110 transition-transform`}>
            {executor.icon}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-foreground text-sm truncate">{label}</h4>
            <Badge variant="outline" className="text-xs mt-1 capitalize">
              {executor.category}
            </Badge>
          </div>
        </div>
        
        {config && Object.keys(config).length > 1 && (
          <div className="text-xs text-muted-foreground space-y-1 border-t border-border pt-2">
            {config.description && (
              <p className="truncate">{config.description}</p>
            )}
          </div>
        )}
      </div>
      
      <Handle 
        type="source" 
        position={Position.Bottom} 
        className="w-3 h-3 !bg-secondary"
      />
    </Card>
  );
});

ExecutorNode.displayName = "ExecutorNode";
