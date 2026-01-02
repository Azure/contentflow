import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Play,
  RefreshCw,
  Eye,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Calendar,
} from "lucide-react";
import { toast } from "sonner";
import { getExecutionHistory, executePipeline } from "@/lib/api/pipelinesApi";
import type { PipelineExecution } from "@/types/components";

interface VaultExecutionsViewProps {
  vaultId: string;
  pipelineId: string;
}

export const VaultExecutionsView = ({
  vaultId,
  pipelineId,
}: VaultExecutionsViewProps) => {
  const [executions, setExecutions] = useState<PipelineExecution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExecuting, setIsExecuting] = useState(false);

  useEffect(() => {
    loadExecutions();
  }, [pipelineId]);

  const loadExecutions = async () => {
    setIsLoading(true);
    try {
      const data = await getExecutionHistory(pipelineId, 50);
      setExecutions(data);
    } catch (error) {
      console.error("Error loading executions:", error);
      toast.error("Failed to load executions");
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecutePipeline = async () => {
    setIsExecuting(true);
    try {
      const result = await executePipeline(pipelineId, { vault_id: vaultId });
      toast.success(`Pipeline execution started: ${result.execution_id}`);
      // Refresh executions after a short delay
      setTimeout(() => loadExecutions(), 1000);
    } catch (error) {
      console.error("Error executing pipeline:", error);
      toast.error("Failed to execute pipeline");
    } finally {
      setIsExecuting(false);
    }
  };

  const handleViewExecution = (executionId: string) => {
    // Navigate to execution detail view (implement as needed)
    toast.info(`View execution: ${executionId}`);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-red-500" />;
      case "running":
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
      completed: "default",
      failed: "destructive",
      running: "secondary",
      pending: "outline",
      cancelled: "outline",
    };

    return (
      <Badge variant={variants[status] || "outline"} className="gap-1">
        {getStatusIcon(status)}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return "N/A";
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Pipeline Executions</h2>
          <p className="text-muted-foreground">
            View and manage pipeline executions for this vault
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={loadExecutions}
            disabled={isLoading}
            className="gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
          <Button
            onClick={handleExecutePipeline}
            disabled={isExecuting}
            className="gap-2"
          >
            <Play className="w-4 h-4" />
            {isExecuting ? "Executing..." : "Execute Pipeline"}
          </Button>
        </div>
      </div>

      {executions.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <Calendar className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-xl font-semibold mb-2">No executions yet</h3>
            <p className="text-muted-foreground mb-4">
              Execute the pipeline to start processing content for this vault
            </p>
            <Button onClick={handleExecutePipeline} disabled={isExecuting} className="gap-2">
              <Play className="w-4 h-4" />
              Execute Pipeline
            </Button>
          </div>
        </Card>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Execution ID</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {executions.map((execution) => (
                <TableRow key={execution.id}>
                  <TableCell className="font-mono text-sm">
                    {execution.id.substring(0, 8)}...
                  </TableCell>
                  <TableCell>{getStatusBadge(execution.status)}</TableCell>
                  <TableCell>{formatDate(execution.started_at)}</TableCell>
                  <TableCell>{formatDuration(execution.duration_seconds)}</TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewExecution(execution.id)}
                      className="gap-2"
                    >
                      <Eye className="w-4 h-4" />
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
};
