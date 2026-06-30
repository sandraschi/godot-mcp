import { Code2, ExternalLink, Loader2 } from "lucide-react";
import { useState } from "react";

const endpoints = [
	{ method: "GET", path: "/api/v1/status", desc: "Server & Godot status" },
	{ method: "GET", path: "/api/v1/artifacts", desc: "List artifacts" },
	{ method: "POST", path: "/api/v1/artifacts", desc: "Register artifact" },
	{ method: "PUT", path: "/api/v1/settings", desc: "Update config" },
	{ method: "GET", path: "/api/v1/itch/status", desc: "Butler/itch status" },
	{ method: "POST", path: "/api/v1/control/tool", desc: "Execute Godot tool" },
];

const methodColor: Record<string, string> = {
	GET: "text-emerald-400",
	POST: "text-blue-400",
	PUT: "text-amber-400",
	DELETE: "text-red-400",
};

function SwaggerThemeInjection() {
	return (
		<script
			// biome-ignore lint/security/noDangerouslySetInnerHtml: intentional CSS injection into Swagger iframe
			dangerouslySetInnerHTML={{
				__html: `
document.querySelector('iframe')?.addEventListener('load', function() {
	try {
		var doc = this.contentDocument || this.contentWindow.document;
		var style = doc.createElement('style');
		style.textContent = \`
			:root {
				--bg: #09090b !important;
				--color: #f4f4f5 !important;
				--border-color: #27272a !important;
			}
			body { background: #09090b !important; color: #f4f4f5 !important; }
			.scheme-container { background: #18181b !important; }
			.btn { border-color: #27272a !important; }
			input { background: #18181b !important; color: #f4f4f5 !important; border-color: #27272a !important; }
			.opblock-tag { border-color: #27272a !important; }
			.opblock { border-color: #27272a !important; background: #18181b !important; }
			.opblock-summary-description { color: #a1a1aa !important; }
			table thead tr td, table thead tr th { border-color: #27272a !important; }
			.responses-inner { background: #18181b !important; }
			.response-col_description { color: #a1a1aa !important; }
			.info { color: #f4f4f5 !important; }
			.info .title { color: #f4f4f5 !important; }
			.info a { color: #f59e0b !important; }
		\`;
		doc.head.appendChild(style);
	} catch(e) {}
});
				`,
			}}
		/>
	);
}

export default function ApiDocsPage() {
	const [iframeLoading, setIframeLoading] = useState(true);
	const [view, setView] = useState<"swagger" | "redoc">("swagger");
	const apiBase = "http://127.0.0.1:10993";

	return (
		<div className="space-y-6 h-full flex flex-col">
			<SwaggerThemeInjection />
			<div className="flex items-center justify-between">
				<h1 className="text-2xl font-bold text-white flex items-center gap-3">
					<Code2 className="text-amber-400" /> API Docs
				</h1>
				<div className="flex items-center gap-2">
					<button
						type="button"
						onClick={() => setView("swagger")}
						className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
							view === "swagger"
								? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
								: "bg-white/10 text-slate-400 border border-transparent hover:text-slate-300"
						}`}
					>
						Swagger UI
					</button>
					<button
						type="button"
						onClick={() => setView("redoc")}
						className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
							view === "redoc"
								? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
								: "bg-white/10 text-slate-400 border border-transparent hover:text-slate-300"
						}`}
					>
						ReDoc
					</button>
					<a
						href={`${apiBase}/docs`}
						target="_blank"
						rel="noopener noreferrer"
						className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-amber-600/20 border border-amber-500/20 text-sm text-amber-300 hover:bg-amber-600/30 transition-all"
					>
						<ExternalLink size={14} /> Open in browser
					</a>
				</div>
			</div>

			<div className="flex gap-2 overflow-x-auto pb-1">
				{endpoints.map((ep) => (
					<div
						key={ep.path}
						className="flex items-center gap-2 shrink-0 px-3 py-1.5 rounded-lg bg-fleet-800 border border-white/10 text-xs"
					>
						<span className={`font-bold ${methodColor[ep.method] || "text-slate-400"}`}>
							{ep.method}
						</span>
						<span className="text-slate-300 font-mono text-[11px]">{ep.path}</span>
					</div>
				))}
			</div>

			<div className="flex-1 bg-fleet-900 border border-white/10 rounded-2xl overflow-hidden relative min-h-[500px]">
				{iframeLoading && (
					<div className="absolute inset-0 flex items-center justify-center bg-fleet-900 z-10">
						<div className="flex items-center gap-2 text-slate-400">
							<Loader2 size={16} className="animate-spin" />
							<span className="text-sm">Loading {view === "swagger" ? "Swagger UI" : "ReDoc"}...</span>
						</div>
					</div>
				)}
				<iframe
					key={view}
					src={view === "swagger" ? `${apiBase}/docs` : `${apiBase}/redoc`}
					className="w-full h-full border-0"
					title={view === "swagger" ? "Swagger API Docs" : "ReDoc API Docs"}
					onLoad={() => setIframeLoading(false)}
				/>
			</div>
		</div>
	);
}
