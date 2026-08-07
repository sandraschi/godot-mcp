import { Loader2, Moon, Sun, Wifi, WifiOff } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import Sidebar from "./Sidebar";
import { useAppStore } from "../store";
import { API_BASE } from "../lib/api";
import useZoom from "../hooks/useZoom";

// EXPERIMENTAL light mode (invert hack). Not fleet standard — see index.css.
// Toggling `.dark` off the root flips the invert filter; persisted so the
// choice survives reloads. Delete this + the CSS block to revert.
const THEME_KEY = "godot-light-mode";

function useExperimentalTheme() {
	const [light, setLight] = useState(() => {
		try {
			return localStorage.getItem(THEME_KEY) === "1";
		} catch {
			return false;
		}
	});

	useEffect(() => {
		document.documentElement.classList.toggle("dark", !light);
		try {
			localStorage.setItem(THEME_KEY, light ? "1" : "0");
		} catch {
			// ignore storage errors
		}
	}, [light]);

	return { light, toggle: () => setLight((v) => !v) };
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
	useZoom();
	const [collapsed, setCollapsed] = useState(false);
	const [connected, setConnected] = useState<boolean | null>(null);
	const { light, toggle } = useExperimentalTheme();
	const { setConnectionStatus, setServerVersion, setGodotAvailable, setTauriAvailable } = useAppStore();
	const [tauri, setTauri] = useState(false);

	const setConn = setConnectionStatus;

	useEffect(() => {
		(async () => {
			try {
				const { isTauri } = await import("../lib/tauri");
				const t = await isTauri();
				setTauri(t);
				setTauriAvailable(t);
			} catch {
				setTauri(false);
				setTauriAvailable(false);
			}
		})();
	}, [setTauriAvailable]);

	useEffect(() => {
		if (!tauri) return;
		let unlisten: (() => void) | undefined;
		(async () => {
			try {
				const { listen } = await import("@tauri-apps/api/event");
				unlisten = await listen<string>("backend-status", (event) => {
					if (event.payload === "ready") {
						refresh();
					} else if (typeof event.payload === "string" && event.payload.startsWith("error:")) {
						setConnected(false);
						setConn("disconnected");
					}
				});
			} catch {
			}
		})();
		return () => { if (unlisten) unlisten(); };
	}, [tauri, setConn]);

	const refresh = useCallback(async () => {
		try {
			const url = tauri ? `${API_BASE}/api/v1/status` : "/api/v1/status";
			const r = await fetch(url);
			const j = await r.json();
			const ok = j.service === "godot-mcp";
			setConnected(ok);
			setConnectionStatus(ok ? "connected" : "disconnected");
			setServerVersion(j.version || "");
			setGodotAvailable(j.godot?.available || false);
		} catch {
			setConnected(false);
			setConnectionStatus("disconnected");
		}
	}, [tauri, setConnectionStatus, setServerVersion, setGodotAvailable]);

	useEffect(() => {
		refresh();
		const id = setInterval(refresh, 10000);
		return () => clearInterval(id);
	}, [refresh]);

	return (
		<div className="flex h-full">
			<Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
			<div className="flex-1 flex flex-col overflow-hidden">
				<header className="h-12 flex items-center justify-end px-6 border-b border-white/10 bg-fleet-950 shrink-0">
					<div className="flex items-center gap-3">
						<button
							type="button"
							onClick={toggle}
							className="p-1.5 rounded-md text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
							title={light ? "Switch to dark (experimental light mode)" : "Switch to light (experimental, ugly)"}
							aria-label="Toggle light mode (experimental)"
						>
							{light ? <Moon size={14} /> : <Sun size={14} />}
						</button>
						<div className="flex items-center gap-2 text-sm">
						{connected === null ? (
							<Loader2 size={12} className="animate-spin text-slate-300" />
						) : connected ? (
							<Wifi size={12} className="text-emerald-400" />
						) : (
							<WifiOff size={12} className="text-red-400" />
						)}
						<span className={connected === true ? "text-emerald-400" : "text-slate-300"}>
							{connected === null ? "Connecting..." : connected ? "Server Ready" : "Server Offline"}
						</span>
					</div>
					</div>
				</header>
				<main className="flex-1 overflow-y-auto p-6">{children}</main>
			</div>
		</div>
	);
}
