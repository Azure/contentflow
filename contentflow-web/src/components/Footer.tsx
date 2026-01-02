import { useState, useEffect } from "react";
import { Github, Activity, RefreshCw, ChevronDown, ChevronRight } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { getHealthCheck } from "@/lib/api/systemApi";
import { ServiceStatus } from "@/lib/api/apiTypes";

interface ServiceHealthItemProps {
  name: string;
  status: "connected" | "degraded" | "offline";
  details?: ServiceStatus;
  getStatusColor: (status: "connected" | "degraded" | "offline") => string;
}

const ServiceHealthItem = ({ name, status, details, getStatusColor }: ServiceHealthItemProps) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="border rounded-lg">
      <div className="p-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 flex-1">
            <div className={`w-3 h-3 rounded-full ${getStatusColor(status)}`} />
            <span className="text-sm font-medium">{name}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground capitalize">{status}</span>
            {details && (
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                  {isOpen ? (
                    <ChevronDown className="h-3 w-3" />
                  ) : (
                    <ChevronRight className="h-3 w-3" />
                  )}
                </Button>
              </CollapsibleTrigger>
            )}
          </div>
        </div>
        {details && (
          <CollapsibleContent className="pt-2">
            <div className="space-y-1 text-xs text-muted-foreground pl-5 border-t mt-2 pt-2">
              {details.name && (
                <div className="flex justify-between">
                  <span className="font-medium">Service:</span>
                  <span>{details.name}</span>
                </div>
              )}
              {details.response_time_ms !== undefined && (
                <div className="flex justify-between">
                  <span className="font-medium">Response Time:</span>
                  <span>{details.response_time_ms}ms</span>
                </div>
              )}
              {details.message && (
                <div className="flex flex-col gap-1">
                  <span className="font-medium">Message:</span>
                  <span className="text-xs break-words">{details.message}</span>
                </div>
              )}
              {details.error && (
                <div className="flex flex-col gap-1">
                  <span className="font-medium text-red-500">Error:</span>
                  <span className="text-xs text-red-400 break-words">{details.error}</span>
                </div>
              )}
              {details.details && Object.keys(details.details).length > 0 && (
                <div className="flex flex-col gap-1">
                  <span className="font-medium">Details:</span>
                  <textarea className="text-xs bg-muted p-1 rounded overflow-x-auto h-36 max-h-40" readOnly>
                    {JSON.stringify(details.details, null, 2)}
                  </textarea>
                </div>
              )}
              {details.last_checked && (
                <div className="flex justify-between">
                  <span className="font-medium">Last Checked:</span>
                  <span>{new Date(details.last_checked).toLocaleTimeString()}</span>
                </div>
              )}
            </div>
          </CollapsibleContent>
        )}
      </div>
    </Collapsible>
  );
};

interface SystemHealth {
  api: "connected" | "offline";
  systemOverall: "connected" | "degraded" | "offline";
  appConfig: "connected" | "offline";
  cosmosDB: "connected" | "offline";
  blobStorage: "connected" | "offline";
  storageQueue: "connected" | "offline";
  worker?: "connected" | "offline";
  lastChecked: Date;
  serviceDetails: {
    appConfig?: ServiceStatus;
    cosmosDB?: ServiceStatus;
    blobStorage?: ServiceStatus;
    storageQueue?: ServiceStatus;
    worker?: ServiceStatus;
  };
}

