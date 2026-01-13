import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Calendar,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  Eye,
  Copy,
  TableOfContents
} from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { getVaultExecutions, getVaultCrawlCheckpoints } from "@/lib/api/vaultsApi";
import type { VaultExecution, VaultCrawlCheckpoint, Vault } from "@/types/components";

interface VaultExecutionsViewProps {
  vault: Vault;
}

export const VaultExecutionsView = ({
  vault,
}: VaultExecutionsViewProps) => {
  const [executions, setExecutions] = useState<VaultExecution[]>([]);
  const [crawlCheckpoints, setCrawlCheckpoints] = useState<VaultCrawlCheckpoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [selectedExecution, setSelectedExecution] = useState<VaultExecution | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedRange, setSelectedRange] = useState<string>("all");
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    loadData();
  }, [vault]);

  useEffect(() => {
    if (selectedRange !== "custom") {
      loadData();
    }
  }, [selectedRange]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      loadData();
    }, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      // Calculate date range based on selected range
      let dateRangeParams: { start_date?: string; end_date?: string } = {};
      const now = new Date();

      if (selectedRange !== "all") {
        const ranges: Record<string, number> = {
          "15min": 15 * 60 * 1000,
          "30min": 30 * 60 * 1000,
          "1hour": 60 * 60 * 1000,
          "4hours": 4 * 60 * 60 * 1000,
          "1day": 24 * 60 * 60 * 1000,
          "7days": 7 * 24 * 60 * 60 * 1000,
          "30days": 30 * 24 * 60 * 60 * 1000,
        };

        const duration = ranges[selectedRange];
        if (duration) {
          dateRangeParams = {
            start_date: new Date(now.getTime() - duration).toISOString(),
            end_date: now.toISOString(),
          };
        }
      }

      const [executionsData, checkpointsData] = await Promise.all([
        getVaultExecutions(vault.id, dateRangeParams),
        getVaultCrawlCheckpoints(vault.id),
      ]);
      // Sort executions by created_at descending (newest first)
      const sortedExecutions = executionsData.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setExecutions(sortedExecutions);
      setCrawlCheckpoints(checkpointsData);
    } catch (error) {
      console.error("Error loading vault data:", error);
      toast.error("Failed to load vault executions. " + (error?.message || ""));
    } finally {
      setIsLoading(false);
    }
  };

  const toggleExpandedRow = (executionId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(executionId)) {
      newExpanded.delete(executionId);
    } else {
      newExpanded.add(executionId);
    }
    setExpandedRows(newExpanded);
  };

  const handleViewDetails = (execution: VaultExecution) => {
    setSelectedExecution(execution);
    setIsDialogOpen(true);
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
    const formattedDate = new Intl.DateTimeFormat(undefined, { // 'undefined' uses the user's default locale
      year: 'numeric',
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false // Use 24-hour format
  }).format(date);
    
    const milliseconds = date.getMilliseconds().toString().padStart(3, "0");
    return `${formattedDate}.${milliseconds}`;
  };

  const formatJson = (data: any): string => {
    try {
      return JSON.stringify(data, null, 2);
    } catch {
      return String(data);
    }
  };

  const calculateDuration = (execution: VaultExecution): string => {
    if (execution.started_at && execution.completed_at) {
      const start = new Date(execution.started_at).getTime();
      const end = new Date(execution.completed_at).getTime();
      const durationMs = end - start;

      const seconds = Math.floor((durationMs / 1000) % 60);
      const minutes = Math.floor((durationMs / (1000 * 60)) % 60);
      const hours = Math.floor((durationMs / (1000 * 60 * 60)) % 24);

      const parts = [];
      if (hours > 0) parts.push(`${hours}h`);
      if (minutes > 0) parts.push(`${minutes}m`);
      parts.push(`${seconds}s`);

      return parts.join(" ");
    }
    return "N/A";
  }

  const handleCopyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text).then(() => {
      toast.success(`${label} copied to clipboard`);
    }).catch(() => {
      toast.error("Failed to copy to clipboard");
    });
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
      <div className="flex items-start justify-between gap-6">
        <div className="flex-1">
          <h2 className="text-4xl font-bold mb-2" title={vault.name}>{vault.name?.length > 42 ? vault.name.slice(0, 42) + "..." : vault.name}</h2>
          <p className="text-lg text-muted-foreground mb-4">
            {vault.description || "No description"}
          </p>
          <div className="flex items-center gap-4">
            {vault.pipeline_name && (
              <div className="text-sm">
                <span className="text-muted-foreground">Pipeline: </span>
                <span className="font-semibold">{vault.pipeline_name}</span>
              </div>
            )}
            {vault.tags && vault.tags.length > 0 && (
              <div className="flex gap-2">
                {vault.tags.map((tag) => (
                  <span key={tag} className="text-xs px-2 py-1 bg-secondary rounded-full">
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* Crawl Checkpoints Display */}
        {crawlCheckpoints.length > 0 && (
          <div className="flex-shrink-0 bg-slate-50 rounded-lg p-4 border border-slate-200 min-w-80">
            <h3 className="text-sm font-semibold mb-3">Latest Crawl Checkpoint</h3>
            <div className="space-y-2">
              {crawlCheckpoints.slice(0, 1).map((checkpoint) => (
                <div key={checkpoint.id} className="text-xs space-y-1">
                  <div className="flex justify-between items-start gap-2">
                    <span className="text-muted-foreground">Checkpoint:</span>
                    <span className="font-mono text-slate-700">{checkpoint.id?.length >= 16 ? checkpoint.id.substring(0, 16) + "..." : checkpoint.id}</span>
                  </div>
                  <div className="flex justify-between items-start gap-2">
                    <span className="text-muted-foreground">Executor:</span>
                    <span className="font-mono text-slate-700">{checkpoint.executor_id?.length >= 16 ? checkpoint.executor_id.substring(0, 16) + "..." : checkpoint.executor_id}</span>
                  </div>
                  <div className="flex justify-between items-start gap-2">
                    <span className="text-muted-foreground">Worker:</span>
                    <span className="font-mono text-slate-700">{checkpoint.worker_id}</span>
                  </div>
                  <div className="flex justify-between items-start gap-2">
                    <span className="text-muted-foreground">Timestamp:</span>
                    <span className="font-mono text-slate-700">{formatDate(checkpoint.checkpoint_timestamp)}</span>
                  </div>
                </div>
              ))}
              
            </div>
          </div>
        )}

        
      </div>

      <div className="flex items-center justify-between gap-2">
        <div></div>
        <div className="flex items-center gap-2">
          <Select value={selectedRange} onValueChange={setSelectedRange}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="15min">Last 15 min</SelectItem>
              <SelectItem value="30min">Last 30 min</SelectItem>
              <SelectItem value="1hour">Last 1 hour</SelectItem>
              <SelectItem value="4hours">Last 4 hours</SelectItem>
              <SelectItem value="1day">Last 1 day</SelectItem>
              <SelectItem value="7days">Last 7 days</SelectItem>
              <SelectItem value="30days">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
          <div className="flex items-center gap-2">
            <Checkbox 
              id="auto-refresh"
              checked={autoRefresh}
              onCheckedChange={(checked) => setAutoRefresh(checked as boolean)}
            />
            <label 
              htmlFor="auto-refresh" 
              className="text-xs font-medium cursor-pointer"
            >
              Auto-Refresh
            </label>
          </div>
          <Button
            variant="outline"
            onClick={loadData}
            disabled={isLoading}
            className="gap-2"
          >
            Refresh
          </Button>
        </div>
      </div>

      {executions.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <Calendar className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-xl font-semibold mb-2">No executions yet</h3>
            <p className="text-muted-foreground">
              Executions will appear here when the vault pipeline is executed
            </p>
          </div>
        </Card>
      ) : (
        <Card>
          <Table className="text-sm">
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-8 py-2"></TableHead>
                <TableHead className="py-2">Execution ID</TableHead>
                <TableHead className="py-2">Status</TableHead>
                <TableHead className="py-2">Number of Items</TableHead>
                <TableHead className="py-2">Created</TableHead>
                <TableHead className="py-2">Started</TableHead>
                <TableHead className="py-2">Completed</TableHead>
                <TableHead className="py-2">Duration</TableHead>
                <TableHead className="w-12 py-2"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {executions.map((execution) => (
                <>
                  <TableRow key={execution.id} className="hover:bg-muted/50">
                    <TableCell className="py-2">
                      <button
                        onClick={() => toggleExpandedRow(execution.id)}
                        className="hover:bg-muted rounded p-1"
                      >
                        {expandedRows.has(execution.id) ? (
                          <ChevronDown className="w-4 h-4" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                      </button>
                    </TableCell>
                    <TableCell className="font-mono text-xs py-2">
                      {execution.id.substring(0, 12)}...
                    </TableCell>
                    <TableCell className="py-2">{getStatusBadge(execution.status)}</TableCell>
                    <TableCell className="py-2">{execution.number_of_items ?? "N/A"}</TableCell>
                    <TableCell className="text-xs py-2">
                      {formatDate(execution.created_at)}
                    </TableCell>
                    <TableCell className="text-xs py-2">{formatDate(execution.started_at)}</TableCell>
                    <TableCell className="text-xs py-2">{formatDate(execution.completed_at)}</TableCell>
                    <TableCell className="py-2">{calculateDuration(execution)}</TableCell>
                    <TableCell className="py-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewDetails(execution)}
                        className="h-6 w-6 p-0"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                  {expandedRows.has(execution.id) && (
                    <TableRow className="bg-muted/30">
                      <TableCell colSpan={9} className="p-3">
                        <div className="space-y-3">
                          {/* Error Section */}
                          {execution.error && (
                            <div className="bg-red-50 border border-red-200 rounded p-3">
                              <div className="flex items-center gap-2 mb-1">
                                <AlertCircle className="w-4 h-4 text-red-600" />
                                <h4 className="font-semibold text-xs text-red-900">Error</h4>
                              </div>
                              <pre className="bg-white rounded p-2 text-xs text-red-900 overflow-y-auto overflow-x-hidden max-h-32 whitespace-pre-wrap break-words">
                                {execution.error}
                              </pre>
                            </div>
                          )}

                          {/* Status Message */}
                          {execution.status_message && (
                            <div>
                              <h4 className="font-semibold text-xs mb-1">Status Message</h4>
                              <p className="text-xs text-muted-foreground">
                                {execution.status_message}
                              </p>
                            </div>
                          )}
                          {/* Source Worker ID */}
                          {execution.source_worker_id && (
                            <div>
                              <h4 className="font-semibold text-xs mb-1">Source Worker ID</h4>
                              <p className="text-xs text-muted-foreground">
                                {execution.source_worker_id}
                              </p>
                            </div>
                          )}
                          {/* Processing Worker ID */}
                          {execution.processing_worker_id && (
                            <div>
                              <h4 className="font-semibold text-xs mb-1">Processing Worker ID</h4>
                              <p className="text-xs text-muted-foreground">
                                {execution.processing_worker_id}
                              </p>
                            </div>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      {/* Details Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-5xl max-h-[90vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>Execution Details</DialogTitle>
            <DialogDescription>
              ID: {selectedExecution?.id}
            </DialogDescription>
          </DialogHeader>
          {selectedExecution && (
            <div className="space-y-6 overflow-y-auto flex-1">
              {/* Metadata Grid - 3 columns */}
              <div>
                <h3 className="font-semibold text-sm mb-3">Execution Metadata</h3>
                <div className="grid grid-cols-3 gap-4">
                  {/* Execution ID */}
                  <div className="bg-slate-50 rounded p-3">
                    <p className="text-xs text-muted-foreground mb-1">Execution ID</p>
                    <p className="font-mono text-xs break-all text-slate-900">
                      {selectedExecution.id}
                    </p>
                  </div>

                  {/* Task ID */}
                  <div className="bg-slate-50 rounded p-3">
                    <p className="text-xs text-muted-foreground mb-1">Task ID</p>
                    <p className="font-mono text-xs break-all text-slate-900">
                      {selectedExecution.task_id}
                    </p>
                  </div>

                  {/* Status */}
                  <div className="bg-slate-50 rounded p-3">
                    <p className="text-xs text-muted-foreground mb-1">Status</p>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(selectedExecution.status)}
                    </div>
                  </div>

                  {/* Created At */}
                  <div className="bg-slate-50 rounded p-3">
                    <p className="text-xs text-muted-foreground mb-1">Created</p>
                    <p className="text-xs text-slate-900">
                      {formatDate(selectedExecution.created_at)}
                    </p>
                  </div>

                  {/* Started At */}
                  <div className="bg-slate-50 rounded p-3">
                    <p className="text-xs text-muted-foreground mb-1">Started</p>
                    <p className="text-xs text-slate-900">
                      {formatDate(selectedExecution.started_at)}
                    </p>
                  </div>

                  {/* Completed At */}
                  <div className="bg-slate-50 rounded p-3">
                    <p className="text-xs text-muted-foreground mb-1">Completed</p>
                    <p className="text-xs text-slate-900">
                      {formatDate(selectedExecution.completed_at)}
                    </p>
                  </div>

                  {/* Duration */}
                  <div className="bg-slate-50 rounded p-3">
                    <p className="text-xs text-muted-foreground mb-1">Duration</p>
                    <p className="text-xs text-slate-900">
                      {calculateDuration(selectedExecution)}
                    </p>
                  </div>

                  {/* Number of Items */}
                  <div className="bg-slate-50 rounded p-3">
                    <p className="text-xs text-muted-foreground mb-1">Number of Items</p>
                    <p className="text-xs text-slate-900">
                      {selectedExecution.number_of_items ?? "N/A"}
                    </p>
                  </div>

                  {/* Source Worker ID */}
                  <div className="bg-slate-50 rounded p-3">
                    <p className="text-xs text-muted-foreground mb-1">Source Worker ID</p>
                    <p className="font-mono text-xs break-all text-slate-900">
                      {selectedExecution.source_worker_id || "N/A"}
                    </p>
                  </div>

                  {/* Processing Worker ID */}
                  <div className="bg-slate-50 rounded p-3">
                    <p className="text-xs text-muted-foreground mb-1">Processing Worker ID</p>
                    <p className="font-mono text-xs break-all text-slate-900">
                      {selectedExecution.processing_worker_id || "N/A"}
                    </p>
                  </div>
                </div>
              </div>

              {/* Error Section */}
              {selectedExecution.error && (
                <div className="bg-red-50 border border-red-200 rounded p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle className="w-4 h-4 text-red-600" />
                    <h4 className="font-semibold text-sm text-red-900">Error</h4>
                  </div>
                  <pre className="bg-white rounded p-2 text-xs text-red-900 overflow-y-auto overflow-x-hidden max-h-40 whitespace-pre-wrap break-words">
                    {selectedExecution.error}
                  </pre>
                </div>
              )}

              {/* Status Message */}
              {selectedExecution.status_message && (
                <div className="border border-slate-200 rounded p-3">
                  <h4 className="font-semibold text-sm mb-2">Status Message</h4>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                    {selectedExecution.status_message}
                  </p>
                </div>
              )}

              {/* Content - Collapsible */}
              {selectedExecution.content && Object.keys(selectedExecution.content).length > 0 && (
                <details className="border border-slate-200 rounded">
                  <summary className="flex items-center justify-between cursor-pointer p-3 bg-slate-50 hover:bg-slate-100">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <TableOfContents /> 
                        <h4 className="font-semibold text-sm">Content</h4>
                        <span className="text-xs text-muted-foreground">
                          ({Object.keys(selectedExecution.content).length} {Object.keys(selectedExecution.content).length === 1 ? 'item' : 'items'})
                        </span>
                      </div>
                      <div className="space-y-1 pl-8">
                        {Object.values(selectedExecution.content).map((item: any, idx: number) => (
                          <li key={idx} className="text-xs text-muted-foreground truncate">
                            {item?.id?.canonical_id || item?.id || `Item ${idx + 1}`}
                          </li>
                        ))}
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.preventDefault();
                        handleCopyToClipboard(formatJson(selectedExecution.content), "Content");
                      }}
                      className="h-6 w-6 p-0 flex-shrink-0 ml-2"
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </summary>
                  <div className="p-3 border-t border-slate-200">
                    <pre className="bg-slate-900 text-slate-50 rounded p-3 text-xs overflow-x-auto max-h-96 whitespace-pre-wrap break-words">
                      {formatJson(selectedExecution.content)}
                    </pre>
                  </div>
                </details>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};
