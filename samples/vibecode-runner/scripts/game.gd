extends Node2D
## Vibecoder Runner — main controller.
## States: title -> running -> game_over (-> title). Pause overlays via HUD.

const HazardFactory := preload("res://scripts/hazard_factory.gd")

const DEATH_LINES := [
	"Context window exceeded",
	"Rate limit: 429 Too Many Requests",
	"Prettier rewrote your soul",
	"Copilot suggested `rm -rf /`",
	"Merge conflict in main.tscn",
	"CI failed on lint-staged",
	"Out of GPU VRAM (vibes only)",
	"Agent hallucinated a platform",
	"Your branch is 42 commits behind main",
]

const LOC_SCALE := 30.0
const CARBON_BASE := 0.45
const CARBON_DATACENTER := 0.35
const MULT_DURATION := 6.0
const SHIP_CHARGES := 3
const SHIP_CARBON_RELIEF := 15.0

const COL_GOOD := Color("#39ff88")
const COL_WARN := Color("#ffb03a")
const COL_BAD := Color("#ff5555")

var _state := "title"
var _score := 0.0
var _distance := 0.0
var _multiplier := 1.0
var _mult_timer := 0.0
var _carbon := 0.0
var _ship_charges := SHIP_CHARGES
var _datacenter: Node2D
var _boss_bonus := 250
var _best_before := 0

@onready var player: CharacterBody2D = $Player
@onready var camera: Camera2D = $Camera2D
@onready var world: Node2D = $World
@onready var spawner: Node = $Spawner
@onready var effects: Node2D = $Effects
@onready var hud: CanvasLayer = $HUD
@onready var title_layer: CanvasLayer = $TitleLayer
@onready var game_over_layer: CanvasLayer = $GameOverLayer
@onready var ground: StaticBody2D = $Ground
@onready var bg_lines: Node2D = $Background/Lines
@onready var far_code: Node2D = $Background/FarCode


func _ready() -> void:
	add_to_group("game")
	player.died.connect(_on_player_died)
	game_over_layer.restart_requested.connect(_start_game)
	title_layer.start_requested.connect(_start_game)
	spawner.set_loc_provider(func() -> float: return _distance)
	spawner.boss_started.connect(_on_boss_started)
	spawner.boss_defeated.connect(_on_boss_defeated)
	_draw_background()
	_draw_ground()
	_datacenter = HazardFactory.make_datacenter()
	_datacenter.position = Vector2(420, 120)
	world.add_child(_datacenter)
	hud.ship_pressed.connect(_ship_it)
	hud.show_banner("you are a vibecoder at 3 AM", COL_GOOD, 3.0)
	_show_title(true)


func is_running() -> bool:
	return _state == "running"


func _process(delta: float) -> void:
	match _state:
		"title":
			if Input.is_action_just_pressed("pause_game"):
				get_tree().quit()
		"running":
			_process_run(delta)
		"paused":
			if Input.is_action_just_pressed("pause_game"):
				_toggle_pause(false)
			elif Input.is_action_just_pressed("mute"):
				_toggle_mute()
		"game_over":
			if Input.is_action_just_pressed("mute"):
				_toggle_mute()


func _process_run(delta: float) -> void:
	_distance += player.RUN_SPEED * delta
	_score += delta * 12.0 * _multiplier

	if _mult_timer > 0.0:
		_mult_timer = max(_mult_timer - delta, 0.0)
		if _mult_timer <= 0.0:
			_multiplier = 1.0

	var carbon_rate := CARBON_BASE
	if is_instance_valid(_datacenter):
		carbon_rate += CARBON_DATACENTER
	_carbon = min(_carbon + carbon_rate * delta, 100.0)
	if _carbon >= 100.0:
		_die("EPA FINED YOU\ninto oblivion.\nCarbon: 100%")

	var boss_msg := ""
	if spawner.get_boss_active():
		boss_msg = "⚔ GEN. BUTLER — survive the Bulerite Jihad!"
	hud.set_score(int(_loc()), int(_distance), boss_msg)
	hud.set_carbon(_carbon)
	hud.set_mult(_multiplier, _mult_timer)
	hud.set_ship(_ship_charges)

	camera.global_position.x = player.global_position.x + 80.0
	_scroll_background(delta)


func _loc() -> float:
	return _distance / LOC_SCALE


# ---------------------------------------------------------------- game flow

