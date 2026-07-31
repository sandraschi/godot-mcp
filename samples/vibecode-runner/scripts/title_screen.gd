extends CanvasLayer
## Title screen — branding, best score, controls, blinking prompt.

signal start_requested

const COL_GOOD := Color("#39ff88")
const COL_DIM := Color(0.45, 0.6, 0.52)

var _prompt_label: Label


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_build_ui()
	var tween := create_tween().set_loops()
	tween.tween_property(_prompt_label, "modulate:a", 0.1, 0.55)
	tween.tween_property(_prompt_label, "modulate:a", 1.0, 0.55)


func _process(_delta: float) -> void:
	if visible and Input.is_action_just_pressed("start"):
		Audio.play(&"click", -4.0)
		start_requested.emit()


func _build_ui() -> void:
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(root)

	var title := Label.new()
	title.text = "VIBECODER\nRUNNER"
	title.set_anchors_preset(Control.PRESET_CENTER)
	title.position = Vector2(-420, -300)
	title.size = Vector2(840, 160)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 64)
	title.add_theme_color_override("font_color", COL_GOOD)
	root.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "ship the feature. survive the AI underworld."
	subtitle.set_anchors_preset(Control.PRESET_CENTER)
	subtitle.position = Vector2(-400, -140)
	subtitle.size = Vector2(800, 30)
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.add_theme_font_size_override("font_size", 18)
	subtitle.add_theme_color_override("font_color", COL_DIM)
	root.add_child(subtitle)

	var best := Label.new()
	best.text = "best: %d LOC" % Save.get_best()
	best.set_anchors_preset(Control.PRESET_CENTER)
	best.position = Vector2(-200, -80)
	best.size = Vector2(400, 30)
	best.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	best.add_theme_font_size_override("font_size", 16)
	best.add_theme_color_override("font_color", Color("#ffb03a"))
	root.add_child(best)

	var controls := Label.new()
	controls.text = (
		"SPACE / W / ↑   jump\n"
		+ "SHIFT          SHIP IT! (clear the screen, 3x)\n"
		+ "ESC            pause\n"
		+ "M              mute"
	)
	controls.set_anchors_preset(Control.PRESET_CENTER)
	controls.position = Vector2(-200, 40)
	controls.size = Vector2(400, 130)
	controls.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	controls.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	controls.add_theme_font_size_override("font_size", 17)
	controls.add_theme_color_override("font_color", Color(0.75, 0.9, 0.8))
	root.add_child(controls)

	var hint := Label.new()
	hint.text = (
		"THE DATACENTER heats the planet — keep CARBON under 100%.\n"
		+ "The VC visits when you're hot. The Hallucinator lies."
	)
	hint.set_anchors_preset(Control.PRESET_CENTER)
	hint.position = Vector2(-350, 200)
	hint.size = Vector2(700, 40)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint.add_theme_font_size_override("font_size", 13)
	hint.add_theme_color_override("font_color", COL_DIM)
	root.add_child(hint)

	_prompt_label = Label.new()
	_prompt_label.text = "> PRESS SPACE TO START"
	_prompt_label.set_anchors_preset(Control.PRESET_CENTER)
	_prompt_label.position = Vector2(-300, 280)
	_prompt_label.size = Vector2(600, 40)
	_prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_prompt_label.add_theme_font_size_override("font_size", 22)
	_prompt_label.add_theme_color_override("font_color", COL_GOOD)
	root.add_child(_prompt_label)

	var footer := Label.new()
	footer.text = "a godot-mcp sample — 100% procedural (no art assets)"
	footer.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	footer.position = Vector2(-300, -30)
	footer.size = Vector2(600, 20)
	footer.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	footer.add_theme_font_size_override("font_size", 11)
	footer.add_theme_color_override("font_color", COL_DIM)
	root.add_child(footer)
