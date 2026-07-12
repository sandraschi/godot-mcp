extends Node2D
## Vibecoder Runner — main game controller.
## AI-themed enemies from the tech underworld.

var score: float = 0.0
var multiplier: float = 1.0
var mult_timer: float = 0.0
var ship_it_charges: int = 3
var carbon_meter: float = 0.0
var game_over: bool = false
var stun_timer: float = 0.0
var vc_cooldown: float = 0.0

var enemy_types := ["Hallucinator", "PromptInjector", "Tokenmaxxer",
	"ContextOverflow", "ClaudeDesktop", "Techbro",
	"LegacyCode", "VC", "Meeting"]
var datacenter: Node2D

@onready var player: CharacterBody2D = $Player
@onready var score_label: Label = $UI/ScoreLabel
@onready var mult_label: Label = $UI/MultLabel
@onready var carbon_bar: ColorRect = $UI/CarbonBar/Fill
@onready var ship_it_btn: Button = $UI/ShipItButton
@onready var stun_label: Label = $UI/StunLabel
@onready var game_over_label: Label = $UI/GameOverLabel
@onready var enemy_container: Node2D = $Enemies
@onready var spawn_timer: Timer = $SpawnTimer

func _ready():
	spawn_timer.timeout.connect(_spawn_enemy)
	spawn_timer.start(1.5)
	datacenter = preload("res://TheDatacenter.tscn").instantiate()
	add_child(datacenter)

func _process(delta):
	if game_over: return
	score += delta * 60 * multiplier
	score_label.text = "LOC: " + str(int(score))
	if stun_timer > 0:
		stun_timer -= delta
		stun_label.show()
		stun_label.text = "STUNNED " + str(ceil(stun_timer)) + "s"
		return
	stun_label.hide()

	if mult_timer > 0:
		mult_timer -= delta
		if mult_timer <= 0:
			multiplier = 1.0
	carbon_bar.size.x = clamp(carbon_meter * 2.0, 0, 200)
	if carbon_meter >= 100:
		game_over = true
		game_over_label.text = "EPA FINED YOU\ninto oblivion.\nCarbon: " + str(int(carbon_meter)) + "%"
		game_over_label.show()

	vc_cooldown -= delta

func _spawn_enemy():
	if game_over: return
	var type = enemy_types[randi() % enemy_types.size()]
	var enemy: Area2D = null
	match type:
		"Hallucinator": enemy = preload("res://Hallucinator.tscn").instantiate()
		"PromptInjector": enemy = preload("res://PromptInjector.tscn").instantiate()
		"Tokenmaxxer": enemy = preload("res://Tokenmaxxer.tscn").instantiate()
		"ContextOverflow": enemy = preload("res://ContextOverflow.tscn").instantiate()
		"ClaudeDesktop": enemy = preload("res://ClaudeDesktop.tscn").instantiate()
		"Techbro": enemy = preload("res://Techbro.tscn").instantiate()
		"LegacyCode": enemy = preload("res://LegacyCode.tscn").instantiate()
		"VC": enemy = preload("res://VC.tscn").instantiate()
		"Meeting": enemy = preload("res://Meeting.tscn").instantiate()
	if enemy:
		enemy.position = Vector2(randf_range(80, 944), -60)
		enemy_container.add_child(enemy)

func add_score(amount: float):
	score += amount * multiplier

func activate_multiplier():
	multiplier = 2.0
	mult_timer = 5.0

func add_carbon(amount: float):
	carbon_meter += amount

func ship_it():
	if ship_it_charges <= 0 or game_over: return
	ship_it_charges -= 1
	for c in enemy_container.get_children():
		c.queue_free()
	score += 50
	carbon_meter = max(carbon_meter - 10, 0)

func stun(duration: float):
	stun_timer = max(stun_timer, duration)

func hit_by_enemy():
	game_over = true
	game_over_label.text = "GAME OVER\nLOC: %d\n\n\"We're hiring!\"\n— Techbro 2.0" % score
	game_over_label.show()
	spawn_timer.stop()

func can_vc_visit() -> bool:
	return vc_cooldown <= 0 and score > 100

func vc_visited():
	vc_cooldown = 15.0
