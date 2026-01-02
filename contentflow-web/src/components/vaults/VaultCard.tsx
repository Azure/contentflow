import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Folder,
  Settings,
  Trash2,
  Eye,
} from "lucide-react";

import type { Vault } from "@/types/components";

interface VaultCardProps {
  vault: Vault;
  onView: (vaultId: string) => void;
  onEdit: (vaultId: string) => void;
  onDelete: (vaultId: string) => void;
}

export const VaultCard = ({
  vault,
  onView,
  onEdit,
  onDelete,
}: VaultCardProps) => {
  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(date);
  };

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow group">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-3">
          <div className="p-3 bg-gradient-primary rounded-lg">
            <Folder className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-semibold mb-1">{vault.name}</h3>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {vault.description}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            size="icon"
            variant="ghost"
            onClick={() => onEdit(vault.id)}
            title="Edit vault"
          >
            <Settings className="w-4 h-4" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            onClick={() => onDelete(vault.id)}
            title="Delete vault"
          >
            <Trash2 className="w-4 h-4 text-destructive" />
          </Button>
        </div>
      </div>

      <div className="space-y-3 mb-4">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Pipeline:</span>
          <Badge variant="secondary">{vault.pipeline_name || "Unknown"}</Badge>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Status:</span>
          <Badge variant={vault.enabled !== false ? "default" : "outline"}>
            {vault.enabled !== false ? "Enabled" : "Disabled"}
          </Badge>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Last updated:</span>
          <span>{formatDate(new Date(vault.updated_at))}</span>
        </div>
      </div>

      {vault.tags && vault.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {vault.tags.map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 pt-4 border-t">
        <Button
          className="flex-1 gap-2"
          variant="default"
          onClick={() => onView(vault.id)}
        >
          <Eye className="w-4 h-4" />
          View Executions
        </Button>
      </div>
    </Card>
  );
};
