extends Node
## Builds every hazard, enemy and pickup from primitives (no art assets).
## Enemies carry meta: kind, move, death_msg, and AI-specific timers that
## scripts/enemy_ai.gd dispatches on. Layer 4 = hazards, layer 2 = player.

enum IdeKind { VSCODE, WINDSURF, CURSOR }
enum EnemyKind {
	HALLUCINATOR, PROMPT_INJECTOR, TOKENMAXXER, CONTEXT_A, CONTEXT_B,
	CLAUDE_DESKTOP, TECHBRO, LEGACY_CODE, THE_VC, MEETING_INVITE, MINE,
}

const FLOOR_Y := 520.0
const HAZARD_LAYER := 4
const PLAYER_LAYER := 2


# ---------------------------------------------------------------- IDE obstacles

static func make_ide(kind: IdeKind) -> StaticBody2D:
	var body := StaticBody2D.new()
	body.collision_layer = HAZARD_LAYER
	body.collision_mask = 0

	var w := 56.0
	var h := 46.0
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(w, h)
	shape.shape = rect
	shape.position = Vector2(w * 0.5, -h * 0.5)
	body.add_child(shape)

	var palette := {
		IdeKind.VSCODE: {
			"bg": Color("#1e1e1e"), "bar": Color("#007acc"),
			"label": "VS Code", "accent": Color("#007acc"),
		},
		IdeKind.WINDSURF: {
			"bg": Color("#0f172a"), "bar": Color("#06b6d4"),
			"label": "Windsurf", "accent": Color("#22d3ee"),
		},
		IdeKind.CURSOR: {
			"bg": Color("#18181b"), "bar": Color("#7c3aed"),
			"label": "Cursor", "accent": Color("#a78bfa"),
		},
	}
	var p: Dictionary = palette[kind]

	var root := Node2D.new()
	root.position = Vector2.ZERO
	body.add_child(root)

	_rect(root, Vector2(w, h), Vector2(w * 0.5, -h * 0.5), p.bg)
	_rect(root, Vector2(w, 12), Vector2(w * 0.5, -h + 6), p.bar)
	for i in 3:
		_rect(root, Vector2(6, 6), Vector2(10 + i * 10, -h + 6), Color(0.9, 0.3 + i * 0.1, 0.3))

	var title := Label.new()
	title.text = p.label
	title.position = Vector2(6, -h + 14)
	title.add_theme_font_size_override("font_size", 9)
	title.add_theme_color_override("font_color", Color.WHITE)
	root.add_child(title)

	var fake_code := Label.new()
	fake_code.text = "main.ts\n// vibe"
	fake_code.position = Vector2(6, -h + 28)
	fake_code.add_theme_font_size_override("font_size", 8)
	fake_code.add_theme_color_override("font_color", p.accent)
	root.add_child(fake_code)

	body.set_meta("kind", "ide")
	body.set_meta("ide_name", p.label)
	return body


# ---------------------------------------------------------------- pickups

static func make_drink(real: bool) -> Area2D:
	var area := _make_area(20.0, "drink" if real else "fake_drink")
	area.set_meta("real", real)
	var root := Node2D.new()
	area.add_child(root)

	var can_color := Color("#123524") if real else Color("#3a2f14")
	var band_color := Color("#39ff88") if real else Color("#ffd166")
	var glow_color := (
		Color(0.2, 1.0, 0.5, 0.10) if real else Color(1.0, 0.8, 0.3, 0.10)
	)
	var can := _rect(root, Vector2(20, 26), Vector2(0, 0), can_color)
	var band := _rect(root, Vector2(20, 5), Vector2(0, -8), band_color)
	band.visible = true
	var bolt := Label.new()
	bolt.text = "⚡" if real else "?"
	bolt.position = Vector2(-9, -9)
	bolt.add_theme_font_size_override("font_size", 12)
	bolt.add_theme_color_override("font_color", Color("#39ff88") if real else Color("#ffb03a"))
	root.add_child(bolt)

	var glow := _rect(root, Vector2(26, 32), Vector2(0, 0), glow_color)
	glow.z_index = -1
	area.set_meta("bob", randf() * TAU)
	area.set_meta("death_msg", "Drank a hallucinated energy drink")
	return area


