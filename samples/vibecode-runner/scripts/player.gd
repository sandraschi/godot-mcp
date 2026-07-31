extends CharacterBody2D
## The Vibecoder — auto-runs right, jumps with coyote time + jump buffer,
## squash & stretch, dust, trail. Procedural visuals, zero art assets.

signal died(reason: String)

const RUN_SPEED := 240.0
const GRAVITY := 1500.0
const JUMP_VELOCITY := -560.0
const COYOTE_TIME := 0.1
const JUMP_BUFFER := 0.12
const FLOOR_Y := 504.0
const HALF_HEIGHT := 17.0

const COL_BODY := Color("#0b1410")
const COL_EDGE := Color("#2e7d54")
const COL_SCREEN := Color("#39ff88")
const COL_HEADPHONE := Color("#ffb03a")

var _alive := true
var _jump_buffered := false
var _coyote := 0.0
var _stun_timer := 0.0
var _hack_jump_timer := 0.0
var _bob_time := 0.0
var _blink_time := 0.0
var _on_ground := false
var _squash := Vector2.ONE
var _squash_speed := 6.0

@onready var visual: Node2D = $Visual
@onready var trail: Line2D = $Trail
@onready var dust: CPUParticles2D = $Dust


func _ready() -> void:
	position.y = FLOOR_Y
	trail.width = 3.0
	trail.default_color = Color(0.45, 0.85, 1.0, 0.35)
	trail.z_index = 5
	_build_visual()


func reset_runner() -> void:
	_alive = true
	_stun_timer = 0.0
	_hack_jump_timer = 0.0
	position = Vector2(96, FLOOR_Y)
	velocity = Vector2.ZERO
	visual.scale = Vector2.ONE
	visual.rotation = 0.0
	trail.clear_points()
	show()


func is_stunned() -> bool:
	return _stun_timer > 0.0


func is_jump_offline() -> bool:
	return _hack_jump_timer > 0.0


func kill(reason: String) -> void:
	if not _alive:
		return
	_alive = false
	velocity = Vector2.ZERO
	died.emit(reason)


func stun(duration: float) -> void:
	_stun_timer = max(_stun_timer, duration)
	Audio.play(&"stun", -4.0)


func hack_jump(duration: float) -> void:
	_hack_jump_timer = max(_hack_jump_timer, duration)


func _physics_process(delta: float) -> void:
	if not _alive:
		return

	_stun_timer = max(_stun_timer - delta, 0.0)
	_hack_jump_timer = max(_hack_jump_timer - delta, 0.0)

	var speed := RUN_SPEED * (0.55 if _stun_timer > 0.0 else 1.0)
	velocity.x = speed
	velocity.y += GRAVITY * delta

	var grounded := is_on_floor()
	if grounded and not _on_ground and velocity.y >= 0.0:
		_landed()
	_on_ground = grounded
	if grounded:
		_coyote = COYOTE_TIME
	else:
		_coyote = max(_coyote - delta, 0.0)

	if Input.is_action_just_pressed("jump"):
		_jump_buffered = true
	if _jump_buffered:
		_jump_buffered = false
		_try_jump()

	if Input.is_action_just_released("jump") and velocity.y < -240.0:
		velocity.y = -240.0

	move_and_slide()

	if _on_ground:
		_coyote = COYOTE_TIME

	for i in get_slide_collision_count():
		var collider := get_slide_collision(i).get_collider()
		if collider is StaticBody2D and collider.get_meta("kind", "") == "ide":
			kill("Tripped on %s" % collider.get_meta("ide_name", "an IDE"))

	if global_position.y > 920.0:
		kill("Fell into /dev/null")

	_bob_time += delta
	_blink_time += delta
	_tick_visual(delta)
	_tick_trail()


func _try_jump() -> void:
	if not _on_ground and _coyote <= 0.0:
		_jump_buffered = true
		return
	if _stun_timer > 0.0 or _hack_jump_timer > 0.0:
		return
	velocity.y = JUMP_VELOCITY
	_coyote = 0.0
	_squash = Vector2(1.18, 0.78)
	Audio.play(&"jump", -6.0)
	_burst_dust(6)


func _landed() -> void:
	_squash = Vector2(0.78, 1.18)
	Audio.play(&"land", -10.0)
	_burst_dust(8)


func _tick_visual(delta: float) -> void:
	_squash = _squash.lerp(Vector2.ONE, delta * _squash_speed)
	visual.scale = _squash

	var air_tilt: float = clamp(velocity.y / 900.0, -0.18, 0.22)
	visual.rotation = air_tilt * (0.0 if _on_ground else 1.0)

	if _blink_time > 2.2:
		_blink_time = 0.0
		var face: Label = visual.get_node_or_null("Face")
		if face:
			face.text = "_"
			await get_tree().create_timer(0.09).timeout
			if is_instance_valid(face):
				face.text = ">_"


func _tick_trail() -> void:
	if _on_ground:
		trail.clear_points()
		return
	trail.add_point(global_position + Vector2(-10, -20))
	if trail.get_point_count() > 16:
		trail.remove_point(0)


func _burst_dust(count: int) -> void:
	if dust:
		dust.amount = count
		dust.restart()
		dust.emitting = true


func _build_visual() -> void:
	var root := Node2D.new()
	root.name = "Visual"

	var legs := _rect(root, Vector2(16, 6), Vector2(-4, 22), Color("#1a2b22"))
	legs.rotation = 0.0

	var body := _rect(root, Vector2(22, 26), Vector2(0, 4), COL_BODY)
	body.position.y = 6
	_rect(root, Vector2(22, 2), Vector2(0, 6), COL_EDGE)

	var head := _rect(root, Vector2(16, 14), Vector2(0, -12), COL_BODY)
	_rect(root, Vector2(16, 2), Vector2(0, -12), COL_EDGE)

	var face := Label.new()
	face.name = "Face"
	face.text = ">_"
	face.position = Vector2(-6, -18)
	face.add_theme_font_size_override("font_size", 9)
	face.add_theme_color_override("font_color", COL_SCREEN)
	root.add_child(face)

	# Headphones: arc + pads
	var band := Line2D.new()
	band.width = 2.5
	band.default_color = COL_HEADPHONE
	for i in 14:
		var a := PI + PI * float(i) / 13.0
		band.add_point(Vector2(cos(a) * 9.0, -18.0 + sin(a) * 7.0))
	root.add_child(band)
	_rect(root, Vector2(3, 5), Vector2(-10, -11), COL_HEADPHONE)
	_rect(root, Vector2(3, 5), Vector2(10, -11), COL_HEADPHONE)

	# Laptop in front
	var laptop := _rect(root, Vector2(12, 8), Vector2(17, 18), Color("#101a14"))
	var screen := ColorRect.new()
	screen.size = Vector2(8, 4)
	screen.position = Vector2(17 - 6 + 2, 18 - 4 + 1)
	screen.color = COL_SCREEN
	root.add_child(screen)

	add_child(root)


func _rect(parent: Node2D, size: Vector2, center: Vector2, color: Color) -> ColorRect:
	var rect := ColorRect.new()
	rect.size = size
	rect.position = center - size * 0.5
	rect.color = color
	parent.add_child(rect)
	return rect
