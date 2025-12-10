import { useEffect, useRef, useState } from "react";
import Editor from "@monaco-editor/react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, Check } from "lucide-react";
import { validateYaml } from "@/lib/pipelineYamlConverter";

interface PipelineYamlEditorProps {
  value: string;
  onChange: (value: string) => void;
  onApply: () => void;
  hasChanges: boolean;
}

export const PipelineYamlEditor = ({
  value,
  onChange,
  onApply,
  hasChanges,
}: PipelineYamlEditorProps) => {
  const [validationError, setValidationError] = useState<string | null>(null);
  const editorRef = useRef<any>(null);

  // Validate YAML on change
  useEffect(() => {
    const { isValid, error } = validateYaml(value);
    setValidationError(isValid ? null : error || "Invalid YAML");
  }, [value]);

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
  };

  const handleApply = () => {
    const { isValid } = validateYaml(value);
    if (isValid) {
      onApply();
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Validation Status */}
      {validationError ? (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{validationError}</AlertDescription>
        </Alert>
      ) : hasChanges ? (
        <Alert className="mb-4 border-yellow-500 text-yellow-700">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            YAML has been modified. Click "Apply Changes" to update the pipeline.
          </AlertDescription>
        </Alert>
      ) : (
        <Alert className="mb-4 border-green-500 text-green-700">
          <Check className="h-4 w-4" />
          <AlertDescription>YAML is valid and in sync with the pipeline</AlertDescription>
        </Alert>
      )}

      {/* Monaco Editor */}
      <Card className="flex-1 overflow-hidden">
        <Editor
          height="100%"
          defaultLanguage="yaml"
          value={value}
          onChange={(value) => onChange(value || "")}
          onMount={handleEditorDidMount}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            wordWrap: "on",
            wrappingStrategy: "advanced",
            formatOnPaste: true,
            formatOnType: true,
          }}
        />
      </Card>

      {/* Apply Button */}
      {hasChanges && (
        <div className="mt-4 flex justify-end">
          <Button
            onClick={handleApply}
            disabled={!!validationError}
            className="bg-gradient-secondary hover:opacity-90"
          >
            Apply Changes
          </Button>
        </div>
      )}
    </div>
  );
};
