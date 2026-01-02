import { useEffect, useState, useRef } from 'react';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  AlertCircle,
  ChevronRight,
  X,
  Activity,
  FileOutput,
} from 'lucide-react';
import type { PipelineExecution, ExecutorOutput, PipelineExecutionEvent } from '@/types/components';
import { getExecutionStatus, streamExecutionEvents } from '@/lib/api/pipelinesApi';

interface PipelineExecutionStatusProps {
  executionId: string;
  onClose: () => void;
}

const statusIcons = {
  pending: <Clock className="w-4 h-4 text-gray-400" />,
  running: <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />,
  completed: <CheckCircle2 className="w-4 h-4 text-green-500" />,
  failed: <XCircle className="w-4 h-4 text-red-500" />,
  skipped: <AlertCircle className="w-4 h-4 text-yellow-500" />,
  cancelled: <XCircle className="w-4 h-4 text-orange-500" />,
};

const statusColors = {
  pending: 'bg-gray-100 text-gray-800',
  running: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  skipped: 'bg-yellow-100 text-yellow-800',
  cancelled: 'bg-orange-100 text-orange-800',
};

export function PipelineExecutionStatus({ executionId, onClose }: PipelineExecutionStatusProps) {
  const [execution, setExecution] = useState<PipelineExecution | null>(null);
  const [selectedExecutor, setSelectedExecutor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isTerminalStateRef = useRef(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const isInitializingRef = useRef(false);

  useEffect(() => {
    // Prevent multiple simultaneous initializations or if already have an event source
    if (isInitializingRef.current || eventSourceRef.current || isTerminalStateRef.current) {
      return;
    }

    const init = async () => {
      isInitializingRef.current = true;

      try {
        const data = await getExecutionStatus(executionId);
        setExecution(data);
        setLoading(false);
        
        // Check if already in terminal state
        if (['completed', 'failed', 'cancelled'].includes(data.status)) {
          isTerminalStateRef.current = true;
          isInitializingRef.current = false;
          // Don't set up stream if already completed
          return;
        }

        // Double-check we don't already have an event source
        if (eventSourceRef.current || isTerminalStateRef.current) {
          isInitializingRef.current = false;
          return;
        }

        // Only set up event stream if execution is still active
        eventSourceRef.current = streamExecutionEvents(
          executionId,
          (event: PipelineExecutionEvent) => {
            setExecution((prev) => {
              if (!prev) return prev;

              // Update executor outputs based on event
              const updatedOutputs = { ...prev.executor_outputs };
              if (event.executor_id) {
                const status = 
                  event.event_type === 'ExecutorCompletedEvent' ? 'completed' :
                  event.event_type === 'ExecutorInvokedEvent' ? 'running' :
                  event.event_type === 'ExecutorFailedEvent' ? 'failed' :
                  updatedOutputs[event.executor_id]?.status || 'pending';

                updatedOutputs[event.executor_id] = {
                  executor_id: event.executor_id,
                  timestamp: event.timestamp,
                  status: status as any,
                  data: event.data,
                  error: event.error,
                };
              }

              // Update overall status
              const overallStatus = 
                event.event_type === 'WorkflowStatusEvent' && event?.additional_info?.state === "IN PROGRESS" ? 'running' :
                event.event_type === 'WorkflowFailedEvent' ? 'failed' :
                event.event_type === 'WorkflowStatusEvent' && event?.additional_info?.state === "IDLE" ? 'completed' :
                prev.status;

              // Check if we've reached a terminal state
              if (['completed', 'failed', 'cancelled'].includes(overallStatus)) {
                isTerminalStateRef.current = true;
                // Close the event source when reaching terminal state
                if (eventSourceRef.current) {
                  eventSourceRef.current.close();
                  eventSourceRef.current = null;
                }
              }

              return {
                ...prev,
                status: overallStatus as any,
                executor_outputs: updatedOutputs,
                events: [...(prev.events || []), event],
              };
            });
          }
        );

        isInitializingRef.current = false;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch execution status');
        setLoading(false);
        isInitializingRef.current = false;
      }
    };

    init();

    return () => {
      // Cleanup: close event source if exists
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      // Don't reset terminal state or initialization flag in cleanup
      // to prevent re-initialization on Strict Mode remount
    };
  }, [executionId]);

  if (loading) {
    return (
      <Dialog open onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Loading Execution Status...</DialogTitle>
          </DialogHeader>
          <div className="flex items-center justify-center p-8">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (error || !execution) {
    return (
      <Dialog open onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Error</DialogTitle>
          </DialogHeader>
          <div className="text-red-500 p-4">
            {error || 'Failed to load execution status'}
          </div>
          <div className="flex justify-end">
            <Button onClick={onClose}>Close</Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  const executorOutputs = Object.values(execution.executor_outputs || {});
  const selectedOutput = selectedExecutor 
    ? execution.executor_outputs?.[selectedExecutor] 
    : null;
  const events = execution.events || [];

  const getEventIcon = (eventType: string) => {
    if (eventType.includes('Completed')) {
      return <CheckCircle2 className="w-4 h-4 text-green-500" />;
    }
    if (eventType.includes('Invoked') || eventType.includes('Started')) {
      return <Activity className="w-4 h-4 text-blue-500" />;
    }
    if (eventType.includes('Output')) {
      return <FileOutput className="w-4 h-4 text-blue-500" />;
    }
    if (eventType === 'error') {
      return <XCircle className="w-4 h-4 text-red-500" />;
    }
    return <AlertCircle className="w-4 h-4 text-gray-500" />;
  };

  return (
    <>
      <Dialog open onOpenChange={onClose}>
        <DialogContent className="max-w-4xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <span>Pipeline Execution: {execution.pipeline_name}</span>
              <Badge className={statusColors[execution.status]}>
                {execution.status.toUpperCase()}
              </Badge>
            </DialogTitle>
            <DialogDescription>
              Execution ID: {execution.id}
              {execution.started_at && (
                <span className="ml-4">
                  Started: {new Date(execution.started_at).toLocaleString()}
                </span>
              )}
              {execution.duration_seconds && (
                <span className="ml-4">
                  Duration: {execution.duration_seconds.toFixed(2)}s
                </span>
              )}
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4">
            {/* Overall Status */}
            {execution.error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <XCircle className="w-5 h-5 text-red-500 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-red-900">Error</h4>
                    <p className="text-sm text-red-700">{execution.error?.slice(0, 200)}...</p>
                  </div>
                </div>
              </div>
            )}

            {/* Tabs for Executors and Events */}
            <Tabs defaultValue="executors" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="executors">
                  Executor Status ({executorOutputs.length})
                </TabsTrigger>
                <TabsTrigger value="events">
                  Events ({events.length})
                </TabsTrigger>
              </TabsList>

              {/* Executor Status Tab */}
              <TabsContent value="executors" className="mt-4">
                <ScrollArea className="h-[400px] border rounded-lg">
                  <div className="p-4 space-y-2">
                    {executorOutputs.length === 0 ? (
                      <p className="text-sm text-gray-500 text-center py-8">
                        No executor outputs yet
                      </p>
                    ) : (
                      executorOutputs.map((output) => (
                        <button
                          key={output.executor_id}
                          onClick={() => setSelectedExecutor(output.executor_id)}
                          className="w-full flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors text-left"
                        >
                          <div className="flex items-center gap-3 flex-1">
                            {statusIcons[output.status]}
                            <div className="flex-1">
                              <div className="font-medium text-sm">
                                {output.executor_id}
                              </div>
                              <div className="text-xs text-gray-500">
                                {new Date(output.timestamp).toLocaleTimeString()}
                              </div>
                            </div>
                            <Badge className={`${statusColors[output.status]} text-xs`}>
                              {output.status}
                            </Badge>
                          </div>
                          <ChevronRight className="w-4 h-4 text-gray-400" />
                        </button>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>

              {/* Events Tab */}
              <TabsContent value="events" className="mt-4">
                <ScrollArea className="h-[400px] border rounded-lg">
                  <div className="p-4 space-y-2">
                    {events.length === 0 ? (
                      <p className="text-sm text-gray-500 text-center py-8">
                        No events yet
                      </p>
                    ) : (
                      events.map((event, index) => (
                        <div
                          key={`${event.timestamp}-${index}`}
                          className="p-3 rounded-lg border bg-white overflow-hidden"
                        >
                          <div className="flex items-start gap-3 min-w-0">
                            {getEventIcon(event.event_type)}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-sm">
                                  {event.event_type}
                                </span>
                                {event.executor_id && (
                                  <Badge variant="outline" className="text-xs">
                                    {event.executor_id}
                                  </Badge>
                                )}
                              </div>
                              <div className="text-xs text-gray-500 mb-2">
                                {new Date(event.timestamp).toLocaleString()}
                              </div>
                              {event.error && (
                                <div className="bg-red-50 border border-red-200 rounded p-3 mb-2 w-full">
                                  <div className="flex items-start gap-2 mb-2">
                                    <XCircle className="w-4 h-4 text-red-500 mt-0.5" />
                                    <h5 className="font-semibold text-xs text-red-900">Error Details</h5>
                                  </div>
                                  <div className="space-y-2 w-full">
                                    {(() => {
                                      try {
                                        const errorObj = typeof event.error === 'string' 
                                          ? JSON.parse(event.error) 
                                          : event.error;
                                        
                                        return (
                                          <>
                                            {/* Error Type */}
                                            {errorObj.error_type && (
                                              <div className="w-full">
                                                <label className="block text-xs font-semibold text-red-900 mb-1">
                                                  Error Type
                                                </label>
                                                <div className="w-full p-2 bg-white border border-red-300 rounded text-xs font-mono text-red-700">
                                                  {errorObj.error_type}
                                                </div>
                                              </div>
                                            )}

                                            {/* Error Message */}
                                            {errorObj.message && (
                                              <div className="w-full">
                                                <label className="block text-xs font-semibold text-red-900 mb-1">
                                                  Message
                                                </label>
                                                <div className="w-full p-2 bg-white border border-red-300 rounded text-xs font-mono text-red-700 whitespace-pre-wrap">
                                                  {errorObj.message}
                                                </div>
                                              </div>
                                            )}

                                            {/* Stack Trace / Traceback */}
                                            {(errorObj.traceback || errorObj.stack) && (
                                              <div className="w-full">
                                                <label className="block text-xs font-semibold text-red-900 mb-1">
                                                  Stack Trace
                                                </label>
                                                <details className="w-full">
                                                  <summary className="cursor-pointer text-xs text-red-700 hover:text-red-900 mb-1">
                                                    View stack trace
                                                  </summary>
                                                  <textarea
                                                    className="w-full h-[200px] p-2 text-xs font-mono border border-red-300 rounded resize-none bg-white text-red-600"
                                                    disabled
                                                    value={errorObj.traceback || errorObj.stack}
                                                  />
                                                </details>
                                              </div>
                                            )}

                                            {/* Full Error Object (if structure is different) */}
                                            {!errorObj.error_type && !errorObj.message && !errorObj.traceback && !errorObj.stack && (
                                              <div className="w-full">
                                                <div className="w-full p-2 bg-white border border-red-300 rounded text-xs font-mono text-red-700 whitespace-pre-wrap max-h-[150px] overflow-auto">
                                                  {typeof errorObj === 'string' ? errorObj : JSON.stringify(errorObj, null, 2)}
                                                </div>
                                              </div>
                                            )}
                                          </>
                                        );
                                      } catch (e) {
                                        // If error is not JSON, just display it as string
                                        return (
                                          <div className="w-full p-2 bg-white border border-red-300 rounded text-xs font-mono text-red-700 whitespace-pre-wrap">
                                            {event.error}
                                          </div>
                                        );
                                      }
                                    })()}
                                  </div>
                                </div>
                              )}
                              {event.data && (
                                <details className="text-xs overflow-hidden">
                                  <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                                    View data
                                  </summary>
                                  <textarea
                                    className="mt-2 p-2 bg-gray-50 rounded text-xs font-mono w-full resize-none border"
                                    rows={10}
                                    disabled
                                    value={JSON.stringify(event.data, null, 2)}
                                  />
                                </details>
                              )}
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>
            </Tabs>

            {/* Actions */}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={onClose}>
                Close
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Executor Output Dialog */}
      {selectedOutput && (
        <Dialog open onOpenChange={() => setSelectedExecutor(null)}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-scroll">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-3">
                <span>{selectedOutput.executor_id}</span>
                <Badge className={statusColors[selectedOutput.status]}>
                  {selectedOutput.status.toUpperCase()}
                </Badge>
              </DialogTitle>
              <DialogDescription>
                Timestamp: {new Date(selectedOutput.timestamp).toLocaleString()}
                {selectedOutput.duration_ms && (
                  <span className="ml-4">
                    Duration: {selectedOutput.duration_ms.toFixed(2)}ms
                  </span>
                )}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              {/* Error */}
              {selectedOutput.error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 w-full">
                  <div className="flex items-start gap-2 mb-3">
                    <XCircle className="w-5 h-5 text-red-500 mt-0.5" />
                    <h4 className="font-semibold text-red-900">Error Details</h4>
                  </div>
                  <div className="space-y-3 w-full">
                    {(() => {
                      const errorObj = typeof selectedOutput.error === 'string' 
                        ? JSON.parse(selectedOutput.error) 
                        : selectedOutput.error;
                      
                      return (
                        <>
                          {/* Error Type */}
                          {errorObj.error_type && (
                            <div className="w-full">
                              <label className="block text-xs font-semibold text-red-900 mb-1">
                                Error Type
                              </label>
                              <div className="w-full p-3 bg-white border border-red-300 rounded text-sm font-mono text-red-700">
                                {errorObj.error_type}
                              </div>
                            </div>
                          )}

                          {/* Error Message */}
                          {errorObj.message && (
                            <div className="w-full">
                              <label className="block text-xs font-semibold text-red-900 mb-1">
                                Message
                              </label>
                              <div className="w-full p-3 bg-white border border-red-300 rounded text-sm font-mono text-red-700 whitespace-pre-wrap">
                                {errorObj.message}
                              </div>
                            </div>
                          )}

                          {/* Stack Trace / Traceback */}
                          {(errorObj.traceback || errorObj.stack) && (
                            <div className="w-full">
                              <label className="block text-xs font-semibold text-red-900 mb-1">
                                Stack Trace
                              </label>
                              <textarea
                                className="w-full h-[300px] p-3 text-xs font-mono border border-red-300 rounded resize-none bg-white text-red-600"
                                disabled
                                value={errorObj.traceback || errorObj.stack}
                              />
                            </div>
                          )}

                          {/* Full Error Object (if structure is different) */}
                          {!errorObj.type && !errorObj.message && !errorObj.traceback && !errorObj.stack && (
                            <div className="w-full">
                              <textarea
                                className="w-full h-[300px] p-3 text-xs font-mono border border-red-300 rounded resize-none bg-white text-red-700"
                                disabled
                                value={JSON.stringify(errorObj, null, 2)}
                              />
                            </div>
                          )}
                        </>
                      );
                    })()}
                  </div>
                </div>
              )}

              {/* Output Data */}
              <div className="overflow-hidden w-full">
                <h4 className="text-sm font-semibold mb-2">Output Data</h4>
                <textarea
                  className="w-full h-[400px] p-4 text-xs font-mono border rounded-lg resize-none bg-white"
                  disabled
                  value={selectedOutput.data 
                    ? JSON.stringify(selectedOutput.data, null, 2)
                    : 'No output data available'}
                />
              </div>

              {/* Actions */}
              <div className="flex justify-end">
                <Button onClick={() => setSelectedExecutor(null)}>
                  Close
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}
