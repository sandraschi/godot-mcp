import { Download, Filter, Loader2, Package, Search } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";

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
	const [search, setSearch] = useState("");
	const [filterType, setFilterType] = useState("All");

	useEffect(() => {
		fetch("/api/v1/artifacts")
			.then((r) => r.json())
			.then((data) => setArtifacts(data.artifacts || data || []))
			.catch(() => {})
			.finally(() => setLoading(false));
	}, []);

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
					<Package className="text-amber-500" size={24} /> Artifact Marketplace
				</h1>
			</div>
			<div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
				<div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-white/10 bg-[#1e1e26] max-w-sm w-full">
					<Search size={14} className="text-slate-300 shrink-0" />
					<input
						type="text"
						placeholder="Search artifacts..."
						value={search}
						onChange={(e) => setSearch(e.target.value)}
						className="bg-transparent text-sm text-slate-200 placeholder-slate-600 outline-none w-full"
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
			) : filtered.length === 0 ? (
				<div className="text-center py-16 text-slate-400">
					<Package size={48} className="mx-auto mb-4 opacity-30" />
					<p className="text-lg">No artifacts found.</p>
					<p className="text-sm">Register one to get started.</p>
				</div>
			) : (
				<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{filtered.map((a) => (
						<div
							key={a.id}
							className="bg-[#1e1e26] border border-white/10 rounded-2xl p-4 space-y-3 hover:border-amber-500/30 transition-all"
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
