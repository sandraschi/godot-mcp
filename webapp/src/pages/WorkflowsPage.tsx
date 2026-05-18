import { CheckCircle2, List, Loader2, Play, X } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";

interface WorkflowStep {
	step: number;
	tool: string;
	input: Record<string, string>;
}

interface WorkflowDef {
	name: string;
	description: string;
	steps: WorkflowStep[];
	parameters: { name: string; type: string; description: string }[];
}

const workflows: WorkflowDef[] = [
	{
		name: "scene_setup",
		description: "Set up a complete 3D scene with lighting, camera, and environment.",
		steps: [
			{ step: 1, tool: "godot_create_camera", input: { fov: "75" } },
			{ step: 2, tool: "godot_add_light", input: { type: "DirectionalLight3D" } },
			{ step: 3, tool: "godot_set_material", input: {} },
		],
		parameters: [
			{ name: "csv_path", type: "string", description: "Path to velocity CSV" },
		],
	},
	{
		name: "particle_cfd",
		description: "Import CFD velocity data and spawn GPU particles for flow visualization.",
		steps: [
			{ step: 1, tool: "godot_load_velocity", input: { csv_path: "{csv_path}" } },
			{ step: 2, tool: "godot_spawn_particles", input: { count: "5000" } },
			{ step: 3, tool: "godot_animate_streamline", input: {} },
		],
		parameters: [
			{ name: "csv_path", type: "string", description: "Path to velocity CSV" },
		],
	},
];

export default function WorkflowsPage() {
	const [running, setRunning] = useState<string | null>(null);
	const [params, setParams] = useState<Record<string, string>>({});
	const [result, setResult] = useState<string | null>(null);
	const [resultLoading, setResultLoading] = useState(false);

	const handleRun = async (w: WorkflowDef) => {
		setRunning(w.name);
		setResult(null);
		setResultLoading(true);
		try {
			const r = await fetch("/api/v1/control/tool", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					tool: "workflow_run",
					args: { workflow: w.name, parameters: params },
				}),
			});
			const j = await r.json();
			setResult(JSON.stringify(j, null, 2));
		} catch (e) {
			setResult(`Error: ${e}`);
		} finally {
			setResultLoading(false);
			setRunning(null);
		}
	};

	const openRunPanel = (w: WorkflowDef) => {
		setRunning(w.name);
		const initial: Record<string, string> = {};
		w.parameters.forEach((p) => (initial[p.name] = ""));
		setParams(initial);
		setResult(null);
	};

	const selected = workflows.find((w) => w.name === running);

	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			className="space-y-6 max-w-6xl"
		>
			<h1 className="text-2xl font-bold text-white flex items-center gap-3">
				<Play className="text-amber-500" size={24} /> Agentic Workflows
			</h1>
			<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
				{workflows.map((w) => (
					<div
						key={w.name}
						className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-3 hover:border-amber-500/30 transition-all"
					>
						<div className="flex items-center justify-between">
							<h3 className="text-sm font-bold text-white">{w.name}</h3>
							<button
								type="button"
								onClick={() => openRunPanel(w)}
								className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/20 text-amber-400 text-xs font-bold hover:bg-amber-500/30 transition-all"
							>
								<Play size={12} /> Run
							</button>
						</div>
						<p className="text-sm text-slate-400">{w.description}</p>
						<div className="flex items-center gap-2 text-xs text-slate-500">
							<List size={12} /> {w.steps.length} steps
						</div>
						<div className="space-y-1">
							{w.steps.map((s) => (
								<div key={s.step} className="flex items-center gap-2 text-xs text-slate-400">
									<CheckCircle2 size={10} className="text-emerald-500 shrink-0" />
									<span className="font-medium text-slate-500">Step {s.step}:</span>{" "}
									<code className="text-blue-400">{s.tool}()</code>
								</div>
							))}
						</div>
					</div>
				))}
			</div>
			{selected && (
				<motion.div
					initial={{ opacity: 0, y: 10 }}
					animate={{ opacity: 1, y: 0 }}
					className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-4"
				>
					<div className="flex items-center justify-between">
						<h2 className="text-sm font-bold text-slate-200">
							Run: <code className="text-amber-400">{selected.name}</code>
						</h2>
						<button type="button" onClick={() => { setRunning(null); setResult(null); }}>
							<X size={14} className="text-slate-400" />
						</button>
					</div>
					{selected.parameters.length > 0 && (
						<div className="space-y-2">
							<p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Parameters</p>
							{selected.parameters.map((p) => (
								<div key={p.name}>
									<label className="text-xs text-slate-400 block mb-1">{p.name}</label>
									<input
										type="text"
										placeholder={p.description}
										value={params[p.name] || ""}
										onChange={(e) => setParams({ ...params, [p.name]: e.target.value })}
										className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/10 text-sm text-slate-200 placeholder-slate-600 outline-none"
									/>
								</div>
							))}
						</div>
					)}
					<button
						type="button"
						onClick={() => handleRun(selected)}
						disabled={resultLoading}
						className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-500/30 transition-all disabled:opacity-50"
					>
						{resultLoading ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
						Execute Workflow
					</button>
					{result && (
						<pre className="p-3 rounded-xl bg-black/40 text-xs text-slate-300 overflow-auto max-h-60 border border-white/10">
							{result}
						</pre>
					)}
				</motion.div>
			)}
		</motion.div>
	);
}
