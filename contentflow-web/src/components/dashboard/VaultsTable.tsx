import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, FolderOpen } from "lucide-react";
import { getVaults } from "@/lib/api/vaultsApi";
import type { Vault } from "@/types/components";

export const VaultsTable = () => {
  const [vaults, setVaults] = useState<Vault[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const loadVaults = async () => {
      try {
        setIsLoading(true);
        const data = await getVaults();
        setVaults(data);
        setError(null);
      } catch (err) {
        console.error("Error loading vaults:", err);
        setError("Failed to load vaults");
      } finally {
        setIsLoading(false);
      }
    };

    loadVaults();
  }, []);

  const handleSelectVault = (vaultId: string) => {
    // Navigate to vaults view with the selected vault
    navigate(`/?view=vaults&vaultId=${vaultId}`);
  };

  if (isLoading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center text-destructive h-64 flex items-center justify-center">
          <p>{error}</p>
        </div>
      </Card>
    );
  }

  if (vaults.length === 0) {
    return (
      <Card className="p-6">
        <div className="text-center text-muted-foreground h-64 flex flex-col items-center justify-center gap-3">
          <FolderOpen className="w-8 h-8 opacity-50" />
          <p>No vaults available yet</p>
          <p className="text-sm">Create your first vault to store pipeline results</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden flex flex-col">
      <div className="px-4 py-2 border-b bg-violet-700/10">
        <div className="flex items-center gap-2">
          <FolderOpen className="w-4 h-4 text-secondary" />
          <h3 className="font-semibold text-sm">Available Vaults</h3>
          <span className="ml-auto text-xs text-muted-foreground">{vaults.length} vault{vaults.length !== 1 ? 's' : ''}</span>
        </div>
      </div>
      <div className="overflow-x-auto flex-1 max-h-72">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b bg-muted/30">
              <th className="text-left px-3 py-2 font-semibold text-muted-foreground">Name</th>
              <th className="text-left px-3 py-2 font-semibold text-muted-foreground">Pipeline</th>
              <th className="text-left px-3 py-2 font-semibold text-muted-foreground">Updated</th>
              <th className="text-right px-3 py-2 font-semibold text-muted-foreground">Action</th>
            </tr>
          </thead>
          <tbody className="overflow-x-auto">
            {vaults.map((vault) => (
              <tr key={vault.id} className="border-b hover:bg-muted/30 transition-colors">
                <td className="px-3 py-1.5 font-medium text-foreground text-left truncate" title={vault.name}>{vault.name.length > 16 ? vault.name.slice(0, 16) + "..." : vault.name}</td>
                <td className="px-3 py-1.5 text-muted-foreground truncate" title={vault.pipeline_name}>{vault.pipeline_name?.length > 16 ? vault.pipeline_name.slice(0, 16) + "..." : vault.pipeline_name || "-"}</td>
                <td className="px-3 py-1.5 text-muted-foreground">
                  {new Date(vault.updated_at).toLocaleDateString() + " " + new Date(vault.updated_at).toLocaleTimeString()}
                </td>
                <td className="px-3 py-1.5 text-right">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleSelectVault(vault.id)}
                    className="hover:bg-secondary/10"
                  >
                    Open
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
