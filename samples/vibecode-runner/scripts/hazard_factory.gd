extends Node

## Builds IDE obstacles and vibecoding enemies from primitives (no art assets).

enum IdeKind { VSCODE, WINDSURF, CURSOR }
enum EnemyKind { POWERSHELL, AGENT_LOOP, API_TOKEN, TRUMPLER, ELONSKY }


static func make_ide(kind: IdeKind) -> StaticBody2D:
	var body := StaticBody2D.new()
	body.collision_layer = 4
	body.collision_mask = 0

	var w := 52.0
	var h := 44.0
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(w, h)
	shape.shape = rect
	shape.position = Vector2(w * 0.5, -h * 0.5)
	body.add_child(shape)

	var palette := {
		IdeKind.VSCODE: {"bg": Color("#1e1e1e"), "bar": Color("#007acc"), "label": "VS Code", "accent": Color("#007acc")},
		IdeKind.WINDSURF: {"bg": Color("#0f172a"), "bar": Color("#06b6d4"), "label": "Windsurf", "accent": Color("#22d3ee")},
		IdeKind.CURSOR: {"bg": Color("#18181b"), "bar": Color("#7c3aed"), "label": "Cursor", "accent": Color("#a78bfa")},
	}
	var p: Dictionary = palette[kind]

	var root := Node2D.new()
	body.add_child(root)

	_add_rect(root, Vector2(w, h), Vector2(w * 0.5, -h * 0.5), p.bg, 4.0)
	_add_rect(root, Vector2(w, 12), Vector2(w * 0.5, -h + 6), p.bar, 4.0)
	for i in 3:
		_add_rect(root, Vector2(6, 6), Vector2(10 + i * 10, -h + 6), Color(0.9, 0.3 + i * 0.1, 0.3), 3.0)

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


static func make_enemy(kind: EnemyKind) -> Area2D:
	var area := Area2D.new()
	area.collision_layer = 4
	area.collision_mask = 0
	area.monitoring = true

	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = 16.0
	shape.shape = circle
	area.add_child(shape)

	var root := Node2D.new()
	area.add_child(root)

	match kind:
		EnemyKind.POWERSHELL:
			area.set_meta("kind", "powershell")
			area.set_meta("death_msg", "Pipe bomb: syntax exploded")
			circle.radius = 18.0
			var lbl := Label.new()
			lbl.text = "| &&"
			lbl.position = Vector2(-18, -14)
			lbl.add_theme_font_size_override("font_size", 16)
			lbl.add_theme_color_override("font_color", Color("#f97316"))
			root.add_child(lbl)
			var sub := Label.new()
			sub.text = "$env:"
			sub.position = Vector2(-20, 2)
			sub.add_theme_font_size_override("font_size", 9)
			sub.add_theme_color_override("font_color", Color("#fdba74"))
			root.add_child(sub)
			area.set_meta("move", "roll")
		EnemyKind.AGENT_LOOP:
			area.set_meta("kind", "agent_loop")
			area.set_meta("death_msg", "Agent loop: max turns exceeded")
			circle.radius = 20.0
			var ring := Line2D.new()
			ring.width = 2.0
			ring.default_color = Color("#22c55e", 0.8)
			for i in 24:
				var a := float(i) / 24.0 * TAU
				ring.add_point(Vector2(cos(a), sin(a)) * 18.0)
			root.add_child(ring)
			var lbl2 := Label.new()
			lbl2.text = "while(true):"
			lbl2.position = Vector2(-34, -8)
			lbl2.add_theme_font_size_override("font_size", 10)
			lbl2.add_theme_color_override("font_color", Color("#4ade80"))
			root.add_child(lbl2)
			area.set_meta("move", "orbit")
		EnemyKind.API_TOKEN:
			area.set_meta("kind", "api_token")
			area.set_meta("death_msg", "API token leaked to stderr")
			circle.radius = 17.0
			_add_rect(root, Vector2(38, 22), Vector2(0, 0), Color("#450a0a"), 6.0)
			var tok := Label.new()
			tok.text = "sk-live…"
			tok.position = Vector2(-22, -10)
			tok.add_theme_font_size_override("font_size", 11)
			tok.add_theme_color_override("font_color", Color("#fca5a5"))
			root.add_child(tok)
			var skull := Label.new()
			skull.text = "🔑💀"
			skull.position = Vector2(-16, -28)
			skull.add_theme_font_size_override("font_size", 14)
			root.add_child(skull)
			area.set_meta("move", "float")
		EnemyKind.TRUMPLER:
			area.set_meta("kind", "trumpler")
			area.set_meta("death_msg", "Ratio'd mid-sprint by a Trumpler")
			circle.radius = 22.0
			_add_rect(root, Vector2(44, 28), Vector2(0, -8), Color("#ea580c"), 8.0)
			var hair := ColorRect.new()
			hair.size = Vector2(36, 10)
			hair.position = Vector2(-18, -28)
			hair.color = Color("#fbbf24")
			root.add_child(hair)
			var name_lbl := Label.new()
			name_lbl.text = "TRUMPLER"
			name_lbl.position = Vector2(-30, -12)
			name_lbl.add_theme_font_size_override("font_size", 10)
			name_lbl.add_theme_color_override("font_color", Color("#fff7ed"))
			root.add_child(name_lbl)
			var post := Label.new()
			post.text = "POST!!!"
			post.position = Vector2(-22, 4)
			post.add_theme_font_size_override("font_size", 12)
			post.add_theme_color_override("font_color", Color("#1d4ed8"))
			root.add_child(post)
			area.set_meta("move", "trumpler")
		EnemyKind.ELONSKY:
			area.set_meta("kind", "elonsky")
			area.set_meta("death_msg", "Elonsky landed on your sprint branch")
			circle.radius = 20.0
			var rocket := Polygon2D.new()
			rocket.polygon = PackedVector2Array([
				Vector2(0, -28), Vector2(14, 12), Vector2(0, 6), Vector2(-14, 12)
			])
			rocket.color = Color("#94a3b8")
			root.add_child(rocket)
			var flame := Polygon2D.new()
			flame.polygon = PackedVector2Array([
				Vector2(0, 14), Vector2(8, 28), Vector2(-8, 28)
			])
			flame.color = Color("#f97316")
			root.add_child(flame)
			var x_lbl := Label.new()
			x_lbl.text = "ELONSKY"
			x_lbl.position = Vector2(-26, -8)
			x_lbl.add_theme_font_size_override("font_size", 9)
			x_lbl.add_theme_color_override("font_color", Color("#e2e8f0"))
			root.add_child(x_lbl)
			area.set_meta("move", "elonsky")

	area.set_meta("enemy_kind", kind)
	return area


static func _add_rect(parent: Node2D, size: Vector2, center: Vector2, color: Color, radius: float) -> void:
	var rect := ColorRect.new()
	rect.size = size
	rect.position = center - size * 0.5
	rect.color = color
	parent.add_child(rect)
