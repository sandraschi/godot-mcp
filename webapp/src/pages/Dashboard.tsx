import {
  AlertTriangle, Box, Camera, CircuitBoard, Cpu,
  FileText, Play, RefreshCw, Rocket, RotateCcw, Settings, Gamepad2
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import { useAppStore } from "../store";

interface GodotStatus {
  available: boolean;
  path: string;
  host: string;
  ws_port: number;
  ws_connected: boolean;
}

interface ItchStatus {
  butler: { found: boolean; path: string };
  auth: { api_key_set: boolean };
  defaults: { itch_target: string };
  last_ship: { page_url?: string };
}

interface StatusData {
  ok: boolean;
  service: string;
  version: string;
  godot: GodotStatus;
  itch?: ItchStatus;
}

function GodotHint({ godot }: { godot: GodotStatus | undefined }) {
  if (!godot) return null;
  if (godot.ws_connected) return null;
  if (godot.available) {
    return (
      <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-sm space-y-2">
        <div className="flex items-center gap-2 text-amber-400 font-bold">
          <Gamepad2 size={16} /> Godot detected — bridge not running
        </div>
        <p className="text-slate-300">
          Godot is installed at <code className="text-xs bg-black/30 px-1.5 py-0.5 rounded">{godot.path}</code>
          but the MCP bridge isn't connected.
        </p>
        <p className="text-slate-400">
          Start the bridge: <code className="text-xs bg-black/30 px-1.5 py-0.5 rounded">just godot-bridge</code>
          {" "}in the repo root, or click Launch Bridge below.
        </p>
        <LaunchBridgeButton />
      </div>
    );
  }
  return (
    <div className="p-4 rounded-2xl bg-zinc-800/50 border border-zinc-700/50 text-sm space-y-2">
      <div className="flex items-center gap-2 text-zinc-400 font-bold">
        <Gamepad2 size={16} /> Godot not installed
      </div>
      <p className="text-slate-400">
        Install Godot 4.x: <code className="text-xs bg-black/30 px-1.5 py-0.5 rounded">just install-godot</code>
        {" "}or download from <a href="https://godotengine.org" className="text-blue-400 hover:underline" target="_blank" rel="noopener">godotengine.org</a>.
      </p>
    </div>
  );
}

function LaunchBridgeButton() {
  const [launching, setLaunching] = useState(false);
  const launch = useCallback(async () => {
    setLaunching(true);
    try {
      await apiFetch("/api/v1/bridge/start", { method: "POST" });
      setTimeout(() => window.location.reload(), 5000);
    } catch {
      setLaunching(false);
    }
  }, []);
  return (
    <button
      type="button"
      onClick={launch}
      disabled={launching}
      className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-500/30 transition-all disabled:opacity-50"
    >
      {launching ? "Launching..." : "Launch Godot Bridge"}
    </button>
  );
}

function OnboardingCard() {
  const [dismissed, setDismissed] = useState(() => {
    try { return localStorage.getItem("godot-mcp-onboarding-dismissed") === "1"; } catch { return false; }
  });
  useEffect(() => {
    if (!dismissed) {
      try { localStorage.setItem("godot-mcp-onboarding-dismissed", "1"); } catch {}
    }
  }, [dismissed]);

  return (
    <div className="bg-gradient-to-br from-fleet-900 to-zinc-900 border border-white/10 rounded-2xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-white">Welcome to Godot MCP</h2>
        <button type="button" onClick={() => setDismissed(true)} className="text-zinc-500 hover:text-white text-xs">Dismiss</button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div className="space-y-1.5 p-3 rounded-xl bg-white/5">
          <div className="text-amber-400 font-bold flex items-center gap-1.5"><span className="w-5 h-5 rounded-full bg-amber-500/20 flex items-center justify-center text-xs font-bold">1</span> Install</div>
          <p className="text-slate-400"><code className="text-xs bg-black/30 px-1 py-0.5 rounded">just install-godot</code> then <code className="text-xs bg-black/30 px-1 py-0.5 rounded">just bootstrap</code></p>
        </div>
        <div className="space-y-1.5 p-3 rounded-xl bg-white/5">
          <div className="text-amber-400 font-bold flex items-center gap-1.5"><span className="w-5 h-5 rounded-full bg-amber-500/20 flex items-center justify-center text-xs font-bold">2</span> Start</div>
          <p className="text-slate-400"><code className="text-xs bg-black/30 px-1 py-0.5 rounded">just serve</code> for backend, <code className="text-xs bg-black/30 px-1 py-0.5 rounded">just godot-bridge</code> for Godot</p>
        </div>
        <div className="space-y-1.5 p-3 rounded-xl bg-white/5">
          <div className="text-amber-400 font-bold flex items-center gap-1.5"><span className="w-5 h-5 rounded-full bg-amber-500/20 flex items-center justify-center text-xs font-bold">3</span> Build</div>
          <p className="text-slate-400">Use <a href="/game-builder" className="text-blue-400 hover:underline">Game Builder</a> or <a href="/tools" className="text-blue-400 hover:underline">Tools</a> to create games</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <a href="/game-builder" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-400 text-xs font-bold hover:bg-amber-500/30 transition-all">Build a Game</a>
        <a href="/ship" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-pink-500/20 text-pink-400 text-xs font-bold hover:bg-pink-500/30 transition-all">Ship to itch.io</a>
        <a href="/tools" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/20 text-indigo-400 text-xs font-bold hover:bg-indigo-500/30 transition-all">Browse Tools</a>
        <a href="/models" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 text-xs font-bold hover:bg-emerald-500/30 transition-all">Import Models</a>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [restarting, setRestarting] = useState(false);
  const [toolCount, setToolCount] = useState<number | null>(null);
  const { tauriAvailable } = useAppStore();

  const refresh = useCallback(() => {
    apiFetch<StatusData>("/api/v1/status")
      .then(setStatus)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to reach backend"));
    apiFetch<{ tool_count: number }>("/api/v1/health")
      .then((d) => setToolCount(d.tool_count))
      .catch(() => {});
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const restartBackend = useCallback(async () => {
    setRestarting(true);
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("start_backend");
      setTimeout(refresh, 3000);
    } catch {
      setRestarting(false);
    }
  }, [refresh]);

  const g = status?.godot;
  const itch = status?.itch;

  return (
    <div className="space-y-6" data-testid="dashboard">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-white" data-testid="dashboard-title">Dashboard</h1>
          <div className="flex items-center gap-1.5 text-xs text-zinc-400">
            <span id="backend-dot" data-testid="backend-dot" className={`w-2 h-2 rounded-full ${status ? "bg-green-500" : error ? "bg-red-500" : "bg-gray-500"} animate-pulse`} />
            <span>{status ? "Connected" : error ? "Offline" : "Connecting..."}</span>
          </div>
        </div>
        {tauriAvailable && status && !status.ok && (
          <button
            type="button"
            onClick={restartBackend}
            disabled={restarting}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-500/30 transition-all disabled:opacity-50"
            data-testid="restart-backend"
          >
            <RotateCcw size={14} className={restarting ? "animate-spin" : ""} />
            {restarting ? "Restarting..." : "Restart Backend"}
          </button>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-3 p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertTriangle size={16} />
          <span className="flex-1">{error}</span>
          <button
            type="button"
            onClick={refresh}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-red-500/20 text-red-400 text-xs font-bold hover:bg-red-500/30 transition-all"
          >
            <RefreshCw size={12} /> Retry
          </button>
        </div>
      )}

      <OnboardingCard />

      {g && !g.ws_connected && <GodotHint godot={g} />}

      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="bg-fleet-900 border border-white/10 rounded-2xl p-5 space-y-3" data-testid="kpi-godot">
          <div className="flex items-center gap-2 text-amber-400">
            <Cpu size={18} /> Godot Engine
          </div>
          <p className="text-sm text-slate-300">
            {!status ? "..." : g?.available ? `Found` : "Godot not detected"}
          </p>
          <p className="text-sm text-slate-400">
            {!status ? "..." : g?.ws_connected ? "Bridge connected" : "Bridge: not connected"}
          </p>
        </div>
        <div className="bg-fleet-900 border border-white/10 rounded-2xl p-5 space-y-3" data-testid="kpi-server">
          <div className="flex items-center gap-2 text-emerald-400">
            <CircuitBoard size={18} /> Server
          </div>
          <p className="text-2xl font-bold text-white" data-testid="server-version">
            {status ? `v${status.version}` : "..."}
          </p>
          <p className="text-sm text-slate-400">
            {status?.service || "godot-mcp"} — {status?.ok ? "Ready" : "Waiting..."}
          </p>
        </div>
        <div className="bg-fleet-900 border border-white/10 rounded-2xl p-5 space-y-3" data-testid="kpi-itch">
          <div className="flex items-center gap-2 text-pink-400">
            <Rocket size={18} /> itch.io / Butler
          </div>
          <p className="text-sm text-slate-300">
            {!status ? "..." : itch?.butler?.found ? "Butler ready" : "Butler not found"}
          </p>
          <p className="text-sm text-slate-400">
            {!status ? "..." : itch?.auth?.api_key_set ? "API key set" : "Set BUTLER_API_KEY"}
          </p>
          <a href="/ship" className="block text-sm text-pink-400 hover:underline">
            Open Ship page
          </a>
        </div>
        <div className="bg-fleet-900 border border-white/10 rounded-2xl p-5 space-y-3" data-testid="kpi-tools">
          <div className="flex items-center gap-2 text-indigo-400">
            <CircuitBoard size={18} /> Tools
          </div>
          <p className="text-2xl font-bold text-white">{toolCount ?? "..."}</p>
          <p className="text-sm text-slate-400">registered MCP tools</p>
        </div>
        <div className="bg-fleet-900 border border-white/10 rounded-2xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-indigo-400">
            <Play size={18} /> Quick Actions
          </div>
          <a href="/tools" className="block text-sm text-blue-400 hover:underline">
            Browse Tools
          </a>
          <a href="/ship" className="block text-sm text-blue-400 hover:underline">
            Ship to itch.io
          </a>
          <a href="/game-builder" className="block text-sm text-blue-400 hover:underline">
            Game Builder
          </a>
          <a href="/settings" className="block text-sm text-blue-400 hover:underline">
            Configure Godot Path
          </a>
        </div>
      </div>

      {g?.ws_connected && (
        <div className="bg-fleet-900 border border-white/10 rounded-2xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-amber-400">
              <Camera size={18} /> Viewport
            </div>
            <button
              type="button"
              onClick={() => {
                const img = document.getElementById("viewport-preview") as HTMLImageElement;
                if (img) img.src = "/api/v1/viewport/live?t=" + Date.now();
              }}
              className="text-xs text-blue-400 hover:underline"
            >
              Refresh
            </button>
          </div>
          <div className="relative bg-black/40 rounded-xl overflow-hidden" style={{ maxHeight: 300 }}>
            <img
              id="viewport-preview"
              src="/api/v1/viewport/live?t=1"
              alt="Godot Viewport"
              className="w-full h-auto"
              style={{ maxHeight: 300, objectFit: "contain" }}
              onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3" data-testid="quick-actions">
        {[
          { href: "/ship", icon: Rocket, label: "Ship itch", desc: "Export to itch.io" },
          { href: "/ship-steam", icon: Rocket, label: "Ship Steam", desc: "SteamPipe upload" },
          { href: "/models", icon: Box, label: "Models", desc: "Import STL/OBJ" },
          { href: "/game-builder", icon: FileText, label: "Game Builder", desc: "Prompt to game" },
          { href: "/tools", icon: Camera, label: "Tools", desc: "All MCP tools" },
          { href: "/settings", icon: Settings, label: "Settings", desc: "Godot config" },
        ].map((item) => (
          <a
            key={item.href}
            href={item.href}
            className="bg-fleet-900 border border-white/10 rounded-2xl p-4 text-center hover:border-amber-500/20 transition-all"
          >
            <item.icon size={24} className="mx-auto mb-2 text-amber-400" />
            <p className="text-sm font-bold text-slate-300">{item.label}</p>
            <p className="text-sm text-slate-400">{item.desc}</p>
          </a>
        ))}
      </div>
    </div>
  );
}