# ---------------------------------------------------------------- enemies

static func make_enemy(kind: EnemyKind) -> Area2D:
	match kind:
		EnemyKind.HALLUCINATOR:
			return _hallucinator()
		EnemyKind.PROMPT_INJECTOR:
			return _prompt_injector()
		EnemyKind.TOKENMAXXER:
			return _tokenmaxxer()
		EnemyKind.CONTEXT_A:
			return _context_bar(true)
		EnemyKind.CONTEXT_B:
			return _context_bar(false)
		EnemyKind.CLAUDE_DESKTOP:
			return _claude_desktop()
		EnemyKind.TECHBRO:
			return _techbro()
		EnemyKind.LEGACY_CODE:
			return _legacy_code()
		EnemyKind.THE_VC:
			return _the_vc()
		EnemyKind.MEETING_INVITE:
			return _meeting_invite()
		EnemyKind.MINE:
			return _mine()
	return _mine()


static func _hallucinator() -> Area2D:
	var area := _make_area(18.0, "hallucinator")
	area.set_meta("death_msg", "The Hallucinator made you touch a lie")
	area.set_meta("teleport_cd", randf_range(1.4, 2.4))
	var root := Node2D.new()
	area.add_child(root)
	var glitch := _rect(root, Vector2(30, 30), Vector2(0, 0), Color("#171c1a"))
	glitch.set_meta("flicker", true)
	var q := Label.new()
	q.text = "?"
	q.position = Vector2(-9, -14)
	q.add_theme_font_size_override("font_size", 18)
	q.add_theme_color_override("font_color", Color("#39ff88"))
	root.add_child(q)
	area.set_meta("move", "teleport")
	return area


static func _prompt_injector() -> Area2D:
	var area := _make_area(16.0, "prompt_injector")
	area.set_meta("death_msg", "Prompt-injected: your jump got pawned")
	area.set_meta("inject_cd", 4.0)
	var root := Node2D.new()
	area.add_child(root)
	var stream := _rect(root, Vector2(8, 40), Vector2(0, 0), Color("#0b3d24"))
	var label := Label.new()
	label.text = "INJ"
	label.position = Vector2(-12, -8)
	label.add_theme_font_size_override("font_size", 11)
	label.add_theme_color_override("font_color", Color("#39ff88"))
	root.add_child(label)
	area.set_meta("move", "hunt_y")
	return area


static func _tokenmaxxer() -> Area2D:
	var area := _make_area(24.0, "tokenmaxxer")
	area.set_meta("death_msg", "The Tokenmaxxer drained you to bankruptcy")
	var root := Node2D.new()
	area.add_child(root)
	_rect(root, Vector2(42, 42), Vector2(0, 0), Color("#3d2f06"))
	var bag := Label.new()
	bag.text = "$"
	bag.position = Vector2(-13, -20)
	bag.add_theme_font_size_override("font_size", 22)
	bag.add_theme_color_override("font_color", Color("#ffd166"))
	root.add_child(bag)
	var ticker := Label.new()
	ticker.name = "Counter"
	ticker.text = "0.00¢"
	ticker.position = Vector2(-22, 8)
	ticker.add_theme_font_size_override("font_size", 10)
	ticker.add_theme_color_override("font_color", Color("#fca5a5"))
	root.add_child(ticker)
	area.set_meta("move", "float_slow")
	return area


