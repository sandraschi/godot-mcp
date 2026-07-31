extends Node
## Dispatches per-kind enemy AI: motion, timed abilities and ambient hazards.
## Scans the World node children every frame. Contact logic lives in game.gd.

const HazardFactory := preload("res://scripts/hazard_factory.gd")
const FLOOR_Y := 520.0

@onready var world: Node2D = $"../World"
@onready var player: CharacterBody2D = $"../Player"
@onready var game: Node2D = $".."


func _process(delta: float) -> void:
	if not is_instance_valid(game) or not game.is_running():
		return
	for child in world.get_children():
		if not child.has_meta("kind"):
			continue
		match child.get_meta("kind"):
			"drink", "fake_drink":
				_tick_bob(child, delta)
			"hallucinator":
				_tick_hallucinator(child, delta)
			"prompt_injector":
				_tick_injector(child, delta)
			"tokenmaxxer":
				_tick_tokenmaxxer(child, delta)
			"context_a", "context_b":
				_tick_context(child, delta)
			"claude_desktop":
				_tick_pulse(child)
			"techbro":
				_tick_techbro(child, delta)
			"legacy_code":
				_tick_pulse(child)
			"the_vc":
				_tick_vc(child, delta)
			"meeting_invite":
				_tick_homing(child, delta)
			"mine":
				_tick_mine(child, delta)
			"pipe":
				_tick_pipe(child, delta)
			"fan_blast":
				_tick_fan_warning(child, delta)
			"datacenter":
				_tick_datacenter(child, delta)


func _tick_bob(child: Node2D, delta: float) -> void:
	var phase: float = child.get_meta("bob", 0.0) + delta * 3.0
	child.set_meta("bob", phase)
	child.position.y = child.get_meta("base_y", child.position.y) + sin(phase) * 6.0
	child.rotation = sin(phase * 0.7) * 0.08


func _tick_hallucinator(child: Node2D, delta: float) -> void:
	var visual: Node2D = child.get_child(1) if child.get_child_count() > 1 else child
	if visual:
		visual.modulate.a = 0.55 + sin(Time.get_ticks_msec() * 0.02) * 0.45
	var cd: float = child.get_meta("teleport_cd", 2.0) - delta
	if cd <= 0.0:
		child.set_meta("teleport_cd", randf_range(1.3, 2.2))
		var target_x := player.global_position.x + randf_range(140.0, 340.0)
		child.position = Vector2(target_x, randf_range(240.0, 440.0))
		var effects := get_tree().get_first_node_in_group("effects")
		if effects:
			effects.burst(child.position, Color("#39ff88"), 8)
		Audio.play(&"teleport", -8.0)
		if randf() < 0.22:
			_spawn_fake_drink(child.position)


func _tick_injector(child: Node2D, delta: float) -> void:
	var target_x := player.global_position.x - 40.0
	child.position.x = move_toward(child.position.x, target_x, 46.0 * delta)
	child.position.y = move_toward(child.position.y, player.global_position.y, 70.0 * delta)
	var cd: float = child.get_meta("inject_cd", 4.0) - delta
	if cd <= 0.0 and child.position.distance_to(player.global_position) < 260.0:
		child.set_meta("inject_cd", 5.0)
		game.hack_jump()


func _tick_tokenmaxxer(child: Node2D, delta: float) -> void:
	var phase: float = child.get_meta("phase", 0.0) + delta * 1.6
	child.set_meta("phase", phase)
	child.position.y = 430.0 + sin(phase) * 12.0
	if child.position.distance_to(player.global_position) < 100.0:
		game.drain_score(20.0 * delta)
		var visual: Node2D = child.get_child(1) if child.get_child_count() > 1 else child
		var counter: Label = visual.get_node_or_null("Counter") if visual else null
		if counter:
			counter.text = "%.2f¢" % (child.get_meta("drained", 0.0))
			child.set_meta("drained", child.get_meta("drained", 0.0) + 20.0 * delta)


func _tick_context(child: Node2D, delta: float) -> void:
	var top: bool = child.get_meta("top")
	var age: float = child.get_meta("age", 0.0) + delta
	child.set_meta("age", age)
	# Top bracket is a visual warning; the bottom bracket closes the floor lane.
	var target_y := 340.0 if top else 450.0
	child.position.y = move_toward(child.position.y, target_y, 95.0 * delta)
	if age > 3.0:
		child.queue_free()