func _start_game() -> void:
	_state = "running"
	_score = 0.0
	_distance = 0.0
	_multiplier = 1.0
	_mult_timer = 0.0
	_carbon = 0.0
	_ship_charges = SHIP_CHARGES
	_best_before = Save.get_best()
	_show_title(false)
	game_over_layer.hide()
	hud.hide_pause()
	hud.show()
	player.reset_runner()
	spawner.reset_spawner()
	Audio.play(&"start", -3.0)
	Audio.start_music()
	hud.show_banner("ship the feature. survive the AI underworld.", COL_GOOD, 2.5)


func _show_title(visible: bool) -> void:
	title_layer.visible = visible
	hud.visible = not visible


func _toggle_pause(paused: bool) -> void:
	if paused:
		_state = "paused"
		get_tree().paused = true
		hud.show_pause()
	else:
		_state = "running"
		get_tree().paused = false
		hud.hide_pause()


func _toggle_mute() -> void:
	var muted := Audio.toggle_mute()
	hud.show_banner("MUTED" if muted else "SOUND ON", COL_GOOD, 1.2)
	Audio.play(&"click", -4.0)


func _die(reason: String) -> void:
	if _state != "running":
		return
	_state = "game_over"
	spawner.stop_spawner()
	var msg: String = reason
	if msg.is_empty():
		msg = DEATH_LINES.pick_random()
	var final_loc := int(_loc())
	var new_best := Save.submit_score(final_loc)
	Audio.play(&"over", -2.0)
	Audio.stop_music()
	game_over_layer.show_result(
		final_loc, int(_distance), msg, Save.get_best(), new_best, _best_before,
	)
	hud.hide()


func _on_player_died(reason: String) -> void:
	_die(reason)


func _on_boss_started() -> void:
	_score += float(_boss_bonus)
	_boss_bonus = 500
	hud.show_banner("⚔ GEN. BUTLER APPROACHES", COL_BAD, 2.0)


func _on_boss_defeated() -> void:
	_score += 500.0
	hud.show_banner("✓ CHANNEL REPUSHED! +500 LOC", COL_GOOD, 3.0)
	effects.shake(6.0, 0.4)
	effects.burst(player.global_position, COL_GOOD, 20)


# ---------------------------------------------------------------- abilities

func _ship_it() -> void:
	if _state != "running" or _ship_charges <= 0:
		return
	_ship_charges -= 1
	for child in world.get_children():
		if child.get_meta("kind", "") in ["datacenter", "fan_blast"]:
			continue
		child.queue_free()
	_score += 50.0
	_carbon = max(_carbon - SHIP_CARBON_RELIEF, 0.0)
	Audio.play(&"ship", -2.0)
	effects.shake(5.0, 0.3)
	effects.burst(player.global_position + Vector2(40, -20), COL_GOOD, 24)
	hud.show_banner("SHIPPED! +50 LOC  (%d left)" % _ship_charges, COL_GOOD, 1.8)


func drink() -> void:
	_multiplier = 2.0
	_mult_timer = MULT_DURATION
	_score += 50.0
	Audio.play(&"drink", -2.0)
	effects.burst(player.global_position + Vector2(0, -20), Color("#39ff88"), 14)
	effects.float_text(player.global_position + Vector2(0, -40), "ENERGY! 2x", COL_GOOD, 18)


func fake_drink() -> void:
	_score = max(_score - 100.0, 0.0)
	player.stun(1.0)
	Audio.play(&"hit", -4.0)
	effects.shake(4.0, 0.25)
	hud.show_banner("HALLUCINATION! -100 LOC", COL_BAD, 2.0)


func add_score(amount: float) -> void:
	_score += amount


func drain_score(amount: float) -> void:
	_score = max(_score - amount, 0.0)


func add_carbon(amount: float) -> void:
	_carbon = min(_carbon + amount, 100.0)


func stun(duration: float) -> void:
	player.stun(duration)
	hud.show_stun(duration)


func hack_jump() -> void:
	player.hack_jump(2.5)
	Audio.play(&"drain", -6.0)
	hud.show_banner("INJECTION: jump offline 2.5s", COL_WARN, 2.0)
	effects.float_text(player.global_position + Vector2(0, -50), "jump() -> 401", COL_WARN, 14)


func take_equity(fraction: float) -> void:
	var taken := int(_score * fraction)
	_score = max(_score - float(taken), 0.0)
	Audio.play(&"drain", -4.0)
	hud.show_banner("THE VC TOOK %d LOC IN EQUITY" % taken, COL_WARN, 2.5)
	effects.float_text(player.global_position + Vector2(0, -60), "-%d equity" % taken, COL_WARN, 16)


