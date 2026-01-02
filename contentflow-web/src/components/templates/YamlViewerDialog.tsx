import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Copy, Check } from "lucide-react";
import { useState } from "react";

interface YamlViewerDialogProps {
  title: string;
  yaml: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const YamlViewerDialog = ({
  title,
  yaml,
  open,
  onOpenChange,
}: YamlViewerDialogProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(yaml);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3 text-xl">
            Pipeline YAML: {title}
          </DialogTitle>
          <DialogDescription>
            This is the YAML definition for the pipeline template
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[calc(90vh-180px)] pr-4">
          <div className="relative">
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto">
              <code className="text-sm font-mono leading-relaxed text-foreground">
                {yaml.split('\n').map((line, idx) => {
                  // Apply syntax highlighting based on line content
                  let lineClass = "text-foreground";
                  let content = line;
                  
                  // Comments
                  if (line.trim().startsWith('#')) {
                    lineClass = "text-muted-foreground italic";
                  }
                  // Keys (before colon)
                  else if (line.includes(':') && !line.trim().startsWith('-')) {
                    const parts = line.split(':');
                    const indent = line.match(/^\s*/)?.[0] || '';
                    const key = parts[0].trim();
                    const value = parts.slice(1).join(':');
                    
                    return (
                      <div key={idx} className="hover:bg-muted/50">
                        <span className="text-muted-foreground">{indent}</span>
                        <span className="text-blue-500 font-semibold">{key}</span>
                        <span className="text-foreground">:</span>
                        {value && (
                          <span className={
                            value.trim().startsWith('"') || value.trim().startsWith("'")
                              ? "text-green-600"
                              : value.trim() === 'true' || value.trim() === 'false'
                              ? "text-purple-600"
                              : /^\d+$/.test(value.trim())
                              ? "text-orange-600"
                              : "text-foreground"
                          }>
                            {value}
                          </span>
                        )}
                      </div>
                    );
                  }
                  // List items
                  else if (line.trim().startsWith('-')) {
                    const indent = line.match(/^\s*/)?.[0] || '';
                    const restOfLine = line.substring(indent.length);
                    
                    return (
                      <div key={idx} className="hover:bg-muted/50">
                        <span className="text-muted-foreground">{indent}</span>
                        <span className="text-cyan-600 font-semibold">-</span>
                        <span className="text-foreground">{restOfLine.substring(1)}</span>
                      </div>
                    );
                  }
                  
                  return (
                    <div key={idx} className={`${lineClass} hover:bg-muted/50`}>
                      {line || '\u00A0'}
                    </div>
                  );
                })}
              </code>
            </pre>
          </div>
        </ScrollArea>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button
            variant="secondary"
            onClick={handleCopy}
            className="gap-2"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy YAML
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
