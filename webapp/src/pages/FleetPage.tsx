import { Box, CircuitBoard, ExternalLink, Globe, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../lib/api";

interface FleetStatus {
  success: boolean;
  exchange_root: string;
  exchange_exists: boolean;
  asset_count: number;
  assets: { name: string; path: string; modified: string }[];
  worldlabs_bridge: string;
  worldlabs_web: string;
  godot_mesh_import: boolean;
  godot_splat_import: boolean;
}

export default function FleetPage() {
  const [status, setStatus] = useState<FleetStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    setLoading(true);
    apiFetch<FleetStatus>("/api/v1/fleet/status")
      .then(setStatus)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return (
    <div className="space-y-6" data-testid="fleet-page">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Globe className="text-amber-400" size={24} />
          <div>
            <h1 className="text-2xl font-bold text-white">Fleet Exchange</h1>
            <p className="text-sm text-slate-400">Cross-repo asset pipeline and World Labs bridge</p>
          </div>
        </div>
        <button
          type="button"
          onClick={refresh}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 text-slate-400 text-xs font-bold hover:bg-zinc-700 transition-all"
        >
          <RefreshCw size={12} /> Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>
      )}

      {loading && !status ? (
        <div className="text-center py-12 text-slate-500">Loading...</div>
      ) : status && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-fleet-900 border border-white/10 rounded-2xl p-5 space-y-2" data-testid="kpi-exchange">
              <div className="flex items-center gap-2 text-emerald-400 text-sm font-bold">
                <Box size={16} /> Exchange
              </div>
              <p className="text-2xl font-bold text-white">{status.asset_count}</p>
              <p className="text-xs text-slate-400">assets in depot</p>
              <p className="text-xs text-slate-500 truncate">{status.exchange_root}</p>
            </div>
            <div className="bg-fleet-900 border border-white/10 rounded-2xl p-5 space-y-2">
              <div className="flex items-center gap-2 text-indigo-400 text-sm font-bold">
                <Globe size={16} /> World Labs
              </div>
              <p className="text-sm text-slate-300">
                Mesh import: <span className={status.godot_mesh_import ? "text-emerald-400" : "text-red-400"}>{status.godot_mesh_import ? "Available" : "No"}</span>
              </p>
              <p className="text-sm text-slate-300">
                Splat import: <span className={status.godot_splat_import ? "text-emerald-400" : "text-yellow-400"}>{status.godot_splat_import ? "Available" : "Spark viewer"}</span>
              </p>
            </div>
            <div className="bg-fleet-900 border border-white/10 rounded-2xl p-5 space-y-2">
              <div className="flex items-center gap-2 text-pink-400 text-sm font-bold">
                <CircuitBoard size={16} /> Bridge
              </div>
              <p className="text-sm text-slate-400 truncate" title={status.worldlabs_bridge}>
                API: {status.worldlabs_bridge || "N/A"}
              </p>
            </div>
            <div className="bg-fleet-900 border border-white/10 rounded-2xl p-5 space-y-2">
              <div className="flex items-center gap-2 text-amber-400 text-sm font-bold">
                <ExternalLink size={16} /> Pipeline
              </div>
              <div className="space-y-1 text-xs">
                <a href="/models" className="block text-blue-400 hover:underline">Import models</a>
                <a href="/game-builder" className="block text-blue-400 hover:underline">Game Builder</a>
                <a href="/ship" className="block text-blue-400 hover:underline">Ship to itch.io</a>
              </div>
            </div>
          </div>

          {status.assets.length > 0 && (
            <div className="bg-fleet-900 border border-white/10 rounded-2xl p-5 space-y-3">
              <h2 className="text-sm font-bold text-slate-300">Exchange Assets</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                {status.assets.map((asset, i) => (
                  <div key={i} className="bg-black/30 rounded-xl p-3 space-y-1">
                    <p className="text-sm text-slate-300 truncate font-medium" title={asset.name}>{asset.name}</p>
                    <p className="text-xs text-slate-500 truncate">{asset.path}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="p-4 rounded-2xl bg-zinc-800/50 border border-zinc-700/50 text-sm text-slate-400">
            <p className="font-bold text-slate-300 mb-1">Pipeline</p>
            <code className="text-xs">blender-mcp --&gt; godot_import_glb --&gt; Godot scene --&gt; godot_export_release --&gt; itch.io/Steam</code>
          </div>
        </>
      )}
    </div>
  );
}
