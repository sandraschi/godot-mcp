extends Area2D

var _velocity := Vector2(-280, 60)
var _age := 0.0
var _lifetime := 8.0


func _ready() -> void:
	collision_layer = 4
	collision_mask = 2
	monitoring = true
	body_entered.connect(_on_body_entered)


func setup(velocity: Vector2, msg: String, color: Color) -> void:
	_velocity = velocity
	set_meta("death_msg", msg)
	_lifetime = 8.0
	_age = 0.0

	for child in get_children():
		child.queue_free()

	var bar := ColorRect.new()
	bar.size = Vector2(max(36.0, msg.length() * 5.5), 10)
	bar.position = Vector2(-bar.size.x * 0.5, -5)
	bar.color = color
	bar.modulate.a = 0.9
	add_child(bar)

	var lbl := Label.new()
	lbl.text = msg
	lbl.position = Vector2(-bar.size.x * 0.5, -16)
	lbl.add_theme_font_size_override("font_size", 8)
	lbl.add_theme_color_override("font_color", color.lightened(0.3))
	add_child(lbl)

	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(bar.size.x, 16)
	shape.shape = rect
	add_child(shape)


func _process(delta: float) -> void:
	position += _velocity * delta
	_age += delta
	if _age > _lifetime:
		queue_free()


func _on_body_entered(body: Node2D) -> void:
	if body.has_method("kill"):
		body.kill(get_meta("death_msg", "Hit by a projectile"))
	queue_free()
