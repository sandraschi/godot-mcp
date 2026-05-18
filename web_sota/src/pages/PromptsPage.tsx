import { Loader2, MessageSquare, Send, Sparkles, X } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";

interface PromptParam {
	name: string;
	type: string;
	description: string;
}

interface PromptDef {
	name: string;
	description: string;
	prompt_template: string;
	parameters: PromptParam[];
}

const prompts: PromptDef[] = [
	{
		name: "describe_scene",
		description: "Generate a natural language description of the current 3D scene.",
		prompt_template: "Describe the current Godot scene in detail, listing all nodes, materials, lights, and cameras.",
		parameters: [],
	},
	{
		name: "suggest_lighting",
		description: "Get AI suggestions for improving scene lighting.",
		prompt_template: "Given a scene with {light_count} lights, suggest improvements for better visual quality.",
		parameters: [
			{ name: "light_count", type: "number", description: "Number of lights in scene" },
		],
	},
];

export default function PromptsPage() {
	const [executing, setExecuting] = useState<string | null>(null);
	const [paramValues, setParamValues] = useState<Record<string, string>>({});
	const [response, setResponse] = useState<string | null>(null);
	const [loading, setLoading] = useState(false);

	const openExecute = (p: PromptDef) => {
		setExecuting(p.name);
		const initial: Record<string, string> = {};
		p.parameters.forEach((pr) => (initial[pr.name] = ""));
		setParamValues(initial);
		setResponse(null);
	};

	const handleExecute = async (prompt: PromptDef) => {
		setLoading(true);
		try {
			const r = await fetch("/api/v1/control/tool", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					tool: "prompt_execute",
					args: { name: prompt.name, parameters: paramValues },
				}),
			});
			const j = await r.json();
			setResponse(typeof j === "string" ? j : JSON.stringify(j, null, 2));
		} catch (e) {
			setResponse(`Error: ${e}`);
		} finally {
			setLoading(false);
		}
	};

	const selected = prompts.find((p) => p.name === executing);

	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			className="space-y-6 max-w-6xl"
		>
			<h1 className="text-2xl font-bold text-white flex items-center gap-3">
				<Sparkles className="text-amber-500" size={24} /> AI Prompt Templates
			</h1>
			<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
				{prompts.map((p) => (
					<div
						key={p.name}
						className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-3 hover:border-amber-500/30 transition-all"
					>
						<div className="flex items-start justify-between">
							<div className="flex items-center gap-2">
								<MessageSquare size={16} className="text-amber-400" />
								<h3 className="text-sm font-bold text-white">{p.name}</h3>
							</div>
							<button
								type="button"
								onClick={() => openExecute(p)}
								className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/20 text-amber-400 text-xs font-bold hover:bg-amber-500/30 transition-all"
							>
								<Send size={12} /> Execute
							</button>
						</div>
						<p className="text-sm text-slate-400">{p.description}</p>
						{p.parameters.length > 0 && (
							<div className="text-xs text-slate-500">
								Parameters: {p.parameters.map((pr) => pr.name).join(", ")}
							</div>
						)}
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
							Execute: <code className="text-amber-400">{selected.name}</code>
						</h2>
						<button type="button" onClick={() => { setExecuting(null); setResponse(null); }}>
							<X size={14} className="text-slate-400" />
						</button>
					</div>
					<pre className="p-3 rounded-xl bg-black/40 text-xs text-slate-400 border border-white/10 overflow-auto">
						{selected.prompt_template}
					</pre>
					{selected.parameters.length > 0 && (
						<div className="space-y-2">
							{selected.parameters.map((pr) => (
								<div key={pr.name}>
									<label className="text-xs text-slate-400 block mb-1">{pr.name}</label>
									<input
										type="text"
										placeholder={pr.description}
										value={paramValues[pr.name] || ""}
										onChange={(e) => setParamValues({ ...paramValues, [pr.name]: e.target.value })}
										className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/10 text-sm text-slate-200 placeholder-slate-600 outline-none"
									/>
								</div>
							))}
						</div>
					)}
					<button
						type="button"
						onClick={() => handleExecute(selected)}
						disabled={loading}
						className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-500/30 transition-all disabled:opacity-50"
					>
						{loading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
						Execute Prompt
					</button>
					{response && (
						<div className="p-3 rounded-xl bg-black/40 text-sm text-slate-300 border border-white/10 overflow-auto max-h-60 whitespace-pre-wrap">
							{response}
						</div>
					)}
				</motion.div>
			)}
		</motion.div>
	);
}
