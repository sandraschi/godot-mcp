extends Area2D
## Context Window Overflow — closing brackets that shrink playable area.
var close_speed: float = 20.0
var side: int = 1  # -1 left wall, 1 right wall

func _ready():
	if position.x < 512:
		side = -1
		modulate = Color(0.3, 1, 0.3)
	else:
		side = 1
		modulate = Color(1, 0.3, 0.3)

func _process(delta):
	position.x += side * close_speed * delta
	if (side == -1 and position.x > 1024) or (side == 1 and position.x < 0):
		queue_free()