static func _context_bar(top: bool) -> Area2D:
	# Top bar: visual only (radius 1 = effectively no collision).
	# Bottom bar: the real threat — rises to y=450, must jump it.
	var area := _make_area(1.0 if top else 55.0, "context_a" if top else "context_b")
	area.set_meta("death_msg", "Context window exceeded — brackets closed on you")
	area.set_meta("top", top)
	var root := Node2D.new()
	area.add_child(root)
	_rect(root, Vector2(240, 26), Vector2(0, 0), Color("#1c2b1c"))
	var bracket := Label.new()
	bracket.text = "]"
	bracket.position = Vector2(-8, -13)
	bracket.add_theme_font_size_override("font_size", 16)
	bracket.add_theme_color_override("font_color", Color("#39ff88"))
	root.add_child(bracket)
	area.set_meta("move", "context")
	return area


static func _claude_desktop() -> Area2D:
	var area := _make_area(30.0, "claude_desktop")
	area.set_meta("death_msg", "Claude Desktop apologized you into the void")
	var root := Node2D.new()
	area.add_child(root)
	_rect(root, Vector2(64, 40), Vector2(0, 0), Color("#26221e"))
	_rect(root, Vector2(64, 6), Vector2(0, -20), Color("#8b4513"))
	var logo := Label.new()
	logo.text = "C"
	logo.position = Vector2(-10, -22)
	logo.add_theme_font_size_override("font_size", 16)
	logo.add_theme_color_override("font_color", Color("#e8c39e"))
	root.add_child(logo)
	var status := Label.new()
	status.text = "apologizing…"
	status.position = Vector2(-30, 2)
	status.add_theme_font_size_override("font_size", 9)
	status.add_theme_color_override("font_color", Color("#a0a0a0"))
	root.add_child(status)
	area.set_meta("move", "static")
	return area


static func _techbro() -> Area2D:
	var area := _make_area(18.0, "techbro")
	area.set_meta("death_msg", "Techbro 2.0 out-jargonized you")
	area.set_meta("mine_cd", 2.2)
	var root := Node2D.new()
	area.add_child(root)
	_rect(root, Vector2(26, 34), Vector2(0, 0), Color("#3a1d05"))
	var badge := Label.new()
	badge.text = "TB"
	badge.position = Vector2(-10, -15)
	badge.add_theme_font_size_override("font_size", 14)
	badge.add_theme_color_override("font_color", Color("#ffb03a"))
	root.add_child(badge)
	area.set_meta("move", "techbro")
	return area


static func _legacy_code() -> Area2D:
	var area := _make_area(30.0, "legacy_code")
	area.set_meta("death_msg", "GOTO: unexpected line — COBOL got you")
	var root := Node2D.new()
	area.add_child(root)
	_rect(root, Vector2(200, 26), Vector2(0, 0), Color("#20242c"))
	var code := Label.new()
	code.text = "      COBOL         GOTO 10"
	code.position = Vector2(-96, -8)
	code.add_theme_font_size_override("font_size", 9)
	code.add_theme_color_override("font_color", Color("#5b7c99"))
	root.add_child(code)
	area.set_meta("move", "static")
	return area


static func _the_vc() -> Area2D:
	var area := _make_area(22.0, "the_vc")
	area.set_meta("death_msg", "The VC took 50% equity and you faded away")
	area.set_meta("phase", 0.0)
	var root := Node2D.new()
	area.add_child(root)
	var cloud := _rect(root, Vector2(46, 30), Vector2(0, 0), Color("#1e1b2e"))
	_rect(root, Vector2(46, 6), Vector2(0, -15), Color("#7c5cff"))
	var label := Label.new()
	label.text = "VC"
	label.position = Vector2(-14, -24)
	label.add_theme_font_size_override("font_size", 15)
	label.add_theme_color_override("font_color", Color("#c4b5fd"))
	root.add_child(label)
	var ask := Label.new()
	ask.text = "valuation?"
	ask.position = Vector2(-28, 4)
	ask.add_theme_font_size_override("font_size", 9)
	ask.add_theme_color_override("font_color", Color("#a78bfa"))
	root.add_child(ask)
	area.set_meta("move", "vc")
	return area


