import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  AlertCircle,
  ChevronRight,
} from 'lucide-react';
import { toast } from 'sonner';
import type { PipelineExecution } from '@/types/components';
import { getExecutionHistory } from '@/lib/api/pipelinesApi';
import { PipelineExecutionStatus } from './PipelineExecutionStatus';

interface PipelineExecutionsListDialogProps {
  pipelineId: string;
  pipelineName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const statusIcons = {
  pending: <Clock className="w-4 h-4 text-gray-400" />,
  running: <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />,
  completed: <CheckCircle2 className="w-4 h-4 text-green-500" />,
  failed: <XCircle className="w-4 h-4 text-red-500" />,
  cancelled: <XCircle className="w-4 h-4 text-orange-500" />,
};

const statusColors = {
  pending: 'bg-gray-100 text-gray-800',
  running: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-orange-100 text-orange-800',
};

export function PipelineExecutionsListDialog({
  pipelineId,
  pipelineName,
  open,
  onOpenChange,
}: PipelineExecutionsListDialogProps) {
  const [executions, setExecutions] = useState<PipelineExecution[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);

  useEffect(() => {
    if (open && pipelineId) {
      loadExecutions();
    }
  }, [open, pipelineId]);

  const loadExecutions = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch last 10 executions
      const data = await getExecutionHistory(pipelineId, 10);
      setExecutions(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load execution history';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(2)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Execution History: {pipelineName}</DialogTitle>
            <DialogDescription>
              Last 10 pipeline executions
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <XCircle className="w-5 h-5 text-red-500 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-red-900">Error</h4>
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                </div>
              </div>
            ) : executions.length === 0 ? (
              <div className="text-center py-12">
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-500">No executions found for this pipeline</p>
              </div>
            ) : (
              <ScrollArea className="h-[500px] border rounded-lg">
                <div className="p-4 space-y-2">
                  {executions.map((execution) => (
                    <button
                      key={execution.id}
                      onClick={() => setSelectedExecutionId(execution.id)}
                      className="w-full flex items-center justify-between p-4 rounded-lg border hover:bg-gray-50 transition-colors text-left"
                    >
                      <div className="flex items-center gap-4 flex-1">
                        {statusIcons[execution.status]}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-sm truncate">
                              {execution.id}
                            </span>
                            <Badge className={`${statusColors[execution.status]} text-xs`}>
                              {execution.status}
                            </Badge>
                          </div>
                          <div className="text-xs text-gray-500 space-y-1">
                            {execution.started_at && (
                              <div>
                                Started: {new Date(execution.started_at).toLocaleString()}
                              </div>
                            )}
                            {execution.completed_at && (
                              <div>
                                Completed: {new Date(execution.completed_at).toLocaleString()}
                              </div>
                            )}
                            {execution.duration_seconds !== undefined && (
                              <div>
                                Duration: {formatDuration(execution.duration_seconds)}
                              </div>
                            )}
                            {execution.error && (
                              <div className="text-red-600 truncate">
                                Error: {execution.error?.slice(0, 100)}...
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
                    </button>
                  ))}
                </div>
              </ScrollArea>
            )}

            {/* Actions */}
            <div className="flex justify-between items-center">
              <Button
                variant="outline"
                onClick={loadExecutions}
                disabled={loading}
                className="gap-2"
              >
                <Loader2 className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Close
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Execution Details Dialog */}
      {selectedExecutionId && (
        <PipelineExecutionStatus
          executionId={selectedExecutionId}
          onClose={() => setSelectedExecutionId(null)}
        />
      )}
    </>
  );
}
