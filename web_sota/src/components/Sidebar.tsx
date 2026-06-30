import { motion } from "framer-motion";
import {
	Archive,
	BookOpen,
	Box,
	ChevronLeft,
	ChevronRight,
	Code2,
	Database,
	Gamepad2,
	HelpCircle,
	LayoutDashboard,
	LayoutGrid,
	Logs,
	MessageSquare,
	Package,
	Play,
	Rocket,
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
		label: "Artifacts",
		items: [
			{ path: "/depot", label: "Artifact Depot", icon: Database },
			{ path: "/marketplace", label: "Browse", icon: Package },
			{ path: "/ship", label: "Ship itch", icon: Rocket },
			{ path: "/ship-steam", label: "Ship Steam", icon: Rocket },
			{ path: "/projects", label: "Projects", icon: Gamepad2 },
		],
	},
	{
		label: "Agentic",
		items: [
			{ path: "/game-builder", label: "Game Builder", icon: Sparkles },
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
			className="flex flex-col bg-fleet-900 border-r border-white/10 h-full shrink-0 overflow-hidden"
		>
			<div className="h-14 flex items-center justify-between gap-3 px-4 border-b border-white/10 shrink-0">
				<div className="flex items-center gap-3 overflow-hidden">
					<Box className="text-amber-400 shrink-0" size={22} />
					{!collapsed && (
						<span className="text-sm font-bold text-white whitespace-nowrap">
							Godot MCP
						</span>
					)}
				</div>
				<button
					type="button"
					onClick={onToggle}
					className="text-slate-400 hover:text-white transition-colors shrink-0"
					title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
				>
					{collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
				</button>
			</div>
			<nav className="flex-1 p-3 overflow-y-auto space-y-4">
				{navGroups.map((group) => (
					<div key={group.label}>
						{!collapsed && (
							<p className="px-3 mb-1 text-xs font-semibold uppercase tracking-widest text-slate-500">
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
												? "bg-amber-500/15 text-amber-400"
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
		</motion.aside>
	);
}
