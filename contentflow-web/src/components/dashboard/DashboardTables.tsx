import { PipelinesTable } from "./PipelinesTable";
import { VaultsTable } from "./VaultsTable";

export const DashboardTables = () => {
  return (
    <div className="grid md:grid-cols-2 gap-6 max-w-6xl mx-auto">
      <PipelinesTable />
      <VaultsTable />
    </div>
  );
};
