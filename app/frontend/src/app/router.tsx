import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./layout/AppShell";
import { ActionQueuePage } from "../pages/ActionQueuePage";
import { ClientGeographyPage } from "../pages/ClientGeographyPage";
import { DataContractsPage } from "../pages/DataContractsPage";
import { ProductReferenceIntelligencePage } from "../pages/ProductReferenceIntelligencePage";
import { ReservationIntelligencePage } from "../pages/ReservationIntelligencePage";

export function AppRouter() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<Navigate to="/data" replace />} />
        <Route path="/data" element={<DataContractsPage />} />
        <Route path="/product-references" element={<ProductReferenceIntelligencePage />} />
        <Route path="/reservations" element={<ReservationIntelligencePage />} />
        <Route path="/action-queue" element={<ActionQueuePage />} />
        <Route path="/geography" element={<ClientGeographyPage />} />
      </Route>
    </Routes>
  );
}
