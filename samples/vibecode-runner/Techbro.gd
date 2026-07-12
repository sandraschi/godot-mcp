extends Area2D
## The Techbro — fast, drops jargon mines, respawns as 2.0 on death.
var speed: float = 150.0
var jargon_cooldown: float = 0.0
var phase: int = 1
var jargons := ["synergy", "pivot", "disrupt", "scale", "leverage", "growth-hack"]

func _ready():
	if name == "Techbro": phase = 1
	modulate = Color(1, 0.6, 0) if phase == 1 else Color(1, 0.3, 0.6)

func _process(delta):
	jargon_cooldown -= delta
	var player = get_node("/root/MainScene/Player")
	if player:
		var dir = sign(player.position.x - position.x)
		position.x += dir * speed * delta
		if jargon_cooldown <= 0 and position.distance_to(player.position) < 250:
			jargon_cooldown = 3.0
			_spawn_jargon_mine()

func _spawn_jargon_mine():
	var mine = ColorRect.new()
	mine.size = Vector2(60, 20)
	mine.color = Color(1, 0.8, 0)
	mine.position = position + Vector2(randf_range(-20, 20), randf_range(-20, 20))
	get_parent().add_child(mine)
	var t = create_tween()
	t.tween_property(mine, "position:y", mine.position.y + 40, 2.0)
	t.tween_callback(mine.queue_free)

func die():
	if phase == 1:
		phase = 2
		var clone = preload("res://Techbro.tscn").instantiate()
		clone.name = "Techbro2"
		clone.position = position + Vector2(30, 0)
		get_parent().add_child(clone)
		position.x -= 30
		modulate = Color(1, 0.3, 0.6)
	else:
		var msg = get_node("/root/MainScene/UI/HackMessage")
		if msg: msg.text = "TECHBRO 2.0: \"We're hiring!\""
		queue_free()

func _on_body_entered(body):
	if body.has_method("hit_by_enemy"):
		die()
