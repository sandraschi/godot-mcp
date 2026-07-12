import { Activity, Search, Shield, Wrench } from "lucide-react";
import { useMemo, useState } from "react";

interface ToolDef {
	name: string;
	description: string;
	annotation: "READ_ONLY" | "MUTATING" | "DESTRUCTIVE";
	version: string;
}

const coreTools: ToolDef[] = [
	{ name: "godot_status", description: "Engine availability, version, scene info, node tree", annotation: "READ_ONLY", version: "0.1.0" },
	{ name: "godot_import_stl", description: "Import STL mesh from qcad-mcp pipeline as MeshInstance3D", annotation: "MUTATING", version: "0.1.0" },
	{ name: "godot_spawn_particles", description: "Create GPU particle system with emission, lifetime, velocity config", annotation: "MUTATING", version: "0.1.0" },
	{ name: "godot_load_velocity", description: "Load FluidX3D velocity field data and bind to particle system", annotation: "MUTATING", version: "0.1.0" },
	{ name: "godot_animate_streamline", description: "Animate particles along streamlines from velocity field", annotation: "MUTATING", version: "0.1.0" },
	{ name: "godot_set_material", description: "Assign PBR materials with albedo, roughness, metallic to meshes", annotation: "MUTATING", version: "0.1.0" },
	{ name: "godot_add_light", description: "Add OmniLight3D, SpotLight3D, or DirectionalLight3D", annotation: "MUTATING", version: "0.1.0" },
	{ name: "godot_create_camera", description: "Create Camera3D with transform, FOV, near/far planes", annotation: "MUTATING", version: "0.1.0" },
	{ name: "godot_export_web", description: "Export scene to HTML5/WebAssembly for Web deployment", annotation: "MUTATING", version: "0.1.0" },
	{ name: "godot_run_simulation", description: "Trigger physics simulation step or particle system run", annotation: "MUTATING", version: "0.1.0" },
	{ name: "godot_list_scenes", description: "List all scenes currently loaded in the Godot editor", annotation: "READ_ONLY", version: "0.1.0" },
	{ name: "godot_get_node_tree", description: "Get full node tree of the active scene", annotation: "READ_ONLY", version: "0.1.0" },
];

const annotationColor = (a: ToolDef["annotation"]) => {
	switch (a) {
		case "READ_ONLY": return "bg-emerald-500/20 text-emerald-400";
		case "MUTATING": return "bg-blue-500/20 text-blue-400";
		case "DESTRUCTIVE": return "bg-red-500/20 text-red-400";
	}
};

export default function ToolsTools() {
	const [search, setSearch] = useState("");

	const filtered = useMemo(() => {
		if (!search.trim()) return coreTools;
		const q = search.toLowerCase();
		return coreTools.filter((t) => t.name.toLowerCase().includes(q) || t.description.toLowerCase().includes(q));
	}, [search]);

	return (
		<div className="space-y-6 max-w-5xl">
			<h1 className="text-2xl font-bold text-white flex items-center gap-3">
				<Wrench className="text-blue-400" /> Tools Analysis
			</h1>
			<div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-white/10 bg-[#1e1e26] max-w-sm">
				<Search size={14} className="text-slate-300 shrink-0" />
				<input
					type="text"
					placeholder="Search tools..."
					value={search}
					onChange={(e) => setSearch(e.target.value)}
					className="bg-transparent text-sm text-slate-200 placeholder-slate-600 outline-none w-full"
				/>
			</div>
			<div className="grid grid-cols-1 md:grid-cols-2 gap-3">
				{filtered.map((tool) => (
					<div key={tool.name} className="bg-[#1e1e26] border border-white/10 rounded-2xl p-4 space-y-2">
						<div className="flex items-center justify-between">
							<code className="text-blue-400 font-bold text-sm">{tool.name}()</code>
							<div className="flex items-center gap-2">
								<span className={`text-xs font-bold uppercase px-2 py-0.5 rounded ${annotationColor(tool.annotation)}`}>
									<Shield size={10} className="inline mr-1" />
									{tool.annotation}
								</span>
								<span className="text-xs text-slate-500">v{tool.version}</span>
							</div>
						</div>
						<p className="text-sm text-slate-400">{tool.description}</p>
						<div className="flex items-center gap-1.5 text-xs text-slate-500">
							<Activity size={12} />
							<span>{tool.annotation === "READ_ONLY" ? "No side effects" : "Modifies engine state"}</span>
						</div>
					</div>
				))}
			</div>
			<p className="text-sm text-slate-500">{filtered.length} of {coreTools.length} tools</p>
		</div>
	);
}
