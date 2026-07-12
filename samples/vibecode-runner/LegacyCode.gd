extends Area2D
## Legacy Code — terrain hazard. Slows player, GOTO teleport.
var teleport_cooldown: float = 0.0

func _ready():
	scale = Vector2(randf_range(1, 3), 1)
	var main = get_node("/root/MainScene")
	if main:
		position.y = 550  # floor level

func _process(delta):
	teleport_cooldown -= delta
	position.x -= 40 * delta  # scrolls left

func _on_body_entered(body):
	if body.has_method("stun"):
		var main = get_node("/root/MainScene")
		if main:
			main.add_score(-5)
			if teleport_cooldown <= 0:
				teleport_cooldown = 4.0
				body.position.x = randf_range(100, 900)
				var msg = main.get_node("UI/HackMessage")
				if msg:
					msg.text = "GOTO unexpected line!"
					msg.show()
					await get_tree().create_timer(1.5).timeout
					msg.hide()
