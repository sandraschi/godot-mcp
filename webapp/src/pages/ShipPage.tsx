import { ExternalLink, Loader2, Package, Rocket, Upload } from "lucide-react";
import { motion } from "framer-motion";
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

interface ItchStatus {
	success: boolean;
	butler: { found: boolean; path: string; version: string | null };
	auth: { api_key_set: boolean; hint: string };
	defaults: {
		game: string;
		itch_target: string;
		channel_web: string;
		channel_windows: string;
	};
	last_ship: Record<string, string>;
}

interface ToolResponse {
	success: boolean;
	data?: Record<string, unknown>;
	error?: string;
	message?: string;
}

export default function ShipPage() {
	const [status, setStatus] = useState<ItchStatus | null>(null);
	const [game, setGame] = useState("dodge");
	const [target, setTarget] = useState<"web" | "windows">("web");
	const [itchTarget, setItchTarget] = useState("");
	const [channel, setChannel] = useState("html");
	const [preview, setPreview] = useState(true);
	const [push, setPush] = useState(true);
	const [hidden, setHidden] = useState(false);
	const [uploadDir, setUploadDir] = useState("");
	const [busy, setBusy] = useState<string | null>(null);
	const [result, setResult] = useState<string | null>(null);

	const loadStatus = useCallback(async () => {
		const j = await apiFetch<ItchStatus>("/api/v1/itch/status");
		setStatus(j);
		if (j.defaults?.game) setGame(j.defaults.game);
		if (j.defaults?.itch_target) setItchTarget(j.defaults.itch_target);
		if (target === "web" && j.defaults?.channel_web) setChannel(j.defaults.channel_web);
		if (target === "windows" && j.defaults?.channel_windows) setChannel(j.defaults.channel_windows);
	}, [target]);

	useEffect(() => {
		loadStatus().catch((e) => setResult(String(e)));
	}, [loadStatus]);

	useEffect(() => {
		if (target === "web") setChannel(status?.defaults?.channel_web ?? "html");
		else setChannel(status?.defaults?.channel_windows ?? "win");
	}, [target, status]);

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
				const exportData = (data.export as Record<string, unknown>) ?? data;
				if (typeof exportData.upload_dir === "string") setUploadDir(exportData.upload_dir);
			}
			await loadStatus();
		} catch (e) {
			setResult(`Error: ${e}`);
		} finally {
			setBusy(null);
		}
	};

	const exportBuild = () =>
		runTool("godot_export_release", { target, game }, "export");

	const previewPush = () => {
		if (!uploadDir) {
			setResult("Export first or set upload directory.");
			return;
		}
		runTool(
			"itch_push_preview",
			{ upload_dir: uploadDir, itch_target: itchTarget || undefined, channel },
			"preview",
		);
	};

	const pushBuild = () => {
		if (!uploadDir) {
			setResult("Export first or set upload directory.");
			return;
		}
		runTool(
			"itch_push",
			{ upload_dir: uploadDir, itch_target: itchTarget || undefined, channel, hidden },
			"push",
		);
	};

	const shipAll = () =>
		runTool(
			"ship_to_itch",
			{
				target,
				game,
				itch_target: itchTarget || undefined,
				channel,
				preview,
				push,
				hidden,
			},
			"ship",
		);

	const butlerOk = status?.butler?.found;
	const keyOk = status?.auth?.api_key_set;

	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			className="space-y-6 max-w-4xl"
		>
			<h1 className="text-2xl font-bold text-white flex items-center gap-3">
				<Rocket className="text-pink-400" size={24} /> Ship to itch.io
			</h1>
			<p className="text-sm text-slate-400">
				Export a sample Godot game, preview Butler diff, and push to itch.io. Set{" "}
				<code className="text-pink-300">BUTLER_API_KEY</code> and{" "}
				<code className="text-pink-300">ITCH_TARGET</code> in your environment (never in this UI).
			</p>

			<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-4 space-y-2">
					<p className="text-xs uppercase tracking-wider text-slate-500 font-bold">Butler</p>
					<p className={`text-sm font-medium ${butlerOk ? "text-emerald-400" : "text-amber-400"}`}>
						{butlerOk ? `Found: ${status?.butler?.path}` : "Not found — install Butler or set BUTLER_PATH"}
					</p>
					{status?.butler?.version && (
						<p className="text-xs text-slate-500">{status.butler.version}</p>
					)}
				</div>
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-4 space-y-2">
					<p className="text-xs uppercase tracking-wider text-slate-500 font-bold">API key</p>
					<p className={`text-sm font-medium ${keyOk ? "text-emerald-400" : "text-amber-400"}`}>
						{keyOk ? "BUTLER_API_KEY set" : "Missing BUTLER_API_KEY"}
					</p>
					<p className="text-xs text-slate-500">{status?.auth?.hint}</p>
				</div>
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-4 space-y-2">
					<p className="text-xs uppercase tracking-wider text-slate-500 font-bold">Last ship</p>
					{status?.last_ship?.page_url ? (
						<a
							href={status.last_ship.page_url}
							target="_blank"
							rel="noopener noreferrer"
							className="text-sm text-pink-400 hover:underline flex items-center gap-1"
						>
							{status.last_ship.itch_ref ?? "View page"} <ExternalLink size={12} />
						</a>
					) : (
						<p className="text-sm text-slate-500">No pushes yet</p>
					)}
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
						Export target
						<select
							value={target}
							onChange={(e) => setTarget(e.target.value as "web" | "windows")}
							className="mt-1 w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none"
						>
							<option value="web">Web (HTML5)</option>
							<option value="windows">Windows desktop</option>
						</select>
					</label>
					<label className="block text-sm text-slate-400">
						itch.io slug (user/game)
						<input
							value={itchTarget}
							onChange={(e) => setItchTarget(e.target.value)}
							placeholder="yourname/my-game"
							className="mt-1 w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none"
						/>
					</label>
					<label className="block text-sm text-slate-400">
						Butler channel
						<input
							value={channel}
							onChange={(e) => setChannel(e.target.value)}
							placeholder="html"
							className="mt-1 w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none"
						/>
					</label>
					<label className="block text-sm text-slate-400 md:col-span-2">
						Upload directory (after export)
						<input
							value={uploadDir}
							onChange={(e) => setUploadDir(e.target.value)}
							placeholder="build/little-game/dodge/web"
							className="mt-1 w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none font-mono text-xs"
						/>
					</label>
				</div>

				<div className="flex flex-wrap gap-4 text-sm text-slate-400">
					<label className="flex items-center gap-2">
						<input type="checkbox" checked={preview} onChange={(e) => setPreview(e.target.checked)} />
						Preview before push
					</label>
					<label className="flex items-center gap-2">
						<input type="checkbox" checked={push} onChange={(e) => setPush(e.target.checked)} />
						Push to itch.io
					</label>
					<label className="flex items-center gap-2">
						<input type="checkbox" checked={hidden} onChange={(e) => setHidden(e.target.checked)} />
						Hidden channel
					</label>
				</div>

				<div className="flex flex-wrap gap-2">
					<button
						type="button"
						onClick={exportBuild}
						disabled={!!busy}
						className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500/20 text-blue-400 text-sm font-bold hover:bg-blue-500/30 disabled:opacity-50"
					>
						{busy === "export" ? <Loader2 size={14} className="animate-spin" /> : <Package size={14} />}
						Export
					</button>
					<button
						type="button"
						onClick={previewPush}
						disabled={!!busy || !butlerOk}
						className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-500/30 disabled:opacity-50"
					>
						{busy === "preview" ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
						Preview push
					</button>
					<button
						type="button"
						onClick={pushBuild}
						disabled={!!busy || !butlerOk || !keyOk}
						className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/20 text-emerald-400 text-sm font-bold hover:bg-emerald-500/30 disabled:opacity-50"
					>
						{busy === "push" ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
						Push
					</button>
					<button
						type="button"
						onClick={shipAll}
						disabled={!!busy || !butlerOk || !keyOk}
						className="flex items-center gap-2 px-4 py-2 rounded-xl bg-pink-500/20 text-pink-400 text-sm font-bold hover:bg-pink-500/30 disabled:opacity-50"
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
