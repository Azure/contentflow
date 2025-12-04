import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { WorkflowTemplate } from "@/types/workflow";
import { CheckCircle2, Clock, Layers, ArrowRight } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

interface TemplatePreviewDialogProps {
  template: WorkflowTemplate | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUse: (template: WorkflowTemplate) => void;
}

export const TemplatePreviewDialog = ({
  template,
  open,
  onOpenChange,
  onUse,
}: TemplatePreviewDialogProps) => {
  if (!template) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3 text-2xl">
            {template.name}
          </DialogTitle>
          <DialogDescription className="text-base">
            {template.description}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[60vh] pr-4">
          <div className="space-y-6 py-4">
            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted">
                <Layers className="w-5 h-5 text-secondary" />
                <div>
                  <p className="text-sm text-muted-foreground">Steps</p>
                  <p className="font-semibold text-foreground">{template.steps}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted">
                <Clock className="w-5 h-5 text-secondary" />
                <div>
                  <p className="text-sm text-muted-foreground">Duration</p>
                  <p className="font-semibold text-foreground">{template.estimatedTime}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted">
                <Badge variant="outline" className="capitalize">
                  {template.category}
                </Badge>
              </div>
            </div>

            <Separator />

            {/* Features */}
            <div>
              <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-secondary" />
                Key Features
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {template.features.map((feature, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-sm">
                    <div className="w-1.5 h-1.5 rounded-full bg-secondary mt-2" />
                    <span className="text-muted-foreground">{feature}</span>
                  </div>
                ))}
              </div>
            </div>

            <Separator />

            {/* Use Cases */}
            <div>
              <h3 className="font-semibold text-foreground mb-3">Use Cases</h3>
              <div className="space-y-2">
                {template.useCases.map((useCase, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                    <div className="w-6 h-6 rounded-full bg-secondary/20 text-secondary flex items-center justify-center text-xs font-semibold flex-shrink-0">
                      {idx + 1}
                    </div>
                    <p className="text-sm text-foreground">{useCase}</p>
                  </div>
                ))}
              </div>
            </div>

            <Separator />

            {/* Pipeline Preview */}
            <div>
              <h3 className="font-semibold text-foreground mb-3">Pipeline Overview</h3>
              <div className="space-y-3">
                {template.nodes.map((node, idx) => (
                  <div key={node.id}>
                    <div className="flex items-center gap-3 p-3 rounded-lg border border-border bg-card hover:bg-muted/50 transition-colors">
                      <div className={`${node.data.executor.color} text-white p-2 rounded-lg`}>
                        <div className="w-4 h-4" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-foreground text-sm">{node.data.label}</p>
                        {node.data.config.description && (
                          <p className="text-xs text-muted-foreground">{node.data.config.description}</p>
                        )}
                      </div>
                      <Badge variant="outline" className="text-xs capitalize">
                        {node.data.executor.category}
                      </Badge>
                    </div>
                    {idx < template.nodes.length - 1 && (
                      <div className="flex justify-center py-1">
                        <ArrowRight className="w-4 h-4 text-secondary rotate-90" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </ScrollArea>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button 
            className="bg-gradient-secondary gap-2"
            onClick={() => {
              onUse(template);
              onOpenChange(false);
            }}
          >
            Use This Template
            <ArrowRight className="w-4 h-4" />
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
