extends Area2D
## The Tokenmaxxer Bankruptor — slow, drains score on touch.
var speed: float = 30.0
var drain_rate: float = 20.0

func _ready():
	scale = Vector2(1.5, 1.5)
	modulate = Color(1, 0.8, 0)

func _process(delta):
	position.y += speed * delta
	var player = get_node("/root/MainScene/Player")
	if player and position.distance_to(player.position) < 60:
		var main = get_node("/root/MainScene")
		if main and main.has_method("add_score"):
			main.add_score(-drain_rate * delta)
	if position.y > 700:
		queue_free()
