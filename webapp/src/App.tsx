import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import ApiDocsPage from "./pages/ApiDocsPage";
import AppsHub from "./pages/AppsHub";
import ChatPage from "./pages/ChatPage";
import Dashboard from "./pages/Dashboard";
import HelpPage from "./pages/HelpPage";
import LogsPage from "./pages/LogsPage";
import ModelsPage from "./pages/ModelsPage";
import SettingsPage from "./pages/SettingsPage";
import ToolsTools from "./pages/ToolsTools";

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
				<Route path="/settings" element={<SettingsPage />} />
				<Route path="/help" element={<HelpPage />} />
				<Route path="*" element={<Navigate to="/" replace />} />
			</Routes>
		</AppLayout>
	);
}