func _tick_pulse(child: Node2D) -> void:
	var pulse := 0.75 + sin(Time.get_ticks_msec() * 0.004) * 0.25
	child.modulate = Color(pulse, pulse, pulse)


func _tick_techbro(child: Node2D, delta: float) -> void:
	child.position.x = move_toward(child.position.x, player.global_position.x + 230.0, 20.0 * delta)
	child.position.y = 480.0 + sin(Time.get_ticks_msec() * 0.01) * 3.0
	var cd: float = child.get_meta("mine_cd", 2.2) - delta
	if cd <= 0.0:
		child.set_meta("mine_cd", 2.4)
		var mine: Area2D = HazardFactory.make_enemy(HazardFactory.EnemyKind.MINE)
		mine.position = Vector2(child.position.x - 40.0, 500.0)
		mine.set_meta("base_y", 500.0)
		world.add_child(mine)
		mine.body_entered.connect(game._on_hazard_contact.bind(mine))


func _tick_vc(child: Node2D, delta: float) -> void:
	var phase: float = child.get_meta("phase", 0.0) + delta
	child.set_meta("phase", phase)
	if phase < 1.2:
		child.position = Vector2(
			player.global_position.x + 420.0 - phase * 260.0,
			-60.0 + phase * 320.0,
		)
	elif phase < 3.2:
		child.position = Vector2(player.global_position.x + 150.0, 300.0 + sin(phase * 2.0) * 14.0)
	else:
		game.take_equity(0.5)
		child.queue_free()


func _tick_homing(child: Node2D, delta: float) -> void:
	var dir := (player.global_position - child.position).normalized()
	child.position += dir * 95.0 * delta
	child.rotation += delta * 3.0


func _tick_mine(child: Node2D, delta: float) -> void:
	var life: float = child.get_meta("lifetime", 6.0) - delta
	child.set_meta("lifetime", life)
	if life < 1.5:
		child.modulate.a = 0.5 + sin(Time.get_ticks_msec() * 0.02) * 0.5
	if life <= 0.0:
		child.queue_free()


func _tick_pipe(child: Node2D, delta: float) -> void:
	child.position.y += 300.0 * delta
	if child.position.y > 760.0:
		child.queue_free()


func _tick_fan_warning(child: Node2D, delta: float) -> void:
	var life: float = child.get_meta("lifetime", 0.8) - delta
	child.set_meta("lifetime", life)
	child.modulate.a = max(life / 0.8, 0.0)
	if life <= 0.0:
		child.queue_free()


func _tick_datacenter(child: Node2D, delta: float) -> void:
	var camera: Camera2D = $"../Camera2D"
	if is_instance_valid(camera):
		child.position.x = camera.global_position.x + 420.0
	for light in child.get_children():
		if light is ColorRect and light.has_meta("blink"):
			var phase: float = light.get_meta("blink") + delta * 6.0
			light.set_meta("blink", phase)
			light.color.a = 0.35 + sin(phase) * 0.35

	var fan_cd: float = child.get_meta("fan_cd", 8.0) - delta
	if fan_cd <= 0.0:
		child.set_meta("fan_cd", randf_range(8.0, 13.0))
		game.fan_blast()

	var pipe_cd: float = child.get_meta("pipe_cd", 12.0) - delta
	if pipe_cd <= 0.0:
		child.set_meta("pipe_cd", randf_range(10.0, 16.0))
		var pipe: Area2D = HazardFactory.make_pipe()
		pipe.position = Vector2(player.global_position.x + randf_range(420.0, 720.0), 320.0)
		world.add_child(pipe)
		pipe.body_entered.connect(game._on_hazard_contact.bind(pipe))


func _spawn_fake_drink(at: Vector2) -> void:
	var fake: Area2D = HazardFactory.make_drink(false)
	fake.position = at + Vector2(randf_range(-40.0, 40.0), randf_range(-30.0, 30.0))
	fake.set_meta("base_y", fake.position.y)
	world.add_child(fake)
	fake.body_entered.connect(game._on_hazard_contact.bind(fake))

