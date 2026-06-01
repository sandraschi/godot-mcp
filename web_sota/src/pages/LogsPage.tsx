import {
	ChevronLeft,
	ChevronRight,
	Download,
	Pause,
	Play,
	ScrollText,
	Trash2,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../lib/api";

type LogEntry = {
	id: string;
	timestamp: string;
	level: string;
	kind: string;
	detail: string;
	meta?: Record<string, unknown>;
};

type LogsResponse = {
	entries: LogEntry[];
	total: number;
	limit: number;
	offset: number;
	max_entries: number;
	sort: string;
};

type LogStats = {
	total: number;
	max_entries: number;
	rotation: string;
	env_var: string;
	by_level: Record<string, number>;
	by_kind: Record<string, number>;
};

const LEVELS = ["", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] as const;
const KINDS = ["", "tool_call", "server", "system", "export"] as const;
const PAGE_SIZES = [25, 50, 100, 200] as const;

function levelClass(level: string): string {
	const l = level.toUpperCase();
	if (l === "ERROR" || l === "CRITICAL") return "text-red-400 bg-red-500/10 border-red-500/20";
	if (l === "WARNING") return "text-amber-400 bg-amber-500/10 border-amber-500/20";
	if (l === "INFO") return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
	if (l === "DEBUG") return "text-slate-400 bg-slate-500/10 border-slate-500/20";
	return "text-slate-300 bg-white/5 border-white/10";
}

export default function LogsPage() {
	const [entries, setEntries] = useState<LogEntry[]>([]);
	const [stats, setStats] = useState<LogStats | null>(null);
	const [total, setTotal] = useState(0);
	const [limit, setLimit] = useState(50);
	const [offset, setOffset] = useState(0);
	const [level, setLevel] = useState("");
	const [kind, setKind] = useState("");
	const [search, setSearch] = useState("");
	const [debouncedSearch, setDebouncedSearch] = useState("");
	const [sort, setSort] = useState<"asc" | "desc">("desc");
	const [tail, setTail] = useState(true);
	const [pauseTail, setPauseTail] = useState(false);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const scrollRef = useRef<HTMLDivElement>(null);
	const atBottomRef = useRef(true);
	const newestIdRef = useRef<string>("");

	useEffect(() => {
		const t = setTimeout(() => setDebouncedSearch(search), 300);
		return () => clearTimeout(t);
	}, [search]);

	const load = useCallback(async (mode: "page" | "tail" = "page") => {
		try {
			const params = new URLSearchParams();
			params.set("limit", String(limit));
			params.set("sort", sort);
			if (level) params.set("level", level);
			if (kind) params.set("kind", kind);
			if (debouncedSearch.trim()) params.set("search", debouncedSearch.trim());

			if (mode === "tail" && tail && !pauseTail && newestIdRef.current) {
				params.set("after_id", newestIdRef.current);
				params.set("sort", "asc");
				params.set("limit", "100");
			} else {
				params.set("offset", String(offset));
			}

			const [logs, statsRes] = await Promise.all([
				apiFetch<LogsResponse>(`/api/logs?${params.toString()}`),
				apiFetch<LogStats>("/api/logs/stats"),
			]);

			if (mode === "tail" && tail && !pauseTail && newestIdRef.current && logs.entries.length) {
				setEntries((prev) => {
					const merged = [...logs.entries, ...prev];
					const seen = new Set<string>();
					return merged.filter((e) => {
						if (seen.has(e.id)) return false;
						seen.add(e.id);
						return true;
					}).slice(0, 500);
				});
			} else {
				setEntries(logs.entries);
			}

			if (logs.entries.length) {
				const newest = sort === "desc" ? logs.entries[0] : logs.entries[logs.entries.length - 1];
				if (newest?.id) newestIdRef.current = newest.id;
			}
			setTotal(logs.total);
			setStats(statsRes);
			setError(null);
		} catch (e) {
			setError(String(e));
		} finally {
			setLoading(false);
		}
	}, [limit, offset, level, kind, debouncedSearch, sort, tail, pauseTail]);

	useEffect(() => {
		setLoading(true);
		load("page").catch(() => undefined);
	}, [load]);

	useEffect(() => {
		if (!tail || pauseTail) return undefined;
		const id = setInterval(() => {
			load("tail").catch(() => undefined);
		}, 2000);
		return () => clearInterval(id);
	}, [tail, pauseTail, load]);

	useEffect(() => {
		if (atBottomRef.current && !pauseTail && scrollRef.current) {
			scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
		}
	}, [entries, pauseTail]);

	const onScroll = () => {
		const el = scrollRef.current;
		if (!el) return;
		const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
		atBottomRef.current = atBottom;
		if (!atBottom) setPauseTail(true);
	};

	const exportLogs = (format: "json" | "csv") => {
		const params = new URLSearchParams({ format });
		if (level) params.set("level", level);
		if (kind) params.set("kind", kind);
		if (debouncedSearch.trim()) params.set("search", debouncedSearch.trim());
		params.set("sort", sort);
		window.open(`/api/logs/export?${params.toString()}`, "_blank");
	};

	const clearLogs = async () => {
		if (!window.confirm("Clear all in-memory log entries?")) return;
		await apiFetch("/api/logs", { method: "DELETE" });
		newestIdRef.current = "";
		setOffset(0);
		await load("page");
	};

	const page = Math.floor(offset / limit) + 1;
	const pageCount = Math.max(1, Math.ceil(total / limit));

	return (
		<div className="space-y-4 max-w-6xl mx-auto">
			<h1 className="text-2xl font-bold text-white flex items-center gap-3">
				<ScrollText className="text-emerald-500" /> Logs
			</h1>
			<p className="text-sm text-slate-400">
				Fleet-standard activity log — ring buffer max {stats?.max_entries ?? 2000} (
				<code className="text-xs text-slate-300">GODOT_LOG_MAX_ENTRIES</code>)
			</p>

			{stats && (
				<div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
					<div className="rounded-lg border border-white/10 bg-[#1e1e26] p-3">
						<div className="text-slate-500">Total</div>
						<div className="text-white font-mono">{stats.total}</div>
					</div>
					<div className="rounded-lg border border-white/10 bg-[#1e1e26] p-3">
						<div className="text-slate-500">Rotation</div>
						<div className="text-white font-mono">{stats.rotation}</div>
					</div>
					<div className="rounded-lg border border-white/10 bg-[#1e1e26] p-3 col-span-2">
						<div className="text-slate-500 mb-1">By kind</div>
						<div className="flex flex-wrap gap-2 font-mono text-xs text-slate-300">
							{Object.entries(stats.by_kind).map(([k, v]) => (
								<span key={k} className="px-2 py-0.5 rounded bg-white/5">
									{k}: {v}
								</span>
							))}
						</div>
					</div>
				</div>
			)}

			<div className="flex flex-wrap items-center gap-2">
				<input
					type="search"
					placeholder="Search detail / meta…"
					value={search}
					onChange={(e) => {
						setSearch(e.target.value);
						setOffset(0);
					}}
					className="min-w-[180px] flex-1 max-w-xs px-3 py-1.5 rounded-lg border border-white/10 bg-[#1e1e26] text-sm text-slate-200 outline-none"
				/>
				<select
					value={level}
					onChange={(e) => {
						setLevel(e.target.value);
						setOffset(0);
					}}
					className="px-2 py-1.5 rounded-lg border border-white/10 bg-[#1e1e26] text-sm text-slate-200"
				>
					{LEVELS.map((lv) => (
						<option key={lv || "all"} value={lv}>
							{lv || "All levels"}
						</option>
					))}
				</select>
				<select
					value={kind}
					onChange={(e) => {
						setKind(e.target.value);
						setOffset(0);
					}}
					className="px-2 py-1.5 rounded-lg border border-white/10 bg-[#1e1e26] text-sm text-slate-200"
				>
					{KINDS.map((k) => (
						<option key={k || "all"} value={k}>
							{k || "All kinds"}
						</option>
					))}
				</select>
				<select
					value={String(limit)}
					onChange={(e) => {
						setLimit(Number(e.target.value));
						setOffset(0);
					}}
					className="px-2 py-1.5 rounded-lg border border-white/10 bg-[#1e1e26] text-sm text-slate-200"
				>
					{PAGE_SIZES.map((n) => (
						<option key={n} value={n}>
							{n} / page
						</option>
					))}
				</select>
				<select
					value={sort}
					onChange={(e) => setSort(e.target.value as "asc" | "desc")}
					className="px-2 py-1.5 rounded-lg border border-white/10 bg-[#1e1e26] text-sm text-slate-200"
				>
					<option value="desc">Newest first</option>
					<option value="asc">Oldest first</option>
				</select>
				<button
					type="button"
					onClick={() => {
						setTail((t) => !t);
						setPauseTail(false);
					}}
					className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-sm ${
						tail ? "border-emerald-500/30 text-emerald-300" : "border-white/10 text-slate-300"
					}`}
				>
					{tail ? <Play size={12} /> : <Pause size={12} />} Live tail
				</button>
				{pauseTail && tail && (
					<button
						type="button"
						onClick={() => {
							setPauseTail(false);
							atBottomRef.current = true;
						}}
						className="px-2.5 py-1.5 rounded-lg border border-amber-500/30 text-sm text-amber-300"
					>
						Resume scroll
					</button>
				)}
				<button
					type="button"
					onClick={() => exportLogs("json")}
					className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-emerald-500/20 text-sm text-emerald-300"
				>
					<Download size={12} /> JSON
				</button>
				<button
					type="button"
					onClick={() => exportLogs("csv")}
					className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-emerald-500/20 text-sm text-emerald-300"
				>
					<Download size={12} /> CSV
				</button>
				<button
					type="button"
					onClick={clearLogs}
					className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-red-500/20 text-sm text-red-300"
				>
					<Trash2 size={12} /> Clear
				</button>
			</div>

			{error && (
				<div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-300">
					{error}
				</div>
			)}

			<div className="bg-[#0a0a0c] border border-white/10 rounded-xl overflow-hidden">
				<div className="px-4 py-2 border-b border-white/10 flex items-center justify-between text-sm text-slate-300">
					<span className="font-mono">/api/logs</span>
					<span>
						{loading ? "Loading…" : `${entries.length} shown · ${total} matched`}
					</span>
				</div>
				<div
					ref={scrollRef}
					onScroll={onScroll}
					className="h-[58vh] overflow-y-auto p-2 font-mono text-xs"
				>
					{entries.length === 0 ? (
						<p className="text-slate-500 italic p-2">No log entries match filters.</p>
					) : (
						entries.map((entry) => (
							<div
								key={entry.id}
								className="flex flex-wrap items-start gap-2 py-1.5 px-2 rounded hover:bg-white/[0.02] border-b border-white/[0.03]"
							>
								<span className="text-slate-500 shrink-0">{entry.timestamp}</span>
								<span
									className={`shrink-0 px-1.5 py-0.5 rounded border text-[10px] font-semibold ${levelClass(entry.level)}`}
								>
									{entry.level}
								</span>
								<span className="text-blue-400/80 shrink-0">[{entry.kind}]</span>
								<span className="text-slate-200 break-all">{entry.detail}</span>
							</div>
						))
					)}
				</div>
				<div className="px-4 py-2 border-t border-white/10 flex items-center justify-between text-sm text-slate-400">
					<button
						type="button"
						disabled={offset <= 0}
						onClick={() => setOffset(Math.max(0, offset - limit))}
						className="flex items-center gap-1 disabled:opacity-40"
					>
						<ChevronLeft size={14} /> Prev
					</button>
					<span>
						Page {page} / {pageCount}
					</span>
					<button
						type="button"
						disabled={offset + limit >= total}
						onClick={() => setOffset(offset + limit)}
						className="flex items-center gap-1 disabled:opacity-40"
					>
						Next <ChevronRight size={14} />
					</button>
				</div>
			</div>
		</div>
	);
}
