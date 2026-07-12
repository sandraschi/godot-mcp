extends Node2D
## The Datacenter — persistent background hazard.
## Carbon meter rises over time. Fan blast pushes player. Water pipes burst.

var fan_timer: float = 0.0
var pipe_timer: float = 0.0
var hum: float = 0.0

func _ready():
	fan_timer = randf_range(5, 10)
	pipe_timer = randf_range(8, 15)

func _process(delta):
	hum += delta * 0.5
	var main = get_node("/root/MainScene")
	if not main or main.game_over: return

	main.add_carbon(delta * 1.5)  # baseline heat

	fan_timer -= delta
	if fan_timer <= 0:
		fan_timer = randf_range(6, 12)
		_fan_blast()

	pipe_timer -= delta
	if pipe_timer <= 0:
		pipe_timer = randf_range(10, 20)
		_burst_pipe()

func _fan_blast():
	var player = get_node("/root/MainScene/Player")
	if not player: return
	var dir = -1 if player.position.x < 512 else 1
	player.position.x += dir * 60  # push toward edge
	var msg = get_node("/root/MainScene/UI/HackMessage")
	if msg:
		msg.text = "FAN BLAST!"
		msg.show()
		await get_tree().create_timer(1.0).timeout
		msg.hide()

func _burst_pipe():
	var pipe = ColorRect.new()
	pipe.size = Vector2(8, randf_range(100, 300))
	pipe.color = Color(0.2, 0.5, 0.8, 0.7)
	pipe.position = Vector2(randf_range(50, 974), 600 - pipe.size.y)
	add_child(pipe)
	var t = create_tween()
	t.tween_property(pipe, "position:y", 600, 2.0)
	t.tween_callback(pipe.queue_free)
