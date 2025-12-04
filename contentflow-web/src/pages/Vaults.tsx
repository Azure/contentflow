import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { VaultCard } from "@/components/vaults/VaultCard";
import { VaultContentView } from "@/components/vaults/VaultContentView";
import { CreateVaultDialog } from "@/components/vaults/CreateVaultDialog";
import { UploadContentDialog } from "@/components/vaults/UploadContentDialog";
import { Plus, Search, ArrowLeft } from "lucide-react";
import { toast } from "sonner";

interface Vault {
  id: string;
  name: string;
  description: string;
  pipelineId: string;
  pipelineName: string;
  tags: string[];
  documentCount: number;
  createdAt: Date;
  updatedAt: Date;
}

interface ContentFile {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadedAt: Date;
  status: "processing" | "ready" | "error";
  extractedEntities?: number;
}

export const Vaults = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [selectedVaultId, setSelectedVaultId] = useState<string | null>(null);
  const [viewingVaultId, setViewingVaultId] = useState<string | null>(null);

  // Mock pipelines data
  const pipelines = [
    { id: "p1", name: "Document Processing Pipeline" },
    { id: "p2", name: "Internal Docs Pipeline" },
    { id: "p3", name: "Research Content Pipeline" },
  ];

  // Mock data - replace with actual API calls
  const [vaults, setVaults] = useState<Vault[]>([
    {
      id: "1",
      name: "Research Papers Collection",
      description: "Academic papers and research documents for ML/AI domain knowledge",
      pipelineId: "p1",
      pipelineName: "Document Processing Pipeline",
      tags: ["research", "ml", "ai"],
      documentCount: 45,
      createdAt: new Date("2024-01-15"),
      updatedAt: new Date("2024-03-10"),
    },
    {
      id: "2",
      name: "Company Documentation",
      description: "Internal company docs, policies, and procedures",
      pipelineId: "p2",
      pipelineName: "Internal Docs Pipeline",
      tags: ["internal", "policies"],
      documentCount: 23,
      createdAt: new Date("2024-02-01"),
      updatedAt: new Date("2024-03-08"),
    },
    {
      id: "3",
      name: "Technical Specifications",
      description: "API documentation, architecture diagrams, and technical specs",
      pipelineId: "p1",
      pipelineName: "Document Processing Pipeline",
      tags: ["technical", "api", "architecture"],
      documentCount: 67,
      createdAt: new Date("2024-01-20"),
      updatedAt: new Date("2024-03-12"),
    },
  ]);

  // Mock content data
  const [vaultContent] = useState<Record<string, ContentFile[]>>({
    "1": [
      {
        id: "f1",
        name: "Attention Is All You Need.pdf",
        type: "pdf",
        size: 2456789,
        uploadedAt: new Date("2024-03-10T14:30:00"),
        status: "ready",
        extractedEntities: 89,
      },
      {
        id: "f2",
        name: "BERT Pre-training of Deep Bidirectional Transformers.pdf",
        type: "pdf",
        size: 1234567,
        uploadedAt: new Date("2024-03-09T10:15:00"),
        status: "ready",
        extractedEntities: 76,
      },
      {
        id: "f3",
        name: "GPT-3 Language Models are Few-Shot Learners.pdf",
        type: "pdf",
        size: 3456789,
        uploadedAt: new Date("2024-03-08T16:45:00"),
        status: "processing",
      },
    ],
    "2": [
      {
        id: "f4",
        name: "Employee Handbook 2024.docx",
        type: "docx",
        size: 567890,
        uploadedAt: new Date("2024-03-08T09:00:00"),
        status: "ready",
        extractedEntities: 34,
      },
    ],
    "3": [
      {
        id: "f5",
        name: "API Documentation v2.1.pdf",
        type: "pdf",
        size: 987654,
        uploadedAt: new Date("2024-03-12T11:20:00"),
        status: "ready",
        extractedEntities: 156,
      },
      {
        id: "f6",
        name: "System Architecture Overview.pptx",
        type: "pptx",
        size: 4567890,
        uploadedAt: new Date("2024-03-11T15:30:00"),
        status: "ready",
        extractedEntities: 92,
      },
    ],
  });

  const handleCreateVault = (vaultData: any) => {
    const pipeline = pipelines.find(p => p.id === vaultData.pipelineId);
    const newVault: Vault = {
      id: Date.now().toString(),
      name: vaultData.name,
      description: vaultData.description,
      pipelineId: vaultData.pipelineId,
      pipelineName: pipeline?.name || "Unknown Pipeline",
      tags: vaultData.tags,
      documentCount: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    setVaults([...vaults, newVault]);
    setIsCreateDialogOpen(false);
    toast.success("Vault created successfully!");
  };

  const handleUploadComplete = () => {
    // Mock upload handling - refresh vault data
    setIsUploadDialogOpen(false);
    
    // Update document count for the selected vault
    if (selectedVaultId) {
      setVaults(vaults.map(v => 
        v.id === selectedVaultId 
          ? { ...v, documentCount: v.documentCount + 1, updatedAt: new Date() }
          : v
      ));
    }
  };

  const handleViewVault = (vaultId: string) => {
    setViewingVaultId(vaultId);
  };

  const handleUploadToVault = (vaultId: string) => {
    setSelectedVaultId(vaultId);
    setIsUploadDialogOpen(true);
  };

  const handleEditVault = (vaultId: string) => {
    toast.info("Edit vault functionality coming soon!");
  };

  const handleDeleteVault = (vaultId: string) => {
    const vault = vaults.find(v => v.id === vaultId);
    if (vault) {
      setVaults(vaults.filter(v => v.id !== vaultId));
      toast.success(`Vault "${vault.name}" deleted successfully!`);
    }
  };

  const handleDeleteFile = (fileId: string) => {
    toast.success("File deleted successfully!");
  };

  const handleViewFile = (fileId: string) => {
    toast.info("File viewer coming soon!");
  };

  const filteredVaults = vaults.filter(vault =>
    vault.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    vault.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    vault.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const viewingVault = viewingVaultId ? vaults.find(v => v.id === viewingVaultId) : null;
  const currentContent = viewingVaultId ? (vaultContent[viewingVaultId] || []) : [];

  // Vault detail view
  if (viewingVault) {
    return (
      <div className="container mx-auto p-8">
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => setViewingVaultId(null)}
            className="gap-2 mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Vaults
          </Button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2">{viewingVault.name}</h1>
              <p className="text-lg text-muted-foreground mb-4">
                {viewingVault.description}
              </p>
              <div className="flex items-center gap-4">
                <div className="text-sm">
                  <span className="text-muted-foreground">Pipeline: </span>
                  <span className="font-semibold">{viewingVault.pipelineName}</span>
                </div>
                <div className="text-sm">
                  <span className="text-muted-foreground">Documents: </span>
                  <span className="font-semibold">{viewingVault.documentCount}</span>
                </div>
              </div>
            </div>
            <Button
              onClick={() => handleUploadToVault(viewingVault.id)}
              className="gap-2"
            >
              <Plus className="w-4 h-4" />
              Upload Content
            </Button>
          </div>
        </div>

        <VaultContentView
          vaultId={viewingVault.id}
          content={currentContent}
          onDelete={handleDeleteFile}
          onView={handleViewFile}
        />

        <UploadContentDialog
          open={isUploadDialogOpen}
          onOpenChange={setIsUploadDialogOpen}
          vaultId={selectedVaultId || ""}
          vaultName={viewingVault.name}
          onUploadComplete={handleUploadComplete}
        />
      </div>
    );
  }

  // Vaults list view
  return (
    <div className="container mx-auto p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-bold mb-2">Content Vaults</h1>
          <p className="text-lg text-muted-foreground">
            Manage your knowledge bases and document collections
          </p>
        </div>
        <Button onClick={() => setIsCreateDialogOpen(true)} className="gap-2">
          <Plus className="w-4 h-4" />
          Create Vault
        </Button>
      </div>

      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            placeholder="Search vaults by name, description, or tags..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 text-lg py-6"
          />
        </div>
      </div>

      {filteredVaults.length === 0 ? (
        <div className="text-center py-16">
          <h3 className="text-xl font-semibold mb-2">No vaults found</h3>
          <p className="text-muted-foreground mb-4">
            {searchQuery
              ? "Try adjusting your search query"
              : "Create your first vault to get started"}
          </p>
          {!searchQuery && (
            <Button onClick={() => setIsCreateDialogOpen(true)} className="gap-2">
              <Plus className="w-4 h-4" />
              Create Your First Vault
            </Button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredVaults.map((vault) => (
            <VaultCard
              key={vault.id}
              vault={vault}
              onView={handleViewVault}
              onUpload={handleUploadToVault}
              onEdit={handleEditVault}
              onDelete={handleDeleteVault}
            />
          ))}
        </div>
      )}

      <CreateVaultDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        onCreateVault={handleCreateVault}
        pipelines={pipelines}
      />

      <UploadContentDialog
        open={isUploadDialogOpen}
        onOpenChange={setIsUploadDialogOpen}
        vaultId={selectedVaultId || ""}
        vaultName={vaults.find(v => v.id === selectedVaultId)?.name || ""}
        onUploadComplete={handleUploadComplete}
      />
    </div>
  );
};
