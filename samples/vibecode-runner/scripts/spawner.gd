extends Node
## Procedural chunk spawner. Builds hazards ahead of the player, ramps
## difficulty with distance, schedules VC visits and the Boss Butler gauntlet.

signal boss_started
signal boss_defeated

const HazardFactory := preload("res://scripts/hazard_factory.gd")
const BossButler := preload("res://scripts/boss_butler.gd")

const MIN_GAP := 150.0
const MAX_GAP := 300.0
const SPAWN_AHEAD := 760.0
const BOSS_EVERY_LOC := 700.0
const FLOOR_Y := 520.0

var _next_x := 640.0
var _difficulty := 1.0
var _active := false
var _boss_active := false
var _next_boss_at := BOSS_EVERY_LOC
var _loc_fn: Callable
var _vc_thresholds := [250, 900, 2100]
var _vc_done: Array[int] = []
var _vc_cooldown := 0.0

@onready var world: Node2D = $"../World"
@onready var player: CharacterBody2D = $"../Player"
@onready var game: Node2D = $".."


func set_loc_provider(fn: Callable) -> void:
	_loc_fn = fn


func reset_spawner() -> void:
	_next_x = player.global_position.x + 420.0
	_difficulty = 1.0
	_boss_active = false
	_next_boss_at = BOSS_EVERY_LOC
	_vc_done = []
	_vc_cooldown = 0.0
	_clear_world()
	_active = true


func stop_spawner() -> void:
	_active = false


func get_boss_active() -> bool:
	return _boss_active


func _current_loc() -> float:
	if _loc_fn.is_valid():
		return float(_loc_fn.call())
	return player.global_position.x


func _process(delta: float) -> void:
	if not _active or _boss_active:
		return

	var loc := _current_loc()
	if loc >= _next_boss_at:
		_start_boss()
		return

	_difficulty = min(_difficulty + delta * 0.018, 2.6)
	_vc_cooldown = max(_vc_cooldown - delta, 0.0)
	_try_vc_visit(loc)

	while _next_x < player.global_position.x + SPAWN_AHEAD:
		_spawn_chunk(loc)
		_next_x += randf_range(MIN_GAP, MAX_GAP) / _difficulty

	_cleanup_behind()


func _try_vc_visit(loc: float) -> void:
	for threshold in _vc_thresholds:
		if loc >= threshold and threshold not in _vc_done and _vc_cooldown <= 0.0:
			_vc_done.append(threshold)
			_vc_cooldown = 40.0
			var vc := HazardFactory.make_enemy(HazardFactory.EnemyKind.THE_VC)
			vc.position = Vector2(player.global_position.x + 420.0, -60.0)
			world.add_child(vc)
			vc.body_entered.connect(game._on_hazard_contact.bind(vc))
			return


func _start_boss() -> void:
	_boss_active = true
	_clear_world()
	boss_started.emit()
	Audio.play(&"boss_alarm", -4.0)

	var boss := Node2D.new()
	boss.set_script(BossButler)
	world.add_child(boss)
	boss.activate(player.global_position.x + 480.0)
	boss.defeated.connect(_on_boss_defeated)


func _on_boss_defeated() -> void:
	_boss_active = false
	_next_boss_at = _current_loc() + BOSS_EVERY_LOC
	_next_x = player.global_position.x + 520.0
	boss_defeated.emit()


func _spawn_chunk(loc: float) -> void:
	var roll := randf()

	if roll < 0.30:
		_spawn_floor_obstacle(loc)
	elif roll < 0.60:
		_spawn_ground_enemy(loc)
	elif roll < 0.80:
		_spawn_air_enemy(loc)
	elif roll < 0.90:
		_spawn_drink(loc)
	# else: breathing room


