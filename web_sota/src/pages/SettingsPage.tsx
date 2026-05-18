import { Cpu, Network, Settings } from "lucide-react";
import { useEffect, useState } from "react";

export default function SettingsPage() {
	const [godotPath, setGodotPath] = useState("");
	const [wsPort, setWsPort] = useState(9080);
	const [wsHost, setWsHost] = useState("127.0.0.1");
	const [status, setStatus] = useState("");

	useEffect(() => {
		fetch("/api/v1/status")
			.then((r) => r.json())
			.then((j) => {
				if (j.godot?.path) setGodotPath(j.godot.path);
				if (j.godot?.ws_port) setWsPort(j.godot.ws_port);
				if (j.godot?.host) setWsHost(j.godot.host);
			})
			.catch(() => {});
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

	return (
		<div className="max-w-2xl space-y-6">
			<h1 className="text-2xl font-bold text-white flex items-center gap-3">
				<Settings className="text-blue-400" /> Settings
			</h1>

			<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-6 space-y-4">
				<div className="flex items-center gap-2 mb-2">
					<Cpu size={16} className="text-blue-400" />
					<h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Godot Engine</h3>
				</div>
				<label className="block text-sm text-slate-400">
					Path to godot.exe (or godot on Linux/macOS)
					<input
						value={godotPath}
						onChange={(e) => setGodotPath(e.target.value)}
						placeholder="C:\Program Files\Godot\godot.exe"
						className="mt-1 w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-blue-500/30"
					/>
				</label>
				<p className="text-sm text-slate-400">
					Godot 4.0 is required. Download from{" "}
					<a href="https://godotengine.org/download" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">
						godotengine.org
					</a>
					. The MCP addon must be loaded in the Godot project for WebSocket commands to work.
				</p>
			</div>

			<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-6 space-y-4">
				<div className="flex items-center gap-2 mb-2">
					<Network size={16} className="text-blue-400" />
					<h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">WebSocket Bridge</h3>
				</div>
				<div className="grid grid-cols-2 gap-4">
					<label className="block text-sm text-slate-400">
						WebSocket Host
						<input
							value={wsHost}
							onChange={(e) => setWsHost(e.target.value)}
							className="mt-1 w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-blue-500/30"
						/>
					</label>
					<label className="block text-sm text-slate-400">
						WebSocket Port
						<input
							type="number"
							min={1024}
							max={65535}
							value={wsPort}
							onChange={(e) => setWsPort(Number.parseInt(e.target.value) || 9080)}
							className="mt-1 w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none focus:border-blue-500/30"
						/>
					</label>
				</div>
				<p className="text-sm text-slate-400">
					The Godot MCP addon listens on this WebSocket port. The MCP server connects as a client to relay tool commands.
				</p>
			</div>

			<button
				type="button"
				onClick={save}
				className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-bold"
			>
				Save Settings
			</button>
			{status && <p className="text-sm text-slate-400">{status}</p>}
		</div>
	);
}
