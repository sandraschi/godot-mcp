import { Hammer, Loader2, Sparkles } from "lucide-react";
import { useState } from "react";
import { apiFetch } from "../lib/api";

type StepResult = Record<string, unknown>;

export default function GameBuilderPage() {
	const [concept, setConcept] = useState("A 2D endless runner with neon cyberpunk vibes");
	const [projectPath, setProjectPath] = useState("");
	const [worldlabsUrl, setWorldlabsUrl] = useState("http://127.0.0.1:10865");
	const [planJson, setPlanJson] = useState("");
	const [worldsJson, setWorldsJson] = useState("");
	const [busy, setBusy] = useState<string | null>(null);
	const [result, setResult] = useState<string | null>(null);

	const post = async (path: string, body: Record<string, unknown>, label: string) => {
		setBusy(label);
		setResult(null);
		try {
			const j = await apiFetch<StepResult>(path, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify(body),
				timeoutMs: 900000,
			});
			setResult(JSON.stringify(j, null, 2));
			if (path.endsWith("/design") && j.plan) {
				setPlanJson(JSON.stringify(j.plan));
			}
			if (path.endsWith("/worlds")) {
				setWorldsJson(JSON.stringify(j));
			}
			if (typeof j.project_path === "string") setProjectPath(j.project_path);
		} catch (e) {
			setResult(`Error: ${e}`);
		} finally {
			setBusy(null);
		}
	};

	return (
		<div className="space-y-6 max-w-4xl mx-auto">
			<h1 className="text-2xl font-bold text-white flex items-center gap-3">
				<Hammer className="text-violet-400" /> Game Builder
			</h1>
			<p className="text-sm text-slate-400">
				Prompt → Marble worlds (fleet-staged GLB) → Godot compose → scripts → export. Requires
				worldlabs bridge, godot-bridge (9080), and LLM sampling for design/logic steps.
			</p>

			<div className="rounded-xl border border-white/10 bg-[#1e1e26] p-4 space-y-3">
				<label className="block text-sm text-slate-300">Game concept</label>
				<textarea
					value={concept}
					onChange={(e) => setConcept(e.target.value)}
					rows={3}
					className="w-full rounded-lg border border-white/10 bg-[#0a0a0c] px-3 py-2 text-sm text-slate-200"
				/>
				<div className="grid md:grid-cols-2 gap-3">
					<div>
						<label className="block text-xs text-slate-500 mb-1">Project path (optional)</label>
						<input
							value={projectPath}
							onChange={(e) => setProjectPath(e.target.value)}
							placeholder="Empty → build/game-builder/&lt;slug&gt;"
							className="w-full rounded-lg border border-white/10 bg-[#0a0a0c] px-3 py-2 text-sm text-slate-200"
						/>
					</div>
					<div>
						<label className="block text-xs text-slate-500 mb-1">World Labs bridge URL</label>
						<input
							value={worldlabsUrl}
							onChange={(e) => setWorldlabsUrl(e.target.value)}
							className="w-full rounded-lg border border-white/10 bg-[#0a0a0c] px-3 py-2 text-sm text-slate-200"
						/>
					</div>
				</div>
			</div>

			<div className="flex flex-wrap gap-2">
				<button
					type="button"
					disabled={!!busy}
					onClick={() => post("/api/v1/game-builder/design", { game_concept: concept }, "Design")}
					className="px-3 py-2 rounded-lg bg-violet-600/20 border border-violet-500/30 text-sm text-violet-200 disabled:opacity-50"
				>
					1. Design
				</button>
				<button
					type="button"
					disabled={!!busy || !planJson}
					onClick={() =>
						post(
							"/api/v1/game-builder/worlds",
							{ game_plan_json: planJson, worldlabs_url: worldlabsUrl },
							"Worlds",
						)
					}
					className="px-3 py-2 rounded-lg bg-blue-600/20 border border-blue-500/30 text-sm text-blue-200 disabled:opacity-50"
				>
					2. Worlds + stage GLB
				</button>
				<button
					type="button"
					disabled={!!busy || !planJson}
					onClick={() =>
						post(
							"/api/v1/game-builder/compose",
							{ game_plan_json: planJson, worlds_result_json: worldsJson },
							"Compose",
						)
					}
					className="px-3 py-2 rounded-lg bg-emerald-600/20 border border-emerald-500/30 text-sm text-emerald-200 disabled:opacity-50"
				>
					3. Compose
				</button>
				<button
					type="button"
					disabled={!!busy || !planJson}
					onClick={() =>
						post(
							"/api/v1/game-builder/logic",
							{ game_plan_json: planJson, game_project_path: projectPath },
							"Logic",
						)
					}
					className="px-3 py-2 rounded-lg bg-amber-600/20 border border-amber-500/30 text-sm text-amber-200 disabled:opacity-50"
				>
					4. Logic + scenes
				</button>
				<button
					type="button"
					disabled={!!busy}
					onClick={() =>
						post(
							"/api/v1/game-builder/build",
							{
								game_concept: concept,
								worldlabs_url: worldlabsUrl,
								game_project_path: projectPath,
								ship: false,
							},
							"Full build",
						)
					}
					className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gradient-to-r from-violet-600/30 to-emerald-600/30 border border-white/10 text-sm text-white disabled:opacity-50"
				>
					<Sparkles size={14} /> Full pipeline
				</button>
			</div>

			{busy && (
				<div className="flex items-center gap-2 text-sm text-slate-400">
					<Loader2 size={14} className="animate-spin" /> {busy}…
				</div>
			)}

			{result && (
				<pre className="text-xs font-mono bg-[#0a0a0c] border border-white/10 rounded-xl p-4 overflow-x-auto text-slate-300 max-h-[50vh]">
					{result}
				</pre>
			)}
		</div>
	);
}
