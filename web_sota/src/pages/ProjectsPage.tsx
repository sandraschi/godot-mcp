import { motion } from "framer-motion";
import {
	AlertTriangle,
	Box,
	ExternalLink,
	FolderOpen,
	Gamepad2,
	Loader2,
	RefreshCw,
} from "lucide-react";
import { useEffect, useState } from "react";

interface Sample {
	name: string;
	description: string;
	genre: string;
	source: string;
	type: string;
}

interface Bundle {
	name: string;
	description: string;
	source: string;
	tags: string[];
}

export default function ProjectsPage() {
	const [samples] = useState<Sample[]>([
		{
			name: "2D Platformer",
			description: "Official Godot 2D platformer demo with character controller, platforms, collectibles, and level design.",
			genre: "2D Platformer",
			source: "godot-demo-projects/2d/platformer",
			type: "sample",
		},
		{
			name: "3D Shooter",
			description: "Third-person 3D shooter demo with navigation, AI enemies, health system, and weapon switching.",
			genre: "3D Shooter",
			source: "godot-demo-projects/3d/shooter",
			type: "sample",
		},
		{
			name: "Procedural Dungeon",
			description: "Procedural dungeon generation demo with rooms, corridors, loot placement, and minimap.",
			genre: "Procedural",
			source: "godot-4-procedural-generation",
			type: "sample",
		},
		{
			name: "Heart Platformer",
			description: "Juicy 2D platformer movement template with coyote time, variable jump height, and particle effects.",
			genre: "2D Platformer",
			source: "heart-platformer",
			type: "sample",
		},
		{
			name: "Open World RPG",
			description: "Bethesda-style 3D open world RPG framework with AI, inventory, factions, and quest systems.",
			genre: "RPG",
			source: "skelerealms",
			type: "sample",
		},
		{
			name: "CFD River Flow",
			description: "Computational fluid dynamics visualization: river geometry with GPU particles following velocity streamlines.",
			genre: "Scientific",
			source: "godot-mcp",
			type: "sample",
		},
	]);

	const [bundles, setBundles] = useState<Bundle[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		loadBundles();
	}, []);

	async function loadBundles() {
		setLoading(true);
		setError(null);
		try {
			const files = [
				"2d-platformer.mcpb.json",
				"heart-platformer.mcpb.json",
				"open-world-rpg.mcpb.json",
				"procedural-generation.mcpb.json",
			];
			const loaded: Bundle[] = [];
			for (const f of files) {
				try {
					const res = await fetch(`/samples/bundles/${f}`);
					if (res.ok) {
						const data = await res.json();
						loaded.push({
							name: data.name || f,
							description: data.description || "",
							source: data.source || "",
							tags: data.tags || [],
						});
					}
				} catch {
					// skip missing
				}
			}
			setBundles(loaded);
		} catch {
			setError("Failed to load bundles");
		} finally {
			setLoading(false);
		}
	}

	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			className="space-y-8 p-6"
		>
			<div>
				<h1 className="text-2xl font-bold text-white flex items-center gap-3">
					<Gamepad2 className="text-blue-400" size={28} />
					Projects
				</h1>
				<p className="text-slate-400 mt-1 text-sm">
					Sample Godot 4 projects and MCPB bundles ready to run or inspect.
				</p>
			</div>

			{/* Sample Projects */}
			<section>
				<h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
					<FolderOpen size={20} className="text-amber-500" />
					Sample Games
				</h2>
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{samples.map((s, i) => (
						<motion.div
							key={s.name}
							initial={{ opacity: 0, y: 10 }}
							animate={{ opacity: 1, y: 0 }}
							transition={{ delay: i * 0.05 }}
							className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 hover:border-blue-500/30 transition-all"
						>
							<div className="flex items-start justify-between mb-3">
								<Box className="text-blue-400 shrink-0" size={20} />
								<span className="text-[10px] font-semibold uppercase tracking-widest text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded-full">
									{s.genre}
								</span>
							</div>
							<h3 className="text-white font-semibold mb-1">{s.name}</h3>
							<p className="text-slate-400 text-sm leading-relaxed mb-3">
								{s.description}
							</p>
							<div className="flex items-center justify-between">
								<span className="text-[10px] text-slate-500 truncate max-w-[180px]">
									{s.source}
								</span>
								<button
									type="button"
									onClick={() => window.open(`https://github.com/sandraschi/godot-mcp/tree/master/samples/${s.source}`, "_blank")}
									className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
								>
									<ExternalLink size={12} />
									Open
								</button>
							</div>
						</motion.div>
					))}
				</div>
			</section>

			{/* MCPB Bundles */}
			<section>
				<h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
					<Box size={20} className="text-blue-500" />
					MCPB Bundles
				</h2>
				{loading ? (
					<div className="flex items-center gap-2 text-slate-400 py-8">
						<Loader2 className="animate-spin" size={16} />
						Loading bundles...
					</div>
				) : error ? (
					<div className="flex items-center gap-3 text-red-400 bg-red-500/10 rounded-xl p-4">
						<AlertTriangle size={18} />
						<span className="text-sm">{error}</span>
						<button type="button" onClick={loadBundles} className="ml-auto text-xs text-red-300 hover:text-red-200 flex items-center gap-1">
							<RefreshCw size={12} /> Retry
						</button>
					</div>
				) : bundles.length === 0 ? (
					<p className="text-slate-500 text-sm py-4">No bundles found.</p>
				) : (
					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						{bundles.map((b, i) => (
							<motion.div
								key={b.name}
								initial={{ opacity: 0, y: 10 }}
								animate={{ opacity: 1, y: 0 }}
								transition={{ delay: i * 0.05 }}
								className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5"
							>
								<h3 className="text-white font-semibold mb-1">{b.name}</h3>
								<p className="text-slate-400 text-sm mb-2">{b.description}</p>
								<div className="flex flex-wrap gap-1 mb-2">
									{b.tags.map((t) => (
										<span key={t} className="text-[10px] text-slate-500 bg-white/5 px-2 py-0.5 rounded-full">
											{t}
										</span>
									))}
								</div>
								<span className="text-[10px] text-slate-500">{b.source}</span>
							</motion.div>
						))}
					</div>
				)}
			</section>
		</motion.div>
	);
}
