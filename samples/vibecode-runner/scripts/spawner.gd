extends Node

const HazardFactory := preload("res://scripts/hazard_factory.gd")
const BossButler := preload("res://scripts/boss_butler.gd")

const MIN_GAP := 140.0
const MAX_GAP := 280.0
const SPAWN_AHEAD := 720.0
const BOSS_EVERY_LOC := 2200.0
const FLYING_AFTER_LOC := 1200.0

signal boss_started
signal boss_defeated

var _next_x := 640.0
var _difficulty := 1.0
var _active := false
var _boss_active := false
var _next_boss_at := BOSS_EVERY_LOC
var _distance_fn: Callable

@onready var world: Node2D = $"../World"
@onready var player: CharacterBody2D = $"../Player"


func set_distance_provider(fn: Callable) -> void:
	_distance_fn = fn


func reset_spawner() -> void:
	_next_x = player.global_position.x + 400.0
	_difficulty = 1.0
	_boss_active = false
	_next_boss_at = BOSS_EVERY_LOC
	_clear_world()
	_active = true


func stop_spawner() -> void:
	_active = false


func get_boss_active() -> bool:
	return _boss_active


func _current_loc() -> float:
	if _distance_fn.is_valid():
		return float(_distance_fn.call())
	return player.global_position.x


func _process(delta: float) -> void:
	if not _active or _boss_active:
		return

	var loc := _current_loc()
	if loc >= _next_boss_at:
		_start_boss()
		return

	_difficulty = min(_difficulty + delta * 0.02, 2.8)

	while _next_x < player.global_position.x + SPAWN_AHEAD:
		_spawn_chunk(loc)
		_next_x += randf_range(MIN_GAP, MAX_GAP) / _difficulty

	_cleanup_behind()


func _start_boss() -> void:
	_boss_active = true
	_clear_world()
	boss_started.emit()

	var boss := Node2D.new()
	boss.set_script(BossButler)
	world.add_child(boss)
	boss.activate(player.global_position.x + 480)
	boss.defeated.connect(_on_boss_defeated)


func _on_boss_defeated() -> void:
	_boss_active = false
	_next_boss_at = _current_loc() + BOSS_EVERY_LOC
	_next_x = player.global_position.x + 500.0
	boss_defeated.emit()


func _spawn_chunk(loc: float) -> void:
	var roll := randf()
	if roll < 0.34:
		_spawn_ide()
	elif roll < 0.68:
		_spawn_enemy(loc)
	# else breathing room


func _spawn_ide() -> void:
	var kinds := [
		HazardFactory.IdeKind.VSCODE,
		HazardFactory.IdeKind.WINDSURF,
		HazardFactory.IdeKind.CURSOR,
	]
	var ide := HazardFactory.make_ide(kinds.pick_random())
	ide.position = Vector2(_next_x, 300)
	world.add_child(ide)


func _spawn_enemy(loc: float) -> void:
	var ground_kinds := [
		HazardFactory.EnemyKind.POWERSHELL,
		HazardFactory.EnemyKind.AGENT_LOOP,
		HazardFactory.EnemyKind.API_TOKEN,
	]
	var kinds: Array = ground_kinds.duplicate()

	if loc >= FLYING_AFTER_LOC:
		if randf() < 0.35:
			kinds = [HazardFactory.EnemyKind.TRUMPLER, HazardFactory.EnemyKind.ELONSKY]
		elif randf() < 0.2:
			kinds.append(HazardFactory.EnemyKind.TRUMPLER)
			kinds.append(HazardFactory.EnemyKind.ELONSKY)

	var kind = kinds.pick_random()
	var enemy := HazardFactory.make_enemy(kind)
	enemy.position = Vector2(_next_x, 140 if kind in [HazardFactory.EnemyKind.TRUMPLER, HazardFactory.EnemyKind.ELONSKY] else 300)
	enemy.body_entered.connect(_on_enemy_hit.bind(enemy))
	world.add_child(enemy)
	enemy.set_meta("base_x", _next_x)
	enemy.set_meta("phase", randf() * TAU)


func _on_enemy_hit(body: Node2D, enemy: Area2D) -> void:
	if body == player and player.has_method("kill"):
		player.kill(enemy.get_meta("death_msg", "Touched a hazard"))


func _cleanup_behind() -> void:
	for child in world.get_children():
		if child.global_position.x < player.global_position.x - 200:
			child.queue_free()


func _clear_world() -> void:
	for child in world.get_children():
		child.queue_free()