func _spawn_floor_obstacle(loc: float) -> void:
	var kinds: Array[int] = [
		HazardFactory.IdeKind.VSCODE,
		HazardFactory.IdeKind.WINDSURF,
		HazardFactory.IdeKind.CURSOR,
	]
	var kind: int = kinds[randi() % kinds.size()]
	if loc >= 400.0 and randf() < 0.25:
		var legacy := HazardFactory.make_enemy(HazardFactory.EnemyKind.LEGACY_CODE)
		legacy.position = Vector2(_next_x, FLOOR_Y - 26.0)
		world.add_child(legacy)
		legacy.body_entered.connect(game._on_hazard_contact.bind(legacy))
		return
	if loc >= 300.0 and randf() < 0.2:
		var desk := HazardFactory.make_enemy(HazardFactory.EnemyKind.CLAUDE_DESKTOP)
		desk.position = Vector2(_next_x, FLOOR_Y - 30.0)
		world.add_child(desk)
		desk.body_entered.connect(game._on_hazard_contact.bind(desk))
		return
	var ide := HazardFactory.make_ide(kind)
	ide.position = Vector2(_next_x, FLOOR_Y)
	world.add_child(ide)


func _spawn_ground_enemy(_loc: float) -> void:
	var kinds: Array[int] = []
	if _loc >= 500.0:
		kinds.append(HazardFactory.EnemyKind.TOKENMAXXER)
	if _loc >= 300.0:
		kinds.append(HazardFactory.EnemyKind.TECHBRO)
	if kinds.is_empty():
		kinds.append(HazardFactory.EnemyKind.MINE)
		kinds.append(HazardFactory.EnemyKind.MINE)
	var kind: int = kinds[randi() % kinds.size()]
	var enemy := HazardFactory.make_enemy(kind)
	enemy.position = Vector2(_next_x, 470.0 if kind == HazardFactory.EnemyKind.TOKENMAXXER else 500.0)
	enemy.set_meta("base_y", enemy.position.y)
	world.add_child(enemy)
	enemy.body_entered.connect(game._on_hazard_contact.bind(enemy))


func _spawn_air_enemy(loc: float) -> void:
	var kinds: Array = []
	if loc >= 1200.0:
		kinds.append(HazardFactory.EnemyKind.CONTEXT_A)
	elif loc >= 400.0:
		kinds.append(HazardFactory.EnemyKind.HALLUCINATOR)
	if loc >= 900.0:
		kinds.append(HazardFactory.EnemyKind.PROMPT_INJECTOR)
	if loc >= 700.0 and kinds.size() >= 1 and randf() < 0.3:
		_spawn_meeting_swarm()
		return
	if kinds.is_empty():
		return
	var kind: int = kinds[randi() % kinds.size()]

	if kind == HazardFactory.EnemyKind.CONTEXT_A:
		var a := HazardFactory.make_enemy(HazardFactory.EnemyKind.CONTEXT_A)
		a.position = Vector2(_next_x, -80.0)
		var b := HazardFactory.make_enemy(HazardFactory.EnemyKind.CONTEXT_B)
		b.position = Vector2(_next_x + 240.0, FLOOR_Y + 80.0)
		world.add_child(a)
		world.add_child(b)
		a.body_entered.connect(game._on_hazard_contact.bind(a))
		b.body_entered.connect(game._on_hazard_contact.bind(b))
		_next_x += 260.0
		return

	var enemy := HazardFactory.make_enemy(kind)
	enemy.position = Vector2(_next_x, randf_range(260.0, 420.0))
	enemy.set_meta("base_y", enemy.position.y)
	world.add_child(enemy)
	enemy.body_entered.connect(game._on_hazard_contact.bind(enemy))


func _spawn_meeting_swarm() -> void:
	for i in 4:
		var invite := HazardFactory.make_enemy(HazardFactory.EnemyKind.MEETING_INVITE)
		invite.position = Vector2(_next_x + i * 60.0, randf_range(140.0, 320.0))
		world.add_child(invite)
		invite.body_entered.connect(game._on_hazard_contact.bind(invite))


func _spawn_drink(_loc: float) -> void:
	var drink := HazardFactory.make_drink(true)
	drink.position = Vector2(_next_x, randf_range(280.0, 430.0))
	drink.set_meta("base_y", drink.position.y)
	world.add_child(drink)
	drink.body_entered.connect(game._on_hazard_contact.bind(drink))


func _cleanup_behind() -> void:
	for child in world.get_children():
		if child.get_meta("kind", "") == "datacenter":
			continue
		if child.get_meta("kind", "") == "fan_blast":
			continue
		if child.global_position.x < player.global_position.x - 260.0:
			child.queue_free()


func _clear_world() -> void:
	for child in world.get_children():
		if child.get_meta("kind", "") == "datacenter":
			continue
		child.queue_free()
