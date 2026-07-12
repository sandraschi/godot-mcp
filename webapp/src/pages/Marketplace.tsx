import { AlertTriangle, Download, Filter, Loader2, Package, RefreshCw, Search } from "lucide-react";
import { motion } from "framer-motion";
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch } from "../lib/api";

interface Artifact {
	id: string;
	name: string;
	type: string;
	description: string;
	author: string;
	tags: string[];
	downloads: number;
}

const allTypes = ["All", "Scene", "Mesh", "Material", "Particle", "Script", "Audio"];

const typeColors: Record<string, string> = {
	Scene: "bg-blue-500/20 text-blue-400",
	Mesh: "bg-emerald-500/20 text-emerald-400",
	Material: "bg-purple-500/20 text-purple-400",
	Particle: "bg-amber-500/20 text-amber-400",
	Script: "bg-indigo-500/20 text-indigo-400",
	Audio: "bg-rose-500/20 text-rose-400",
};

export default function Marketplace() {
	const [artifacts, setArtifacts] = useState<Artifact[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [search, setSearch] = useState("");
	const [filterType, setFilterType] = useState("All");

	const load = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const data = await apiFetch<{ artifacts?: Artifact[] }>("/api/v1/artifacts");
			setArtifacts(data.artifacts || []);
		} catch (e) {
			setError(e instanceof Error ? e.message : "Failed to load artifacts");
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => { load(); }, [load]);

	const filtered = useMemo(() => {
		return artifacts.filter((a) => {
			const matchSearch =
				!search ||
				a.name.toLowerCase().includes(search.toLowerCase()) ||
				a.description.toLowerCase().includes(search.toLowerCase());
			const matchType = filterType === "All" || a.type === filterType;
			return matchSearch && matchType;
		});
	}, [artifacts, search, filterType]);

	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			className="space-y-6 max-w-6xl"
		>
			<div className="flex items-center justify-between">
				<h1 className="text-2xl font-bold text-white flex items-center gap-3">
					<Package className="text-amber-500" size={24} /> Artifact Library
				</h1>
			</div>
			<div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
				<div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-white/10 bg-fleet-900 max-w-sm w-full">
					<Search size={14} className="text-slate-300 shrink-0" />
					<input
						type="text"
						placeholder="Search artifacts..."
						value={search}
						onChange={(e) => setSearch(e.target.value)}
						className="bg-transparent text-sm text-slate-200 placeholder-slate-500 outline-none w-full"
					/>
				</div>
				<div className="flex items-center gap-1.5 flex-wrap">
					<Filter size={14} className="text-slate-400" />
					{allTypes.map((t) => (
						<button
							key={t}
							type="button"
							onClick={() => setFilterType(t)}
							className={`text-xs font-bold px-2.5 py-1 rounded-lg transition-all ${
								filterType === t
									? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
									: "bg-white/10 text-slate-400 border border-transparent hover:text-slate-300"
							}`}
						>
							{t}
						</button>
					))}
				</div>
			</div>
			{loading ? (
				<div className="flex justify-center py-16">
					<Loader2 className="animate-spin text-amber-500" size={32} />
				</div>
			) : error ? (
				<div className="text-center py-16 text-red-400">
					<AlertTriangle size={48} className="mx-auto mb-4 opacity-70" />
					<p className="text-lg font-bold mb-2">Failed to load artifacts</p>
					<p className="text-sm mb-4">{error}</p>
					<button
						type="button"
						onClick={load}
						className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-500/30 transition-all"
					>
						<RefreshCw size={14} /> Retry
					</button>
				</div>
			) : filtered.length === 0 ? (
				<div className="text-center py-16 text-slate-400">
					<Package size={48} className="mx-auto mb-4 opacity-30" />
					<p className="text-lg">No artifacts found.</p>
					<p className="text-sm mb-2">This is a local artifact depot for storing Godot assets (scenes, meshes, materials, scripts) uploaded to this server.</p>
					<p className="text-sm text-slate-500">
						Go to <a href="/depot" className="text-amber-400 hover:underline">Artifact Depot</a> to register new items, or import via the MCP tools.
					</p>
				</div>
			) : (
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{filtered.map((a) => (
						<div
							key={a.id}
							className="bg-fleet-900 border border-white/10 rounded-2xl p-4 space-y-3 hover:border-amber-500/30 transition-all"
						>
							<div className="flex items-start justify-between">
								<h3 className="text-sm font-bold text-white">{a.name}</h3>
								<span
									className={`text-xs font-bold uppercase px-2 py-0.5 rounded ${
										typeColors[a.type] || "bg-slate-500/20 text-slate-400"
									}`}
								>
									{a.type}
								</span>
							</div>
							<p className="text-sm text-slate-400 line-clamp-2">{a.description}</p>
							<div className="flex items-center gap-2 text-xs text-slate-500">
								<span>by {a.author}</span>
							</div>
							{a.tags && a.tags.length > 0 && (
								<div className="flex flex-wrap gap-1">
									{a.tags.map((tag) => (
										<span
											key={tag}
											className="text-xs bg-white/10 text-slate-400 px-1.5 py-0.5 rounded"
										>
											{tag}
										</span>
									))}
								</div>
							)}
							<a
								href={`/api/v1/artifacts/${a.id}/download`}
								download
								className="flex items-center justify-center gap-2 w-full py-2 rounded-xl bg-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-500/30 transition-all"
							>
								<Download size={14} /> Download
							</a>
						</div>
					))}
				</div>
			)}
		</motion.div>
	);
}
