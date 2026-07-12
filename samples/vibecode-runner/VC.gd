extends Area2D
## The VC — appears periodically, asks valuation. Score halved if not growing.
var lifetime: float = 8.0

func _ready():
	var main = get_node("/root/MainScene")
	if not main: return
	if not main.can_vc_visit():
		queue_free()
		return
	main.vc_visited()
	position.y = 150
	$Question.show()
	$Timer.start(3.0)
	$Timer.timeout.connect(_ask)

func _ask():
	var main = get_node("/root/MainScene")
	if not main or main.game_over:
		return
	var current = main.score
	var asked = current * 0.5
	main.add_score(-asked)
	main.score = max(main.score, 0)
	$Label.text = "TOOK " + str(asked) + " equity!"
	$Label.modulate = Color(1, 0.2, 0.2)
	$Question.hide()
	$Label.show()
	await get_tree().create_timer(2.0).timeout
	queue_free()

func _process(delta):
	lifetime -= delta
	if lifetime <= 0:
		queue_free()
