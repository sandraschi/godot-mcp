extends Node2D
## Scanline CRT overlay — drawn once, screen-fixed (CanvasLayer child).


func _draw() -> void:
	for y in range(0, 720, 3):
		draw_line(Vector2(0, y), Vector2(1280, y), Color(0, 0, 0, 0.13))
