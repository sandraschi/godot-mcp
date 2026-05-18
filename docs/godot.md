# Godot Engine — Complete Reference

## What Is Godot Engine?

Godot is a free, open-source, cross-platform game engine released under the MIT license. Unlike Unity (per-seat licensing) or Unreal (5% royalty on gross revenue), Godot imposes no fees, no royalties, and no restrictions. You own everything you make.

- **Download size**: ~40 MB (yes, megabytes — not gigabytes)
- **License**: MIT (fully permissive, no copyleft)
- **Platforms**: Windows, macOS, Linux, Android, iOS, Web (HTML5/WASM), and consoles (via W4 Games)
- **Website**: https://godotengine.org

## Current State (May 2026)

### Godot 4.6.2 (Stable)

Released January 2026. Major features:

- **Jolt Physics** is now the **default** physics engine (replacing GodotPhysics)
- **Direct3D 12** rendering backend is now the **default on Windows** (faster than Vulkan on many Windows GPUs)
- Improved C# integration with .NET 8 support
- Editor performance improvements (faster script reloads, better large-scene handling)
- Metal rendering backend for macOS (native Apple Silicon support)
- Android OpenGL ES 3.0 renderer improvements

### Godot 4.7 (Beta)

In development as of May 2026. Planned features:

- **HDR display support** (HDR10, scRGB)
- Ray tracing groundwork (BVH infrastructure, not full RT pipeline yet)
- Vulkan pipeline cache improvements
- Multi-window editor support
- Audio mixing improvements

## Version History

| Version | Release | Key Features |
|---------|---------|-------------|
| **1.0** | Dec 2014 | Initial open-source release. 2D engine, GDScript, basic 3D |
| **2.0** | Feb 2016 | Improved UI, Web export (Emscripten), 2D skeletal animation |
| **2.1** | Jul 2016 | Asset library, plugin system, PBR materials |
| **3.0** | Jan 2018 | PBR renderer, OpenGL ES 3.0, new audio engine, Bullet physics |
| **3.1** | Mar 2019 | OpenGL ES 2.0 fallback, VR support, static typing in GDScript |
| **3.2** | Jan 2020 | WebXR, RTX support, pseudo-3D, improved Web export |
| **3.3** | Apr 2021 | Web editor, improved import pipeline |
| **3.4** | Nov 2021 | Last 3.x release. Stability and bugfixes |
| **3.5** | Aug 2022 | Backported features, async shader compilation |
| **4.0** | Mar 2023 | **Vulkan renderer**, new GDScript 2.0, SDFGI, volumetric fog |
| **4.1** | Jul 2023 | FSR 2.2, better particles, editor UX polish |
| **4.2** | Nov 2023 | AMD FSR 2.2, lightmapper improvements, Jolt Physics integration |
| **4.3** | Aug 2024 | Skeletal animation retargeting, Wayland support, improved C# |
| **4.4** | Mar 2025 | Jolt Physics (opt-in), improved rendering, Meta Quest 3 support |
| **4.5** | Sep 2025 | Jolt Physics improvements, Direct3D 12 on Windows, metal improvements |
| **4.6** | Jan 2026 | **Jolt Physics default**, **Direct3D 12 default on Windows** |
| **4.6.2** | Apr 2026 | Current stable. Bugfixes, .NET 8 improvements |

### The Unity Exodus (Sep 2023)

In September 2023, Unity announced a controversial "Runtime Fee" charging developers per game install. This triggered a mass migration to Godot, with thousands of developers switching engines. The Godot Foundation received over €1 million in donations in the weeks following, and the community grew substantially. This event accelerated Godot 4 adoption and cemented its position as the leading open-source game engine.

## Architecture

### Node/Scene System

Godot's architecture is built around **nodes** organized in **scenes**. This is fundamentally different from Unity's GameObject/Component model.

**Key concepts**:

- **Node**: The fundamental building block. Everything is a node — sprites, 3D models, lights, cameras, timers.
- **Scene**: A saved collection of nodes. Scenes can be instantiated as children of other scenes.
- **Scene Tree**: The runtime hierarchy of all active nodes. The root is a `Viewport`.

**Inheritance hierarchy** (simplified):

