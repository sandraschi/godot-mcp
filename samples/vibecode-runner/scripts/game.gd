extends Node2D

const DEATH_LINES := [
	"Context window exceeded",
	"Rate limit: 429 Too Many Requests",
	"Prettier rewrote your soul",
	"Copilot suggested `rm -rf /`",
	"Merge conflict in main.tscn",
	"CI failed on lint-staged",
	"Out of GPU VRAM (vibes only)",
	"Agent hallucinated a platform",
]

@onready var player: CharacterBody2D = $Player
@onready var camera: Camera2D = $Camera2D
@onready var spawner: Node = $Spawner
@onready var hud: CanvasLayer = $HUD
@onready var title_layer: CanvasLayer = $TitleLayer
@onready var game_over_layer = $GameOverLayer
@onready var ground: StaticBody2D = $Ground
@onready var bg_lines: Node2D = $Background/Lines

var _running := false
var _score := 0.0
var _distance := 0.0


func _ready() -> void:
	player.died.connect(_on_player_died)
	game_over_layer.restart_requested.connect(_start_game)
	spawner.set_distance_provider(func(): return _distance)
	spawner.boss_started.connect(_on_boss_started)
	spawner.boss_defeated.connect(_on_boss_defeated)
	_draw_background()
	_show_title(true)
	game_over_layer.hide()


func _process(delta: float) -> void:
	if not _running:
		if Input.is_action_just_pressed("start"):
			_start_game()
		return

	_distance += player.RUN_SPEED * delta
	_score += delta * 12.0
	var boss_msg := ""
	if spawner.get_boss_active():
		boss_msg = "⚔ GEN. BUTLER — survive the Bulerite Jihad!"
	hud.set_score(int(_score), int(_distance), boss_msg)

	camera.global_position.x = player.global_position.x + 80
	_scroll_background(delta)


func _start_game() -> void:
	_running = true
	_score = 0.0
	_distance = 0.0
	_show_title(false)
	game_over_layer.hide()
	player.reset_runner()
	spawner.reset_spawner()


func _on_boss_started() -> void:
	_score += 250.0
	hud.set_score(int(_score), int(_distance), "⚔ GEN. BUTLER approaches…")


func _on_boss_defeated() -> void:
	_score += 500.0
	hud.set_score(int(_score), int(_distance), "✓ Channel repushed! Keep shipping.")


func _on_player_died(reason: String) -> void:
	if not _running:
		return
	_running = false
	spawner.stop_spawner()
	var msg: String = reason
	if msg.is_empty():
		msg = DEATH_LINES.pick_random()
	game_over_layer.show_result(int(_score), int(_distance), msg)


func _show_title(visible: bool) -> void:
	title_layer.visible = visible


func _draw_background() -> void:
	for i in 40:
		var line := ColorRect.new()
		line.size = Vector2(randf_range(40, 220), 1)
		line.color = Color(0.2, 0.85, 0.55, randf_range(0.08, 0.2))
		line.position = Vector2(randf_range(0, 2000), randf_range(40, 280))
		bg_lines.add_child(line)


func _scroll_background(delta: float) -> void:
	for child in bg_lines.get_children():
		child.position.x -= player.RUN_SPEED * delta * 0.35
		if child.position.x < camera.global_position.x - 400:
			child.position.x += 1200
