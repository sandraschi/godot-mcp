import { Bot, Download, Eraser, Send, User } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

const HISTORY_KEY = "godot-mcp-chat-history";
const PERSONALITY_KEY = "godot-mcp-chat-personality";
const MAX_HISTORY = 100;

const PERSONALITIES: Record<string, string> = {
	"Research Assistant": "You are a research assistant specializing in Godot 4 game engine and MCP tooling. Answer concisely with relevant technical details.",
	"Expert Reviewer": "You are a senior Godot developer reviewing game builds and pipelines. Be critical and thorough.",
	"Quick Summarizer": "Keep responses to 2-3 sentences. Focus on key facts.",
	"Custom": "Custom prompt — editable below.",
};

interface Message {
	role: "user" | "assistant";
	content: string;
	ts?: string;
}

function loadHistory(): Message[] {
	try { const raw = localStorage.getItem(HISTORY_KEY); return raw ? JSON.parse(raw) : []; } catch { return []; }
}

function buildSystemPrompt(personalityId: string, customPrompt: string): string {
	const skill = "You are an assistant for Godot MCP — a server with 49 tools for Godot 4 engine control, asset import, game building, itch.io shipping, Steam publishing, and fleet coordination.";
	const role = PERSONALITIES[personalityId] || PERSONALITIES["Research Assistant"];
	if (personalityId === "Custom") return customPrompt || skill;
	return `${skill}\n\n---\n\n## Role\n${role}`;
}

export default function ChatPage() {
	const [chat, setChat] = useState<Message[]>(() => loadHistory());
	const [input, setInput] = useState("");
	const [loading, setLoading] = useState(false);
	const [personality, setPersonality] = useState(() => localStorage.getItem(PERSONALITY_KEY) || "Research Assistant");
	const [customPrompt, setCustomPrompt] = useState("");
	const bottomRef = useRef<HTMLDivElement>(null);

	useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chat]);

	const sendMessage = useCallback(async (prompt: string) => {
		const userMsg: Message = { role: "user", content: prompt, ts: new Date().toISOString() };
		setChat((prev) => { const next = [...prev, userMsg]; localStorage.setItem(HISTORY_KEY, JSON.stringify(next.slice(-MAX_HISTORY))); return next; });
		setLoading(true);
		try {
			const r = await fetch("/api/llm/chat", {
				method: "POST", headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ prompt, system: buildSystemPrompt(personality, customPrompt) }),
			});
			const data = await r.json();
			const reply = data.response || data.error || "No response";
			const assistantMsg: Message = { role: "assistant", content: reply, ts: new Date().toISOString() };
			setChat((prev) => { const next = [...prev, assistantMsg]; localStorage.setItem(HISTORY_KEY, JSON.stringify(next.slice(-MAX_HISTORY))); return next; });
		} catch (e) {
			const errMsg: Message = { role: "assistant", content: String(e), ts: new Date().toISOString() };
			setChat((prev) => { const next = [...prev, errMsg]; localStorage.setItem(HISTORY_KEY, JSON.stringify(next.slice(-MAX_HISTORY))); return next; });
		}
		setLoading(false);
	}, [personality, customPrompt]);

	const handleSend = () => { if (!input.trim()) return; sendMessage(input.trim()); setInput(""); };

	const handleClear = () => { setChat([]); localStorage.removeItem(HISTORY_KEY); };

	const handleExport = () => {
		if (chat.length === 0) return;
		const lines = chat.map((m) => `[${m.ts || "no-ts"}] ${m.role}: ${m.content}`);
		const blob = new Blob([lines.join("\n")], { type: "text/plain" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a"); a.href = url; a.download = `godot-mcp-chat-${new Date().toISOString().slice(0, 10)}.txt`; a.click();
		URL.revokeObjectURL(url);
	};

	return (
		<div data-testid="chat-page" className="flex flex-col h-full max-w-4xl mx-auto">
			<div className="flex items-center justify-between mb-4" data-testid="chat-controls">
				<h1 className="text-2xl font-bold text-white flex items-center gap-3">
					<Bot className="text-blue-400" /> Chat
				</h1>
				<div className="flex items-center gap-3">
					<select
						data-testid="personality-select"
						className="bg-zinc-800 text-zinc-100 border border-zinc-600 rounded-lg px-3 py-1.5 text-sm"
						value={personality}
						onChange={(e) => { setPersonality(e.target.value); localStorage.setItem(PERSONALITY_KEY, e.target.value); }}
					>
						{Object.keys(PERSONALITIES).map((p) => <option key={p} value={p}>{p}</option>)}
					</select>
					<button data-testid="chat-export" onClick={handleExport} disabled={chat.length === 0} className="bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 text-zinc-300 text-xs px-3 py-1.5 rounded-lg border border-zinc-600 flex items-center gap-1"><Download size={12} /> Export</button>
					<button data-testid="chat-clear" onClick={handleClear} disabled={chat.length === 0} className="bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 text-zinc-300 text-xs px-3 py-1.5 rounded-lg border border-zinc-600 flex items-center gap-1"><Eraser size={12} /> Clear</button>
				</div>
			</div>

			{personality === "Custom" && (
				<textarea className="w-full bg-zinc-800 border border-zinc-600 rounded-lg px-3 py-2 text-sm mb-4" rows={2} placeholder="Enter your custom system prompt..." value={customPrompt} onChange={(e) => setCustomPrompt(e.target.value)} />
			)}

			<div data-testid="chat-messages" className="flex-1 overflow-y-auto space-y-3 pr-2 mb-4">
				{chat.length === 0 && (
					<div className="text-zinc-500 text-sm text-center pt-12">Ask a question about Godot MCP tools, pipeline, or fleet.</div>
				)}
				{chat.map((m, i) => (
					<div key={`${m.role}-${i}`} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
						<div className={`flex gap-3 max-w-[80%] ${m.role === "user" ? "flex-row-reverse" : ""}`}>
							<div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${m.role === "user" ? "bg-blue-600 text-white" : "bg-indigo-600 text-white"}`}>
								{m.role === "user" ? <User size={14} /> : <Bot size={14} />}
							</div>
							<div className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${m.role === "user" ? "bg-blue-600/20 text-slate-200" : "bg-[#1e1e26] border border-white/10 text-slate-300"}`}>
								{m.content}
							</div>
						</div>
					</div>
				))}
				{loading && <div className="text-zinc-500 text-sm animate-pulse pl-11">Thinking...</div>}
				<div ref={bottomRef} />
			</div>

			<div className="flex items-center gap-2 bg-[#1e1e26] border border-white/10 rounded-2xl px-4 py-3">
				<input
					data-testid="chat-input"
					type="text"
					value={input}
					onChange={(e) => setInput(e.target.value)}
					onKeyDown={(e) => { if (e.key === "Enter") handleSend(); }}
					placeholder="Ask about Godot MCP tools, pipeline, or fleet..."
					className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-600 outline-none"
				/>
				<button
					data-testid="chat-send"
					type="button"
					onClick={handleSend}
					disabled={loading || !input.trim()}
					className="w-9 h-9 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-700 flex items-center justify-center text-white transition-all"
				>
					<Send size={14} />
				</button>
			</div>
		</div>
	);
}
