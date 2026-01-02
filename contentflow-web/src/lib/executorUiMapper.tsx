import {
  FileText, Brain, GitBranch, Database, FileImage, FileVideo, FileAudio, 
  Languages, Image, Video, Music, Sparkles, Tag, Search, Filter, Combine, 
  Split, Link, FileCode, Mail, Globe, BookOpen, Hash, Clock, AlertCircle, 
  CheckCircle, XCircle, Zap, Settings, FileJson, FileSpreadsheet, Percent, 
  Type, Palette, Film, Wand2, Network, Cloud, HardDrive, FolderInput, Save, 
  CloudUpload, Server, Container, Eye, MessageSquare, FileSearch, Mic, 
  ScanText, BookText, Sparkle, Layers, Box, Workflow,
  Download,
  TableRowsSplit, Square,
  Smile, Folder,
  Shield, Key,
  ArrowRight,
  TextSearch, Map
} from "lucide-react";
import type { ExecutorCatalogDefinition } from "@/types/components";
import { TableRow } from "@/components/ui/table";

/**
 * Extended executor type that includes UI metadata
 */
export interface ExecutorWithUI extends ExecutorCatalogDefinition {
  icon: React.ReactNode;
  color: string;
}

/**
 * Default UI metadata for executors not in the map
 */
const defaultUI = {
  icon: <Settings className="w-5 h-5" />,
  color: "bg-gray-500"
};

/**
 * Map executor IDs to their UI metadata (icon and color)
 */
const executorUIIconMap: Record<string, React.ReactNode> = {
  
  "download": <Download className="w-5 h-5" />,
  "cloud": <Cloud className="w-5 h-5" />,
  "file-text": <FileText className="w-5 h-5" />,
  "file-spreadsheet": <FileSpreadsheet className="w-5 h-5" />,
  "scan-text": <ScanText className="w-5 h-5" />,
  "sparkles": <Sparkles className="w-5 h-5" />,
  "split": <Split className="w-5 h-5" />,
  "table-rows-split": <TableRowsSplit className="w-5 h-5" />,
  "brain": <Brain className="w-5 h-5" />,
  "square": <Square className="w-5 h-5" />,
  "tag": <Tag className="w-5 h-5" />,
  "smile": <Smile className="w-5 h-5" />,
  "folder": <Folder className="w-5 h-5" />,
  "shield": <Shield className="w-5 h-5" />,
  "key": <Key className="w-5 h-5" />,
  "globe": <Globe className="w-5 h-5" />,
  "languages": <Languages className="w-5 h-5" />,
  "forward": <ArrowRight className="w-5 h-5" />,
  "text-search": <TextSearch className="w-5 h-5" />,
  "cloud-upload": <CloudUpload className="w-5 h-5" />,
  "map": <Map className="w-5 h-5" />,
  "filter": <Filter className="w-5 h-5" />,
  "link": <Link className="w-5 h-5" />,
  "combine": <Combine className="w-5 h-5" />,
};

/**
 * Get UI metadata based on executor category
 */
const getCategoryDefaultUI = (category: string): { icon: React.ReactNode; color: string } => {
  const categoryDefaults: Record<string, { icon: React.ReactNode; color: string }> = {
    input: { icon: <FolderInput className="w-5 h-5" />, color: "bg-sky-500" },
    extract: { icon: <FileText className="w-5 h-5" />, color: "bg-red-500" },
    media: { icon: <Film className="w-5 h-5" />, color: "bg-purple-500" },
    transform: { icon: <GitBranch className="w-5 h-5" />, color: "bg-emerald-500" },
    analyse: { icon: <Brain className="w-5 h-5" />, color: "bg-purple-500" },
    enrichment: { icon: <Wand2 className="w-5 h-5" />, color: "bg-purple-600" },
    output: { icon: <Save className="w-5 h-5" />, color: "bg-green-500" },
    utility: { icon: <Settings className="w-5 h-5" />, color: "bg-gray-500" },
    pipeline: { icon: <Network className="w-5 h-5" />, color: "bg-violet-500" },
  };
  
  return categoryDefaults[category] || defaultUI;
};

/** 
 * Get executor icon and color based on category and UI metadata
 */
const getExecutorIcon = (executorCategory: string, executorUIMetadataIcon: string): { icon: React.ReactNode; color: string } => {
  
    const icon = executorUIIconMap[executorUIMetadataIcon] || defaultUI.icon;
    const color = getCategoryDefaultUI(executorCategory).color;
    return { icon, color };
}

/**
 * Enrich executor with UI metadata (icon and color)
 */
export const enrichExecutorWithUI = (executor: ExecutorCatalogDefinition): ExecutorWithUI => {
  const uiMetadata = getExecutorIcon(executor.category, executor.ui_metadata?.icon || "");
  
  return {
    ...executor,
    icon: uiMetadata.icon,
    color: uiMetadata.color,
  };
};

/**
 * Enrich multiple executors with UI metadata
 */
export const enrichExecutorsWithUI = (executors: ExecutorCatalogDefinition[]): ExecutorWithUI[] => {
  return executors.map(enrichExecutorWithUI);
};
