import { Bot, Send, User } from "lucide-react";
import { useState } from "react";

interface Message {
	role: "user" | "assistant";
	content: string;
}

export default function ChatPage() {
	const [messages, setMessages] = useState<Message[]>([
		{ role: "assistant", content: "Hello! I'm the Godot MCP assistant. Ask me about engine control, particle systems, STL import, or fleet pipelines." },
	]);
	const [input, setInput] = useState("");

	const send = () => {
		if (!input.trim()) return;
		setMessages((prev) => [...prev, { role: "user", content: input.trim() }]);
		setInput("");
	};

	return (
		<div className="flex flex-col h-full max-w-4xl mx-auto">
			<h1 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
				<Bot className="text-blue-400" /> Chat
			</h1>
			<div className="flex-1 overflow-y-auto space-y-3 pr-2 mb-4">
				{messages.map((m, i) => (
					<div key={`${m.role}-${i}`} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
						<div
							className={`flex gap-3 max-w-[80%] ${
								m.role === "user" ? "flex-row-reverse" : ""
							}`}
						>
							<div
								className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
									m.role === "user"
										? "bg-blue-600 text-white"
										: "bg-indigo-600 text-white"
								}`}
							>
								{m.role === "user" ? <User size={14} /> : <Bot size={14} />}
							</div>
							<div
								className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
									m.role === "user"
										? "bg-blue-600/20 text-slate-200"
										: "bg-[#1e1e26] border border-white/10 text-slate-300"
								}`}
							>
								{m.content}
							</div>
						</div>
					</div>
				))}
			</div>
			<div className="flex items-center gap-2 bg-[#1e1e26] border border-white/10 rounded-2xl px-4 py-3">
				<input
					type="text"
					value={input}
					onChange={(e) => setInput(e.target.value)}
					onKeyDown={(e) => { if (e.key === "Enter") send(); }}
					placeholder="Ask about Godot MCP tools, pipeline, or fleet..."
					className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-600 outline-none"
				/>
				<button
					type="button"
					onClick={send}
					className="w-9 h-9 rounded-xl bg-blue-600 hover:bg-blue-500 flex items-center justify-center text-white transition-all"
				>
					<Send size={14} />
				</button>
			</div>
		</div>
	);
}
