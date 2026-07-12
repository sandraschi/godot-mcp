import {
	BookOpen,
	Box,
	ExternalLink,
	HelpCircle,
	Network,
	Package,
	Wrench,
} from "lucide-react";
import { useState } from "react";

const sections = [
	{ id: "intro", label: "Overview", icon: BookOpen },
	{ id: "tools", label: "MCP Tools", icon: Wrench },
	{ id: "game-builder", label: "Game Builder", icon: Box },
	{ id: "plugins", label: "Plugins", icon: Package },
	{ id: "llm", label: "LLM Setup", icon: Network },
	{ id: "fleet", label: "Fleet", icon: ExternalLink },
	{ id: "godot", label: "Bridge Addon", icon: BookOpen },
	{ id: "links", label: "Links", icon: ExternalLink },
];

export default function HelpPage() {
	const [tab, setTab] = useState("intro");
	return (
		<div className="max-w-4xl space-y-6">
			<h1 className="text-2xl font-bold text-white flex items-center gap-3">
				<HelpCircle className="text-blue-400" /> Help &amp; Reference
			</h1>
			<div className="flex flex-wrap gap-1.5 p-1 bg-white/10 rounded-2xl">
				{sections.map((s) => (
					<button
						type="button"
						key={s.id}
						onClick={() => setTab(s.id)}
						className={`px-3.5 py-2 rounded-xl text-sm font-bold uppercase tracking-wider transition-all ${tab === s.id ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20" : "text-slate-300 hover:text-slate-300"}`}
					>
						<s.icon size={13} className="inline mr-1.5" />
						{s.label}
					</button>
				))}
			</div>
			<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-6 text-sm text-slate-400 leading-relaxed space-y-4">
				{tab === "intro" && (
					<>
						<p><strong className="text-slate-200">Godot MCP</strong> is a FastMCP 3.4 server with 80+ tools for Godot 4 engine control, AI-powered game generation, and cross-repo publishing pipelines.</p>
						<div className="grid grid-cols-2 gap-3 mt-3">
							{[
								["Engine Control", "20 bridge tools: scene, import, particles, cameras, materials, viewport capture, input simulation, procedural textures"],
								["Game Builder", "design_game -> GamePlan -> GDScript -> validate -> test -> dialogue -> export. Full pipeline from prompt to HTML5."],
								["Publishing", "itch.io + Steam via portmanteau tools. Fleet exchange for cross-repo assets."],
								["LLM Detection", "Auto GPU detection, model recommendation by VRAM tier. Default gemma4:12b."],
							].map(([title, desc]) => (
								<div key={title} className="bg-white/10 rounded-xl p-3">
									<p className="text-blue-400 font-bold text-sm">{title}</p>
									<p className="text-xs text-slate-400 mt-1">{desc}</p>
								</div>
							))}
						</div>
					</>
				)}

				{tab === "tools" && (
					<>
						<p><strong className="text-slate-200">80+ MCP tools</strong> across all modules. Key categories:</p>
						<div className="space-y-2 mt-3">
							<h4 className="text-blue-400 font-bold text-sm">Engine Control (20)</h4>
							{[
								["godot_status", "Engine version, FPS, node count, bridge state"],
								["godot_import_stl / glb / obj", "Import 3D meshes (STL binary, GLTF, Wavefront)"],
								["godot_capture_viewport", "Screenshot Godot viewport as PNG"],
								["godot_simulate_input", "Send keyboard events for agent playtesting"],
								["godot_scene", "Portmanteau: add/remove/modify nodes, save scene"],
								["godot_generate_procedural_texture", "Create gradient/noise/checker/solid textures at runtime"],
								["godot_spawn_particles / animate_streamlines", "GPU particles with CFD velocity field advection"],
								["godot_create_camera / add_light / set_material", "Scene setup tools"],
								["godot_export_web", "HTML5/WebAssembly export via godot --headless"],
								["start_bridge", "Auto-launch Godot headless with the bridge addon"],
							].map(([name, desc]) => (
								<div key={name} className="bg-white/10 rounded-xl p-2.5 flex items-start gap-2">
									<code className="text-blue-400 font-bold text-xs shrink-0 w-44">{name}</code>
									<span className="text-xs text-slate-300">{desc}</span>
								</div>
							))}
						</div>
						<div className="space-y-2 mt-4">
							<h4 className="text-green-400 font-bold text-sm">Publishing Portmanteaus</h4>
							{[
								["itch_ops", "status/export/preview/push/latest/ship — one tool for all itch.io operations"],
								["steam_ops", "status/checklist/monetization/stage/prerelease/release/ship — Steam publishing"],
								["fleet_ops", "exchange_status/import/worldlabs_get/stage_mesh/stage_splat/import_mesh"],
							].map(([name, desc]) => (
								<div key={name} className="bg-white/10 rounded-xl p-2.5 flex items-start gap-2">
									<code className="text-green-400 font-bold text-xs shrink-0 w-28">{name}</code>
									<span className="text-xs text-slate-300">{desc}</span>
								</div>
							))}
						</div>
					</>
				)}

				{tab === "game-builder" && (
					<>
						<p><strong className="text-slate-200">Game Builder</strong> — turn a natural language concept into a Godot game.</p>
						<div className="space-y-2 mt-3">
							{[
								["design_game", "LLM creates a GamePlan (title, scenes, scripts, hazards, scoring, NPCs, narrative)"],
								["generate_game_logic", "GDScript generation validated by gdlint + godot --check-only, auto-repaired by LLM"],
								["generate_game_tests", "GUT unit test generation, run via Godot headless"],
								["generate_dialogue", "Creates DialogueManager.gd from NPC data + Dialogic .dtl timelines"],
								["godot_generate_procedural_texture", "Procedural textures for backgrounds, UI, effects"],
								["build_game", "Full pipeline: design -> compose -> logic -> test -> dialogue -> export"],
							].map(([name, desc]) => (
								<div key={name} className="bg-white/10 rounded-xl p-2.5 flex items-start gap-2">
									<code className="text-amber-400 font-bold text-xs shrink-0 w-44">{name}</code>
									<span className="text-xs text-slate-300">{desc}</span>
								</div>
							))}
						</div>
						<p className="mt-3 text-xs text-slate-500">Try: <code className="text-blue-400">just gb-smoke</code> or <code className="text-blue-400">just gb-demo "A 2D platformer"</code></p>
					</>
				)}

				{tab === "plugins" && (
					<>
						<p><strong className="text-slate-200">Community Plugins</strong> — 7 curated Godot plugins installable from the dashboard.</p>
						<div className="space-y-2 mt-3">
							{[
								["Dialogic", "dialogic-godot/dialogic", "Branching dialogue system with timelines and characters"],
								["Godot Behavior Tree", "viniciusgerevini/godot-behavior-tree", "BT-based NPC AI with composite/decorator/leaf nodes"],
								["GUT", "bitwes/Gut", "GDScript unit testing framework with CI support"],
								["Aseprite Wizard", "viniciusgerevini/godot-aseprite-wizard", "Aseprite sprite sheet importer with auto-reimport"],
								["Terrain3D", "TokisanGames/Terrain3D", "High-performance 3D terrain with painting and LOD"],
								["Godot Voxel", "Zylann/godot_voxel", "Voxel terrain engine for block-style worlds"],
								["Godot XR Tools", "GodotVR/godot-xr-tools", "AR/VR interaction toolkit"],
							].map(([name, repo, desc]) => (
								<div key={name} className="bg-white/10 rounded-xl p-2.5">
									<p className="text-blue-400 font-bold text-xs">{name}</p>
									<p className="text-xs text-slate-500">{repo}</p>
									<p className="text-xs text-slate-300 mt-0.5">{desc}</p>
								</div>
							))}
						</div>
						<p className="mt-3 text-xs text-slate-500">Install via <code className="text-blue-400">/plugins</code> page or <code className="text-blue-400">POST /api/v1/plugins/install</code></p>
					</>
				)}

				{tab === "llm" && (
					<>
						<p><strong className="text-slate-200">LLM Setup</strong> — auto-detects your GPU and recommends the best model.</p>
						<p className="text-xs text-slate-500 mt-1">The server probes NVIDIA GPU via nvidia-smi and checks Ollama for installed models.</p>
						<div className="space-y-2 mt-3">
							<h4 className="text-green-400 font-bold text-xs">VRAM-based model recommendations</h4>
							{[
								["32 GB+", "qwen2.5-coder:32b — Monster tier"],
								["20 GB+", "gemma4:12b (default) — High-end"],
								["14 GB+", "qwen2.5-coder:7b — Mid"],
								["10 GB+", "llama3.2:3b — Entry"],
								["6 GB+", "llama3.2:1b — Minimal"],
								["No GPU", "DeepSeek V4 Flash (cloud)"],
							].map(([vram, model]) => (
								<div key={vram} className="bg-white/10 rounded-xl p-2 flex items-center gap-3">
									<span className="text-amber-400 font-bold text-xs w-14">{vram}</span>
									<span className="text-xs text-slate-300">{model}</span>
								</div>
							))}
						</div>
						<p className="mt-3 text-xs text-slate-500">See <code className="text-blue-400">/settings</code> for your GPU detection card. Set cloud API keys there too.</p>
					</>
				)}

				{tab === "pipeline" && (
					<>
						<h3 className="text-lg font-bold text-white mb-2">STL Import Pipeline</h3>
						<div className="space-y-2 mb-6">
							{[
								["1. Export", "qcad-mcp plan_extrude → STL mesh file"],
								["2. Import", "godot-mcp godot_import_stl → MeshInstance3D in scene"],
								["3. Material", "godot_mcp godot_set_material → PBR albedo/roughness/metallic"],
								["4. Light", "godot_mcp godot_add_light → scene illumination"],
								["5. Camera", "godot_mcp godot_create_camera → render viewpoints"],
								["6. Export", "godot_mcp godot_export_web → HTML5 build or Resonite import"],
							].map(([step, desc]) => (
								<div key={step} className="flex gap-3 bg-white/10 rounded-lg p-2.5">
									<span className="text-blue-400 font-bold text-sm shrink-0 w-20">{step}</span>
									<span className="text-sm text-slate-300">{desc}</span>
								</div>
							))}
						</div>

						<h3 className="text-lg font-bold text-white mb-2">Velocity Field Pipeline</h3>
						<div className="space-y-2 mb-6">
							{[
								["1. Simulate", "FluidX3D CFD → velocity field (.vti or raw binary)"],
								["2. Load", "godot_mcp godot_load_velocity → GPU buffer"],
								["3. Spawn", "godot_mcp godot_spawn_particles → emit at sample points"],
								["4. Animate", "godot_mcp godot_animate_streamline → particle advection"],
								["5. Render", "godot_mcp godot_create_camera → capture animation frames"],
								["6. Export", "godot_mcp godot_export_web → interactive Web visualization"],
							].map(([step, desc]) => (
								<div key={step} className="flex gap-3 bg-white/10 rounded-lg p-2.5">
									<span className="text-blue-400 font-bold text-sm shrink-0 w-20">{step}</span>
									<span className="text-sm text-slate-300">{desc}</span>
								</div>
							))}
						</div>

						<h3 className="text-lg font-bold text-white mb-2">Cross-Repo Chain</h3>
						<p className="text-sm text-slate-300 mb-3">
							Chain with <strong className="text-slate-200">qcad-mcp</strong> and{" "}
							<strong className="text-slate-200">resonite-mcp</strong> for full pipeline:
						</p>
						<div className="space-y-2">
							{[
								["qcad-mcp", "plan_extrude → STL (DXF walls to 3D mesh)"],
								["godot-mcp", "godot_import_stl → Godot scene"],
								["FluidX3D", "CFD simulation → velocity field data"],
								["godot-mcp", "godot_load_velocity + godot_spawn_particles → GPU visualization"],
								["godot-mcp", "godot_export_web → HTML5/WebAssembly"],
								["resonite-mcp", "Import HTML5/STL → XR world"],
							].map(([repo, desc]) => (
								<div key={repo} className="flex gap-3 bg-white/10 rounded-lg p-2.5">
									<span className="text-blue-400 font-bold text-sm shrink-0 w-28">{repo}</span>
									<span className="text-sm text-slate-300">{desc}</span>
								</div>
							))}
						</div>
					</>
				)}

				{tab === "fleet" && (
					<>
						<p className="text-sm text-slate-300 mb-3">
							godot-mcp connects to the MCP fleet via shared formats (STL, OBJ) and direct MCP tool chaining:
						</p>
						<div className="space-y-3">
							{[
								["qcad-mcp", "10966", "DXF/DWG → STL extrusion (plan_extrude)", "STL"],
								["freecad-mcp", "10944", "STL → solid → BIM → IFC: mesh_to_solid, bim_create_*", "STL/FCStd"],
								["resonite-mcp", "10979", "Import STL as XR world: static or interactive", "STL"],
								["unity3d-mcp", "10831", "Import STL into Unity game engine scenes", "STL"],
								["blender-mcp", "10848", "Import STL into Blender for advanced materials", "STL"],
								["multi-backup-mcp", "10799", "Backup STL/velocity/outputs to cloud", "any"],
							].map(([repo, port, desc, fmt]) => (
								<div key={repo} className="bg-white/10 rounded-xl p-3">
									<div className="flex items-center gap-2 mb-1">
										<code className="text-blue-400 font-bold text-sm">{repo}</code>
										<span className="text-xs text-slate-500">:{port}</span>
										<span className="text-xs px-2 py-0.5 rounded bg-white/10 text-slate-400">
											{fmt}
										</span>
									</div>
									<p className="text-sm text-slate-300">{desc}</p>
								</div>
							))}
						</div>
					</>
				)}

				{tab === "godot" && (
					<>
						<p>
							<strong className="text-slate-200">Godot MCP Addon</strong> — a GDScript plugin
							must be loaded in the Godot project for MCP to accept commands.
							The addon runs a <strong className="text-slate-200">TCP server</strong> on port 9080
							inside the Godot engine.
						</p>
						<h3 className="text-base font-bold text-white mt-4 mb-2">Auto-install (recommended)</h3>
						<div className="bg-fleet-800 rounded-xl p-4 font-mono text-sm space-y-1 overflow-x-auto">
							<div className="text-emerald-400"># Via CLI — installs addon into your Godot project</div>
							<div className="text-slate-300">just install-addon /path/to/godot/project</div>
							<div className="text-emerald-400">{"\n"}# Or via MCP tool</div>
							<div className="text-slate-300">{'install_godot_addon(project_path="res://path/to/project")'}</div>
						</div>
						<h3 className="text-base font-bold text-white mt-4 mb-2">Manual install</h3>
						<div className="space-y-2">
							<div className="flex gap-3 bg-white/10 rounded-lg p-2.5">
								<span className="text-amber-400 font-bold text-sm shrink-0 w-24">1. Copy file</span>
								<span className="text-sm text-slate-300">
									Copy <code className="text-blue-400">src/godot_mcp/bridge/mcp_bridge.gd</code> to
									your Godot project at <code className="text-blue-400">res://addons/mcp_bridge/mcp_bridge.gd</code>
								</span>
							</div>
							<div className="flex gap-3 bg-white/10 rounded-lg p-2.5">
								<span className="text-amber-400 font-bold text-sm shrink-0 w-24">2. Plugin cfg</span>
								<span className="text-sm text-slate-300">
									Create <code className="text-blue-400">res://addons/mcp_bridge/plugin.cfg</code>:
								</span>
							</div>
						</div>
						<div className="bg-fleet-800 rounded-xl p-4 font-mono text-sm space-y-1 overflow-x-auto mt-2">
							<div className="text-slate-400"># addons/mcp_bridge/plugin.cfg</div>
							<div>[plugin]</div>
							<div>name=MCP Bridge</div>
							<div>description=TCP server for MCP commands</div>
							<div>author=godot-mcp</div>
							<div>version=0.1.0</div>
							<div>script=mcp_bridge.gd</div>
							<div>{"\n"}</div>
							<div className="text-slate-400"># Protocol: JSON-RPC over TCP</div>
							<div>{'{"action": "import_stl", "params": {"path": "model.stl"}, "request_id": "1"}'}</div>
							<div>{'{"action": "result", "data": {"node": "/root/MeshInstance3D", "vertices": 15234}, "request_id": "1"}'}</div>
						</div>
						<p className="text-sm text-slate-400 mt-2">
							3. In Godot, go to Project {'>'} Project Settings {'>'} Autoload and add
							<code className="text-blue-400"> addons/mcp_bridge/mcp_bridge.gd</code> as a singleton.
						</p>
					</>
				)}

				{tab === "links" && (
					<div className="space-y-2">
						{[
							["godotengine.org", "Official Godot Engine website (download + docs)", "https://godotengine.org"],
							["docs.godotengine.org", "Godot 4.0 documentation (stable)", "https://docs.godotengine.org/en/stable/"],
							["docs.godotengine.org/classes", "Godot 4.0 class reference", "https://docs.godotengine.org/en/stable/classes/"],
							["FluidX3D", "Computational Fluid Dynamics on GPU (velocity fields)", "https://github.com/ProjectPhysX/FluidX3D"],
							["qcad-mcp", "DXF/DWG floor plans → STL extrusion (upstream)", "https://github.com/sandraschi/qcad-mcp"],
							["resonite-mcp", "Social XR platform for world imports (downstream)", "https://github.com/sandraschi/resonite-mcp"],
							["freecad-mcp", "STL → solid → BIM → IFC (upstream/downstream)", "https://github.com/sandraschi/freecad-mcp"],
						].map(([label, desc, url]) => (
							<a
								key={url}
								href={url}
								target="_blank"
								rel="noopener noreferrer"
								className="flex items-center justify-between p-3 rounded-xl bg-white/10 hover:bg-white/10 transition-all group"
							>
								<div>
									<span className="text-blue-400 font-bold text-sm group-hover:text-blue-300">
										{label}
									</span>
									<p className="text-sm text-slate-300">{desc}</p>
								</div>
								<ExternalLink size={14} className="text-slate-400 group-hover:text-slate-400" />
							</a>
						))}
					</div>
				)}
			</div>
		</div>
	);
}
