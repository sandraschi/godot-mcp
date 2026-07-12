import { Bot, Download, Eraser, Send, User } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../lib/api";

const HISTORY_KEY = "godot-mcp-chat-history";
const PERSONALITY_KEY = "godot-mcp-chat-personality";
const MAX_HISTORY = 100;

interface Message { role: "user" | "assistant"; content: string; ts?: string }

const PERSONALITIES: Record<string, string> = {
	"Research Assistant": "You are a research assistant specializing in Godot 4 game engine and MCP tooling. Answer concisely with relevant technical details.",
	"Expert Reviewer": "You are a senior Godot developer reviewing game builds and pipelines. Be critical and thorough.",
	"Quick Summarizer": "Keep responses to 2-3 sentences. Focus on key facts.",
	"Custom": "Custom prompt — editable below.",
};

const EXAMPLE_PROMPTS = [
	{ group: "Engine", prompts: [
		"How do I create a 2D platformer character?",
		"Show me how to use signals for event handling",
		"What's the best way to manage scenes?",
	]},
	{ group: "Pipeline", prompts: [
		"Build and export the current project",
		"Set up an itch.io deployment",
		"Check the Godot bridge status",
	]},
	{ group: "Fleet", prompts: [
		"List all registered workflows",
		"Show me the asset import pipeline",
		"Generate a Steam publishing plan",
	]},
];

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
	const [streaming, setStreaming] = useState(false);
	const [personality, setPersonality] = useState(() => localStorage.getItem(PERSONALITY_KEY) || "Research Assistant");
	const [customPrompt, setCustomPrompt] = useState("");
	const [skillName, setSkillName] = useState<string | null>(null);
	const [providerOk, setProviderOk] = useState(true);
	const bottomRef = useRef<HTMLDivElement>(null);

	useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chat]);

	// Skill fetch on mount
	useEffect(() => {
		(async () => {
			try {
				const data = await apiFetch<any>("/api/v1/skills");
				const skills = data?.skills ?? [];
				if (skills.length > 0) setSkillName(skills[0].name || skills[0]);
			} catch { /* no skills */ }
		})();
	}, []);

	// Provider detection
	useEffect(() => {
		(async () => {
			try {
				const r = await fetch("http://localhost:11434/api/tags", { signal: AbortSignal.timeout(3000) });
				setProviderOk(r.ok);
			} catch { /* stays optimistic */ }
		})();
	}, []);

	const sendMessage = useCallback(async (text: string) => {
		if (!text.trim() || streaming) return;
		const userMsg: Message = { role: "user", content: text.trim(), ts: new Date().toISOString() };
		const updated = [...chat, userMsg].slice(-MAX_HISTORY);
		setChat(updated);
		setStreaming(true);

		const system = buildSystemPrompt(personality, customPrompt);
		const body = {
			provider: "ollama",
			model: "llama3.2",
			messages: chat.slice(-20).map((m) => ({ role: m.role, content: m.content })),
			prompt: text.trim(),
			system,
		};

		try {
			const r = await fetch("/api/llm/chat/stream", {
				method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
			});
			if (!r.ok || !r.body) throw new Error(`HTTP ${r.status}`);

			const partial: Message = { role: "assistant", content: "", ts: new Date().toISOString() };
			setChat((prev) => [...prev, partial]);

			const reader = r.body.getReader();
			const decoder = new TextDecoder();
			let buffer = "";
			while (true) {
				const { done, value } = await reader.read();
				if (done) break;
				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split("\n");
				buffer = lines.pop() || "";
				for (const line of lines) {
					if (!line.startsWith("data: ")) continue;
					const data = line.slice(6).trim();
					if (data === "[DONE]") break;
					try {
						const parsed = JSON.parse(data);
						if (parsed.c) {
							partial.content += parsed.c;
							setChat((prev) => { const c = [...prev]; c[c.length - 1] = { ...partial }; return c; });
						}
						if (parsed.error) throw new Error(parsed.error);
					} catch { /* skip */ }
				}
			}
			const final = [...chat, userMsg, { ...partial }].slice(-MAX_HISTORY);
			setChat(final);
			localStorage.setItem(HISTORY_KEY, JSON.stringify(final));
		} catch (e) {
			const msg = e instanceof Error ? e.message : String(e);
			const errMsg: Message = { role: "assistant", content: `Error: ${msg}`, ts: new Date().toISOString() };
			const final = [...updated, errMsg].slice(-MAX_HISTORY);
			setChat(final);
			localStorage.setItem(HISTORY_KEY, JSON.stringify(final));
		}
		setStreaming(false);
	}, [input, chat, streaming, personality, customPrompt]);

	const handleSend = () => { if (!input.trim()) return; sendMessage(input.trim()); setInput(""); };

	const handleClear = () => { setChat([]); localStorage.removeItem(HISTORY_KEY); };

	const handleExport = () => {
		if (chat.length === 0) return;
		const lines = chat.map((m) => `[${m.ts || "no-ts"}] ${m.role === "user" ? "You" : "AI"}: ${m.content}`);
		const blob = new Blob([lines.join("\n\n---\n\n")], { type: "text/plain" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a"); a.href = url; a.download = `godot-mcp-chat-${new Date().toISOString().slice(0, 10)}.txt`; a.click();
		URL.revokeObjectURL(url);
	};

	return (
		<div data-testid="chat-page" className="flex flex-col h-full max-w-4xl mx-auto">
			<div className="flex items-center justify-between mb-4" data-testid="chat-controls">
				<h1 className="text-2xl font-bold text-white flex items-center gap-3">
					<Bot className="text-blue-400" /> Chat
					{skillName && <span className="text-[10px] text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded font-mono">skill:{skillName}</span>}
				</h1>
				<div className="flex items-center gap-3">
					<div className="flex items-center gap-1.5 text-xs text-zinc-500">
						<div className={`w-1.5 h-1.5 rounded-full ${providerOk ? "bg-green-500" : "bg-red-500"}`} />
						<span>{providerOk ? "Ollama" : "offline"}</span>
					</div>
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
					<div className="text-zinc-500 text-sm text-center pt-8">
						<Bot className="w-12 h-12 mx-auto mb-3 opacity-20" />
						<p>Ask a question about Godot MCP tools, pipeline, or fleet.</p>
						<p className="text-xs text-zinc-600 mt-1">Personality: {personality}{skillName && ` | skill: ${skillName}`}</p>
						<div data-testid="example-prompts" className="mt-6 max-w-lg mx-auto space-y-3">
							{EXAMPLE_PROMPTS.map((group) => (
								<div key={group.group}>
									<p className="text-[10px] uppercase tracking-wider text-zinc-600 text-left mb-1.5 px-1">{group.group}</p>
									<div className="flex flex-wrap gap-1.5 justify-center">
										{group.prompts.map((p) => (
											<button key={p} onClick={() => setInput(p)}
												className="text-xs px-2.5 py-1.5 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-zinc-200 transition-colors text-left">
												{p}
											</button>
										))}
									</div>
								</div>
							))}
						</div>
					</div>
				)}
				{chat.map((m, i) => (
					<div key={`${m.role}-${i}`} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
						<div className={`flex gap-3 max-w-[80%] ${m.role === "user" ? "flex-row-reverse" : ""}`}>
							<div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${m.role === "user" ? "bg-blue-600 text-white" : "bg-indigo-600 text-white"}`}>
								{m.role === "user" ? <User size={14} /> : <Bot size={14} />}
							</div>
							<div className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${m.role === "user" ? "bg-blue-600/20 text-slate-200" : "bg-[#1e1e26] border border-white/10 text-slate-300"}`}>
								{m.content || (i === chat.length - 1 && streaming ? <span className="animate-pulse">...</span> : "")}
							</div>
						</div>
					</div>
				))}
				{streaming && chat.length > 0 && chat[chat.length - 1].content && (
					<div className="text-zinc-500 text-xs animate-pulse pl-11">Generating...</div>
				)}
				<div ref={bottomRef} />
			</div>

			<div className="flex items-center gap-2 bg-[#1e1e26] border border-white/10 rounded-2xl px-4 py-3">
				<input
					data-testid="chat-input"
					type="text"
					value={input}
					onChange={(e) => setInput(e.target.value)}
					onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
					placeholder="Ask about Godot MCP tools, pipeline, or fleet..."
					disabled={streaming}
					className="flex-1 bg-transparent text-sm text-slate-200 placeholder-slate-600 outline-none disabled:opacity-50"
				/>
				<button
					data-testid="chat-send"
					type="button"
					onClick={handleSend}
					disabled={streaming || !input.trim()}
					className="w-9 h-9 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-700 flex items-center justify-center text-white transition-all"
				>
					<Send size={14} />
				</button>
			</div>
		</div>
	);
}
