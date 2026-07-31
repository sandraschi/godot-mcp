extends Node2D
## Screen shake, floating text and particle bursts.
## Added to the "effects" group from Main.tscn.

var _shake_strength := 0.0
var _shake_time := 0.0
var _camera: Camera2D


func _ready() -> void:
	add_to_group("effects")
	_camera = get_node_or_null("../Camera2D")


func shake(strength: float, duration: float = 0.25) -> void:
	_shake_strength = max(_shake_strength, strength)
	_shake_time = max(_shake_time, duration)


func _process(delta: float) -> void:
	if _shake_time > 0.0 and _camera:
		_shake_time -= delta
		var intensity: float = _shake_strength * max(_shake_time, 0.0) / 0.25
		_camera.offset = Vector2(
			randf_range(-intensity, intensity),
			randf_range(-intensity, intensity)
		)
		if _shake_time <= 0.0:
			_shake_strength = 0.0
			_camera.offset = Vector2.ZERO


func float_text(world_pos: Vector2, text: String, color: Color, size: int = 16) -> void:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", color)
	label.position = world_pos - Vector2(40, 0)
	label.z_index = 50
	add_child(label)
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(label, "position:y", label.position.y - 42.0, 0.9).set_ease(Tween.EASE_OUT)
	tween.tween_property(label, "modulate:a", 0.0, 0.9).set_delay(0.25)
	tween.chain().tween_callback(label.queue_free)


func burst(world_pos: Vector2, color: Color, count: int = 12, spread: float = 160.0) -> void:
	var particles := CPUParticles2D.new()
	particles.amount = count
	particles.lifetime = 0.5
	particles.one_shot = true
	particles.explosiveness = 1.0
	particles.direction = Vector2.ZERO
	particles.spread = spread
	particles.gravity = Vector2(0, 500)
	particles.initial_velocity_min = 60.0
	particles.initial_velocity_max = 220.0
	particles.scale_amount_min = 2.0
	particles.scale_amount_max = 4.0
	particles.color = color
	particles.position = world_pos
	particles.z_index = 40
	add_child(particles)
	particles.emitting = true
	particles.finished.connect(particles.queue_free)
