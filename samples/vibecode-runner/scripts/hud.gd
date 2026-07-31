extends CanvasLayer
## HUD — LOC, carbon bar, ship-it button, banners, pause overlay.

signal ship_pressed

const COL_GOOD := Color("#39ff88")
const COL_WARN := Color("#ffb03a")
const COL_BAD := Color("#ff5555")

var _loc_label: Label
var _dist_label: Label
var _carbon_label: Label
var _carbon_fill: ColorRect
var _ship_button: Button
var _mult_label: Label
var _boss_label: Label
var _banner_label: Label
var _stun_label: Label
var _pause_overlay: ColorRect
var _banner_tween: Tween


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_build_ui()
	hide_pause()
	show_stun_hidden()


func set_score(loc: int, distance: float, boss_msg: String = "") -> void:
	_loc_label.text = "LOC: %d" % loc
	_dist_label.text = "distance: %d" % int(distance)
	if boss_msg.is_empty():
		_boss_label.hide()
	else:
		_boss_label.text = boss_msg
		_boss_label.show()


func set_carbon(value: float) -> void:
	var pct := int(value)
	_carbon_label.text = "CARBON %d%%" % pct
	_carbon_fill.size.x = clamp(200.0 * value / 100.0, 0.0, 200.0)
	_carbon_fill.color = COL_GOOD if pct < 60 else (COL_WARN if pct < 85 else COL_BAD)
	_carbon_fill.modulate.a = 0.85


func set_mult(multiplier: float, timer: float) -> void:
	if multiplier > 1.0:
		_mult_label.text = "⚡ %dx ENERGY  %.1fs" % [int(multiplier), timer]
		_mult_label.show()
	else:
		_mult_label.hide()


func set_ship(charges: int) -> void:
	_ship_button.text = "SHIP IT! (%d)  [SHIFT]" % charges
	_ship_button.disabled = charges <= 0


func show_banner(text: String, color: Color, duration: float) -> void:
	if _banner_tween and _banner_tween.is_valid():
		_banner_tween.kill()
	_banner_label.text = text
	_banner_label.add_theme_color_override("font_color", color)
	_banner_label.modulate.a = 1.0
	_banner_label.show()
	_banner_tween = create_tween()
	_banner_tween.tween_interval(duration)
	_banner_tween.tween_property(_banner_label, "modulate:a", 0.0, 0.4)
	_banner_tween.tween_callback(_banner_label.hide)


func show_stun(duration: float) -> void:
	_stun_label.text = "STUNNED %.1fs" % duration
	_stun_label.show()


func show_stun_hidden() -> void:
	_stun_label.hide()


func show_pause() -> void:
	_pause_overlay.show()


func hide_pause() -> void:
	_pause_overlay.hide()


func _build_ui() -> void:
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(root)

	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 18)
	margin.add_theme_constant_override("margin_top", 14)
	root.add_child(margin)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 4)
	margin.add_child(vbox)

	_loc_label = Label.new()
	_loc_label.add_theme_font_size_override("font_size", 30)
	_loc_label.add_theme_color_override("font_color", COL_GOOD)
	vbox.add_child(_loc_label)

	_dist_label = Label.new()
	_dist_label.add_theme_font_size_override("font_size", 13)
	_dist_label.add_theme_color_override("font_color", Color(0.6, 0.75, 0.66))
	vbox.add_child(_dist_label)

	var best := Label.new()
	best.text = "best: %d" % Save.get_best()
	best.add_theme_font_size_override("font_size", 12)
	best.add_theme_color_override("font_color", Color(0.45, 0.6, 0.52))
	vbox.add_child(best)

	# Right column: carbon + ship
	var right := VBoxContainer.new()
	right.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	right.position = Vector2(-220, 14)
	right.add_theme_constant_override("separation", 8)
	root.add_child(right)

	_carbon_label = Label.new()
	_carbon_label.text = "CARBON 0%"
	_carbon_label.add_theme_font_size_override("font_size", 14)
	_carbon_label.add_theme_color_override("font_color", COL_GOOD)
	right.add_child(_carbon_label)

	var bar_bg := ColorRect.new()
	bar_bg.size = Vector2(200, 10)
	bar_bg.color = Color(0.1, 0.14, 0.12)
	right.add_child(bar_bg)
	_carbon_fill = ColorRect.new()
	_carbon_fill.size = Vector2(0, 10)
	_carbon_fill.color = COL_GOOD
	_carbon_fill.modulate.a = 0.85
	bar_bg.add_child(_carbon_fill)

	_ship_button = Button.new()
	_ship_button.text = "SHIP IT! (3)  [SHIFT]"
	_ship_button.pressed.connect(func() -> void: ship_pressed.emit())
	_ship_button.add_theme_color_override("font_color", Color(0.05, 0.1, 0.07))
	right.add_child(_ship_button)

	_mult_label = Label.new()
	_mult_label.text = ""
	_mult_label.add_theme_font_size_override("font_size", 15)
	_mult_label.add_theme_color_override("font_color", COL_WARN)
	right.add_child(_mult_label)
	_mult_label.hide()

	# Boss banner + stun + message center
	_boss_label = Label.new()
	_boss_label.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_boss_label.position = Vector2(-300, 46)
	_boss_label.size = Vector2(600, 30)
	_boss_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_boss_label.add_theme_font_size_override("font_size", 20)
	_boss_label.add_theme_color_override("font_color", COL_BAD)
	root.add_child(_boss_label)
	_boss_label.hide()

	_banner_label = Label.new()
	_banner_label.set_anchors_preset(Control.PRESET_CENTER)
	_banner_label.position = Vector2(-400, 120)
	_banner_label.size = Vector2(800, 40)
	_banner_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner_label.add_theme_font_size_override("font_size", 20)
	root.add_child(_banner_label)
	_banner_label.hide()

	_stun_label = Label.new()
	_stun_label.set_anchors_preset(Control.PRESET_CENTER)
	_stun_label.position = Vector2(-200, 40)
	_stun_label.size = Vector2(400, 30)
	_stun_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_stun_label.add_theme_font_size_override("font_size", 22)
	_stun_label.add_theme_color_override("font_color", Color("#8fb8d9"))
	root.add_child(_stun_label)
	_stun_label.hide()

	var hint := Label.new()
	hint.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	hint.position = Vector2(-330, -22)
	hint.size = Vector2(320, 18)
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	hint.text = "SPACE jump · SHIFT ship it · M mute · ESC pause"
	hint.add_theme_font_size_override("font_size", 11)
	hint.add_theme_color_override("font_color", Color(0.4, 0.55, 0.47))
	root.add_child(hint)

	# Pause overlay
	_pause_overlay = ColorRect.new()
	_pause_overlay.color = Color(0, 0, 0, 0.55)
	_pause_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(_pause_overlay)
	var pause_label := Label.new()
	pause_label.text = "PAUSED\n\nESC — resume\nM — mute\nQ — quit"
	pause_label.set_anchors_preset(Control.PRESET_CENTER)
	pause_label.position = Vector2(-200, -90)
	pause_label.size = Vector2(400, 180)
	pause_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pause_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	pause_label.add_theme_font_size_override("font_size", 24)
	pause_label.add_theme_color_override("font_color", COL_GOOD)
	_pause_overlay.add_child(pause_label)
	_pause_overlay.hide()