func fan_blast() -> void:
	if _state != "running":
		return
	player.velocity.x += 220.0
	effects.shake(7.0, 0.35)
	Audio.play(&"powerup", -6.0)
	var warning := HazardFactory.make_fan_warning()
	warning.position = player.global_position + Vector2(150, 0)
	world.add_child(warning)
	hud.show_banner("FAN BLAST! +SPEED", Color("#7dd3fc"), 1.2)


# ---------------------------------------------------------------- contact

func _on_hazard_contact(body: Node2D, area: Area2D) -> void:
	if body != player or not player.has_method("kill"):
		return
	var kind: String = area.get_meta("kind", "")
	match kind:
		"drink":
			drink()
			area.queue_free()
		"fake_drink":
			fake_drink()
			area.queue_free()
		"claude_desktop":
			stun(1.5)
			hud.show_banner("\"I'm sorry — I can't do that\"", Color("#d6b48c"), 1.8)
			effects.shake(3.0, 0.2)
		"meeting_invite":
			stun(1.2)
			hud.show_banner("45-min status update. Could have been an email.", Color("#ff8f8f"), 2.0)
			area.queue_free()
		"legacy_code":
			_score = max(_score - 5.0, 0.0)
			hud.show_banner("GOTO: unexpected line", Color("#8fb8d9"), 1.4)
			if randf() < 0.3:
				player.global_position.x += 180.0
				effects.shake(5.0, 0.3)
				hud.show_banner("GOTO 10 — TELEPORTED", Color("#8fb8d9"), 1.4)
		"the_vc":
			take_equity(0.5)
			area.queue_free()
		"tokenmaxxer", "pipe", "mine", "hallucinator", "prompt_injector", "context_a", "context_b":
			player.kill(area.get_meta("death_msg", "Touched a hazard"))


# ---------------------------------------------------------------- background

func _draw_background() -> void:
	for i in 46:
		var line := ColorRect.new()
		line.size = Vector2(randf_range(50, 240), 1)
		line.color = Color(0.2, 0.85, 0.55, randf_range(0.06, 0.16))
		line.position = Vector2(randf_range(0, 3000), randf_range(30, 460))
		bg_lines.add_child(line)

	var code_words := [
		"git push", ">_", "PR #42", "npm i", "FIXME", "TODO", "sudo", "404", "vibe",
	]
	for i in 8:
		var label := Label.new()
		label.text = code_words[i % code_words.size()]
		label.position = Vector2(randf_range(0, 2600), randf_range(60, 380))
		label.add_theme_font_size_override("font_size", 40 + randi_range(0, 30))
		label.add_theme_color_override("font_color", Color(0.1, 0.45, 0.3, 0.25))
		far_code.add_child(label)


func _scroll_background(delta: float) -> void:
	for child in bg_lines.get_children():
		child.position.x -= player.RUN_SPEED * delta * 0.3
		if child.position.x < camera.global_position.x - 400:
			child.position.x += 1600
	for child in far_code.get_children():
		child.position.x -= player.RUN_SPEED * delta * 0.12
		if child.position.x < camera.global_position.x - 600:
			child.position.x += 3200


func _draw_ground() -> void:
	var strip := ColorRect.new()
	strip.size = Vector2(16000, 200)
	strip.position = Vector2(-400, 520)
	strip.color = Color("#060b08")
	ground.add_child(strip)

	var top_line := ColorRect.new()
	top_line.size = Vector2(16000, 2)
	top_line.position = Vector2(-400, 520)
	top_line.color = Color(0.2, 0.85, 0.55, 0.7)
	ground.add_child(top_line)

	var code_texts := [
		"if (you.can) { ship(); }", "git commit -m \"vibe\"", ">_", "semicolons();",
		"PR MERGED ✓", "npm run dev -- --fix", "deploy: success", "lint: 0 errors",
		"0xDEADBEEF", "autocomplete.exe",
	]
	for i in 40:
		var label := Label.new()
		label.text = code_texts[i % code_texts.size()]
		label.position = Vector2(200 + i * 400.0, 545)
		label.add_theme_font_size_override("font_size", 10)
		label.add_theme_color_override("font_color", Color(0.16, 0.5, 0.34, 0.55))
		ground.add_child(label)
