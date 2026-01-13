import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { VaultCard } from "@/components/vaults/VaultCard";
import { VaultExecutionsView } from "@/components/vaults/VaultExecutionsView";
import { CreateVaultDialog } from "@/components/vaults/CreateVaultDialog";
import { UpdateVaultDialog } from "@/components/vaults/UpdateVaultDialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Plus, Search, ArrowLeft, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { getVaults, createVault, updateVault, deleteVault } from "@/lib/api/vaultsApi";
import { getPipelines } from "@/lib/api/pipelinesApi";
import type { Vault, CreateVaultRequest, UpdateVaultRequest } from "@/types/components";
import type { Pipeline } from "@/types/components";

export const Vaults = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isUpdateDialogOpen, setIsUpdateDialogOpen] = useState(false);
  const [vaultToEdit, setVaultToEdit] = useState<Vault | null>(null);
  const [viewingVaultId, setViewingVaultId] = useState<string | null>(null);
  const [vaults, setVaults] = useState<Vault[]>([]);
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [vaultToDelete, setVaultToDelete] = useState<string | null>(null);

  // Fetch vaults and pipelines on mount
  useEffect(() => {
    
    // Get vault-id from query params to view specific vault
    const params = new URLSearchParams(window.location.search);
    const vaultIdFromParams = params.get("vaultId");
    if (vaultIdFromParams) {
      setViewingVaultId(vaultIdFromParams);
    }

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
      toast.error("Failed to load vaults. Please try again.");
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
      toast.error("Failed to create vault. " + (error?.message || ""));
    } finally {
      setIsUpdating(false);
    }
  };

  const handleViewVault = (vaultId: string) => {
    setViewingVaultId(vaultId);
    // update URL params
    const params = new URLSearchParams(window.location.search);
    params.set("vaultId", vaultId);
    const newUrl = window.location.pathname + `?${params.toString()}`;
    window.history.replaceState({}, "", newUrl);
  };

  const handleEditVault = (vaultId: string) => {
    const vault = vaults.find(v => v.id === vaultId);
    if (vault) {
      setVaultToEdit(vault);
      setIsUpdateDialogOpen(true);
    }
  };

  const handleUpdateVault = async (vaultId: string, vaultData: UpdateVaultRequest) => {
    setIsUpdating(true);
    try {
      const updatedVault = await updateVault(vaultId, vaultData);
      setVaults(vaults.map(v => v.id === vaultId ? updatedVault : v));
      setIsUpdateDialogOpen(false);
      setVaultToEdit(null);
      toast.success("Vault updated successfully!");
    } catch (error) {
      console.error("Error updating vault:", error);
      toast.error("Failed to update vault. " + (error?.message || ""));
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteVault = async (vaultId: string) => {
    setVaultToDelete(vaultId);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteVault = async () => {
    if (!vaultToDelete) return;

    setIsUpdating(true);
    try {
      await deleteVault(vaultToDelete);
      setVaults(vaults.filter(v => v.id !== vaultToDelete));
      toast.success("Vault deleted successfully!");
      setDeleteDialogOpen(false);
      setVaultToDelete(null);
    } catch (error) {
      console.error("Error deleting vault:", error);
      toast.error("Failed to delete vault. " + (error?.message || ""));
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
            onClick={() => {
              setViewingVaultId(null); 
              // remove vaultId from URL params
              const params = new URLSearchParams(window.location.search);
              params.delete("vaultId");
              const newUrl = window.location.pathname + (params.toString() ? `?${params.toString()}` : "");
              window.history.replaceState({}, "", newUrl);
            }}
            className="gap-2 mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Vaults
          </Button>
        </div>

        <VaultExecutionsView
          vault={viewingVault}
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

      <UpdateVaultDialog
        open={isUpdateDialogOpen}
        onOpenChange={setIsUpdateDialogOpen}
        vault={vaultToEdit}
        onUpdateVault={handleUpdateVault}
        isLoading={isUpdating}
      />

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Vault</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{vaultToDelete ? vaults.find(v => v.id === vaultToDelete)?.name : ''}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDeleteDialogOpen(false);
                setVaultToDelete(null);
              }}
              disabled={isUpdating}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDeleteVault}
              disabled={isUpdating}
            >
              {isUpdating ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
