extends CharacterBody2D

const GRAVITY := 980.0
const JUMP_VELOCITY := -340.0
const RUN_SPEED := 200.0
const FLOOR_Y := 300.0

signal died(reason: String)

@onready var sprite_root: Node2D = $Visual
@onready var trail: Line2D = $Trail

var _bob_time := 0.0
var _alive := true


func _ready() -> void:
	position.y = FLOOR_Y
	trail.width = 3.0
	trail.default_color = Color(0.45, 0.85, 1.0, 0.35)


func reset_runner() -> void:
	_alive = true
	position = Vector2(96, FLOOR_Y)
	velocity = Vector2.ZERO
	trail.clear_points()
	show()


func kill(reason: String) -> void:
	if not _alive:
		return
	_alive = false
	velocity = Vector2.ZERO
	died.emit(reason)


func _physics_process(delta: float) -> void:
	if not _alive:
		return

	velocity.y += GRAVITY * delta
	velocity.x = RUN_SPEED

	if is_on_floor() and Input.is_action_just_pressed("jump"):
		velocity.y = JUMP_VELOCITY
		_bob_time = 0.0

	move_and_slide()

	for i in get_slide_collision_count():
		var col := get_slide_collision(i)
		var collider = col.get_collider()
		if collider is StaticBody2D and collider.get_meta("kind", "") == "ide":
			kill("Tripped on %s" % collider.get_meta("ide_name", "an IDE"))

	if global_position.y > FLOOR_Y + 120:
		kill("Fell into /dev/null")

	_bob_time += delta
	if sprite_root:
		sprite_root.position.y = sin(_bob_time * 14.0) * 2.0

	_trail_tick()


func _trail_tick() -> void:
	trail.add_point(global_position + Vector2(-8, -18))
	if trail.get_point_count() > 14:
		trail.remove_point(0)
