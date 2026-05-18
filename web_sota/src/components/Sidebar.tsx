import { motion } from "framer-motion";
import {
	Archive,
	Book,
	BookOpen,
	Box,
	Code2,
	Database,
	HelpCircle,
	LayoutDashboard,
	LayoutGrid,
	Logs,
	MessageSquare,
	Package,
	Play,
	Settings,
	Sparkles,
	Wrench,
} from "lucide-react";
import { NavLink } from "react-router-dom";

const navGroups = [
	{
		label: "Core",
		items: [
			{ path: "/", label: "Dashboard", icon: LayoutDashboard },
			{ path: "/models", label: "Models", icon: Box },
			{ path: "/logs", label: "Logs", icon: Logs },
		],
	},
	{
		label: "Fleet",
		items: [
			{ path: "/apps", label: "Apps Hub", icon: LayoutGrid },
			{ path: "/tools", label: "Tools", icon: Wrench },
			{ path: "/api-docs", label: "API Docs", icon: Code2 },
		],
	},
	{
		label: "Marketplace",
		items: [
			{ path: "/marketplace", label: "Marketplace", icon: Package },
			{ path: "/depot", label: "Depot", icon: Database },
		],
	},
	{
		label: "Agentic",
		items: [
			{ path: "/workflows", label: "Workflows", icon: Play },
			{ path: "/prefabs", label: "Prefabs", icon: Box },
			{ path: "/prompts", label: "Prompts", icon: Sparkles },
		],
	},
	{
		label: "Advanced",
		items: [
			{ path: "/bundles", label: "Bundles", icon: Archive },
			{ path: "/skills", label: "Skills", icon: BookOpen },
			{ path: "/chat", label: "Chat", icon: MessageSquare },
		],
	},
	{
		label: "Support",
		items: [
			{ path: "/settings", label: "Settings", icon: Settings },
			{ path: "/help", label: "Help", icon: HelpCircle },
		],
	},
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
			<nav className="flex-1 p-3 overflow-y-auto space-y-4">
				{navGroups.map((group) => (
					<div key={group.label}>
						{!collapsed && (
							<p className="px-3 mb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
								{group.label}
							</p>
						)}
						<div className="space-y-0.5">
							{group.items.map((item) => (
								<NavLink
									key={item.path}
									to={item.path}
									end={item.path === "/"}
									className={({ isActive }) =>
										`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
											isActive
												? "bg-blue-600/20 text-blue-400"
												: "text-slate-400 hover:text-slate-200 hover:bg-white/[0.08]"
										}`
									}
								>
									<item.icon size={16} className="shrink-0" />
									{!collapsed && (
										<span className="whitespace-nowrap">{item.label}</span>
									)}
								</NavLink>
							))}
						</div>
					</div>
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
