import { AlertTriangle, Box, Camera, CircuitBoard, Cpu, FileText, Lightbulb, Play, RefreshCw, Settings } from "lucide-react";
import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

interface GodotStatus {
	available: boolean;
	path: string;
	host: string;
	ws_port: number;
	ws_connected: boolean;
}

interface StatusData {
	ok: boolean;
	service: string;
	version: string;
	godot: GodotStatus;
}

export default function Dashboard() {
	const [status, setStatus] = useState<StatusData | null>(null);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		apiFetch<StatusData>("/api/v1/status")
			.then(setStatus)
			.catch((e) => setError(e instanceof Error ? e.message : "Failed to reach backend"));
	}, []);

	const g = status?.godot;

	return (
		<div className="space-y-6">
			<h1 className="text-2xl font-bold text-white">Dashboard</h1>
			{error && (
				<div className="flex items-center gap-3 p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
					<AlertTriangle size={16} />
					<span className="flex-1">{error}</span>
					<button
						type="button"
						onClick={() => {
							setError(null);
							apiFetch<StatusData>("/api/v1/status")
								.then(setStatus)
								.catch((e) => setError(e instanceof Error ? e.message : "Failed to reach backend"));
						}}
						className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-500/20 text-red-400 text-xs font-bold hover:bg-red-500/30 transition-all"
					>
						<RefreshCw size={12} /> Retry
					</button>
				</div>
			)}
			<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-3">
					<div className="flex items-center gap-2 text-blue-400">
						<Cpu size={18} /> Godot Engine
					</div>
					<p className="text-sm text-slate-300">
						{!status ? "..." : g?.available ? `Found: ${g.path}` : "Godot not detected"}
					</p>
					<p className="text-sm text-slate-400">
						{!status ? "..." : g?.ws_connected ? "WebSocket connected" : "WebSocket: not connected"}
					</p>
				</div>
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-3">
					<div className="flex items-center gap-2 text-emerald-400">
						<CircuitBoard size={18} /> Server
					</div>
					<p className="text-2xl font-bold text-white">
						{status ? `v${status.version}` : "..."}
					</p>
					<p className="text-sm text-slate-400">
						{status?.service || "godot-mcp"} — {status?.ok ? "Ready" : "Waiting..."}
					</p>
				</div>
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-3">
					<div className="flex items-center gap-2 text-indigo-400">
						<Play size={18} /> Quick Actions
					</div>
					<a href="/models" className="block text-sm text-blue-400 hover:underline">
						Import STL / OBJ Models
					</a>
					<a href="/logs" className="block text-sm text-blue-400 hover:underline">
						View Server Logs
					</a>
					<a href="/settings" className="block text-sm text-blue-400 hover:underline">
						Configure Godot Path
					</a>
				</div>
			</div>
			<div className="grid grid-cols-2 md:grid-cols-5 gap-3">
				{[
					{ href: "/models", icon: Box, label: "Models", desc: "Import STL/OBJ" },
					{ href: "/models", icon: FileText, label: "Velocity", desc: "FluidX3D fields" },
					{ href: "/models", icon: Camera, label: "Cameras", desc: "Scene cameras" },
					{ href: "/models", icon: Lightbulb, label: "Lights", desc: "Dynamic lighting" },
					{ href: "/settings", icon: Settings, label: "Settings", desc: "Godot config" },
				].map((item) => (
					<a
						key={item.href}
						href={item.href}
						className="bg-[#1e1e26] border border-white/10 rounded-2xl p-4 text-center hover:border-blue-500/20 transition-all"
					>
						<item.icon size={24} className="mx-auto mb-2 text-blue-400" />
						<p className="text-sm font-bold text-slate-300">{item.label}</p>
						<p className="text-sm text-slate-400">{item.desc}</p>
					</a>
				))}
			</div>
		</div>
	);
}
