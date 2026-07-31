extends Node
## High-score + settings persistence (autoload "Save").
## user:// maps to IndexedDB on web exports and %APPDATA% on desktop.

const SAVE_PATH := "user://vibecoder_save.cfg"
const SECTION := "game"

var _best := 0
var _muted := false
var _loaded := false


func _ready() -> void:
	_load()


func _load() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) != OK:
		return
	_best = int(cfg.get_value(SECTION, "best_score", 0))
	_muted = bool(cfg.get_value(SECTION, "muted", false))
	_loaded = true


func get_best() -> int:
	if not _loaded:
		_load()
	return _best


## Returns true when score is a new personal best.
func submit_score(score: int) -> bool:
	if not _loaded:
		_load()
	if score > _best:
		_best = score
		_save()
		return true
	return false


func is_muted() -> bool:
	return _muted


func set_muted(muted: bool) -> void:
	_muted = muted
	_save()


func _save() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value(SECTION, "best_score", _best)
	cfg.set_value(SECTION, "muted", _muted)
	cfg.save(SAVE_PATH)
