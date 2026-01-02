import { Button } from "@/components/ui/button";
import { ArrowRight, FileText, Network, Sparkles, Zap } from "lucide-react";

interface HeroProps {
  onGetStarted: () => void;
}

export const Hero = ({ onGetStarted }: HeroProps) => {
  return (
    <div className="relative overflow-hidden">
      {/* Gradient Mesh Background */}
      <div className="absolute inset-0 bg-gradient-mesh opacity-40" />
      
      <div className="container mx-auto px-6 py-20 relative">
        {/* Hero Section */}
        <div className="max-w-4xl mx-auto text-center mb-20">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-secondary/20 border border-secondary/30 mb-6 animate-slide-in">
            <Sparkles className="w-4 h-4 text-secondary" />
            <span className="text-sm font-medium text-secondary">Agentic AI-Powered Content Intelligence</span>
          </div>
          
          <h1 className="font-display text-6xl md:text-7xl font-bold mb-6 text-foreground leading-tight">
            Transform Content Into
            <span className="block bg-gradient-secondary bg-clip-text text-transparent">
              <img src="/contentflow.svg" alt="Connected Knowledge" className="inline-block w-16 h-16 ml-1" /> Connected Knowledge
            </span>
          </h1>
          
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Build intelligent pipelines that crack, extract, and transform unstructured content 
            into living knowledge powered by <img src="/MicrosoftFoundry-e59cae5b.svg" alt="Azure AI Agents" className="inline-block w-6 h-6 ml-1" /> Microsoft Foundry.
          </p>
          
          <div className="flex items-center justify-center gap-4">
            <Button 
              size="lg" 
              onClick={onGetStarted}
              className="bg-gradient-primary hover:opacity-90 text-primary-foreground shadow-lg group"
            >
              Start Building
              <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Button>
            <Button size="lg" variant="outline">
              Watch Demo
            </Button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-6 max-w-6xl mx-auto">
          <FeatureCard
            icon={<Zap className="w-6 h-6" />}
            title="Pipeline Builder"
            description="Design custom processing pipelines with drag-and-drop executors for any content type"
            color="primary"
          />
          <FeatureCard
            icon={<FileText className="w-6 h-6" />}
            title="Smart Extraction"
            description="AI-powered document cracking, entity extraction, and content transformation"
            color="secondary"
          />
          <FeatureCard
            icon={<Network className="w-6 h-6" />}
            title="Connected Knowledge"
            description="Visualize and explore interconnected entities with interactive graph views"
            color="accent"
          />
        </div>

        {/* Visual Element */}
        {/* <div className="mt-20 max-w-5xl mx-auto">
          <div className="relative rounded-2xl overflow-hidden border border-border bg-card shadow-lg">
            <div className="absolute inset-0 bg-gradient-mesh opacity-20" />
            <div className="relative p-12">
              <div className="grid grid-cols-3 gap-8 items-center">
                <ProcessNode label="Upload" active />
                <ProcessNode label="Process" active />
                <ProcessNode label="Visualize" active />
              </div>
            </div>
          </div>
        </div> */}
      </div>
    </div>
  );
};

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: "primary" | "secondary" | "accent";
}

const FeatureCard = ({ icon, title, description, color }: FeatureCardProps) => {
  const colorClasses = {
    primary: "text-primary border-primary/20 bg-primary/5",
    secondary: "text-secondary border-secondary/20 bg-secondary/5",
    accent: "text-accent border-accent/20 bg-accent/5",
  };

  return (
    <div className="p-6 rounded-xl border border-border bg-card hover:shadow-md transition-all duration-300 group">
      <div className={`w-12 h-12 rounded-lg ${colorClasses[color]} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
        {icon}
      </div>
      <h3 className="font-display text-xl font-bold mb-2 text-foreground">{title}</h3>
      <p className="text-muted-foreground">{description}</p>
    </div>
  );
};

const ProcessNode = ({ label, active = false }: { label: string; active?: boolean }) => {
  return (
    <div className="text-center">
      <div className={`w-16 h-16 rounded-xl mx-auto mb-3 flex items-center justify-center transition-all duration-300 ${
        active 
          ? "bg-gradient-secondary shadow-glow animate-pulse-glow" 
          : "bg-muted"
      }`}>
        <div className="w-8 h-8 rounded-lg bg-background/20" />
      </div>
      <span className={`text-sm font-medium ${active ? "text-secondary" : "text-muted-foreground"}`}>
        {label}
      </span>
    </div>
  );
};