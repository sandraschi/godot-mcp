import { CheckCircle2, Hammer, Loader2, Play, Sparkles, XCircle } from "lucide-react";
import { useState } from "react";
import { apiFetch } from "../lib/api";

type StepResult = Record<string, unknown>;

interface PipelineStep {
	key: string;
	label: string;
	desc: string;
}

const PIPELINE: PipelineStep[] = [
	{ key: "design", label: "Design", desc: "LLM plans the game" },
	{ key: "worlds", label: "Worlds", desc: "Marble world gen" },
	{ key: "compose", label: "Compose", desc: "Godot scene setup" },
	{ key: "logic", label: "Logic", desc: "GDScript generation" },
	{ key: "export", label: "Export", desc: "HTML5 / Windows" },
	{ key: "ship", label: "Ship", desc: "itch.io / Steam" },
];

function PipelineViz({ steps }: { steps: Record<string, "idle" | "running" | "done" | "failed"> }) {
	return (
		<div className="flex items-center gap-1 md:gap-2" data-testid="pipeline-viz">
			{PIPELINE.map((step, i) => {
				const status = steps[step.key] || "idle";
				const isLast = i === PIPELINE.length - 1;
				return (
					<div key={step.key} className="flex items-center gap-1 md:gap-2 flex-1 min-w-0">
						<div
							className={`flex items-center gap-1.5 px-2 md:px-3 py-1.5 rounded-lg text-xs font-bold transition-all whitespace-nowrap ${
								status === "done"
									? "bg-emerald-500/20 text-emerald-400"
									: status === "running"
									? "bg-amber-500/20 text-amber-400 animate-pulse"
									: status === "failed"
									? "bg-red-500/20 text-red-400"
									: "bg-zinc-800/50 text-zinc-500"
							}`}
							title={step.desc}
						>
							{status === "done" ? <CheckCircle2 size={12} /> : status === "running" ? <Loader2 size={12} className="animate-spin" /> : status === "failed" ? <XCircle size={12} /> : <Play size={12} />}
							<span className="hidden md:inline">{step.label}</span>
						</div>
						{!isLast && <div className="h-px flex-1 bg-white/10 min-w-[8px]" />}
					</div>
				);
			})}
		</div>
	);
}

