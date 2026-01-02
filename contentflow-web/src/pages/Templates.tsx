import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Footer } from "@/components/Footer";
import { 
  FileText, 
  Brain, 
  Network, 
  Search, 
  ArrowRight,
  Sparkles,
  BookOpen,
  Mail,
  Image as ImageIcon,
} from "lucide-react";
import { TemplatePreviewDialog } from "@/components/templates/TemplatePreviewDialog";
import { PipelineTemplate } from "@/types/pipeline";
import { pipelineTemplates } from "@/data/pipelineTemplates";

export default function Templates() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [previewTemplate, setPreviewTemplate] = useState<PipelineTemplate | null>(null);

  const categories = [
    { id: "all", label: "All Templates", icon: <Sparkles className="w-4 h-4" /> },
    { id: "extraction", label: "Extraction", icon: <FileText className="w-4 h-4" /> },
    { id: "analysis", label: "Analysis", icon: <Brain className="w-4 h-4" /> },
    { id: "knowledge", label: "Knowledge", icon: <Network className="w-4 h-4" /> },
  ];

  const filteredTemplates = pipelineTemplates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         template.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "all" || template.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleUseTemplate = (template: PipelineTemplate) => {
    // Store template in localStorage to load in pipeline builder
    localStorage.setItem("selectedTemplate", JSON.stringify(template));
    navigate("/?view=pipeline");
  };

  return (
    <div className="min-h-screen bg-background pb-12">
      {/* Header */}
      <div className="border-b border-border bg-card/50 backdrop-blur-lg">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h1 className="font-display text-4xl font-bold mb-2 text-foreground">
                Pipeline Templates
              </h1>
              <p className="text-muted-foreground text-lg">
                Pre-built pipelines ready to use in your projects
              </p>
            </div>
            <Button onClick={() => navigate("/?view=pipeline")}>
              Create from Scratch
              <ArrowRight className="ml-2 w-4 h-4" />
            </Button>
          </div>

          {/* Search */}
          <div className="relative max-w-xl">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <Input
              placeholder="Search templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-5 gap-6">
          {/* Category Sidebar */}
          <Card className="lg:col-span-1 p-4 h-fit">
            <h3 className="font-semibold mb-3 text-foreground">Categories</h3>
            <div className="space-y-1">
              {categories.map((category) => (
                <Button
                  key={category.id}
                  variant={selectedCategory === category.id ? "secondary" : "ghost"}
                  className="w-full justify-start gap-2"
                  onClick={() => setSelectedCategory(category.id)}
                >
                  {category.icon}
                  {category.label}
                </Button>
              ))}
            </div>
          </Card>

          {/* Template Grid */}
          <div className="lg:col-span-4">
            {filteredTemplates.length === 0 ? (
              <Card className="p-12 text-center">
                <Search className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground">No templates found</p>
              </Card>
            ) : (
              <div className="grid md:grid-cols-2 gap-6">
                {filteredTemplates.map((template) => (
                  <TemplateCard
                    key={template.id}
                    template={template}
                    onPreview={() => setPreviewTemplate(template)}
                    onUse={() => handleUseTemplate(template)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <TemplatePreviewDialog
        template={previewTemplate}
        open={!!previewTemplate}
        onOpenChange={(open) => !open && setPreviewTemplate(null)}
        onUse={handleUseTemplate}
      />

      <Footer />
    </div>
  );
}

interface TemplateCardProps {
  template: PipelineTemplate;
  onPreview: () => void;
  onUse: () => void;
}

const TemplateCard = ({ template, onPreview, onUse }: TemplateCardProps) => {
  const getIconForCategory = (category: string) => {
    switch (category) {
      case "extraction": return <FileText className="w-5 h-5" />;
      case "analysis": return <Brain className="w-5 h-5" />;
      case "knowledge": return <Network className="w-5 h-5" />;
      default: return <Sparkles className="w-5 h-5" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "extraction": return "bg-primary";
      case "analysis": return "bg-accent";
      case "knowledge": return "bg-secondary";
      default: return "bg-muted";
    }
  };

  return (
    <Card className="p-6 hover:shadow-lg transition-all duration-300 group cursor-pointer" onClick={onPreview}>
      <div className="flex items-start gap-4 mb-4">
        <div className={`${getCategoryColor(template.category)} text-white p-3 rounded-xl group-hover:scale-110 transition-transform`}>
          {getIconForCategory(template.category)}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-display text-lg font-bold text-foreground mb-1 group-hover:text-secondary transition-colors">
            {template.name}
          </h3>
          <Badge variant="outline" className="capitalize text-xs">
            {template.category}
          </Badge>
        </div>
      </div>

      <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
        {template.description}
      </p>

      <div className="flex items-center justify-between pt-4 border-t border-border">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-secondary" />
            {template.steps} steps
          </div>
          <span>•</span>
          <span>{template.estimatedTime}</span>
        </div>
        <Button 
          size="sm" 
          className="bg-gradient-secondary"
          onClick={(e) => {
            e.stopPropagation();
            onUse();
          }}
        >
          Use Template
        </Button>
      </div>
    </Card>
  );
};