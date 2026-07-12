extends Area2D
## The Prompt Injector — approaches player, swaps a key binding temporarily.
var speed: float = 80.0
var hack_interval: float = 5.0
var hack_timer: float = 0.0

func _ready():
	modulate = Color(0, 1, 0.3)

func _process(delta):
	var player = get_node("/root/MainScene/Player")
	if player:
		position.y = move_toward(position.y, player.position.y, speed * delta)
	hack_timer += delta
	if hack_timer >= hack_interval and position.distance_to(player.position) < 300:
		hack_timer = 0
		_hack_player(player)

func _hack_player(_player):
	var keys = ["ui_up", "ui_down", "ui_left", "ui_right"]
	var old = keys[randi() % keys.size()]
	var new = keys[randi() % keys.size()]
	var msg = get_node("/root/MainScene/UI/HackMessage")
	if msg:
		msg.text = "INJECTION: %s -> %s" % [old, new]
		msg.show()
		await get_tree().create_timer(2.0).timeout
		msg.hide()

func _on_body_entered(body):
	if body.has_method("hit_by_enemy"):
		body.hit_by_enemy()
