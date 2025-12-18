import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Hero } from "@/components/Hero";
import { PipelineBuilder } from "@/components/PipelineBuilder";
import { KnowledgeGraph } from "@/components/KnowledgeGraph";
import { Vaults } from "@/pages/Vaults";
import { Footer } from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { BookOpen, FolderOpen, Workflow } from "lucide-react";

const Index = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const viewParam = searchParams.get("view");
  const [activeView, setActiveView] = useState<"home" | "pipeline" | "graph" | "vaults">(
    (viewParam as "home" | "pipeline" | "graph" | "vaults") || "home"
  );

  useEffect(() => {
    if (viewParam && ["home", "pipeline", "graph", "vaults"].includes(viewParam)) {
      setActiveView(viewParam as "home" | "pipeline" | "graph" | "vaults");
    }
  }, [viewParam]);

  return (
    <div className="min-h-screen bg-background pb-12">
      <nav className="fixed top-0 w-full z-50 border-b border-border bg-background/80 backdrop-blur-lg">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
              {/* <Workflow className="w-5 h-5 text-white" /> */}
              <img src="/01038-icon-service-Collaborative-Service.svg" alt="ContentFlow" className="inline-block w-5 h-5" />
            </div>
            <span className="font-display text-xl font-bold text-foreground">ContentFlow</span>
            </div>
          <div className="flex items-center gap-4">
            <Button
              variant={activeView === "home" ? "default" : "ghost"}
              onClick={() => setActiveView("home")}
            >
              Home
            </Button>
            <Button
              variant={activeView === "pipeline" ? "default" : "ghost"}
              onClick={() => setActiveView("pipeline")}
            >
              Pipeline Builder
            </Button>
            {/* <Button
              variant={activeView === "graph" ? "default" : "ghost"}
              onClick={() => setActiveView("graph")}
            >
              Knowledge Graph
            </Button> */}
            <Button
              variant={activeView === "vaults" ? "default" : "ghost"}
              onClick={() => setActiveView("vaults")}
              className="gap-2"
            >
              <FolderOpen className="w-4 h-4" />
              Vaults
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate("/templates")}
              className="gap-2"
            >
              <BookOpen className="w-4 h-4" />
              Templates
            </Button>
          </div>
        </div>
      </nav>

      <main className="pt-20">
        {activeView === "home" && <Hero onGetStarted={() => setActiveView("pipeline")} />}
        {activeView === "pipeline" && <PipelineBuilder />}
        {activeView === "graph" && <KnowledgeGraph />}
        {activeView === "vaults" && <Vaults />}
      </main>

      <Footer />
    </div>
  );
};

export default Index;