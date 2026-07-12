extends Area2D
## Claude Desktop — immobile desk. Sits there. Apology stun on touch.
var apology_cooldown: float = 0.0

func _ready():
	scale = Vector2(1.2, 1.0)
	var main = get_node("/root/MainScene")
	if not main: return
	# Place at random X, fixed lower position
	position.y = randf_range(350, 500)

func _process(delta):
	apology_cooldown -= delta
	# Chain-of-thought beam visual pulse
	modulate = Color.WHITE if sin(Time.get_ticks_msec() * 0.003) > 0.6 else Color(0.8, 0.8, 1)

func _on_body_entered(body):
	if not body.has_method("stun"): return
	if apology_cooldown <= 0:
		apology_cooldown = 8.0
		var main = get_node("/root/MainScene")
		if main:
			main.stun(3.0)
