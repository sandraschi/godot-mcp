extends Node

@onready var world: Node2D = $"../World"
@onready var player: CharacterBody2D = $"../Player"


func _process(delta: float) -> void:
	for child in world.get_children():
		if not child is Area2D:
			continue
		if not child.has_meta("move"):
			continue
		var base_x: float = child.get_meta("base_x", child.position.x)
		var phase: float = child.get_meta("phase", 0.0)
		phase += delta * 3.0
		child.set_meta("phase", phase)

		match child.get_meta("move"):
			"roll":
				child.position.y = 300 + sin(phase * 2.0) * 4.0
				child.rotation += delta * 4.0
			"orbit":
				child.position.y = 300 - 40 + sin(phase) * 18.0
				child.position.x = base_x + cos(phase * 0.7) * 12.0
			"float":
				child.position.y = 300 - 55 + sin(phase * 1.3) * 22.0
				child.position.x = base_x + sin(phase * 0.9) * 10.0
			"trumpler":
				child.position.y = 120 + sin(phase * 0.8) * 35.0
				child.position.x = base_x + sin(phase * 1.6) * 40.0
				if sin(phase * 2.4) > 0.85:
					child.position.y += 80
			"elonsky":
				child.position.y = 80 + abs(sin(phase * 0.5)) * 60.0
				child.position.x = base_x - phase * 18.0
				child.rotation = sin(phase) * 0.4
				if child.position.y > 240:
					child.position.y = 240
