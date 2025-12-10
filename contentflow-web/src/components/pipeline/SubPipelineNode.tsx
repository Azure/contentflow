import { memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Workflow, ExternalLink } from "lucide-react";


export const SubPipelineNode = ({ data, id }: NodeProps) => {
  const { label, config, selectedPipelineId, savedPipelines = [] } = data;

  // Find the selected pipeline
  const selectedPipeline = savedPipelines.find((p: any) => p.id === selectedPipelineId);
  const executorCount = selectedPipeline ? selectedPipeline.nodes.length : 0;


  return (
    <Card className="shadow-lg hover:shadow-xl transition-all duration-300 border-2 border-secondary/30 min-w-[260px]">
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
            <div className="flex items-center gap-2 mt-1">
              <Badge className="text-xs bg-secondary/20 text-secondary hover:bg-secondary/30">
                Sub-Pipeline
              </Badge>
              {executorCount > 0 && (
                <Badge variant="outline" className="text-xs">
                  {executorCount} executor{executorCount !== 1 ? 's' : ''}
                </Badge>
              )}
            </div>
          </div>
        </div>
        
        {config?.description && (
          <p className="text-xs text-muted-foreground mb-3 line-clamp-2">
            {config.description}
          </p>
        )}

        {/* Selected Pipeline Display */}
        <div className="border border-border rounded-lg p-3 bg-background/30">
          {selectedPipeline ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <ExternalLink className="w-3.5 h-3.5 text-secondary" />
                <p className="text-xs font-medium text-foreground">{selectedPipeline.name}</p>
              </div>
              {selectedPipeline.description && (
                <p className="text-[10px] text-muted-foreground line-clamp-2">
                  {selectedPipeline.description}
                </p>
              )}
              {executorCount > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {selectedPipeline.nodes.slice(0, 3).map((node: any) => (
                    <Badge key={node.id} variant="secondary" className="text-[10px] px-1.5 py-0.5">
                      {node.data.label}
                    </Badge>
                  ))}
                  {executorCount > 3 && (
                    <Badge variant="outline" className="text-[10px] px-1.5 py-0.5">
                      +{executorCount - 3} more
                    </Badge>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-2">
              <Workflow className="w-4 h-4 text-muted-foreground mx-auto mb-1" />
              <p className="text-[10px] text-muted-foreground">No pipeline selected</p>
              <p className="text-[9px] text-muted-foreground mt-0.5">Double-click to select</p>
            </div>
          )}
        </div>
      </div>
      
      <Handle 
        type="source" 
        position={Position.Bottom} 
        className="w-3 h-3 !bg-secondary"
      />
    </Card>
  );
};

SubPipelineNode.displayName = "SubPipelineNode";