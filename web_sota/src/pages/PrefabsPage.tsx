import { Box, Layers, Loader2, Sliders, X } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";

interface PrefabParam {
	name: string;
	type: string;
	default: string | number | boolean;
	description: string;
}

interface PrefabDef {
	name: string;
	description: string;
	category: string;
	tags: string[];
	params: PrefabParam[];
}

const categories = ["All", "Lighting", "Camera", "Particles", "Materials"];

const prefabs: PrefabDef[] = [
	{
		name: "three_point_lighting",
		description: "Key, fill, and rim lights for professional scene lighting.",
		category: "Lighting",
		tags: ["lighting", "studio"],
		params: [
			{ name: "key_intensity", type: "number", default: 1.0, description: "Key light intensity" },
			{ name: "fill_intensity", type: "number", default: 0.5, description: "Fill light intensity" },
			{ name: "rim_intensity", type: "number", default: 0.8, description: "Rim light intensity" },
		],
	},
	{
		name: "orbital_camera",
		description: "Camera rig that orbits around a target point.",
		category: "Camera",
		tags: ["camera", "orbit"],
		params: [
			{ name: "target", type: "string", default: "Vector3(0,0,0)", description: "Orbit target position" },
			{ name: "distance", type: "number", default: 5.0, description: "Orbit distance" },
		],
	},
	{
		name: "gpu_particle_burst",
		description: "High-performance GPU particle burst effect.",
		category: "Particles",
		tags: ["particles", "gpu"],
		params: [
			{ name: "count", type: "number", default: 5000, description: "Particle count" },
			{ name: "lifetime", type: "number", default: 2.0, description: "Particle lifetime (seconds)" },
		],
	},
	{
		name: "pbr_metal",
		description: "Metallic PBR material preset with roughness control.",
		category: "Materials",
		tags: ["pbr", "metal"],
		params: [
			{ name: "roughness", type: "number", default: 0.3, description: "Surface roughness" },
			{ name: "metallic", type: "number", default: 1.0, description: "Metallic factor" },
		],
	},
];

export default function PrefabsPage() {
	const [category, setCategory] = useState("All");
	const [applying, setApplying] = useState<string | null>(null);
	const [paramValues, setParamValues] = useState<Record<string, string>>({});
	const [result, setResult] = useState<string | null>(null);
	const [resultLoading, setResultLoading] = useState(false);

	const filtered = category === "All" ? prefabs : prefabs.filter((p) => p.category === category);

	const openApply = (p: PrefabDef) => {
		setApplying(p.name);
		const initial: Record<string, string> = {};
		p.params.forEach((pr) => (initial[pr.name] = String(pr.default ?? "")));
		setParamValues(initial);
		setResult(null);
	};

	const handleApply = async (prefab: PrefabDef) => {
		setResultLoading(true);
		try {
			const args: Record<string, unknown> = { prefab: prefab.name };
			prefab.params.forEach((p) => {
				args[p.name] = paramValues[p.name];
			});
			const r = await fetch("/api/v1/control/tool", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ tool: "prefab_apply", args }),
			});
			const j = await r.json();
			setResult(JSON.stringify(j, null, 2));
		} catch (e) {
			setResult(`Error: ${e}`);
		} finally {
			setResultLoading(false);
		}
	};

	const selected = prefabs.find((p) => p.name === applying);

	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			className="space-y-6 max-w-6xl"
		>
			<h1 className="text-2xl font-bold text-white flex items-center gap-3">
				<Box className="text-amber-500" size={24} /> Prefab Templates
			</h1>
			<div className="flex items-center gap-1.5 flex-wrap">
				<Layers size={14} className="text-slate-400" />
				{categories.map((c) => (
					<button
						key={c}
						type="button"
						onClick={() => setCategory(c)}
						className={`text-xs font-bold px-2.5 py-1 rounded-lg transition-all ${
							category === c
								? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
								: "bg-white/10 text-slate-400 border border-transparent hover:text-slate-300"
						}`}
					>
						{c}
					</button>
				))}
			</div>
			<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
				{filtered.map((p) => (
					<div
						key={p.name}
						className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-3 hover:border-amber-500/30 transition-all"
					>
						<div className="flex items-start justify-between">
							<div>
								<h3 className="text-sm font-bold text-white">{p.name}</h3>
								<span className="text-xs text-amber-400/70 uppercase">{p.category}</span>
							</div>
							<button
								type="button"
								onClick={() => openApply(p)}
								className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/20 text-amber-400 text-xs font-bold hover:bg-amber-500/30 transition-all"
							>
								<Sliders size={12} /> Apply
							</button>
						</div>
						<p className="text-sm text-slate-400">{p.description}</p>
						<div className="flex items-center gap-2 text-xs text-slate-500">
							{/* icons replaced params count */}
							<span>{p.params.length} parameters</span>
						</div>
						{p.tags.length > 0 && (
							<div className="flex flex-wrap gap-1">
								{p.tags.map((t) => (
									<span key={t} className="text-xs bg-white/10 text-slate-400 px-1.5 py-0.5 rounded">
										{t}
									</span>
								))}
							</div>
						)}
					</div>
				))}
			</div>
			{selected && (
				<motion.div
					initial={{ opacity: 0, y: 10 }}
					animate={{ opacity: 1, y: 0 }}
					className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-4"
				>
					<div className="flex items-center justify-between">
						<h2 className="text-sm font-bold text-slate-200">
							Apply: <code className="text-amber-400">{selected.name}</code>
						</h2>
						<button type="button" onClick={() => { setApplying(null); setResult(null); }}>
							<X size={14} className="text-slate-400" />
						</button>
					</div>
					<div className="space-y-3">
						{selected.params.map((pr) => (
							<div key={pr.name}>
								<label className="text-xs text-slate-400 block mb-1">
									{pr.name} <span className="text-slate-600">({pr.type})</span>
								</label>
								<input
									type={pr.type === "number" ? "number" : "text"}
									placeholder={pr.description}
									value={paramValues[pr.name] ?? ""}
									onChange={(e) => setParamValues({ ...paramValues, [pr.name]: e.target.value })}
									className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/10 text-sm text-slate-200 placeholder-slate-600 outline-none"
								/>
							</div>
						))}
					</div>
					<button
						type="button"
						onClick={() => handleApply(selected)}
						disabled={resultLoading}
						className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-500/30 transition-all disabled:opacity-50"
					>
						{resultLoading ? <Loader2 size={14} className="animate-spin" /> : <Sliders size={14} />}
						Apply Prefab
					</button>
					{result && (
						<pre className="p-3 rounded-xl bg-black/40 text-xs text-slate-300 overflow-auto max-h-60 border border-white/10">
							{result}
						</pre>
					)}
				</motion.div>
			)}
		</motion.div>
	);
}
