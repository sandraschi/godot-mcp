import { ExternalLink, Loader2, Package, Rocket, Upload } from "lucide-react";
import { motion } from "framer-motion";
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

interface SteamStatus {
	success: boolean;
	steam_mcp_url: string;
	app_id: number;
	depot_id: number;
	content_root: string;
	publish: Record<string, unknown>;
	steamcmd: Record<string, unknown>;
	last_ship: Record<string, unknown>;
}

interface ToolResponse {
	success: boolean;
	data?: Record<string, unknown>;
	error?: string;
	message?: string;
}

export default function ShipSteamPage() {
	const [status, setStatus] = useState<SteamStatus | null>(null);
	const [game, setGame] = useState("dodge");
	const [phase, setPhase] = useState<"prerelease" | "release">("prerelease");
	const [dryRun, setDryRun] = useState(true);
	const [contentRoot, setContentRoot] = useState("");
	const [busy, setBusy] = useState<string | null>(null);
	const [result, setResult] = useState<string | null>(null);

	const loadStatus = useCallback(async () => {
		const j = await apiFetch<SteamStatus>("/api/v1/steam/status");
		setStatus(j);
		if (j.content_root) setContentRoot(j.content_root);
	}, []);

	useEffect(() => {
		loadStatus().catch((e) => setResult(String(e)));
	}, [loadStatus]);

	const runTool = async (tool: string, args: Record<string, unknown>, label: string) => {
		setBusy(label);
		setResult(null);
		try {
			const j = await apiFetch<ToolResponse>("/api/v1/control/tool", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ tool, arguments: args }),
				timeoutMs: 900000,
			});
			setResult(JSON.stringify(j, null, 2));
			if (j.success && j.data) {
				const data = j.data as Record<string, unknown>;
				const stage = (data.stage as Record<string, unknown>) ?? data;
				if (typeof stage.content_root === "string") setContentRoot(stage.content_root);
			}
			await loadStatus();
		} catch (e) {
			setResult(`Error: ${e}`);
		} finally {
			setBusy(null);
		}
	};

	const stageBuild = () => runTool("steam_stage_build", { game }, "stage");

	const uploadBuild = () =>
		runTool(
			phase === "release" ? "ship_to_steam_release" : "ship_to_steam_prerelease",
			{ content_root: contentRoot || undefined, dry_run: dryRun },
			"upload",
		);

	const shipAll = () =>
		runTool(
			"ship_to_steam",
			{ game, phase, dry_run: dryRun },
			"ship",
		);

	const checklist = () =>
		runTool("steam_checklist", { content_root: contentRoot || undefined }, "checklist");

	const appOk = (status?.app_id ?? 0) > 0;
	const depotOk = (status?.depot_id ?? 0) > 0;
	const publishReady = Boolean(
		(status?.publish as Record<string, unknown>)?.ready_for_upload ??
			(status?.publish as Record<string, unknown>)?.checklist_summary,
	);

	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			className="space-y-6 max-w-4xl"
		>
			<h1 className="text-2xl font-bold text-white flex items-center gap-3">
				<Rocket className="text-sky-400" size={24} /> Ship to Steam
			</h1>
			<p className="text-sm text-slate-400">
				Export Windows build, stage to fleet exchange, generate VDF, upload via steam-mcp. Set{" "}
				<code className="text-sky-300">STEAM_APP_ID</code>,{" "}
				<code className="text-sky-300">STEAM_DEPOT_ID</code>,{" "}
				<code className="text-sky-300">STEAM_USERNAME</code>, and{" "}
				<code className="text-sky-300">STEAMCMD_PATH</code> in your environment. Uploads default to{" "}
				<strong className="text-amber-400">dry run</strong>.
			</p>

			<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-4 space-y-2">
					<p className="text-xs uppercase tracking-wider text-slate-500 font-bold">steam-mcp</p>
					<p className="text-sm text-slate-300 font-mono">{status?.steam_mcp_url ?? "…"}</p>
					<p className={`text-xs ${appOk && depotOk ? "text-emerald-400" : "text-amber-400"}`}>
						App {status?.app_id || "—"} · Depot {status?.depot_id || "—"}
					</p>
				</div>
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-4 space-y-2">
					<p className="text-xs uppercase tracking-wider text-slate-500 font-bold">Content root</p>
					<p className="text-xs text-slate-400 font-mono break-all">{status?.content_root ?? "—"}</p>
				</div>
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-4 space-y-2">
					<p className="text-xs uppercase tracking-wider text-slate-500 font-bold">Readiness</p>
					<p className={`text-sm font-medium ${publishReady ? "text-emerald-400" : "text-amber-400"}`}>
						{publishReady ? "Checklist mostly green" : "Configure env + stage build"}
					</p>
					<a
						href="https://partner.steamgames.com"
						target="_blank"
						rel="noopener noreferrer"
						className="text-xs text-sky-400 hover:underline flex items-center gap-1"
					>
						Steamworks partner <ExternalLink size={12} />
					</a>
				</div>
			</div>

			<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-4">
				<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
					<label className="block text-sm text-slate-400">
						Sample game
						<select
							value={game}
							onChange={(e) => setGame(e.target.value)}
							className="mt-1 w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none"
						>
							{["dodge", "heart", "platformer", "pong", "procedural", "skelerealms", "vibecode"].map((g) => (
								<option key={g} value={g}>
									{g}
								</option>
							))}
						</select>
					</label>
					<label className="block text-sm text-slate-400">
						Upload phase
						<select
							value={phase}
							onChange={(e) => setPhase(e.target.value as "prerelease" | "release")}
							className="mt-1 w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none"
						>
							<option value="prerelease">Prerelease (beta branch)</option>
							<option value="release">Release (default branch)</option>
						</select>
					</label>
					<label className="block text-sm text-slate-400 md:col-span-2">
						Content root (after stage)
						<input
							value={contentRoot}
							onChange={(e) => setContentRoot(e.target.value)}
							placeholder="_exchange/steam-builds/1234560/content"
							className="mt-1 w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none font-mono text-xs"
						/>
					</label>
				</div>

				<label className="flex items-center gap-2 text-sm text-slate-400">
					<input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} />
					Dry run (recommended — no real steamcmd upload)
				</label>

				<div className="flex flex-wrap gap-2">
					<button
						type="button"
						onClick={stageBuild}
						disabled={!!busy}
						className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500/20 text-blue-400 text-sm font-bold hover:bg-blue-500/30 disabled:opacity-50"
					>
						{busy === "stage" ? <Loader2 size={14} className="animate-spin" /> : <Package size={14} />}
						Export + stage
					</button>
					<button
						type="button"
						onClick={checklist}
						disabled={!!busy}
						className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-500/30 disabled:opacity-50"
					>
						{busy === "checklist" ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
						Checklist
					</button>
					<button
						type="button"
						onClick={uploadBuild}
						disabled={!!busy || !contentRoot}
						className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/20 text-emerald-400 text-sm font-bold hover:bg-emerald-500/30 disabled:opacity-50"
					>
						{busy === "upload" ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
						Upload {phase}
					</button>
					<button
						type="button"
						onClick={shipAll}
						disabled={!!busy}
						className="flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-500/20 text-sky-400 text-sm font-bold hover:bg-sky-500/30 disabled:opacity-50"
					>
						{busy === "ship" ? <Loader2 size={14} className="animate-spin" /> : <Rocket size={14} />}
						Ship all
					</button>
				</div>
			</div>

			{result && (
				<pre className="p-4 rounded-2xl bg-black/40 text-xs text-slate-300 overflow-auto max-h-96 border border-white/10">
					{result}
				</pre>
			)}
		</motion.div>
	);
}