```
Object
└── Node
    ├── CanvasItem (2D)
    │   ├── Node2D
    │   │   ├── Sprite2D
    │   │   ├── TileMap
    │   │   └── ...
    │   └── Control (UI)
    │       ├── Button
    │       ├── Label
    │       └── ...
    └── Node3D (3D)
        ├── MeshInstance3D
        ├── Camera3D
        ├── Light3D
        │   ├── DirectionalLight3D
        │   ├── OmniLight3D
        │   └── SpotLight3D
        ├── GPUParticles3D
        └── ...
```

### Signals

Godot's observer pattern. Nodes emit signals that other nodes can connect to:

```gdscript
button.pressed.connect(_on_button_pressed)

func _on_button_pressed():
    print("Button clicked!")
```

Signals are the recommended way to decouple game logic — they replace Unity's `SendMessage` and Unreal's event dispatchers.

### Groups

Nodes can be assigned to groups for mass operations:

```gdscript
get_tree().call_group("enemies", "take_damage", 10)
```

## Rendering

Godot 4 supports four rendering backends:

| Backend | Platform | Default Since | Notes |
|---------|----------|---------------|-------|
| **Vulkan** | Windows, Linux | 4.0 | Original 4.0 backend. Most stable on Linux. |
| **Direct3D 12** | Windows | 4.6 | Better performance on Windows GPUs. |
| **Metal** | macOS, iOS | 4.4 | Native Apple Silicon support. |
| **OpenGL ES 3.0** | Android, Web | 4.0 | Compatibility backend for older devices. |

### Rendering Features (Godot 4.x)

- **Physically Based Rendering (PBR)**: StandardMaterial3D with metallic-roughness workflow
- **Signed Distance Field Global Illumination (SDFGI)**: Real-time GI without lightmap baking
- **Volumetric Fog**: Atmosphere and height-based fog
- **Screen-Space Reflections (SSR)**: Real-time reflections on specular surfaces
- **Cascaded Shadow Maps**: Directional light shadows up to 4 cascades
- **GPU Particles**: GPUParticles3D/GPUParticles2D — compute millions of particles
- **Post-Processing**: Tonemapping (ACES, Filmic, Linear), color correction, glow/bloom
- **Temporal Anti-Aliasing (TAA)**: Built-in temporal anti-aliasing
- **FSR 2.2**: AMD FidelityFX Super Resolution upscaling (since 4.1)
- **Decals**: Projected decal system for surface detail

## Physics

### Jolt Physics (Default since 4.6)

Godot switched from GodotPhysics to **Jolt Physics** as the default physics engine in version 4.6. Jolt is the same physics engine used by Horizon Forbidden West and was developed by Jorrit Rouwe (ex-Sony Guerrilla Games).

**Benefits over GodotPhysics**:
- Better performance on multi-threaded CPUs
- More stable stacking behavior
- Continuous collision detection (CCD) improvements
- Industry-proven in AAA games
- Active maintenance and community

**Configuration**: Set in Project Settings > Physics > 3D > Physics Engine

### GodotPhysics (Built-in, Legacy)

Still available as an option but no longer the default. Suitable for simple 2D games or when Jolt compatibility is not needed.

### Physics Features

- RigidBody3D/RigidBody2D — full physics simulation
- CharacterBody3D/CharacterBody2D — player movement without full simulation
- StaticBody3D/StaticBody2D — immovable colliders
- Area3D/Area2D — trigger zones (no physics response)
- Joint system — hinges, sliders, springs
- SoftBody3D — deformable objects (cloth, jelly)
- Raycasting and shape queries

## Scripting Languages

### GDScript (Primary)

GDScript is Godot's built-in scripting language. It's designed specifically for the Godot engine with tight engine integration.

**Characteristics**:
- **Python-like syntax** — uses indentation for blocks, similar keyword set
- **Statically typed** — optional type hints that improve performance
- **40%+ faster than dynamic GDScript** when using full static typing (Godot 4.x)
- **Engine-native** — no external runtime, no marshalling overhead
- **LLM-friendly** — syntax is close enough to Python that LLMs write it fluently

#### GDScript Syntax Primer

**Variables**:
```gdscript
var health: int = 100                # Typed
var name: String = "Player"          # Typed
var position = Vector3(0, 0, 0)      # Inferred type
const MAX_SPEED := 500.0             # Compile-time constant
@export var damage: float = 10.0     # Exposed to editor/inspector
@onready var sprite = $Sprite2D      # Initialized when node enters tree
```

