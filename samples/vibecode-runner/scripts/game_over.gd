extends CanvasLayer
## Game over — death reason, stats, best score, restart.

signal restart_requested

const COL_GOOD := Color("#39ff88")
const COL_BAD := Color("#ff5555")
const COL_WARN := Color("#ffb03a")

var _reason_label: Label
var _stats_label: Label


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_build_ui()


func show_result(
	loc: int, distance: int, reason: String, best: int, new_best: bool, best_before: int,
) -> void:
	show()
	_reason_label.text = reason
	_reason_label.add_theme_color_override("font_color", COL_BAD if not new_best else COL_WARN)
	var stats_text := "LOC shipped: %d\ncommits: %d" % [loc, distance]
	if new_best:
		stats_text += "\n\n★ NEW PERSONAL BEST! (%d → %d) ★" % [
			best_before, best,
		]
	else:
		stats_text += "\nbest: %d" % best
	_stats_label.text = stats_text
	if new_best:
		Audio.play(&"powerup", -2.0)


func _process(_delta: float) -> void:
	if visible and Input.is_action_just_pressed("start"):
		restart_requested.emit()
		hide()


func _build_ui() -> void:
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(root)

	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.7)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(dim)

	var title := Label.new()
	title.text = "GAME OVER"
	title.set_anchors_preset(Control.PRESET_CENTER)
	title.position = Vector2(-300, -260)
	title.size = Vector2(600, 60)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 44)
	title.add_theme_color_override("font_color", COL_BAD)
	root.add_child(title)

	_reason_label = Label.new()
	_reason_label.set_anchors_preset(Control.PRESET_CENTER)
	_reason_label.position = Vector2(-400, -180)
	_reason_label.size = Vector2(800, 50)
	_reason_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_reason_label.add_theme_font_size_override("font_size", 20)
	root.add_child(_reason_label)

	_stats_label = Label.new()
	_stats_label.set_anchors_preset(Control.PRESET_CENTER)
	_stats_label.position = Vector2(-300, -60)
	_stats_label.size = Vector2(600, 160)
	_stats_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_stats_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_stats_label.add_theme_font_size_override("font_size", 20)
	_stats_label.add_theme_color_override("font_color", COL_GOOD)
	root.add_child(_stats_label)

	var hint := Label.new()
	hint.text = "> PRESS SPACE — ship another build"
	hint.set_anchors_preset(Control.PRESET_CENTER)
	hint.position = Vector2(-300, 180)
	hint.size = Vector2(600, 40)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint.add_theme_font_size_override("font_size", 20)
	hint.add_theme_color_override("font_color", COL_GOOD)
	root.add_child(hint)
