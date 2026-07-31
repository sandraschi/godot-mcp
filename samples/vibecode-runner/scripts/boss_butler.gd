extends Node2D
## GEN. BUTLER — the boss gauntlet. Survive his Bulerite Jihad.
## HP decays over time; phase 2 at 50% doubles the barrage.

signal defeated

const Projectile := preload("res://scripts/projectile.gd")

const DURATION := 18.0
const SHOOT_INTERVAL := 1.25
const SHOTS: Array[Array] = [
	[Vector2(-300, 90), "butler push --force", Color("#fa5c5c")],
	[Vector2(-260, 130), "wharf jihad deploy", Color("#e11d48")],
	[Vector2(-320, 50), "itch.io excommunicated", Color("#fb7185")],
]

var _timer := 0.0
var _shoot_cd := 0.5
var _hp := 100.0
var _active := false
var _hp_bar: ColorRect
var _hp_bg: ColorRect

@onready var world: Node2D = get_parent()
@onready var player: CharacterBody2D = $"../../Player"


func activate(at_x: float) -> void:
	_timer = 0.0
	_shoot_cd = 0.6
	_hp = 100.0
	_active = true
	position = Vector2(at_x, 180)
	show()


func _ready() -> void:
	_build_visual()
	var body := _make_body()
	add_child(body)
	body.body_entered.connect(_on_boss_touch)


func _process(delta: float) -> void:
	if not _active:
		return

	_timer += delta
	_shoot_cd -= delta

	position.x = player.global_position.x + 430.0 + sin(_timer * 2.2) * 30.0
	position.y = 160.0 + cos(_timer * 1.4) * 25.0

	var phase2 := _hp <= 50.0
	_hp -= delta * (7.0 if phase2 else 5.0)
	_update_hp_bar()

	if _shoot_cd <= 0.0:
		_shoot_cd = (SHOOT_INTERVAL * 0.6) if phase2 else SHOOT_INTERVAL
		_fire_push(phase2)

	if _hp <= 0.0 or _timer >= DURATION:
		_active = false
		Audio.play(&"boss_hit", -2.0)
		defeated.emit()
		queue_free()


func _fire_push(phase2: bool) -> void:
	for s in SHOTS:
		var proj := Area2D.new()
		proj.set_script(Projectile)
		world.add_child(proj)
		proj.global_position = global_position + Vector2(-30, 20)
		proj.setup(s[0], s[1], s[2])
	if phase2:
		var extra := Area2D.new()
		extra.set_script(Projectile)
		world.add_child(extra)
		extra.global_position = global_position + Vector2(-30, 20)
		extra.setup(Vector2(-340, -40), "rate limited 429", Color("#f472b6"))


func _on_boss_touch(body: Node2D) -> void:
	if body == player and body.has_method("kill"):
		body.kill("General Butler pushed your build to /dev/null")


func _build_visual() -> void:
	var crown := Label.new()
	crown.text = "⚔️🛡️"
	crown.position = Vector2(-28, -58)
	crown.add_theme_font_size_override("font_size", 22)
	add_child(crown)

	var title := Label.new()
	title.text = "GEN. BUTLER"
	title.position = Vector2(-42, -38)
	title.add_theme_font_size_override("font_size", 14)
	title.add_theme_color_override("font_color", Color("#fecaca"))
	add_child(title)

	var sub := Label.new()
	sub.text = "Bulerite Jihad"
	sub.position = Vector2(-38, -22)
	sub.add_theme_font_size_override("font_size", 10)
	sub.add_theme_color_override("font_color", Color("#fa5c5c"))
	add_child(sub)

	var robe := ColorRect.new()
	robe.size = Vector2(72, 48)
	robe.position = Vector2(-36, -10)
	robe.color = Color("#7f1d1d")
	add_child(robe)

	var badge := Label.new()
	badge.text = "butler"
	badge.position = Vector2(-22, 4)
	badge.add_theme_font_size_override("font_size", 16)
	badge.add_theme_color_override("font_color", Color.WHITE)
	add_child(badge)

	_hp_bg = ColorRect.new()
	_hp_bg.size = Vector2(80, 6)
	_hp_bg.position = Vector2(-40, 44)
	_hp_bg.color = Color(0.2, 0.2, 0.2)
	add_child(_hp_bg)

	_hp_bar = ColorRect.new()
	_hp_bar.size = Vector2(80, 6)
	_hp_bar.position = Vector2(-40, 44)
	_hp_bar.color = Color("#22c55e")
	add_child(_hp_bar)


func _update_hp_bar() -> void:
	if _hp_bar:
		_hp_bar.size.x = max(4.0, 80.0 * (_hp / 100.0))
		_hp_bar.color = Color("#eab308") if _hp <= 50.0 else Color("#22c55e")


func _make_body() -> Area2D:
	var area := Area2D.new()
	area.set_meta("kind", "boss_body")
	area.collision_layer = 4
	area.collision_mask = 2
	area.monitoring = true
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(64, 50)
	shape.shape = rect
	shape.position = Vector2(0, 10)
	area.add_child(shape)
	return area