export const Footer = () => {
  const [systemHealth, setSystemHealth] = useState<SystemHealth>({
    api: "offline",
    systemOverall: "offline",
    appConfig: "offline",
    cosmosDB: "offline",
    blobStorage: "offline",
    storageQueue: "offline",
    worker: "offline",
    lastChecked: new Date(),
    serviceDetails: {},
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  const checkHealth = async () => {
    setIsRefreshing(true);
    try {
      const healthData = await getHealthCheck();
      
      // If we got here, the API is at least reachable        
      setSystemHealth({
        api: "connected",
        systemOverall: healthData.status === "connected" ? "connected" : healthData.status === "degraded" ? "degraded" : "offline",
        appConfig: healthData.services.app_config?.status === "connected" ? "connected" : "offline",
        cosmosDB: healthData.services.cosmos_db?.status === "connected" ? "connected" : "offline",
        blobStorage: healthData.services.blob_storage?.status === "connected" ? "connected" : "offline",
        storageQueue: healthData.services.storage_queue?.status === "connected" ? "connected" : "offline",
        worker: healthData.services.worker?.status === "connected" ? "connected" : "offline",
        lastChecked: new Date(),
        serviceDetails: {
          appConfig: healthData.services.app_config,
          cosmosDB: healthData.services.cosmos_db,
          blobStorage: healthData.services.blob_storage,
          storageQueue: healthData.services.storage_queue,
          worker: healthData.services.worker,
        },
      });
    } catch (error) {
      setSystemHealth({
        api: "offline",
        systemOverall: "offline",
        appConfig: "offline",
        cosmosDB: "offline",
        blobStorage: "offline",
        storageQueue: "offline",
        worker: "offline",
        lastChecked: new Date(),
        serviceDetails: {},
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {

    checkHealth();
    const interval = setInterval(checkHealth, 600000); // Check every 10 minutes

    return () => clearInterval(interval);
  }, []);

  const getOverallStatus = (): "connected" | "degraded" | "offline" => {
    if (systemHealth.api === "offline") {
      return "offline";
    }
    return systemHealth.systemOverall;
  };

  const getStatusColor = (status: "connected" | "degraded" | "offline") => {
    switch (status) {
      case "connected":
        return "bg-green-500";
      case "degraded":
        return "bg-yellow-500";
      case "offline":
        return "bg-red-500";
    }
  };

  const getStatusText = (status: "connected" | "degraded" | "offline") => {
    switch (status) {
      case "connected":
        return "All systems operational";
      case "degraded":
        return "Some systems degraded";
      case "offline":
        return "Systems offline";
    }
  };

  const overallStatus = getOverallStatus();

  return (
    <footer className="fixed bottom-0 w-full border-t border-border bg-background/80 backdrop-blur-sm">
      <div className="container mx-auto px-6 py-2 flex items-center justify-between">
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <a
            href="https://github.com/Azure/contentflow"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 hover:text-foreground transition-colors"
          >
            <Github className="w-3.5 h-3.5" />
            <span>GitHub</span>
          </a>

          <Dialog>
            <DialogTrigger asChild>
              <button className="flex items-center gap-1.5 hover:text-foreground transition-colors">
                <Activity className="w-3.5 h-3.5" />
                <span>System Health</span>
                <span
                  className={`w-2 h-2 rounded-full ${getStatusColor(overallStatus)} animate-pulse`}
                  title={getStatusText(overallStatus)}
                />
              </button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <DialogTitle>System Health Status</DialogTitle>
                    <DialogDescription>
                      Current status of all ContentFlow services
                    </DialogDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={checkHealth}
                    disabled={isRefreshing}
                    className="h-8 w-8 p-0"
                  >
                    <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                  </Button>
                </div>
              </DialogHeader>
              <div className="space-y-3 py-4">
                <div className="border rounded-lg p-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-3 h-3 rounded-full ${getStatusColor(systemHealth.api)}`}
                      />
                      <span className="text-sm font-medium">API Service</span>
                    </div>
                    <span className="text-sm text-muted-foreground capitalize">
                      {systemHealth.api}
                    </span>
                  </div>
                </div>

                <ServiceHealthItem
                  name="Cosmos DB"
                  status={systemHealth.cosmosDB}
                  details={systemHealth.serviceDetails.cosmosDB}
                  getStatusColor={getStatusColor}
                />

                <ServiceHealthItem
                  name="App Config"
                  status={systemHealth.appConfig}
                  details={systemHealth.serviceDetails.appConfig}
                  getStatusColor={getStatusColor}
                />

                <ServiceHealthItem
                  name="Blob Storage"
                  status={systemHealth.blobStorage}
                  details={systemHealth.serviceDetails.blobStorage}
                  getStatusColor={getStatusColor}
                />

                <ServiceHealthItem
                  name="Storage Queue"
                  status={systemHealth.storageQueue}
                  details={systemHealth.serviceDetails.storageQueue}
                  getStatusColor={getStatusColor}
                />

                <ServiceHealthItem
                  name="Worker Engine"
                  status={systemHealth.worker}
                  details={systemHealth.serviceDetails.worker}
                  getStatusColor={getStatusColor}
                />

                <div className="pt-4 border-t border-border">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>Last checked:</span>
                    <span>{systemHealth.lastChecked.toLocaleTimeString()}</span>
                  </div>
                </div>

                <div className="flex items-center justify-center gap-2 pt-2">
                  <div
                    className={`w-3 h-3 rounded-full ${getStatusColor(overallStatus)}`}
                  />
                  <span className="text-sm font-medium">{getStatusText(overallStatus)}</span>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        <div className="text-xs text-muted-foreground">
          ContentFlow - Build XX.YY.ZZ
        </div>
      </div>
    </footer>
  );
};
