import { Check, Cpu, Download, KeyRound, Loader2, Network, Rocket, Settings } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

interface ItchStatus {
	butler: { found: boolean; path: string; version: string | null };
	auth: { api_key_set: boolean; hint: string };
	defaults: { game: string; itch_target: string; channel_web: string; channel_windows: string };
}

export default function SettingsPage() {
	const [godotPath, setGodotPath] = useState("");
	const [wsPort, setWsPort] = useState(9080);
	const [wsHost, setWsHost] = useState("127.0.0.1");
	const [status, setStatus] = useState("");
	const [itch, setItch] = useState<ItchStatus | null>(null);
	const [addonPath, setAddonPath] = useState("");
	const [addonInstalling, setAddonInstalling] = useState(false);
	const [addonResult, setAddonResult] = useState("");
	const [llmDetect, setLlmDetect] = useState<Record<string, unknown> | null>(null);
	const [llmRec, setLlmRec] = useState<Record<string, unknown> | null>(null);

	useEffect(() => {
		fetch("/api/v1/status")
			.then((r) => r.json())
			.then((j) => {
				if (j.godot?.path) setGodotPath(j.godot.path);
				if (j.godot?.port) setWsPort(j.godot.port);
				if (j.godot?.host) setWsHost(j.godot.host);
				if (j.itch) setItch(j.itch);
			})
			.catch(() => {});
		apiFetch<Record<string, unknown>>("/api/v1/llm/detect").then(setLlmDetect).catch(() => {});
		apiFetch<Record<string, unknown>>("/api/v1/llm/recommend").then(setLlmRec).catch(() => {});
	}, []);

	const save = async () => {
		setStatus("Saving...");
		try {
			await fetch("/api/v1/settings", {
				method: "PUT",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					godot_path: godotPath,
					godot_host: wsHost,
					godot_ws_port: wsPort,
				}),
			});
			setStatus("Saved.");
		} catch {
			setStatus("Error saving.");
		}
	};

	const refreshItch = async () => {
		try {
			const j = await apiFetch<ItchStatus>("/api/v1/itch/status");
			setItch(j);
		} catch {
			setStatus("Could not refresh itch status.");
		}
	};

	const installAddon = useCallback(async () => {
		if (!addonPath.trim()) return;
		setAddonInstalling(true);
		setAddonResult("");
		try {
			const r = await fetch("/api/v1/addon/install", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ project_path: addonPath }),
			});
			const j = await r.json();
			if (j.success) {
				setAddonResult(`Installed at ${j.addon_path}. Add as Autoload in Godot.`);
			} else {
				setAddonResult(`Error: ${j.error || "Unknown error"}`);
			}
		} catch (e) {
			setAddonResult(`Error: ${e instanceof Error ? e.message : "Connection failed"}`);
		} finally {
			setAddonInstalling(false);
		}
	}, [addonPath]);

	return (
		<div className="max-w-2xl space-y-6">
			<h1 className="text-2xl font-bold text-white flex items-center gap-3">
				<Settings className="text-amber-400" /> Settings
			</h1>

			{llmRec && (
				<div className="bg-fleet-900 border border-white/10 rounded-2xl p-5 space-y-3">
					<div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
						<Cpu size={16} /> LLM
					</div>
					{(llmRec as Record<string, string>).mode === "local" ? (
						<>
							<p className="text-sm text-slate-300">
								GPU: {(llmDetect as Record<string, Record<string, string>>)?.gpu?.name || "Unknown"} ({(llmRec as Record<string, number>).vram_gb} GB) — Tier {(llmRec as Record<string, number>).tier}: {(llmRec as Record<string, string>).tier_label}
							</p>
							<p className="text-sm">
								<span className="text-amber-400 font-bold">Model: {(llmRec as Record<string, string>).model}</span>
								<span className={`ml-2 text-xs ${(llmRec as Record<string, boolean>).installed ? "text-emerald-400" : "text-yellow-400"}`}>
									{(llmRec as Record<string, boolean>).installed ? "installed" : "not installed — run ollama pull"}
								</span>
							</p>
						</>
					) : (
						<p className="text-sm text-slate-400">
							No GPU or Ollama detected.{' '}
							<span className="text-blue-400">Configure a cloud API key below, or install Ollama.</span>
						</p>
					)}
					<p className="text-xs text-slate-500">{(llmRec as Record<string, string>).message}</p>
				</div>
			)}

			<div className="bg-fleet-900 border border-white/10 rounded-2xl p-6 space-y-4">
				<div className="flex items-center gap-2 mb-2">
					<Cpu size={16} className="text-amber-400" />
					<h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Godot Engine</h3>
				</div>
				<label className="block text-sm text-slate-400">
					Path to godot.exe (or godot on Linux/macOS)
					<input
						value={godotPath}
						onChange={(e) => setGodotPath(e.target.value)}
						placeholder="C:\Program Files\Godot\godot.exe"
						className="mt-1 w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-amber-500/30"
					/>
				</label>
				<p className="text-sm text-slate-400">
					Godot 4.0 is required. Download from{" "}
					<a href="https://godotengine.org/download" target="_blank" rel="noopener noreferrer" className="text-amber-400 hover:underline">
						godotengine.org
					</a>
					.
				</p>
			</div>

			<div className="bg-fleet-900 border border-white/10 rounded-2xl p-6 space-y-4">
				<div className="flex items-center gap-2 mb-2">
					<Download size={16} className="text-amber-400" />
					<h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">MCP Bridge Addon</h3>
				</div>
				<p className="text-sm text-slate-400">
					Install the MCP Bridge GDScript addon into a Godot project so it can receive MCP commands.
					After installation, add <code className="text-amber-400">addons/mcp_bridge/mcp_bridge.gd</code> as an Autoload
					in Project &gt; Project Settings &gt; Autoload.
				</p>
				<label className="block text-sm text-slate-400">
					Godot project path (folder containing project.godot)
					<div className="flex gap-2 mt-1">
						<input
							value={addonPath}
							onChange={(e) => setAddonPath(e.target.value)}
							placeholder="C:\MyGodotProject"
							className="flex-1 bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-amber-500/30"
						/>
						<button
							type="button"
							onClick={installAddon}
							disabled={addonInstalling || !addonPath.trim()}
							className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-600/20 border border-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-600/30 transition-all disabled:opacity-50"
						>
							{addonInstalling ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
							{addonInstalling ? "Installing..." : "Install Addon"}
						</button>
					</div>
				</label>
				{addonResult && (
					<p className={`text-sm ${addonResult.startsWith("Error") ? "text-red-400" : "text-emerald-400"}`}>
						{addonResult}
					</p>
				)}
			</div>

			<div className="bg-fleet-900 border border-white/10 rounded-2xl p-6 space-y-4">
				<div className="flex items-center gap-2 mb-2">
					<Network size={16} className="text-amber-400" />
					<h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Bridge Connection</h3>
				</div>
				<div className="grid grid-cols-2 gap-4">
					<label className="block text-sm text-slate-400">
						Host
						<input
							value={wsHost}
							onChange={(e) => setWsHost(e.target.value)}
							className="mt-1 w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-amber-500/30"
						/>
					</label>
					<label className="block text-sm text-slate-400">
						TCP Port
						<input
							type="number"
							min={1024}
							max={65535}
							value={wsPort}
							onChange={(e) => setWsPort(Number.parseInt(e.target.value) || 9080)}
							className="mt-1 w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-amber-500/30"
						/>
					</label>
				</div>
				<p className="text-sm text-slate-400">
					The Godot MCP addon listens on this TCP port. The MCP server connects as a client to relay tool commands.
				</p>
			</div>

			<div className="bg-fleet-900 border border-white/10 rounded-2xl p-6 space-y-4">
				<div className="flex items-center justify-between mb-2">
					<div className="flex items-center gap-2">
						<Rocket size={16} className="text-pink-400" />
						<h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">itch.io / Butler</h3>
					</div>
					<button type="button" onClick={refreshItch} className="text-xs text-pink-400 hover:underline">
						Refresh
					</button>
				</div>
				<div className="space-y-2 text-sm text-slate-400">
					<p className="flex items-center gap-2">
						<KeyRound size={14} />
						{itch?.auth?.api_key_set ? "BUTLER_API_KEY is set" : "BUTLER_API_KEY not set"}
					</p>
					<p>
						Butler: {itch?.butler?.found ? itch.butler.path : "not found"}
						{itch?.butler?.version ? ` (${itch.butler.version})` : ""}
					</p>
					<p>Default game: {itch?.defaults?.game ?? "dodge"}</p>
					<p>ITCH_TARGET: {itch?.defaults?.itch_target || "(not set)"}</p>
				</div>
				<p className="text-xs text-slate-500">
					Secrets are read from environment only: BUTLER_API_KEY, ITCH_TARGET, BUTLER_PATH, ITCH_CHANNEL_WEB, ITCH_CHANNEL_WIN, GODOT_EXPORT_GAME.
					Use the <a href="/ship" className="text-pink-400 hover:underline">Ship page</a> to export and push.
				</p>
			</div>

			<button
				type="button"
				onClick={save}
				className="px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-sm font-bold transition-all"
			>
				Save Settings
			</button>
			{status && <p className="text-sm text-slate-400">{status}</p>}
		</div>
	);
}
