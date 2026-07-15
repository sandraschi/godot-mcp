import { motion } from "framer-motion";
import {
    FlaskConical, Play, Square, Camera, Gamepad2, MousePointer2,
    Activity, Box, Layers, FileText, ShieldCheck, BarChart3,
    Keyboard, MonitorPlay, Split,
} from "lucide-react";

const demoGroups = [
    {
        label: "Deterministic Playtesting",
        items: [
            { icon: Square, title: "Freeze Clock", desc: "Pause the game loop with Engine.time_scale=0. Bridge stays alive for commands.", code: 'await godot_game_time(action="freeze")' },
            { icon: Gamepad2, title: "Inject Input", desc: "Send analog actions, joypad axis, mouse-look, or text into the frozen game.", code: 'await godot_simulate_input(actions=[{"action": "jump", "strength": 1.0}])' },
            { icon: Play, title: "Step-Until", desc: "Advance frame-by-frame until a GDScript expression is true. No polling, no racing.", code: 'await godot_step_until(condition="get_node(\'Player\').is_on_floor()")' },
            { icon: Camera, title: "Capture Result", desc: "Screenshot the viewport at the exact frame the condition triggered.", code: "await godot_capture_viewport()" },
            { icon: MonitorPlay, title: "Full Flow", desc: "Freeze → input → step-until → read state → screenshot. Deterministic end-to-end.", code: "await godot_game_time(action=\"freeze\")\nawait godot_simulate_input(...)\nawait godot_step_until(condition=...)\nawait godot_state_digest(...)\nawait godot_capture_viewport()" },
        ],
    },
    {
        label: "Scene & Resources",
        items: [
            { icon: Box, title: "Read Node", desc: "Read any node's properties by name or path. Lightweight alternative to full tree dump.", code: 'await godot_read_node(node="Player")' },
            { icon: Layers, title: "Inspect Resource", desc: "Type-aware viewing of SpriteFrames, TileSet, Materials, and Textures as JSON.", code: 'await godot_inspect_resource(path="res://characters/player.tres")' },
            { icon: Split, title: "TileMap Cells", desc: "Read or write TileMapLayer/GridMap cells. Only way agents can edit tile data.", code: 'await godot_tilemap(operation="read", node="GroundLayer")' },
        ],
    },
    {
        label: "Animation & Keyframes",
        items: [
            { icon: FileText, title: "List Animations", desc: "Query all animations on an AnimationPlayer node.", code: 'await godot_animation(operation="list_animations", node="AnimationPlayer")' },
            { icon: Keyboard, title: "Inspect Tracks", desc: "List all tracks: type, path, interpolation mode, key count.", code: 'await godot_animation(operation="list_tracks", node="AnimationPlayer", animation="walk")' },
            { icon: MousePointer2, title: "Edit Keyframes", desc: "Insert or remove keyframes, change track interpolation.", code: 'await godot_animation(operation="insert_keyframe", node="AnimationPlayer", animation="walk", track=0, time=1.5, value=100.0)' },
        ],
    },
    {
        label: "Profiling & Validation",
        items: [
            { icon: Activity, title: "Snapshot", desc: "Read 14 Godot performance metrics: FPS, memory, render, physics, audio.", code: 'await godot_profile(operation="snapshot")' },
            { icon: BarChart3, title: "Spike Detection", desc: "Auto-sample 300 frames, detect anomalies >2 stddev from the mean.", code: 'await godot_profile(operation="history")' },
            { icon: ShieldCheck, title: "Mesh Validation", desc: "Scan all meshes for NaN vertices, degenerate triangles, zero normals.", code: "await godot_validate_meshes()" },
        ],
    },
];

export default function DemoShowcase() {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8 max-w-6xl"
        >
            <div className="flex items-center gap-3 mb-2">
                <FlaskConical className="text-amber-400" size={28} />
                <div>
                    <h1 className="text-2xl font-bold text-white">Demo Showcase</h1>
                    <p className="text-sm text-slate-400 mt-1">
                        End-to-end tool demonstrations. Start the bridge then try these sequences.
                    </p>
                </div>
            </div>

            {demoGroups.map((group) => (
                <section key={group.label}>
                    <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
                        {group.label}
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {group.items.map((item) => (
                            <div
                                key={item.title}
                                className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-3 hover:border-amber-500/30 transition-all"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-lg bg-amber-500/10">
                                        <item.icon className="text-amber-400" size={18} />
                                    </div>
                                    <h3 className="text-sm font-bold text-white">{item.title}</h3>
                                </div>
                                <p className="text-xs text-slate-400 leading-relaxed">{item.desc}</p>
                                <pre className="text-xs bg-black/30 text-amber-300/90 px-3 py-2 rounded-xl overflow-x-auto font-mono leading-relaxed">
                                    {item.code}
                                </pre>
                            </div>
                        ))}
                    </div>
                </section>
            ))}

            <div className="bg-[#1e1e26] border border-white/10 rounded-2xl p-5 space-y-3">
                <h2 className="text-sm font-bold text-white">Quick Start Checklist</h2>
                <ol className="text-xs text-slate-400 space-y-1.5 list-decimal list-inside">
                    <li>Start the server: <code className="text-amber-300">just serve</code></li>
                    <li>Launch Godot bridge: <code className="text-amber-300">just godot-bridge</code></li>
                    <li>Verify connection: <code className="text-amber-300">just bridge-status</code></li>
                    <li>Run a demo: <code className="text-amber-300">uv run python demos/playtesting.py</code></li>
                    <li>Or use individual tools from the <code className="text-amber-300">/tools</code> page</li>
                </ol>
            </div>
        </motion.div>
    );
}
