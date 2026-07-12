import { AlertTriangle, Book, BookOpen, FileText, Loader2, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

interface SkillInfo {
	name: string;
	path: string;
}

interface SkillDetail {
	name: string;
	content: string;
	tools: string[];
	workflows: string[];
}

export default function SkillsPage() {
	const [skills, setSkills] = useState<SkillInfo[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [selected, setSelected] = useState<SkillDetail | null>(null);
	const [detailLoading, setDetailLoading] = useState(false);

	const load = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const data = await apiFetch<{ skills?: SkillInfo[] }>("/api/v1/skills");
			setSkills(data.skills || []);
		} catch (e) {
			setError(e instanceof Error ? e.message : "Failed to load skills");
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => { load(); }, [load]);

	const viewSkill = async (skill: SkillInfo) => {
		setDetailLoading(true);
		setSelected(null);
		try {
			const j = await apiFetch<{ name?: string; content?: string; tools?: string[]; workflows?: string[] }>(
				`/api/v1/skills/${encodeURIComponent(skill.name)}`
			);
			setSelected({
				name: j.name || skill.name,
				content: j.content || "",
				tools: j.tools || [],
				workflows: j.workflows || [],
			});
		} catch (e) {
			setSelected({
				name: skill.name,
				content: `Error loading skill: ${e}`,
				tools: [],
				workflows: [],
			});
		} finally {
			setDetailLoading(false);
		}
	};

	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			className="space-y-6 max-w-6xl"
		>
			<h1 className="text-2xl font-bold text-white flex items-center gap-3">
				<Book className="text-amber-500" size={24} /> Server Skills
			</h1>
			<div className="grid grid-cols-1 md:grid-cols-3 gap-6">
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-4 space-y-2 md:col-span-1">
					<h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
						<FileText size={14} /> Skill List
					</h2>
					{loading ? (
						<div className="flex justify-center py-8">
							<Loader2 className="animate-spin text-amber-500" size={24} />
						</div>
					) : error ? (
						<div className="text-center py-8 text-red-400">
							<AlertTriangle size={24} className="mx-auto mb-2 opacity-70" />
							<p className="text-xs mb-3">{error}</p>
							<button
								type="button"
								onClick={load}
								className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-400 text-xs font-bold hover:bg-amber-500/30 transition-all"
							>
								<RefreshCw size={12} /> Retry
							</button>
						</div>
					) : skills.length === 0 ? (
						<p className="text-sm text-slate-400">No skills registered.</p>
					) : (
						<div className="space-y-1">
							{skills.map((s) => (
								<button
									key={s.name}
									type="button"
									onClick={() => viewSkill(s)}
									className={`w-full text-left px-3 py-2 rounded-xl text-sm transition-all ${
										selected?.name === s.name
											? "bg-amber-500/20 text-amber-400"
											: "text-slate-400 hover:text-slate-200 hover:bg-white/[0.08]"
									}`}
								>
									<BookOpen size={14} className="inline mr-2" />
									{s.name}
								</button>
							))}
						</div>
					)}
				</div>
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-4 space-y-3 md:col-span-2 min-h-[300px]">
					{detailLoading ? (
						<div className="flex justify-center py-16">
							<Loader2 className="animate-spin text-amber-500" size={24} />
						</div>
					) : selected ? (
						<>
							<h2 className="text-sm font-bold text-white flex items-center gap-2">
								<BookOpen size={16} className="text-amber-400" /> {selected.name}
							</h2>
							{selected.tools.length > 0 && (
								<div>
									<p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Tool Categories</p>
									<div className="flex flex-wrap gap-1">
										{selected.tools.map((t) => (
											<span key={t} className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">
												{t}
											</span>
										))}
									</div>
								</div>
							)}
							{selected.workflows.length > 0 && (
								<div>
									<p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Workflow Patterns</p>
									<div className="flex flex-wrap gap-1">
										{selected.workflows.map((w) => (
											<span key={w} className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded">
												{w}
											</span>
										))}
									</div>
								</div>
							)}
							{selected.content && (
								<div>
									<p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Content</p>
									<pre className="p-3 rounded-xl bg-black/40 text-xs text-slate-300 overflow-auto max-h-80 border border-white/10 whitespace-pre-wrap">
										{selected.content}
									</pre>
								</div>
							)}
						</>
					) : (
						<div className="flex flex-col items-center justify-center py-16 text-slate-500">
							<BookOpen size={40} className="mb-3 opacity-30" />
							<p className="text-sm">Select a skill from the list</p>
						</div>
					)}
				</div>
			</div>
		</motion.div>
	);
}