export default function GameBuilderPage() {
	const [concept, setConcept] = useState("A 2D endless runner with neon cyberpunk vibes");
	const [projectPath, setProjectPath] = useState("");
	const [worldlabsUrl, setWorldlabsUrl] = useState("http://127.0.0.1:10865");
	const [planJson, setPlanJson] = useState("");
	const [worldsJson, setWorldsJson] = useState("");
	const [busy, setBusy] = useState<string | null>(null);
	const [result, setResult] = useState<string | null>(null);
	const [pipelineStatus, setPipelineStatus] = useState<Record<string, "idle" | "running" | "done" | "failed">>({});

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
				setPipelineStatus((s) => ({ ...s, design: "done" }));
			}
			if (path.endsWith("/worlds")) {
				setWorldsJson(JSON.stringify(j));
				setPipelineStatus((s) => ({ ...s, worlds: "done" }));
			}
			if (path.endsWith("/compose")) setPipelineStatus((s) => ({ ...s, compose: "done" }));
			if (path.endsWith("/logic")) setPipelineStatus((s) => ({ ...s, logic: "done" }));
			if (path.endsWith("/export")) setPipelineStatus((s) => ({ ...s, export: "done" }));
			if (typeof j.project_path === "string") setProjectPath(j.project_path);
		} catch (e) {
			setResult(`Error: ${e}`);
		} finally {
			setBusy(null);
		}
	};

	const buildAll = async () => {
		setPipelineStatus({ design: "running", worlds: "idle", compose: "idle", logic: "idle", export: "idle", ship: "idle" });
		setResult(null);
		try {
			const j = await apiFetch<StepResult & { summary?: string }>("/api/v1/game-builder/build", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ game_concept: concept, worldlabs_url: worldlabsUrl, game_project_path: projectPath }),
				timeoutMs: 900000,
			});
			setResult(JSON.stringify(j, null, 2));
			if (j.project_path) setProjectPath(j.project_path as string);
			setPipelineStatus({ design: "done", worlds: "done", compose: "done", logic: "done", export: "done", ship: "idle" });
		} catch (e) {
			setResult(`Error: ${e}`);
			setPipelineStatus((s) => ({ ...s, design: "failed" }));
		}
	};

	return (
		<div className="space-y-6 max-w-4xl mx-auto">
			<div className="flex items-center gap-3">
				<Hammer className="text-violet-400" size={24} />
				<div>
					<h1 className="text-2xl font-bold text-white">Game Builder</h1>
					<p className="text-sm text-slate-400">Prompt — Godot scene — GDScript — export</p>
				</div>
			</div>

			<PipelineViz steps={pipelineStatus} />

			<div className="grid grid-cols-1 md:grid-cols-2 gap-3">
				{PIPELINE.map((step) => (
					<button
						key={step.key}
						type="button"
						disabled={busy !== null || step.key === "ship"}
						onClick={() => {
							setPipelineStatus((s) => ({ ...s, [step.key]: "running" }));
							const body: Record<string, unknown> = {};
							if (step.key === "design") body.game_concept = concept;
							if (step.key === "worlds") { body.game_plan_json = planJson; body.worldlabs_url = worldlabsUrl; }
							if (step.key === "compose") { body.game_plan_json = planJson; body.worlds_result_json = worldsJson; }
							if (step.key === "logic") { body.game_plan_json = planJson; body.game_project_path = projectPath; }
							if (step.key === "export") { body.game_plan_json = planJson; body.game_project_path = projectPath; }
							post(`/api/v1/game-builder/${step.key}`, body, step.label);
						}}
						className={`flex items-center gap-3 p-4 rounded-2xl border transition-all text-left ${
							pipelineStatus[step.key] === "done"
								? "bg-emerald-500/10 border-emerald-500/30"
								: "bg-fleet-900 border-white/10 hover:border-amber-500/30"
						} ${busy !== null ? "opacity-50" : "cursor-pointer"}`}
					>
						<div className={`p-2 rounded-xl ${step.key === "ship" ? "bg-pink-500/20" : "bg-amber-500/20"}`}>
							{step.key === "ship" ? <Sparkles size={16} className="text-pink-400" /> : <Play size={16} className="text-amber-400" />}
						</div>
						<div className="flex-1 min-w-0">
							<p className="text-sm font-bold text-white">{step.label}</p>
							<p className="text-xs text-slate-400">{step.desc}</p>
						</div>
						{pipelineStatus[step.key] === "done" && <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />}
						{pipelineStatus[step.key] === "running" && <Loader2 size={16} className="text-amber-400 animate-spin shrink-0" />}
					</button>
				))}
			</div>

			<button
				type="button"
				onClick={buildAll}
				disabled={busy !== null}
				className="w-full px-6 py-3 rounded-xl bg-violet-500/20 text-violet-400 text-sm font-bold hover:bg-violet-500/30 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
			>
				{busy ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
				{busy ? `Building: ${busy}...` : "Build Full Game"}
			</button>

			<div className="rounded-xl border border-white/10 bg-fleet-900 p-4 space-y-3">
				<label htmlFor="game-concept" className="block text-sm text-slate-300">Game concept</label>
				<textarea
					id="game-concept"
					value={concept}
					onChange={(e) => setConcept(e.target.value)}
					rows={2}
					className="w-full rounded-lg border border-white/10 bg-[#0a0a0c] px-3 py-2 text-sm text-slate-200"
				/>
				<div className="grid md:grid-cols-2 gap-3">
					<div>
						<label className="text-xs text-slate-500">World Labs URL</label>
						<input value={worldlabsUrl} onChange={(e) => setWorldlabsUrl(e.target.value)} className="w-full rounded-lg border border-white/10 bg-[#0a0a0c] px-3 py-2 text-sm text-slate-200" />
					</div>
					<div>
						<label className="text-xs text-slate-500">Project path (auto)</label>
						<input value={projectPath} readOnly className="w-full rounded-lg border border-white/10 bg-[#0a0a0c] px-3 py-2 text-sm text-slate-500" />
					</div>
				</div>
			</div>

			{result && (
				<details open className="rounded-xl border border-white/10 bg-fleet-900 p-4">
					<summary className="text-sm font-bold text-slate-300 cursor-pointer">Result JSON</summary>
					<pre className="mt-3 text-xs text-slate-400 overflow-auto max-h-96 whitespace-pre-wrap font-mono">{result}</pre>
				</details>
			)}
		</div>
	);
}
