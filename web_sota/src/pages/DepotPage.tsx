import { AlertTriangle, Database, Loader2, Plus, RefreshCw, Trash2, X } from "lucide-react";
import { motion } from "framer-motion";
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

interface ArtifactEntry {
	id: string;
	name: string;
	type: string;
	author: string;
	size_kb: number;
	created_at: string;
}

const artifactTypes = ["Scene", "Mesh", "Material", "Particle", "Script", "Audio"];

export default function DepotPage() {
	const [artifacts, setArtifacts] = useState<ArtifactEntry[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [showForm, setShowForm] = useState(false);
	const [form, setForm] = useState({ name: "", type: "Mesh", description: "", author: "", tags: "" });
	const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

	const load = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const data = await apiFetch<{ artifacts?: ArtifactEntry[] }>("/api/v1/artifacts");
			setArtifacts(data.artifacts || []);
		} catch (e) {
			setError(e instanceof Error ? e.message : "Failed to load artifacts");
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => { load(); }, [load]);

	const handleRegister = async () => {
		const tags = form.tags.split(",").map((t) => t.trim()).filter(Boolean);
		try {
			await apiFetch("/api/v1/artifacts", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ name: form.name, type: form.type, description: form.description, author: form.author, tags }),
			});
			setShowForm(false);
			setForm({ name: "", type: "Mesh", description: "", author: "", tags: "" });
			load();
		} catch {
			// register failed — load will show error
		}
	};

	const handleDelete = async (id: string) => {
		try {
			await apiFetch(`/api/v1/artifacts/${id}`, { method: "DELETE" });
			setConfirmDelete(null);
			load();
		} catch {
			// delete failed — load will show error
		}
	};

	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			className="space-y-6 max-w-6xl"
		>
			<div className="flex items-center justify-between">
				<h1 className="text-2xl font-bold text-white flex items-center gap-3">
					<Database className="text-amber-500" size={24} /> Artifact Depot
				</h1>
				<div className="flex items-center gap-2">
					<button
						type="button"
						onClick={load}
						className="flex items-center gap-2 text-sm text-slate-400 hover:text-white"
					>
						<RefreshCw size={14} /> Refresh
					</button>
					<button
						type="button"
						onClick={() => setShowForm(!showForm)}
						className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-500/30 transition-all"
					>
						<Plus size={14} /> Register
					</button>
				</div>
			</div>
			{showForm && (
				<motion.div
					initial={{ opacity: 0, height: 0 }}
					animate={{ opacity: 1, height: "auto" }}
					className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-3"
				>
					<div className="flex items-center justify-between">
						<h2 className="text-sm font-bold text-slate-200">Register New Artifact</h2>
						<button type="button" onClick={() => setShowForm(false)}>
							<X size={14} className="text-slate-400" />
						</button>
					</div>
					<div className="grid grid-cols-2 gap-3">
						<input
							type="text"
							placeholder="Name"
							value={form.name}
							onChange={(e) => setForm({ ...form, name: e.target.value })}
							className="px-3 py-2 rounded-lg bg-white/10 border border-white/10 text-sm text-slate-200 placeholder-slate-600 outline-none"
						/>
						<select
							value={form.type}
							onChange={(e) => setForm({ ...form, type: e.target.value })}
							className="px-3 py-2 rounded-lg bg-white/10 border border-white/10 text-sm text-slate-200 outline-none"
						>
							{artifactTypes.map((t) => (
								<option key={t} value={t}>{t}</option>
							))}
						</select>
						<input
							type="text"
							placeholder="Description"
							value={form.description}
							onChange={(e) => setForm({ ...form, description: e.target.value })}
							className="px-3 py-2 rounded-lg bg-white/10 border border-white/10 text-sm text-slate-200 placeholder-slate-600 outline-none col-span-2"
						/>
						<input
							type="text"
							placeholder="Author"
							value={form.author}
							onChange={(e) => setForm({ ...form, author: e.target.value })}
							className="px-3 py-2 rounded-lg bg-white/10 border border-white/10 text-sm text-slate-200 placeholder-slate-600 outline-none"
						/>
						<input
							type="text"
							placeholder="Tags (comma separated)"
							value={form.tags}
							onChange={(e) => setForm({ ...form, tags: e.target.value })}
							className="px-3 py-2 rounded-lg bg-white/10 border border-white/10 text-sm text-slate-200 placeholder-slate-600 outline-none"
						/>
					</div>
					<button
						type="button"
						onClick={handleRegister}
						className="px-4 py-2 rounded-xl bg-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-500/30 transition-all"
					>
						Save Artifact
					</button>
				</motion.div>
			)}
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
			) : artifacts.length === 0 ? (
				<div className="text-center py-16 text-slate-400">
					<Database size={48} className="mx-auto mb-4 opacity-30" />
					<p className="text-lg">No artifacts registered.</p>
				</div>
			) : (
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl overflow-hidden">
					<table className="w-full text-sm">
						<thead>
							<tr className="border-b border-white/10 text-slate-400 text-xs uppercase tracking-wider">
								<th className="text-left px-4 py-3 font-bold">Name</th>
								<th className="text-left px-4 py-3 font-bold">Type</th>
								<th className="text-left px-4 py-3 font-bold">Author</th>
								<th className="text-right px-4 py-3 font-bold">Size</th>
								<th className="text-right px-4 py-3 font-bold">Date</th>
								<th className="text-right px-4 py-3 font-bold">Actions</th>
							</tr>
						</thead>
						<tbody>
							{artifacts.map((a) => (
								<tr key={a.id} className="border-b border-white/10 hover:bg-white/[0.04] transition-all">
									<td className="px-4 py-3 text-slate-200 font-medium">{a.name}</td>
									<td className="px-4 py-3">
										<span className="text-xs font-bold uppercase px-2 py-0.5 rounded bg-amber-500/20 text-amber-400">
											{a.type}
										</span>
									</td>
									<td className="px-4 py-3 text-slate-400">{a.author}</td>
									<td className="px-4 py-3 text-right text-slate-300">{a.size_kb} KB</td>
									<td className="px-4 py-3 text-right text-slate-400">
										{a.created_at ? new Date(a.created_at).toLocaleDateString() : "-"}
									</td>
									<td className="px-4 py-3 text-right">
										{confirmDelete === a.id ? (
											<div className="flex items-center justify-end gap-1">
												<button
													type="button"
													onClick={() => handleDelete(a.id)}
													className="text-xs px-2 py-1 rounded bg-red-500/20 text-red-400 font-bold"
												>
													Confirm
												</button>
												<button
													type="button"
													onClick={() => setConfirmDelete(null)}
													className="text-xs px-2 py-1 rounded bg-white/10 text-slate-400"
												>
													Cancel
												</button>
											</div>
										) : (
											<button
												type="button"
												onClick={() => setConfirmDelete(a.id)}
												className="text-red-400 hover:text-red-300 transition-all"
											>
												<Trash2 size={14} />
											</button>
										)}
									</td>
								</tr>
							))}
						</tbody>
					</table>
				</div>
			)}
		</motion.div>
	);
}
