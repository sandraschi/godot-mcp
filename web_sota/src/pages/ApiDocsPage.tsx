import { Code2, ExternalLink, Loader2 } from "lucide-react";
import { useState } from "react";

export default function ApiDocsPage() {
	const [iframeLoading, setIframeLoading] = useState(true);

	return (
		<div className="space-y-6 h-full flex flex-col">
			<div className="flex items-center justify-between">
				<h1 className="text-2xl font-bold text-white flex items-center gap-3">
					<Code2 className="text-amber-400" /> API Docs
				</h1>
				<a
					href="http://localhost:10993/docs"
					target="_blank"
					rel="noopener noreferrer"
					className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-amber-600/20 border border-amber-500/20 text-sm text-amber-300 hover:bg-amber-600/30 transition-all"
				>
					<ExternalLink size={14} /> Open in browser
				</a>
			</div>
			<div className="flex-1 bg-[#1e1e26] border border-white/10 rounded-2xl overflow-hidden relative min-h-[500px]">
				{iframeLoading && (
					<div className="absolute inset-0 flex items-center justify-center bg-[#1e1e26] z-10">
						<div className="flex items-center gap-2 text-slate-400">
							<Loader2 size={16} className="animate-spin" />
							<span className="text-sm">Loading Swagger UI...</span>
						</div>
					</div>
				)}
				<iframe
					src="/docs"
					className="w-full h-full border-0"
					title="Swagger API Docs"
					onLoad={() => setIframeLoading(false)}
				/>
			</div>
		</div>
	);
}
