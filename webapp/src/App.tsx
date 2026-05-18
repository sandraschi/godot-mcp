import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import HelpPage from "./pages/HelpPage";
import LogsPage from "./pages/LogsPage";
import ModelsPage from "./pages/ModelsPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
	return (
		<AppLayout>
			<Routes>
				<Route path="/" element={<Dashboard />} />
				<Route path="/models" element={<ModelsPage />} />
				<Route path="/logs" element={<LogsPage />} />
				<Route path="/settings" element={<SettingsPage />} />
				<Route path="/help" element={<HelpPage />} />
				<Route path="*" element={<Navigate to="/" replace />} />
			</Routes>
		</AppLayout>
	);
}