static func _meeting_invite() -> Area2D:
	var area := _make_area(12.0, "meeting_invite")
	area.set_meta("death_msg", "The Meeting's status update consumed you")
	var root := Node2D.new()
	area.add_child(root)
	_rect(root, Vector2(22, 22), Vector2(0, 0), Color("#3a0d0d"))
	var cal := Label.new()
	cal.text = "📅"
	cal.position = Vector2(-10, -11)
	cal.add_theme_font_size_override("font_size", 13)
	root.add_child(cal)
	area.set_meta("move", "homing")
	return area


static func _mine() -> Area2D:
	var area := _make_area(10.0, "mine")
	area.set_meta("death_msg", "Stepped on a jargon mine")
	area.set_meta("lifetime", 6.0)
	var root := Node2D.new()
	area.add_child(root)
	_rect(root, Vector2(16, 16), Vector2(0, 0), Color("#4a2202"))
	var bomb := Label.new()
	bomb.text = "💣"
	bomb.position = Vector2(-8, -8)
	bomb.add_theme_font_size_override("font_size", 12)
	root.add_child(bomb)
	area.set_meta("move", "static")
	return area


# ---------------------------------------------------------------- ambient

static func make_datacenter() -> Node2D:
	var root := Node2D.new()
	root.set_meta("kind", "datacenter")
	root.set_meta("fan_cd", randf_range(7.0, 11.0))
	root.set_meta("pipe_cd", randf_range(11.0, 16.0))
	root.set_meta("carbon_rate", 1.1)

	_rect(root, Vector2(200, 110), Vector2(0, 0), Color("#0d1215"))
	for row in 3:
		for col in 8:
			var light := ColorRect.new()
			light.size = Vector2(6, 6)
			light.position = Vector2(-80 + col * 22, -38 + row * 24)
			light.color = Color(0.2, 1.0, 0.5, 0.7) if (row + col) % 2 == 0 else Color(1.0, 0.4, 0.3, 0.7)
			light.set_meta("blink", randf() * TAU)
			root.add_child(light)
	var label := Label.new()
	label.text = "THE DATACENTER"
	label.position = Vector2(-80, 52)
	label.add_theme_font_size_override("font_size", 10)
	label.add_theme_color_override("font_color", Color("#39ff88"))
	root.add_child(label)
	root.set_meta("move", "datacenter")
	return root


static func make_fan_warning() -> Node2D:
	var root := Node2D.new()
	root.set_meta("kind", "fan_blast")
	root.set_meta("lifetime", 0.8)
	_rect(root, Vector2(44, 90), Vector2(0, 0), Color(0.4, 0.9, 1.0, 0.25))
	var label := Label.new()
	label.text = "FAN"
	label.position = Vector2(-18, -8)
	label.add_theme_font_size_override("font_size", 12)
	label.add_theme_color_override("font_color", Color(0.6, 0.95, 1.0))
	root.add_child(label)
	return root


static func make_pipe() -> Area2D:
	var area := _make_area(6.0, "pipe")
	area.set_meta("death_msg", "A burst pipe waterboarded your sprint")
	area.set_meta("move", "fall")
	var root := Node2D.new()
	area.add_child(root)
	_rect(root, Vector2(10, 180), Vector2(0, 0), Color(0.2, 0.5, 0.8, 0.8))
	return area


# ---------------------------------------------------------------- helpers

static func _make_area(radius: float, kind: String) -> Area2D:
	var area := Area2D.new()
	area.collision_layer = HAZARD_LAYER
	area.collision_mask = 0
	area.monitoring = true
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = radius
	shape.shape = circle
	area.add_child(shape)
	area.set_meta("kind", kind)
	return area


static func _rect(parent: Node2D, size: Vector2, center: Vector2, color: Color) -> ColorRect:
	var rect := ColorRect.new()
	rect.size = size
	rect.position = center - size * 0.5
	rect.color = color
	parent.add_child(rect)
	return rect

