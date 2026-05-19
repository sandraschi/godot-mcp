import { Archive, Loader2, PackagePlus, Search, X } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";
import { apiFetch } from "../lib/api";

export default function BundlesPage() {
	const [name, setName] = useState("");
	const [description, setDescription] = useState("");
	const [toolSequence, setToolSequence] = useState("[\n  {\n    \"tool\": \"godot_create_camera\",\n    \"args\": {}\n  }\n]");
	const [buildResult, setBuildResult] = useState<string | null>(null);
	const [building, setBuilding] = useState(false);

	const [inspectPath, setInspectPath] = useState("");
	const [inspectResult, setInspectResult] = useState<string | null>(null);
	const [inspecting, setInspecting] = useState(false);

	const handleBuild = async () => {
		setBuilding(true);
		setBuildResult(null);
		try {
			let sequence;
			try {
				sequence = JSON.parse(toolSequence);
			} catch {
				setBuildResult("Error: Invalid JSON in tool sequence.");
				return;
			}
			const j = await apiFetch("/api/v1/control/tool", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					tool: "mcpb_build",
					args: { name, description, tool_sequence: sequence },
				}),
			});
			setBuildResult(JSON.stringify(j, null, 2));
		} catch (e) {
			setBuildResult(`Error: ${e}`);
		} finally {
			setBuilding(false);
		}
	};

	const handleInspect = async () => {
		setInspecting(true);
		setInspectResult(null);
		try {
			const j = await apiFetch("/api/v1/control/tool", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					tool: "mcpb_inspect",
					args: { path: inspectPath },
				}),
			});
			setInspectResult(JSON.stringify(j, null, 2));
		} catch (e) {
			setInspectResult(`Error: ${e}`);
		} finally {
			setInspecting(false);
		}
	};

	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			className="space-y-6 max-w-6xl"
		>
			<h1 className="text-2xl font-bold text-white flex items-center gap-3">
				<Archive className="text-amber-500" size={24} /> MCPB Bundles
			</h1>
			<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-4">
					<h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
						<PackagePlus size={16} className="text-amber-400" /> Create Bundle
					</h2>
					<input
						type="text"
						placeholder="Bundle name"
						value={name}
						onChange={(e) => setName(e.target.value)}
						className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/10 text-sm text-slate-200 placeholder-slate-600 outline-none"
					/>
					<input
						type="text"
						placeholder="Description"
						value={description}
						onChange={(e) => setDescription(e.target.value)}
						className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/10 text-sm text-slate-200 placeholder-slate-600 outline-none"
					/>
					<div>
						<label className="text-xs text-slate-500 block mb-1">Tool Sequence (JSON)</label>
						<textarea
							rows={8}
							value={toolSequence}
							onChange={(e) => setToolSequence(e.target.value)}
							className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/10 text-sm text-slate-200 placeholder-slate-600 outline-none font-mono"
						/>
					</div>
					<button
						type="button"
						onClick={handleBuild}
						disabled={building}
						className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-500/30 transition-all disabled:opacity-50"
					>
						{building ? <Loader2 size={14} className="animate-spin" /> : <PackagePlus size={14} />}
						Build Bundle
					</button>
					{buildResult && (
						<div className="relative">
							<button
								type="button"
								onClick={() => setBuildResult(null)}
								className="absolute top-2 right-2"
							>
								<X size={12} className="text-slate-400" />
							</button>
							<pre className="p-3 rounded-xl bg-black/40 text-xs text-slate-300 overflow-auto max-h-40 border border-white/10">
								{buildResult}
							</pre>
						</div>
					)}
				</div>
				<div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-4">
					<h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
						<Search size={16} className="text-amber-400" /> Inspect Bundle
					</h2>
					<input
						type="text"
						placeholder="Path to .mcpb file"
						value={inspectPath}
						onChange={(e) => setInspectPath(e.target.value)}
						className="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/10 text-sm text-slate-200 placeholder-slate-600 outline-none"
					/>
					<button
						type="button"
						onClick={handleInspect}
						disabled={inspecting}
						className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/20 text-amber-400 text-sm font-bold hover:bg-amber-500/30 transition-all disabled:opacity-50"
					>
						{inspecting ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
						Inspect
					</button>
					{inspectResult && (
						<div className="relative">
							<button
								type="button"
								onClick={() => setInspectResult(null)}
								className="absolute top-2 right-2"
							>
								<X size={12} className="text-slate-400" />
							</button>
							<pre className="p-3 rounded-xl bg-black/40 text-xs text-slate-300 overflow-auto max-h-60 border border-white/10">
								{inspectResult}
							</pre>
						</div>
					)}
				</div>
			</div>
		</motion.div>
	);
}
