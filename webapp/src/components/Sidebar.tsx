import { motion } from "framer-motion";
import {
	Box,
	FileText,
	HelpCircle,
	LayoutDashboard,
	Logs,
	Settings,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const navItems = [
	{ path: "/", label: "Dashboard", icon: LayoutDashboard },
	{ path: "/models", label: "Models", icon: Box },
	{ path: "/logs", label: "Logs", icon: Logs },
	{ path: "/settings", label: "Settings", icon: Settings },
	{ path: "/help", label: "Help", icon: HelpCircle },
];

export default function Sidebar({
	collapsed,
	onToggle,
}: { collapsed: boolean; onToggle: () => void }) {
	return (
		<motion.aside
			animate={{ width: collapsed ? 72 : 240 }}
			className="flex flex-col bg-[#1e1e26] border-r border-white/10 h-full shrink-0 overflow-hidden"
		>
			<div className="h-14 flex items-center gap-3 px-4 border-b border-white/10">
				<Box className="text-blue-400 shrink-0" size={22} />
				{!collapsed && (
					<span className="text-sm font-bold text-white whitespace-nowrap">
						Godot MCP
					</span>
				)}
			</div>
			<nav className="flex-1 p-3 space-y-1 overflow-y-auto">
				{navItems.map((item) => (
					<NavLink
						key={item.path}
						to={item.path}
						end={item.path === "/"}
						className={({ isActive }) =>
							`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
								isActive
									? "bg-blue-600 text-white shadow-lg shadow-blue-600/20"
									: "text-slate-400 hover:text-slate-200 hover:bg-white/[0.12]"
							}`
						}
					>
						<item.icon size={18} className="shrink-0" />
						{!collapsed && (
							<span className="whitespace-nowrap">{item.label}</span>
						)}
					</NavLink>
				))}
			</nav>
			<button
				type="button"
				onClick={onToggle}
				className="p-3 text-sm text-slate-400 hover:text-slate-400 border-t border-white/10"
			>
				{collapsed ? ">>" : "Collapse"}
			</button>
		</motion.aside>
	);
}
