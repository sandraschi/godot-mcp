import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import ApiDocsPage from "./pages/ApiDocsPage";
import AppsHub from "./pages/AppsHub";
import BundlesPage from "./pages/BundlesPage";
import ChatPage from "./pages/ChatPage";
import Dashboard from "./pages/Dashboard";
import DepotPage from "./pages/DepotPage";
import GameBuilderPage from "./pages/GameBuilderPage";
import HelpPage from "./pages/HelpPage";
import LogsPage from "./pages/LogsPage";
import Marketplace from "./pages/Marketplace";
import ModelsPage from "./pages/ModelsPage";
import PrefabsPage from "./pages/PrefabsPage";
import ProjectsPage from "./pages/ProjectsPage";
import PromptsPage from "./pages/PromptsPage";
import SettingsPage from "./pages/SettingsPage";
import ShipPage from "./pages/ShipPage";
import ShipSteamPage from "./pages/ShipSteamPage";
import SkillsPage from "./pages/SkillsPage";
import ToolsTools from "./pages/ToolsTools";
import WorkflowsPage from "./pages/WorkflowsPage";

export default function App() {
	return (
		<AppLayout>
			<Routes>
				<Route path="/" element={<Dashboard />} />
				<Route path="/models" element={<ModelsPage />} />
				<Route path="/logs" element={<LogsPage />} />
				<Route path="/apps" element={<AppsHub />} />
				<Route path="/tools" element={<ToolsTools />} />
				<Route path="/chat" element={<ChatPage />} />
				<Route path="/api-docs" element={<ApiDocsPage />} />
				<Route path="/marketplace" element={<Marketplace />} />
				<Route path="/ship" element={<ShipPage />} />
				<Route path="/ship-steam" element={<ShipSteamPage />} />
				<Route path="/game-builder" element={<GameBuilderPage />} />
				<Route path="/depot" element={<DepotPage />} />
				<Route path="/workflows" element={<WorkflowsPage />} />
				<Route path="/prefabs" element={<PrefabsPage />} />
				<Route path="/projects" element={<ProjectsPage />} />
				<Route path="/prompts" element={<PromptsPage />} />
				<Route path="/bundles" element={<BundlesPage />} />
				<Route path="/skills" element={<SkillsPage />} />
				<Route path="/settings" element={<SettingsPage />} />
				<Route path="/help" element={<HelpPage />} />
				<Route path="*" element={<Navigate to="/" replace />} />
			</Routes>
		</AppLayout>
	);
}
