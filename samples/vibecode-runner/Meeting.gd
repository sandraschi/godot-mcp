extends Area2D
## The Meeting — a swarm of calendar invites. Catch = 45s status update stun.
var speed: float = 100.0
var lifetime: float = 12.0

func _ready():
	scale = Vector2(0.8, 0.8)

func _process(delta):
	lifetime -= delta
	if lifetime <= 0:
		queue_free()
		return
	var player = get_node("/root/MainScene/Player")
	if player:
		var dir = sign(player.position.x - position.x)
		position.x += dir * speed * delta
		position.y = move_toward(position.y, player.position.y, speed * 0.5 * delta)

func _on_body_entered(body):
	if not body.has_method("stun"): return
	var main = get_node("/root/MainScene")
	if not main: return
	main.stun(4.0)
	var msg = main.get_node("UI/HackMessage")
	if msg:
		msg.text = "45-min status update. Could have been an email."
		msg.show()
		await get_tree().create_timer(2.5).timeout
		msg.hide()
	queue_free()
