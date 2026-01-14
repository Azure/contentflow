import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Workflow } from "lucide-react";
import { getPipelines } from "@/lib/api/pipelinesApi";
import type { Pipeline } from "@/types/components";

export const PipelinesTable = () => {
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const loadPipelines = async () => {
      try {
        setIsLoading(true);
        const data = await getPipelines();
        setPipelines(data);
        setError(null);
      } catch (err) {
        console.error("Error loading pipelines:", err);
        setError("Failed to load pipelines");
      } finally {
        setIsLoading(false);
      }
    };

    loadPipelines();
  }, []);

  const handleSelectPipeline = (pipelineId: string) => {
    // Navigate to pipeline view with the selected pipeline
    navigate(`/?view=pipeline&pipeline=${pipelineId}`);
  };

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center text-destructive h-64 flex items-center justify-center">
          <p>{error}</p>
        </div>
      </Card>
    );
  }

  if (pipelines.length === 0) {
    return (
      <Card className="p-6">
        <div className="text-center text-muted-foreground h-64 flex flex-col items-center justify-center gap-3">
          <Workflow className="w-8 h-8 opacity-50" />
          <p>No pipelines available yet</p>
          <p className="text-sm">Create your first pipeline to get started</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden flex flex-col">
      <div className="px-4 py-2 border-b bg-violet-700/10">
        <div className="flex items-center gap-2">
          <Workflow className="w-4 h-4 text-secondary" />
          <h3 className="font-semibold text-sm">Available Pipelines</h3>
          <span className="ml-auto text-xs text-muted-foreground">{pipelines.length} pipeline{pipelines.length !== 1 ? 's' : ''}</span>
        </div>
      </div>
      <div className="overflow-x-auto flex-1 max-h-72">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b bg-muted/30">
              <th className="text-left px-3 py-2 font-semibold text-muted-foreground">Name</th>
              {/* <th className="text-left px-3 py-2 font-semibold text-muted-foreground">Description</th> */}
              <th className="text-left px-3 py-2 font-semibold text-muted-foreground">Updated</th>
              <th className="text-right px-3 py-2 font-semibold text-muted-foreground">Action</th>
            </tr>
          </thead>
          <tbody>
            {pipelines.map((pipeline) => (
              <tr key={pipeline.id} className="border-b hover:bg-muted/30 transition-colors">
                <td className="px-3 py-1.5 font-medium text-foreground text-left truncate" title={pipeline.name}>{pipeline.name.length > 25 ? pipeline.name.slice(0, 25) + "..." : pipeline.name}</td>
                {/* <td className="px-3 py-1.5 text-muted-foreground truncate">{pipeline.description || "-"}</td> */}
                <td className="px-3 py-1.5 text-muted-foreground">
                  {new Date(pipeline.updated_at).toLocaleDateString() + " " + new Date(pipeline.updated_at).toLocaleTimeString()}
                </td>
                <td className="px-3 py-1.5 text-right">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleSelectPipeline(pipeline.id)}
                    className="hover:bg-primary/10"
                  >
                    Open
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
