export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: "extraction" | "analysis" | "knowledge";
  steps: number;
  estimatedTime: string;
  nodes: TemplateNode[];
  edges: TemplateEdge[];
  useCases: string[];
  features: string[];
}

export interface TemplateNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    executor: {
      id: string;
      type: string;
      name: string;
      color: string;
      category: string;
    };
    config: Record<string, any>;
  };
}

export interface TemplateEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
  animated?: boolean;
}
