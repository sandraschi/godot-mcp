import { CheckCircle, Download, ExternalLink, Puzzle, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

interface Plugin {
	name: string;
	repo: string;
	description: string;
	installed: boolean;
}

export default function PluginsPage() {
	const [plugins, setPlugins] = useState<Plugin[]>([]);
	const [loading, setLoading] = useState(true);
	const [installing, setInstalling] = useState<string | null>(null);
	const [message, setMessage] = useState<{ text: string; ok: boolean } | null>(null);

	const refresh = useCallback(() => {
		setLoading(true);
		apiFetch<{ success: boolean; plugins: Plugin[] }>("/api/v1/plugins")
			.then((d) => setPlugins(d.plugins))
			.catch(() => setPlugins([]))
			.finally(() => setLoading(false));
	}, []);

	useEffect(() => { refresh(); }, [refresh]);

	const install = useCallback(async (name: string) => {
		setInstalling(name);
		setMessage(null);
		try {
			const r = await apiFetch<{ success: boolean; error?: string }>("/api/v1/plugins/install", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ plugin_name: name, project_path: "" }),
				timeoutMs: 120000,
			});
			if (r.success) {
				setMessage({ text: `"${name}" installed. Enable it in Project > Project Settings > Plugins.`, ok: true });
				refresh();
			} else {
				setMessage({ text: r.error || "Install failed", ok: false });
			}
		} catch (e) {
			setMessage({ text: e instanceof Error ? e.message : "Install failed", ok: false });
		}
		setInstalling(null);
	}, [refresh]);

	return (
		<div className="space-y-6" data-testid="plugins-page">
			<div className="flex items-center gap-3">
				<Puzzle className="text-amber-400" size={24} />
				<div>
					<h1 className="text-2xl font-bold text-white">Plugins</h1>
					<p className="text-sm text-slate-400">Community Godot plugins — install from GitHub</p>
				</div>
			</div>

			{message && (
				<div className={`flex items-center gap-3 p-4 rounded-2xl text-sm ${message.ok ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400" : "bg-red-500/10 border border-red-500/20 text-red-400"}`}>
					{message.ok ? <CheckCircle size={16} /> : <XCircle size={16} />}
					<span>{message.text}</span>
				</div>
			)}

			{loading ? (
				<div className="text-center py-12 text-slate-500">Loading plugins...</div>
			) : (
				<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
					{plugins.map((p) => (
						<div key={p.name} className="bg-fleet-900 border border-white/10 rounded-2xl p-5 space-y-3">
							<div className="flex items-start justify-between gap-3">
								<div className="space-y-1 min-w-0">
									<div className="flex items-center gap-2">
										<h3 className="text-base font-bold text-white truncate">{p.name}</h3>
										{p.installed ? (
											<span className="text-xs text-emerald-400 flex items-center gap-1">
												<CheckCircle size={12} /> installed
											</span>
										) : (
											<span className="text-xs text-slate-500">not installed</span>
										)}
									</div>
									<p className="text-sm text-slate-400 line-clamp-2">{p.description}</p>
								</div>
							</div>
							<div className="flex items-center gap-2">
								<a
									href={`https://github.com/${p.repo}`}
									target="_blank"
									rel="noopener"
									className="flex items-center gap-1 text-xs text-blue-400 hover:underline"
								>
									<ExternalLink size={12} /> {p.repo}
								</a>
							</div>
							<div className="pt-1">
								{p.installed ? (
									<span className="text-xs text-emerald-400/60">Already installed</span>
								) : (
									<button
										type="button"
										onClick={() => install(p.name)}
										disabled={installing === p.name}
										className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-400 text-xs font-bold hover:bg-amber-500/30 transition-all disabled:opacity-50"
									>
										<Download size={12} className={installing === p.name ? "animate-bounce" : ""} />
										{installing === p.name ? "Installing..." : "Install"}
									</button>
								)}
							</div>
						</div>
					))}
				</div>
			)}

			<div className="p-4 rounded-2xl bg-zinc-800/50 border border-zinc-700/50 text-sm text-slate-400">
				<p className="font-bold text-slate-300 mb-1">How plugins work</p>
				<p>Plugins are downloaded from GitHub (latest release or main branch) and extracted to <code className="text-xs bg-black/30 px-1.5 py-0.5 rounded">addons/&lt;name&gt;/</code> in your Godot project. After installation, enable the plugin in Project &gt; Project Settings &gt; Plugins. See <code className="text-xs bg-black/30 px-1.5 py-0.5 rounded">docs/godot-ecosystem.md</code> for the full catalog.</p>
			</div>
		</div>
	);
}
