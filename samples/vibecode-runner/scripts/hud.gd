extends CanvasLayer

@onready var score_label: Label = $Margin/VBox/Score
@onready var dist_label: Label = $Margin/VBox/Distance
@onready var boss_banner: Label = $Margin/VBox/BossBanner


func set_score(vibe: int, meters: int, boss_text: String = "") -> void:
	score_label.text = "vibe score: %d" % vibe
	dist_label.text = "LOC shipped: %d" % meters
	if boss_banner:
		boss_banner.visible = not boss_text.is_empty()
		if boss_banner.visible:
			boss_banner.text = boss_text
