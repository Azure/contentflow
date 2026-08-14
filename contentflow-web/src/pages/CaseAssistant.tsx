import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  Download,
  FileCheck2,
  FileSearch,
  Loader2,
  LockKeyhole,
  Search,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  getSarspCaseExecutionStatus,
  SarspExecutionStatusResponse,
  startSarspCaseValidation,
} from "@/lib/api/sarspApi";

type ProcessingStatus = "Idle" | "Queued" | "Running" | "Validating" | "Completed" | "Failed" | "Cancelled";
type Recommendation = "Approve" | "Decline";
type LicenseType = "new" | "renewal";

const NEW_LICENSE_CONTAINER = "sql-fetch-data";
const RENEWAL_LICENSE_CONTAINER = "farmacia-nueva-renewal";

interface ValidationCheck {
  name: string;
  result: "Passed" | "Failed";
  detail: string;
}

interface DocumentFinding {
  document: string;
  status: "Accepted" | "Needs Correction" | "Missing";
  finding: string;
  guidance: string;
}

interface CaseResult {
  caseId: string;
  status: ProcessingStatus;
  recommendation: Recommendation | null;
  confidence: number | null;
  completedAt: string | null;
  checks: ValidationCheck[];
  missingDocuments: MissingDocument[];
  findings: DocumentFinding[];
  report?: Record<string, unknown> | null;
}

interface MissingDocument {
  documentType: string;
  message: string;
}

const statusSteps: ProcessingStatus[] = ["Queued", "Running", "Validating", "Completed"];

const statusProgress: Record<ProcessingStatus, number> = {
  Idle: 0,
  Queued: 20,
  Running: 50,
  Validating: 78,
  Completed: 100,
  Failed: 100,
  Cancelled: 100,
};

const activeStatuses: ProcessingStatus[] = ["Queued", "Running", "Validating"];

function normalizeStatus(status: string): ProcessingStatus {
  const lowered = status.toLowerCase();
  if (lowered === "queued") return "Queued";
  if (lowered === "running") return "Running";
  if (lowered === "validating") return "Validating";
  if (lowered === "completed") return "Completed";
  if (lowered === "failed") return "Failed";
  if (lowered === "cancelled") return "Cancelled";
  return "Queued";
}

function toValidationCheck(item: Record<string, unknown>): ValidationCheck {
  const rawResult = String(item.result ?? "Failed");
  const normalizedResult = rawResult.toLowerCase() === "passed" ? "Passed" : "Failed";

  return {
    name: String(item.name ?? "Unnamed check"),
    result: normalizedResult,
    detail: String(item.detail ?? "No additional detail available."),
  };
}

function toDocumentFinding(item: Record<string, unknown>): DocumentFinding {
  const rawStatus = String(item.status ?? "Missing");
  const normalizedStatus: DocumentFinding["status"] =
    rawStatus === "Accepted" || rawStatus === "Needs Correction" || rawStatus === "Missing"
      ? rawStatus
      : "Missing";

  return {
    document: String(item.document ?? "Unspecified document"),
    status: normalizedStatus,
    finding: String(item.finding ?? "No finding details returned."),
    guidance: String(item.guidance ?? "Reviewer guidance not provided."),
  };
}

