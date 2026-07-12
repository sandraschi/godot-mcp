extends Area2D
## The Hallucinator — teleports randomly, spawns fake power-ups that damage.
var speed: float = 0.0
var teleport_timer: float = 0.0
var flicker: float = 0.0
var fake_spawned: bool = false

func _ready():
	scale = Vector2(0.8, 0.8)
	teleport_timer = randf_range(1.5, 3.0)

func _process(delta):
	teleport_timer -= delta
	flicker += delta * 20
	modulate.a = 0.6 + sin(flicker) * 0.4
	if teleport_timer <= 0:
		teleport_timer = randf_range(1.0, 2.5)
		position = Vector2(randf_range(50, 974), randf_range(50, 400))
		$TeleportParticles.emitting = true
		if not fake_spawned and randf() < 0.3:
			_spawn_fake_powerup()
			fake_spawned = true

func _spawn_fake_powerup():
	var fake = ColorRect.new()
	fake.name = "FakePowerUp"
	fake.size = Vector2(20, 20)
	fake.color = Color.YELLOW
	fake.position = position + Vector2(randf_range(-30, 30), randf_range(-30, 30))
	get_parent().add_child(fake)
	var t = create_tween()
	t.tween_property(fake, "position:y", fake.position.y - 30, 1.0)
	t.tween_callback(func(): fake.queue_free())

func _on_body_entered(body):
	if body.has_method("hit_by_enemy"):
		body.hit_by_enemy()
