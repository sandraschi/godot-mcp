extends SceneTree
## Headless smoke test: boots Main.tscn, starts a run, simulates jumps,
## steps ~12 seconds, then reports state and quits.
##
## Usage:  godot --headless --path samples/vibecode-runner --script tools/smoke_test.gd

var _frames := 0
var _main: Node2D
var _jump_tick := 0
var _started := false
var _phase := "run"


func _initialize() -> void:
	var packed: PackedScene = load("res://Main.tscn")
	_main = packed.instantiate()
	root.add_child(_main)
	process_frame.connect(_on_frame)


func _on_frame() -> void:
	_frames += 1
	if not _started:
		_started = true
		_main.call("_start_game")
		return

	_jump_tick += 1
	if _jump_tick % 30 == 0:
		Input.action_press("jump")
	if _jump_tick % 33 == 0:
		Input.action_release("jump")

	if _phase == "run":
		if _jump_tick % 150 == 0:
			Input.action_press("ship_it")
		if _jump_tick % 153 == 0:
			Input.action_release("ship_it")
		if _main.get("_state") != "running" and _jump_tick % 40 == 0:
			_main.call("_start_game")
		if _frames >= 500:
			_phase = "systems"
			_exercise_systems()
	elif _phase == "systems":
		_frames = 0
		_phase = "boss"
		_main.call("_on_boss_started")
		var spawner := _main.get_node("Spawner")
		var world := _main.get_node("World")
		var boss := Node2D.new()
		boss.set_script(load("res://scripts/boss_butler.gd"))
		world.add_child(boss)
		boss.activate(_main.get_node("Player").global_position.x + 480.0)
		boss.defeated.connect(spawner._on_boss_defeated)
	elif _phase == "boss":
		if _frames >= 400:
			_finish()


func _exercise_systems() -> void:
	print("SMOKE exercising systems…")
	_main.call("drink")
	_main.call("fake_drink")
	_main.call("take_equity", 0.5)
	_main.call("fan_blast")
	_main.call("hack_jump")
	_main.call("stun", 1.0)
	_main.call("_ship_it")
	_main.call("_ship_it")
	_main.call("_ship_it")


func _finish() -> void:
	var state: String = _main.get("_state")
	var loc: int = int(_main.call("_loc"))
	var carbon: float = _main.get("_carbon")
	var world_count := _main.get_node("World").get_child_count()
	print("SMOKE state=%s loc=%d carbon=%.0f world_children=%d" % [state, loc, carbon, world_count])
	if state == "running":
		print("SMOKE PASS — game running, %d world entities" % world_count)
		quit(0)
	else:
		print("SMOKE FAIL — unexpected state: %s" % state)
		quit(1)
