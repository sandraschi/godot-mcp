extends CanvasLayer

signal restart_requested

@onready var title: Label = $Panel/Title
@onready var stats: Label = $Panel/Stats
@onready var hint: Label = $Panel/Hint


func show_result(vibe: int, loc: int, reason: String) -> void:
	show()
	title.text = reason
	stats.text = "vibe score: %d  ·  LOC shipped: %d" % [vibe, loc]
	hint.text = "SPACE — ship another build"


func _process(_delta: float) -> void:
	if visible and Input.is_action_just_pressed("start"):
		restart_requested.emit()
		hide()
