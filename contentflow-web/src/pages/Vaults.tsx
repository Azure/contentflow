import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { VaultCard } from "@/components/vaults/VaultCard";
import { VaultExecutionsView } from "@/components/vaults/VaultExecutionsView";
import { CreateVaultDialog } from "@/components/vaults/CreateVaultDialog";
import { Plus, Search, ArrowLeft, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { getVaults, createVault, updateVault, deleteVault } from "@/lib/api/vaultsApi";
import { getPipelines } from "@/lib/api/pipelinesApi";
import type { Vault, CreateVaultRequest, UpdateVaultRequest } from "@/types/components";
import type { Pipeline } from "@/types/components";

export const Vaults = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [viewingVaultId, setViewingVaultId] = useState<string | null>(null);
  const [vaults, setVaults] = useState<Vault[]>([]);
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);

  // Fetch vaults and pipelines on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [vaultsData, pipelinesData] = await Promise.all([
        getVaults(),
        getPipelines(),
      ]);
      setVaults(vaultsData);
      setPipelines(pipelinesData);
    } catch (error) {
      console.error("Error loading data:", error);
      toast.error("Failed to load vaults and pipelines");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateVault = async (vaultData: CreateVaultRequest) => {
    setIsUpdating(true);
    try {
      const newVault = await createVault(vaultData);
      setVaults([...vaults, newVault]);
      setIsCreateDialogOpen(false);
      toast.success("Vault created successfully!");
    } catch (error) {
      console.error("Error creating vault:", error);
      toast.error("Failed to create vault");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleViewVault = (vaultId: string) => {
    setViewingVaultId(vaultId);
  };

  const handleEditVault = (vaultId: string) => {
    // TODO: Implement edit dialog
    toast.info("Edit vault functionality coming soon!");
  };

  const handleDeleteVault = async (vaultId: string) => {
    const vault = vaults.find(v => v.id === vaultId);
    if (!vault) return;

    if (!confirm(`Are you sure you want to delete "${vault.name}"?`)) {
      return;
    }

    setIsUpdating(true);
    try {
      await deleteVault(vaultId);
      setVaults(vaults.filter(v => v.id !== vaultId));
      toast.success(`Vault "${vault.name}" deleted successfully!`);
    } catch (error) {
      console.error("Error deleting vault:", error);
      toast.error("Failed to delete vault");
    } finally {
      setIsUpdating(false);
    }
  };

  const filteredVaults = vaults.filter(vault =>
    vault.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    vault.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    vault.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const viewingVault = viewingVaultId ? vaults.find(v => v.id === viewingVaultId) : null;

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
            <div className="flex-1">
              <h1 className="text-4xl font-bold mb-2">{viewingVault.name}</h1>
              <p className="text-lg text-muted-foreground mb-4">
                {viewingVault.description || "No description"}
              </p>
              <div className="flex items-center gap-4">
                <div className="text-sm">
                  <span className="text-muted-foreground">Pipeline: </span>
                  <span className="font-semibold">{viewingVault.pipeline_name || "Unknown"}</span>
                </div>
                {viewingVault.tags && viewingVault.tags.length > 0 && (
                  <div className="flex gap-2">
                    {viewingVault.tags.map((tag) => (
                      <span key={tag} className="text-xs px-2 py-1 bg-secondary rounded-full">
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <VaultExecutionsView
          vaultId={viewingVault.id}
          pipelineId={viewingVault.pipeline_id}
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
        <Button onClick={() => setIsCreateDialogOpen(true)} className="gap-2" disabled={isUpdating}>
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

      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : filteredVaults.length === 0 ? (
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
        isLoading={isUpdating}
      />
    </div>
  );
};
