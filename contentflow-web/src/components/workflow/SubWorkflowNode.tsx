import { memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Workflow } from "lucide-react";

export const SubWorkflowNode = memo(({ data }: NodeProps) => {
  const { label, config } = data;
  
  return (
    <Card className="min-w-[240px] shadow-lg hover:shadow-xl transition-all duration-300 border-2 border-secondary/30">
      <Handle 
        type="target" 
        position={Position.Top} 
        className="w-3 h-3 !bg-secondary"
      />
      
      <div className="p-4 bg-gradient-to-br from-secondary/10 to-transparent">
        <div className="flex items-start gap-3 mb-3">
          <div className="bg-gradient-secondary text-white p-2.5 rounded-xl">
            <Workflow className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-foreground text-sm truncate">{label}</h4>
            <Badge className="text-xs mt-1 bg-secondary/20 text-secondary hover:bg-secondary/30">
              Sub-Workflow
            </Badge>
          </div>
        </div>
        
        {config?.steps && (
          <div className="text-xs text-muted-foreground">
            <span className="font-medium">{config.steps} nested steps</span>
          </div>
        )}
        
        {config?.description && (
          <p className="text-xs text-muted-foreground mt-2 line-clamp-2">
            {config.description}
          </p>
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

SubWorkflowNode.displayName = "SubWorkflowNode";