**Functions**:
```gdscript
func take_damage(amount: int) -> void:
    health -= amount
    if health <= 0:
        die()

func calculate_damage(base: float, multiplier: float) -> float:
    return base * multiplier

# Static function
static func spawn_enemy(type: String) -> Node:
    ...
```

**Classes**:
```gdscript
class_name Enemy
extends CharacterBody3D

var patrol_points: Array[Vector3] = []

func _physics_process(delta: float) -> void:
    move_and_slide()
```

**Signals**:
```gdscript
signal health_changed(new_health: int)

func take_damage(amount: int):
    health -= amount
    health_changed.emit(health)
```

**Coroutines (await)**:
```gdscript
func attack_sequence():
    await get_tree().create_timer(0.5).timeout
    swing_sword()
    await get_tree().create_timer(0.3).timeout
    recover()
```

**Built-in callbacks**:
```gdscript
func _ready():               # Called when node enters scene tree
func _process(delta):        # Called every frame
func _physics_process(delta): # Called at fixed physics rate (60Hz default)
func _input(event):           # Called on input events
func _unhandled_input(event): # Called if input wasn't consumed
```

### C# (.NET)

Full C# support via .NET (formerly Mono). Since Godot 4, .NET 6+ is required.

**When to use C# over GDScript**:
- You need raw computation performance (physics simulations, procedural generation)
- Your team already knows C#
- You want to reuse existing .NET libraries
- You're writing complex algorithmic code