function toMissingDocument(item: unknown): MissingDocument | null {
  if (typeof item === "object" && item !== null) {
    const value = item as Record<string, unknown>;
    return {
      documentType: String(value.documentType ?? value.document_type ?? "Missing document"),
      message: String(value.message_en ?? value.message ?? value.message_es ?? "Required document was not found."),
    };
  }

  if (typeof item === "string") {
    const documentType = item.match(/documentType['\"]?\s*:\s*['\"]([^'\"]+)/)?.[1];
    const message = item.match(/message_en['\"]?\s*:\s*['\"]([^'\"]+)/)?.[1];
    if (documentType) {
      return {
        documentType,
        message: message ?? "Required document was not found.",
      };
    }

    return { documentType: item, message: "Required document was not found." };
  }

  return null;
}

function toCaseResult(response: SarspExecutionStatusResponse): CaseResult {
  const recommendation =
    response.recommendation === "Approve" || response.recommendation === "Decline"
      ? response.recommendation
      : null;

  const checks = (response.checks ?? [])
    .filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null)
    .map(toValidationCheck);

  const report = response.report ?? null;
  const reportMissingDocuments = Array.isArray(report?.missingDocuments)
    ? report.missingDocuments
    : Array.isArray(report?.missing_documents)
      ? report.missing_documents
      : [];
  const rawMissingDocuments = reportMissingDocuments.length > 0
    ? reportMissingDocuments
    : response.missing_documents ?? [];
  const missingDocuments = rawMissingDocuments
    .map(toMissingDocument)
    .filter((item): item is MissingDocument => item !== null);

  const findings = (response.findings ?? [])
    .filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null)
    .map(toDocumentFinding);

  return {
    caseId: response.case_id,
    status: normalizeStatus(response.status),
    recommendation,
    confidence: typeof response.confidence === "number" ? response.confidence : null,
    completedAt: response.completed_at ?? null,
    checks,
    missingDocuments,
    findings,
    report: response.report ?? null,
  };
}

export default function CaseAssistant() {
  const [caseId, setCaseId] = useState("");
  const [licenseType, setLicenseType] = useState<LicenseType>("renewal");
  const [submittedCaseId, setSubmittedCaseId] = useState("");
  const [executionId, setExecutionId] = useState("");
  const [status, setStatus] = useState<ProcessingStatus>("Idle");
  const [statusMessage, setStatusMessage] = useState("No case submitted");
  const [result, setResult] = useState<CaseResult | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const selectedContainer = licenseType === "new" ? NEW_LICENSE_CONTAINER : RENEWAL_LICENSE_CONTAINER;

  useEffect(() => {
    if (!submittedCaseId || !executionId || !activeStatuses.includes(status)) {
      return;
    }

    let isActive = true;
    let timeoutId: number | undefined;

    const poll = async () => {
      try {
        const response = await getSarspCaseExecutionStatus(submittedCaseId, executionId);
        if (!isActive) {
          return;
        }

        const nextStatus = normalizeStatus(response.status);
        setStatus(nextStatus);
        setStatusMessage(response.message || "Execution updated");

        if (nextStatus === "Completed") {
          setResult(toCaseResult(response));
          return;
        }

        if (nextStatus === "Failed" || nextStatus === "Cancelled") {
          setApiError(response.message || `Execution ${nextStatus.toLowerCase()}`);
          return;
        }

        timeoutId = window.setTimeout(poll, 2500);
      } catch (error) {
        if (!isActive) {
          return;
        }

        console.error("Error polling case status", error);
        setApiError("Unable to retrieve case status from API.");
      }
    };

    void poll();

    return () => {
      isActive = false;
      if (timeoutId !== undefined) {
        window.clearTimeout(timeoutId);
      }
    };
  }, [executionId, submittedCaseId]);

  const passedDocuments = result?.findings.filter((finding) => finding.status === "Accepted").length ?? 0;
  const failedDocuments = result?.findings.filter((finding) => finding.status === "Needs Correction" || finding.status === "Missing").length ?? 0;
  const activeStatusIndex = statusSteps.indexOf(status);

  const reportUrl = useMemo(() => {
    if (!result?.report) {
      return "";
    }

    const blob = new Blob([JSON.stringify(result.report, null, 2)], { type: "application/json" });
    return URL.createObjectURL(blob);
  }, [result?.report]);

  useEffect(() => {
    return () => {
      if (reportUrl) {
        URL.revokeObjectURL(reportUrl);
      }
    };
  }, [reportUrl]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const normalizedCaseId = caseId.trim().toUpperCase();
    if (!normalizedCaseId) {
      return;
    }

    setApiError(null);
    setResult(null);
    setStatus("Queued");
    setStatusMessage("Submitting case to pipeline...");
    setSubmittedCaseId(normalizedCaseId);
    setCaseId(normalizedCaseId);

    try {
      const response = await startSarspCaseValidation(normalizedCaseId, {
        configuration: {
          case_container: selectedContainer,
          license_type: licenseType,
        },
      });
      setExecutionId(response.execution_id);
      setStatus(normalizeStatus(response.status));
      setStatusMessage(response.message);
    } catch (error) {
      console.error("Error starting case validation", error);
      setExecutionId("");
      setStatus("Failed");
      setApiError("Failed to submit case. Confirm API is reachable and SARSP pipeline is configured.");
      setStatusMessage("Case submission failed");
    }
  };

  return (
    <div className="min-h-screen bg-[#f7f8fb] text-slate-950">
      <header className="border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="container mx-auto flex flex-col gap-5 px-6 py-5 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#0f5132] text-white shadow-sm">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">SARSP Frontend</p>
              <h1 className="font-display text-2xl font-bold tracking-normal">Case Assistant</h1>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-semibold uppercase tracking-[0.06em] text-amber-900">
              Disclaimer: Demo purposes only, not intended for PROD
            </div>
            <div className="flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-900">
              <LockKeyhole className="h-4 w-4" />
              Secure reviewer portal
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto grid gap-6 px-6 py-8 xl:grid-cols-[420px_1fr]">
        <section className="space-y-6">
          <Card className="rounded-lg border-slate-200 p-6 shadow-sm">
            <div className="mb-6">
              <h2 className="font-display text-3xl font-bold tracking-normal text-slate-950">Validate a pharmacy license case</h2>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                Enter a Case ID to submit it to the SARSP AI pipeline and review the generated validation outcome.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <label htmlFor="case-id" className="text-sm font-semibold text-slate-700">
                Case ID
              </label>
              <div className="flex gap-2">
                <Input
                  id="case-id"
                  value={caseId}
                  onChange={(event) => setCaseId(event.target.value)}
                  placeholder="SARSP-2026-0142"
                  className="h-11 rounded-md border-slate-300 bg-white uppercase"
                />
                <Button type="submit" className="h-11 gap-2 rounded-md bg-[#164b35] px-5 hover:bg-[#0f3d2b]">
                  {activeStatuses.includes(status) ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                  Submit
                </Button>
              </div>

              <div className="space-y-2">
                <p className="text-sm font-semibold text-slate-700">License Type</p>
                <div className="space-y-2 rounded-md border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="license-type-new"
                      checked={licenseType === "new"}
                      onCheckedChange={(checked) => {
                        if (checked === true) {
                          setLicenseType("new");
                        }
                      }}
                    />
                    <Label htmlFor="license-type-new" className="cursor-pointer text-sm text-slate-700">
                      New license (container: {NEW_LICENSE_CONTAINER})
                    </Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="license-type-renewal"
                      checked={licenseType === "renewal"}
                      onCheckedChange={(checked) => {
                        if (checked === true) {
                          setLicenseType("renewal");
                        }
                      }}
                    />
                    <Label htmlFor="license-type-renewal" className="cursor-pointer text-sm text-slate-700">
                      Renewal license (container: {RENEWAL_LICENSE_CONTAINER})
                    </Label>
                  </div>
                </div>
              </div>
            </form>
          </Card>

          <Card className="rounded-lg border-slate-200 p-6 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h2 className="font-display text-xl font-bold tracking-normal">Processing Status</h2>
                <p className="text-sm text-slate-500">{submittedCaseId || "No case submitted"}</p>
              </div>
              <StatusBadge status={status} />
            </div>
            <p className="mb-4 text-sm text-slate-600">{statusMessage}</p>
            {executionId && <p className="mb-4 text-xs font-medium text-slate-500">Execution ID: {executionId}</p>}
            <Progress value={statusProgress[status]} className="h-2 bg-slate-200 [&>div]:bg-[#0f766e]" />
            <div className="mt-5 grid grid-cols-4 gap-2 text-xs font-medium text-slate-500">
              {statusSteps.map((step, index) => {
                const isActive = activeStatusIndex >= index;
                return (
                  <div key={step} className="flex flex-col items-center gap-2 text-center">
                    <div className={`flex h-8 w-8 items-center justify-center rounded-full border ${isActive ? "border-[#0f766e] bg-[#0f766e] text-white" : "border-slate-300 bg-white text-slate-400"}`}>
                      {isActive ? <CheckCircle2 className="h-4 w-4" /> : <Clock3 className="h-4 w-4" />}
                    </div>
                    <span>{step}</span>
                  </div>
                );
              })}
            </div>
            {apiError && (
              <div className="mt-5 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                {apiError}
              </div>
            )}
          </Card>
        </section>

        <section className="space-y-6">
          <div className="grid gap-4 md:grid-cols-4">
            <SummaryTile
              label="Recommendation"
              value={result?.recommendation ?? "Pending"}
              tone={result?.recommendation === "Approve" ? "success" : result?.recommendation === "Decline" ? "danger" : "neutral"}
            />
            <SummaryTile label="Passed Docs" value={String(passedDocuments)} tone="success" />
            <SummaryTile label="Failed Docs" value={String(failedDocuments)} tone={failedDocuments ? "danger" : "neutral"} />
            <SummaryTile label="Missing Docs" value={String(result?.missingDocuments.length ?? 0)} tone={result?.missingDocuments.length ? "warning" : "neutral"} />
          </div>

          <Card className="rounded-lg border-slate-200 p-6 shadow-sm">
            <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="font-display text-xl font-bold tracking-normal">Validation Summary</h2>
                <p className="text-sm text-slate-500">
                  {result?.confidence !== null && result?.confidence !== undefined
                    ? `${result.confidence}% confidence, completed ${result.completedAt ? new Date(result.completedAt).toLocaleString() : "recently"}`
                    : "Awaiting pipeline results"}
                </p>
              </div>
              <Button asChild disabled={!result?.report || !reportUrl} variant="outline" className="gap-2 rounded-md border-slate-300">
                <a href={reportUrl || undefined} download={`${result?.caseId ?? "case"}-results.json`} aria-disabled={!result?.report || !reportUrl}>
                  <Download className="h-4 w-4" />
                  Download results.json
                </a>
              </Button>
            </div>

            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Validation Check</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Result Detail</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(result?.checks ?? []).map((check) => (
                  <TableRow key={`${check.name}-${check.result}`}>
                    <TableCell className="font-medium text-slate-900">{check.name}</TableCell>
                    <TableCell>
                      <ResultBadge result={check.result} />
                    </TableCell>
                    <TableCell className="text-slate-600">{check.detail}</TableCell>
                  </TableRow>
                ))}
                {!result && (
                  <TableRow>
                    <TableCell colSpan={3} className="h-28 text-center text-slate-500">
                      Submit a Case ID to view validation checks.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Card>

          <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
            <Card className="rounded-lg border-slate-200 p-6 shadow-sm">
              <div className="mb-5 flex items-center gap-3">
                <FileSearch className="h-5 w-5 text-[#0f766e]" />
                <h2 className="font-display text-xl font-bold tracking-normal">Document Findings</h2>
              </div>
              <div className="space-y-3">
                {(result?.findings ?? []).map((finding) => (
                  <div key={`${finding.document}-${finding.status}`} className="rounded-lg border border-slate-200 bg-white p-4">
                    <div className="mb-2 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                      <h3 className="font-semibold text-slate-950">{finding.document}</h3>
                      <DocumentStatusBadge status={finding.status} />
                    </div>
                    <p className="text-sm leading-6 text-slate-600">{finding.finding}</p>
                    <p className="mt-2 text-sm font-medium text-slate-800">{finding.guidance}</p>
                  </div>
                ))}
                {!result && <EmptyState icon={<FileCheck2 className="h-5 w-5" />} text="Document-level findings will appear after validation completes." />}
              </div>
            </Card>

            <Card className="rounded-lg border-slate-200 p-6 shadow-sm">
              <div className="mb-5 flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-amber-600" />
                <h2 className="font-display text-xl font-bold tracking-normal">Missing Documents</h2>
              </div>
              <div className="space-y-3">
                {(result?.missingDocuments ?? []).map((document) => (
                  <div key={document.documentType} className="rounded-md border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-950">
                    <p className="font-semibold">{document.documentType}</p>
                    <p className="mt-1 text-xs leading-5">{document.message}</p>
                  </div>
                ))}
                {result && result.missingDocuments.length === 0 && <EmptyState icon={<CheckCircle2 className="h-5 w-5" />} text="No missing documents detected." />}
                {!result && <EmptyState icon={<Clock3 className="h-5 w-5" />} text="Missing document checks are pending." />}
              </div>
            </Card>
          </div>
        </section>
      </main>
    </div>
  );
}

function StatusBadge({ status }: { status: ProcessingStatus }) {
  const isBusy = activeStatuses.includes(status);
  const isFailure = status === "Failed" || status === "Cancelled";

  return (
    <Badge className={`${status === "Completed" ? "bg-emerald-700" : isBusy ? "bg-[#0f766e]" : isFailure ? "bg-red-700" : "bg-slate-500"} text-white hover:opacity-90`}>
      {isBusy && <Loader2 className="mr-1 h-3 w-3 animate-spin" />}
      {status}
    </Badge>
  );
}

function ResultBadge({ result }: { result: ValidationCheck["result"] }) {
  return result === "Passed" ? (
    <Badge className="bg-emerald-700 text-white hover:bg-emerald-700">
      <CheckCircle2 className="mr-1 h-3 w-3" />
      Passed
    </Badge>
  ) : (
    <Badge className="bg-red-700 text-white hover:bg-red-700">
      <XCircle className="mr-1 h-3 w-3" />
      Failed
    </Badge>
  );
}

function DocumentStatusBadge({ status }: { status: DocumentFinding["status"] }) {
  const styles = {
    Accepted: "border-emerald-200 bg-emerald-50 text-emerald-900",
    "Needs Correction": "border-amber-200 bg-amber-50 text-amber-900",
    Missing: "border-red-200 bg-red-50 text-red-900",
  };

  return <Badge variant="outline" className={styles[status]}>{status}</Badge>;
}

function SummaryTile({ label, value, tone }: { label: string; value: string; tone: "success" | "danger" | "warning" | "neutral" }) {
  const tones = {
    success: "border-emerald-200 bg-emerald-50 text-emerald-950",
    danger: "border-red-200 bg-red-50 text-red-950",
    warning: "border-amber-200 bg-amber-50 text-amber-950",
    neutral: "border-slate-200 bg-white text-slate-950",
  };

  return (
    <div className={`rounded-lg border p-5 shadow-sm ${tones[tone]}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.12em] opacity-70">{label}</p>
      <p className="mt-2 font-display text-3xl font-bold tracking-normal">{value}</p>
    </div>
  );
}

function EmptyState({ icon, text }: { icon: ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">
      {icon}
      <span>{text}</span>
    </div>
  );
}
