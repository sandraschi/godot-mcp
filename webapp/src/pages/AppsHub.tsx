import { Activity, Server, Wifi } from "lucide-react";
import { useEffect, useState } from "react";

interface ServiceCard {
	name: string;
	port: number;
	description: string;
}

const fleetServices: ServiceCard[] = [
	{ name: "godot-mcp", port: 10993, description: "Godot 4.0 engine control & visualization" },
	{ name: "qcad-mcp", port: 10966, description: "DXF/DWG floor plans → STL extrusion" },
	{ name: "freecad-mcp", port: 10944, description: "STL → solid → BIM → IFC" },
	{ name: "resonite-mcp", port: 10979, description: "Social XR platform for world imports" },
	{ name: "blender-mcp", port: 10848, description: "Advanced materials & rendering" },
	{ name: "multi-backup-mcp", port: 10799, description: "Cloud backups of fleet outputs" },
];

export default function AppsHub() {
	const [localStatus, setLocalStatus] = useState<string | null>(null);

	useEffect(() => {
		fetch("/api/v1/status")
			.then((r) => r.json())
			.then((j) => setLocalStatus(j.service || "unknown"))
			.catch(() => setLocalStatus(null));
	}, []);

	return (
		<div className="space-y-6">
			<h1 className="text-2xl font-bold text-white">Fleet Discovery</h1>
			<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-3">
				<div className="flex items-center gap-2 text-emerald-400">
					<Server size={18} /> This Server
				</div>
				<p className="text-sm text-slate-300">
					{localStatus ? `Service: ${localStatus}` : "Checking..."}
				</p>
				<p className="text-sm text-slate-400">Port: 10992 (frontend) / 10993 (backend)</p>
			</div>
			<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{fleetServices.map((svc) => (
					<div
						key={svc.name}
						className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-3 hover:border-blue-500/20 transition-all"
					>
						<div className="flex items-center justify-between">
							<div className="flex items-center gap-2 text-blue-400">
								<Wifi size={16} />
								<span className="font-bold text-sm">{svc.name}</span>
							</div>
							<span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400">
								:{svc.port}
							</span>
						</div>
						<p className="text-sm text-slate-400">{svc.description}</p>
						<div className="flex items-center gap-1.5 text-xs text-slate-500">
							<Activity size={12} />
							<span>Port {svc.port}</span>
						</div>
					</div>
				))}
			</div>
		</div>
	);
}