**Trade-offs**:
- Larger build size (.NET runtime bundled)
- Slower iteration (compile step required)
- Less idiomatic Godot API (C# bindings generated from GDScript API)
- Can't be used for web exports (WASM support is limited)

### C++ (GDExtension)

GDExtension is Godot's native extension API (replacing GDNative from 3.x).

**When to use C++**:
- Maximum performance (physics engines, AI, rendering)
- Integration with native libraries
- Shipping proprietary code as compiled binary

**Trade-offs**:
- Complex build setup
- Platform-specific compilation required
- API changes may require recompilation

### GDScript vs C# vs C++ Decision Guide

| Criteria | GDScript | C# | C++ (GDExtension) |
|----------|----------|----|--------------------|
| **Learning curve** | Low (Python-like) | Medium | High |
| **Performance** | Good (typed) | Better | Best |
| **Iteration speed** | Instant (no compile) | Fast | Slow (recompile) |
| **Web export** | Yes | Limited | No |
| **Godot integration** | Native | Generated bindings | Manual |
| **LLM compatibility** | Best | Good | Poor |
| **Use case** | Gameplay, UI, quick proto | Logic-heavy, .NET reuse | Engine extensions |

## 2D Engine

Godot's 2D engine is considered **best-in-class** among general-purpose game engines. It's a dedicated 2D system, not a 3D engine with 2D overlay (unlike Unity).

**Key features**:
- **Dedicated coordinate system**: Origin at top-left (pixel coordinates) or center (normalized)
- **TileMap node**: Tile-based level editing with terrains, patterns, and navigation
- **ParallaxBackground**: Multi-layer parallax scrolling
- **2D Lighting**: PointLight2D, DirectionalLight2D with normal maps
- **2D Particles**: GPUParticles2D with dedicated particle materials
- **2D Skeletal Animation**: Skeleton2D + Bone2D with inverse kinematics
- **Pixel snap**: Perfect pixel rendering for retro games
- **CanvasLayer**: Separate draw layers (HUD, menus) unaffected by world camera

## 3D Engine

Godot 4.0 brought the 3D engine to competitive level with modern engines.

**Key features**:
- **PBR Materials**: StandardMaterial3D with metallic/roughness workflow, subsurface scattering, anisotropy
- **SDFGI**: Real-time global illumination without pre-baking
- **Real-time Shadows**: Cascaded shadow maps (directional), omni shadows (point), PSSM
- **GPU Particles**: GPUParticles3D with emission shapes (box, sphere, cylinder), turbulence, sub-emitters
- **Volumetric Fog**: Height fog, density-based volume
- **Reflection Probes**: Cube map and screen-space reflections
- **Decals**: Projected decals for surface detail (cracks, stains, bullet holes)
- **Lightmapper**: GPU-accelerated baked lightmaps (alternative to SDFGI for static scenes)
- **LOD system**: Automatic and manual LOD for mesh optimization
- **Occlusion Culling**: Portal-based and automatic geometry occlusion

## XR Support

Godot has first-class XR support:

- **OpenXR**: Standard API for VR/AR headsets (Meta Quest, HTC Vive, Valve Index, Pico)
- **WebXR**: Web-based VR/AR experiences via HTML5 export
- **Meta Quest Native**: Dedicated Meta Quest support since 4.4 (Android build + OpenXR)
- **XR Tools**: ARVRController, ARVRCamera, hand tracking
- **Passthrough**: AR passthrough on Quest devices

Godot is the most accessible engine for XR development — free, lightweight, and actively maintained for XR workflows.

## Animation

### AnimationPlayer

The central animation node. Keyframes any property on any node in the scene.

```gdscript
var anim_player = $AnimationPlayer
anim_player.play("walk")
anim_player.speed_scale = 2.0
```

### AnimationTree

Advanced animation blending and state machines.

- **Blend Trees**: Blend between animations based on parameters
- **State Machine**: Transition between states with conditions
- **BlendSpace1D/2D**: Blend based on 1D or 2D input (e.g., movement direction)
- **Root Motion**: Extract movement from animation data

### Skeletal Animation

- Import from Blender, Maya, 3ds Max (GLTF 2.0 format)
- **Animation Retargeting** (since 4.3): Reuse animations across different skeletons
- **IK**: Full-body IK and procedural animation
- **Bone Attachment**: Attach objects to bones (weapons, hats, etc.)

## UI System

Godot has a full-featured UI system built on Control nodes.

**Key Control nodes**:
- **Container nodes**: VBoxContainer, HBoxContainer, GridContainer — automatic layout
- **Button, CheckBox, ColorPicker**: Standard form controls
- **RichTextLabel**: BBCode-formatted text with hyperlinks, images
- **GraphEdit/GraphNode**: Node graph editor (used to build Godot's own visual shader editor)
- **Popup/PopupMenu**: Modal dialogs and context menus

**Themes**: Create and apply themes to style all controls consistently. Themes are resources that define default styles.

**Anchors and Margins**: Responsive layout system. Controls anchor to parent edges and resize automatically.

**UI Input**: Controls handle their own input events, with focus management and keyboard navigation.

## Export Targets

| Platform | Format | Notes |
|----------|--------|-------|
| **Windows** | .exe | x86_64, with or without console |
| **macOS** | .app bundle | Universal binary (Intel + Apple Silicon) |
| **Linux** | x86_64 binary | AppImage or raw binary |
| **Android** | .apk / .aab | ARM64, optional 32-bit arm |
| **iOS** | .ipa | Requires Xcode and Apple Developer account |
| **Web** | HTML5 + WASM | Runs in any browser. ~15 MB for minimal project. |
| **Consoles** | Native | Via W4 Games porting services (Switch, PS5, Xbox) |

### Web Export Specifics

- Uses Emscripten to compile to WebAssembly
- OpenGL ES 3.0 renderer (not Vulkan on web)
- Files served via HTTP (no file:// access)
- Minimal project ~15 MB compressed
- SharedArrayBuffer required for threading (COOP/COEP headers)
- Good for puzzles, casual games, visualization tools
- Not suitable for AAA 3D due to WebGL limits

## Notable Games Made with Godot

### Commercial Successes

| Game | Developer | Release | Notes |
|------|-----------|---------|-------|
| **Cassette Beasts** | Bytten Studio | 2023 | Open-world monster-collecting RPG. 95% positive on Steam. |
| **Brotato** | Blobfish | 2023 | Vampire Survivors-like. 3+ million copies sold. |
| **Buckshot Roulette** | Mike Klubnika | 2024 | Horror tabletop game. Viral hit. |
| **Dome Keeper** | Bippinbits | 2022 | Mining roguelike. 500,000+ copies sold. |
| **Halls of Torment** | Chasing Carrots | 2024 | Diablo-inspired survival game. |
| **Endoparasitic** | Narayana Walters | 2022 | Body horror survival. |
| **Battlefield 6 Portal** | EA/DICE | 2021 | Portal mode UI built with Godot (embedded within Frostbite) |

### Notable Projects

- **Sonic Colors: Ultimate** (menu system)
- **Tesla in-car display** (UI prototypes)
- **Various Netflix interactive specials**

## Godot Foundation and Community

### Foundation

The Godot Foundation is a non-profit organization (based in the Netherlands) that:
- Manages Godot's development and infrastructure
- Accepts tax-deductible donations
- Employs core developers (Juan Linietsky, Rémi Verschelde, and others)
- Runs the Godot Asset Library
- Organizes GodotCon and other community events

**Funding**: Community donations via Open Collective, GitHub Sponsors, and direct donations. Major sponsors include Google, Meta, Microsoft, and Re-Logic (Terraria).

### Community Size (2026)
- 1,800+ contributors on GitHub
- 200,000+ Discord members
- 400,000+ Reddit subscribers (r/godot)
- Active forum at https://forum.godotengine.org

### W4 Games

W4 Games is a company founded by Godot's original creators (Juan Linietsky, Rémi Verschelde) to provide:
- **Console porting**: Switch, PS5, Xbox Series X/S support
- **Enterprise support**: SLAs, priority bug fixes
- **Mobile optimization**: Fine-tuned mobile builds
- **W4 Cloud**: Backend services for Godot games

W4 Games is separate from the Godot Foundation. Revenue from W4 Games helps fund Godot development.

## Web Editor

Godot can run entirely in a browser at **editor.godotengine.org**. The web editor:
- Requires no installation
- Syncs with GitHub for project storage
- Supports GDScript editing with full autocomplete
- Can export to HTML5 directly
- Limited to Web-compatible features (no desktop-only backends)

## CLI / Headless Mode

Godot's command-line interface is critical for CI/CD and automated pipelines:

```bash
# Run a GDScript in headless mode
godot --headless --script path/to/script.gd

# Export a project from command line
godot --headless --export-release "Windows" build/game.exe

# Run editor tests
godot --headless --test

# Benchmark
godot --benchmark
```

**godot-mcp** leverages headless mode for automated scene manipulation without opening the editor UI.

## Comparison with Unity and Unreal

| Feature | Godot 4 | Unity | Unreal 5 |
|---------|---------|-------|----------|
| **Download size** | ~40 MB | ~10 GB | ~40 GB |
| **License** | MIT (free) | Per-seat ($2,040/year) | 5% royalty over $1M |
| **Primary language** | GDScript (Python-like) | C# | C++ / Blueprints |
| **2D engine** | Best-in-class dedicated | 2D toolkit overlay | Overkill (3D-only approach) |
| **3D quality** | Excellent (4.x) | Mature | AAA-grade |
| **GPU particles** | Built-in GPUParticles3D | VFX Graph | Niagara |
| **Physics** | Jolt (default since 4.6) | PhysX | Chaos |
| **Web export** | Yes (HTML5/WASM) | Yes (heavy) | No (Pixel Streaming) |
| **VR/XR** | OpenXR, WebXR, Quest native | XR Interaction Toolkit | Built-in OpenXR |
| **Source access** | Full (MIT) | Read-only (enterprise) | Full (with registration) |
| **Asset store** | Community-run, free | Massive, mixed | FAB (Epic marketplace) |
| **CI/CD** | `godot --headless` | Unity BuildPipeline | Unreal Automation Tool |
| **LLM compatibility** | GDScript (best) | C# (good) | C++ (poor) |

### When to Use Godot

- You value open-source and want to own your tools
- Your game is 2D or 2.5D (Godot's 2D is unmatched)
- You're an indie or small team with no engine budget
- You want lightweight builds (~15 MB minimum vs ~200 MB for Unity)
- You're building educational tools or visualizations
- Your AI/LLM pipeline needs a scriptable game engine
- You want a future-proof, community-owned platform

### When to Use Unity

- Your team already has deep Unity expertise
- You need specific Unity Asset Store plugins
- You're targeting consoles and need the Unity porting pipeline
- You're building for the Chinese market (Unity has better localization)

### When to Use Unreal

- You need AAA-quality photorealistic graphics (Nanite/Lumen)
- Your team includes C++ engine programmers
- You're making a large 3D open-world game
- You're targeting high-end PC and next-gen consoles only

## Future Roadmap

### Godot 4.7 (Late 2026)
- HDR display support (HDR10, scRGB)
- Ray tracing groundwork (BVH infrastructure)
- Vulkan pipeline cache for faster shader compilation
- Multi-window editor support

### Beyond 4.7
- Full ray tracing pipeline (RT reflections, RT shadows, RT GI)
- GPU-driven rendering (Nanite-like mesh shaders)
- Improved C# hot reload
- Better Web export (WebGPU backend)
- AI-assisted editor features
