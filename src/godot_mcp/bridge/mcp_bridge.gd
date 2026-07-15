# Godot-MCP Bridge — WebSocket server running inside Godot 4.0+
# Place at res://mcp_bridge.gd and add as Autoload in project.godot
extends Node

var _server := TCPServer.new()
var _peer: StreamPeerTCP = null
var _port := 9080
var _running := false

# Scene tree access
var _stl_mesh_parent: Node3D = null
var _particle_system: GPUParticles3D = null
var _camera: Camera3D = null

# Profiler ring buffer (last 300 frames for spike detection)
var _profile_history: Array = []
const _PROFILE_HISTORY_MAX := 300
var _profile_enabled := false

# Playtest state machine (deterministic step control)
enum PlaytestState { RUNNING, FROZEN, STEPPING }
var _playtest_state := PlaytestState.RUNNING
var _step_pending := 0
var _step_until_request_id := ""
var _step_until_condition := ""
var _step_until_counter := 0
var _step_until_timeout := 0

func _ready():
	print("[MCP-Bridge] Initializing Godot MCP bridge v0.1.0...")
	start_server(_port)

func start_server(port: int = 9080) -> bool:
	_port = port
	var err := _server.listen(port)
	if err == OK:
		_running = true
		print("[MCP-Bridge] WebSocket server listening on port %d" % port)
		return true
	else:
		printerr("[MCP-Bridge] Failed to listen on port %d: %d" % [port, err])
		return false

func stop_server():
	_running = false
	_server.stop()
	if _peer:
		_peer = null
	print("[MCP-Bridge] Server stopped")

func _process(_delta: float):
	if not _running:
		return

	# Accept new connections
	if not _peer or _peer.get_status() == StreamPeerTCP.STATUS_NONE:
		_peer = _server.take_connection()
		if _peer:
			print("[MCP-Bridge] Client connected")
			# Send handshake
			_send_json({"type": "handshake", "version": "0.1.0", "godot_version": Engine.get_version_info(), "ready": true})

	# Process incoming data (always runs — bridge is an Autoload)
	if _peer and _peer.get_status() == StreamPeerTCP.STATUS_CONNECTED:
		var available := _peer.get_available_bytes()
		if available > 0:
			var data := _peer.get_string(available)
			if data:
				_handle_message(data)

	# Handle disconnection
	if _peer and _peer.get_status() == StreamPeerTCP.STATUS_ERROR:
		print("[MCP-Bridge] Client disconnected")
		_peer = null

	# ─── Profiler auto-sampling (if enabled) ──────────────────────────────
	if _profile_enabled:
		var snap := _collect_profile_snapshot()
		_profile_history.append(snap)
		if _profile_history.size() > _PROFILE_HISTORY_MAX:
			_profile_history.pop_front()

	# ─── Deterministic stepping logic ─────────────────────────────────────
	if _playtest_state == PlaytestState.STEPPING:
		Engine.time_scale = 1.0  # this frame advances in real time
		_step_pending -= 1
		_step_until_counter += 1

		# Evaluate step-until condition if active
		if _step_until_condition != "":
			var expr := Expression.new()
			var parse_err := expr.parse(_step_until_condition)
			if parse_err == OK:
				var met = expr.execute([], get_tree().get_root(), true)
				if met == true:
					_playtest_state = PlaytestState.FROZEN
					Engine.time_scale = 0
					_send_response(_step_until_request_id, {
						"condition_met": true,
						"condition": _step_until_condition,
						"frames_elapsed": _step_until_counter,
					})
					_step_until_condition = ""
					_step_until_request_id = ""
					return
			else:
					printerr("[MCP-Bridge] step_until expression parse error: %s" % parse_err)

		# Timeout check
		if _step_until_timeout > 0 and _step_until_counter >= _step_until_timeout:
			_playtest_state = PlaytestState.FROZEN
			Engine.time_scale = 0
			_send_response(_step_until_request_id, {
				"condition_met": false,
				"condition": _step_until_condition,
				"frames_elapsed": _step_until_counter,
				"timed_out": true,
			})
			_step_until_condition = ""
			_step_until_request_id = ""
			return

		# Plain step count exhausted — re-freeze
		if _step_pending <= 0 and _step_until_condition == "":
			_playtest_state = PlaytestState.FROZEN
			Engine.time_scale = 0

	elif _playtest_state == PlaytestState.FROZEN:
		Engine.time_scale = 0

func _handle_message(raw: String):
	var json := JSON.new()
	var err := json.parse(raw)
	if err != OK:
		_send_error("Invalid JSON: %s" % json.get_error_message())
		return

	var msg: Dictionary = json.get_data()
	if typeof(msg) != TYPE_DICTIONARY:
		_send_error("Expected JSON object")
		return

	var action: String = msg.get("action", "")
	var params: Dictionary = msg.get("params", {})
	var request_id: String = msg.get("request_id", "")

	print("[MCP-Bridge] Action: %s" % action)

	match action:
		"status":
			_cmd_status(request_id)
		"import_stl":
			_cmd_import_stl(request_id, params)
		"import_vrm":
			_cmd_import_vrm(request_id, params)
		"import_glb":
			_cmd_import_glb(request_id, params)
		"import_obj":
			_cmd_import_obj(request_id, params)
		"load_velocity_field":
			_cmd_load_velocity(request_id, params)
		"spawn_particles":
			_cmd_spawn_particles(request_id, params)
		"animate_streamlines":
			_cmd_animate_streamlines(request_id, params)
		"create_camera":
			_cmd_create_camera(request_id, params)
		"add_light":
			_cmd_add_light(request_id, params)
		"set_material":
			_cmd_set_material(request_id, params)
		"export_web":
			_cmd_export_web(request_id, params)
		"read_scene_tree":
			_cmd_read_scene_tree(request_id)
		"set_config":
			_cmd_set_config(request_id, params)
		"headless_verify":
			_cmd_headless_verify(request_id, params)
		"add_node":
			_cmd_add_node(request_id, params)
		"remove_node":
			_cmd_remove_node(request_id, params)
		"modify_node":
			_cmd_modify_node(request_id, params)
		"save_scene":
			_cmd_save_scene(request_id, params)
		"play_animation":
			_cmd_play_animation(request_id, params)
		"capture_viewport":
			_cmd_capture_viewport(request_id, params)
		"simulate_input":
			_cmd_simulate_input(request_id, params)
		"generate_procedural_texture":
			_cmd_generate_procedural_texture(request_id, params)
		"read_node":
			_cmd_read_node(request_id, params)
		"inspect_resource":
			_cmd_inspect_resource(request_id, params)
		"tilemap_read":
			_cmd_tilemap_read(request_id, params)
		"tilemap_edit":
			_cmd_tilemap_edit(request_id, params)
		"animation_edit":
			_cmd_animation_edit(request_id, params)
		"profile_snapshot":
			_cmd_profile_snapshot(request_id)
		"profile_enable":
			_cmd_profile_enable(request_id, params)
		"profile_history":
			_cmd_profile_history(request_id)
		"validate_meshes":
			_cmd_validate_meshes(request_id)
		"import_splat":
			_cmd_import_splat(request_id, params)
		"state_digest":
			_cmd_state_digest(request_id, params)
		"state_watch_add":
			_cmd_state_watch_add(request_id, params)
		"state_watch_remove":
			_cmd_state_watch_remove(request_id, params)
		"game_time_freeze":
			_cmd_game_time_freeze(request_id)
		"game_time_unfreeze":
			_cmd_game_time_unfreeze(request_id)
		"game_time_step":
			_cmd_game_time_step(request_id, params)
		"game_time_step_until":
			_cmd_game_time_step_until(request_id, params)
		_:
			_send_error("Unknown action: %s" % action, request_id)

# ─── Command Handlers ────────────────────────────────────────────────

func _cmd_status(request_id: String):
	var children: Array = []
	var root := get_tree().get_root() if get_tree() else null
	if root:
		for child in root.get_children():
			children.append({"name": child.name, "type": child.get_class()})

	_send_response(request_id, {
		"godot_version": "%d.%d.%d" % [Engine.get_version_info().major, Engine.get_version_info().minor, Engine.get_version_info().patch],
		"node_count": children.size(),
		"root_nodes": children,
		"fps": Engine.get_frames_per_second(),
	})

func _cmd_import_stl(request_id: String, params: Dictionary):
	var path: String = params.get("path", "")
	var mesh_name: String = params.get("name", "STL_Mesh")

	if path.is_empty():
		_send_error("Missing path parameter", request_id)
		return

	if not FileAccess.file_exists(path):
		_send_error("File not found: %s" % path, request_id)
		return

	# Create mesh instance
	var mesh_instance := MeshInstance3D.new()
	mesh_instance.name = mesh_name

	# Load STL (Godot 4 supports STL via ResourceLoader in 4.x)
	var mesh: ArrayMesh = _load_stl_mesh(path)
	if not mesh:
		_send_error("Failed to load STL mesh", request_id)
		return

	mesh_instance.mesh = mesh

	# Add to scene
	var parent := _get_or_create_container("STL_Imports")
	parent.add_child(mesh_instance)

	# Center and scale
	var aabb := mesh.get_aabb()
	var scale_vec: float = params.get("scale", 1.0)
	mesh_instance.scale = Vector3(scale_vec, scale_vec, scale_vec)

	var pos: Dictionary = params.get("position", {"x": 0, "y": 0, "z": 0})
	mesh_instance.position = Vector3(
		pos.get("x", 0.0),
		pos.get("y", 0.0),
		pos.get("z", 0.0)
	)

	_send_response(request_id, {
		"imported": true,
		"name": mesh_instance.name,
		"vertices": mesh.get_surface_count() > 0 if mesh else 0,
		"aabb": {"size_x": aabb.size.x, "size_y": aabb.size.y, "size_z": aabb.size.z},
	})

func _cmd_import_vrm(request_id: String, params: Dictionary):
	var vrm_path: String = params.get("path", "")
	var import_name: String = params.get("name", "VRM_Import")

	if vrm_path.is_empty():
		_send_error("Missing path parameter", request_id)
		return

	if not FileAccess.file_exists(vrm_path):
		_send_error("File not found: %s" % vrm_path, request_id)
		return

	# Copy VRM into project models/ directory so the V-Sekai addon processes it
	var project_root := ProjectSettings.globalize_path("res://")
	var models_dir := project_root.path_join("models")
	DirAccess.make_dir_recursive_absolute(models_dir)
	var dest := models_dir.path_join(import_name + ".vrm")
	DirAccess.copy_absolute(vrm_path, dest)

	# Load via ResourceLoader — the V-Sekai addon handles VRM→scene conversion
	var scene := ResourceLoader.load("res://models/" + import_name + ".vrm")
	if not scene:
		_send_error("VRM addon failed to import: resource returned null", request_id)
		return

	var instance := scene.instantiate()
	if not instance:
		_send_error("Failed to instantiate VRM scene", request_id)
		return

	instance.name = import_name
	var parent := _get_or_create_container("VRM_Imports")
	parent.add_child(instance)

	_send_response(request_id, {
		"imported": true,
		"name": import_name,
		"vrm_path": dest,
	})


func _cmd_import_glb(request_id: String, params: Dictionary):
	var path: String = params.get("path", "")
	var import_name: String = params.get("name", "GLB_Import")

	if path.is_empty():
		_send_error("Missing path parameter", request_id)
		return

	if not FileAccess.file_exists(path):
		_send_error("File not found: %s" % path, request_id)
		return

	# Godot 4.0+ native GLTF import via GLTFDocument
	var gltf_doc := GLTFDocument.new()
	var gltf_state := GLTFState.new()
	var err := gltf_doc.append_from_file(path, gltf_state, 0)
	if err != OK:
		_send_error("Failed to import GLB/GLTF: error %d" % err, request_id)
		return

	var imported_scene := gltf_doc.generate_scene(gltf_state)
	if not imported_scene:
		_send_error("GLTFDocument.generate_scene returned null", request_id)
		return

	imported_scene.name = import_name

	var scale_vec: float = params.get("scale", 1.0)
	var pos: Dictionary = params.get("position", {"x": 0, "y": 0, "z": 0})
	imported_scene.scale = Vector3(scale_vec, scale_vec, scale_vec)
	imported_scene.position = Vector3(
		pos.get("x", 0.0), pos.get("y", 0.0), pos.get("z", 0.0)
	)

	var parent := _get_or_create_container("GLB_Imports")
	parent.add_child(imported_scene)

	# Count total nodes and meshes in the imported scene
	var node_count := _count_nodes(imported_scene)
	var mesh_count := _count_meshes(imported_scene)

	_send_response(request_id, {
		"imported": true,
		"name": imported_scene.name,
		"total_nodes": node_count,
		"mesh_count": mesh_count,
	})

func _count_meshes(node: Node) -> int:
	var count := 0
	if node is MeshInstance3D:
		count += 1
	for child in node.get_children():
		count += _count_meshes(child)
	return count

func _cmd_load_velocity(request_id: String, params: Dictionary):
	var csv_path: String = params.get("csv_path", "")
	var field_name: String = params.get("name", "VelocityField")

	if csv_path.is_empty():
		_send_error("Missing csv_path parameter", request_id)
		return

	var file := FileAccess.open(csv_path, FileAccess.READ)
	if not file:
		_send_error("Cannot read CSV file", request_id)
		return

	var header := file.get_csv_line()
	var points := PackedVector3Array()
	var vectors := PackedVector3Array()
	var bbox_min := Vector3(1e30, 1e30, 1e30)
	var bbox_max := Vector3(-1e30, -1e30, -1e30)

	while not file.eof_reached():
		var line := file.get_csv_line()
		if line.size() < 6:
			continue
		var px := float(line[0])
		var py := float(line[1])
		var pz := float(line[2])
		var vx := float(line[3])
		var vy := float(line[4])
		var vz := float(line[5])

		points.append(Vector3(px, py, pz))
		vectors.append(Vector3(vx, vy, vz))
		bbox_min = bbox_min.min(Vector3(px, py, pz))
		bbox_max = bbox_max.max(Vector3(px, py, pz))

	file.close()

	# Store as scene metadata
	var data_node := Node3D.new()
	data_node.name = field_name
	data_node.set_meta("velocity_points", points)
	data_node.set_meta("velocity_vectors", vectors)
	data_node.set_meta("bbox_min", bbox_min)
	data_node.set_meta("bbox_max", bbox_max)
	data_node.set_meta("point_count", points.size())

	var parent := _get_or_create_container("Velocity_Fields")
	parent.add_child(data_node)

	_send_response(request_id, {
		"loaded": true,
		"name": field_name,
		"point_count": points.size(),
		"bbox": {"min_x": bbox_min.x, "min_y": bbox_min.y, "min_z": bbox_min.z,
		          "max_x": bbox_max.x, "max_y": bbox_max.y, "max_z": bbox_max.z},
	})

func _cmd_spawn_particles(request_id: String, params: Dictionary):
	var count: int = params.get("count", 1000)
	var color_hex: String = params.get("color", "#00aaff")
	var spread_x: float = params.get("spread_x", 0.0)
	var spread_y: float = params.get("spread_y", 0.0)
	var spread_z: float = params.get("spread_z", 0.0)

	# Create GPU particles node
	var particles := GPUParticles3D.new()
	particles.name = params.get("name", "StreamlineParticles")
	particles.amount = count
	particles.lifetime = 5.0
	particles.explosiveness = 1.0
	particles.one_shot = false

	# Create particle material
	var mat := ParticleProcessMaterial.new()
	mat.direction = Vector3(1, 0, 0)
	mat.spread = 180.0
	mat.initial_velocity_min = 0.01
	mat.initial_velocity_max = 0.05
	mat.gravity = Vector3(0, 0, 0)
	particles.process_material = mat

	# Create draw pass mesh (small sphere)
	var sphere := SphereMesh.new()
	sphere.radius = 0.05
	sphere.height = 0.1
	particles.draw_pass_1 = sphere

	# Set emission box
	var box := BoxMesh.new()
	box.size = Vector3(spread_x, spread_y, spread_z)
	particles.draw_pass_1 = sphere

	var parent := _get_or_create_container("Particle_Systems")
	parent.add_child(particles)

	_send_response(request_id, {
		"spawned": true,
		"name": particles.name,
		"count": count,
		"particle_system": particles.name,
	})

func _cmd_animate_streamlines(request_id: String, params: Dictionary):
	var field_name: String = params.get("velocity_field", "VelocityField")
	var particle_name: String = params.get("particle_system", "StreamlineParticles")
	var speed: float = params.get("speed", 1.0)

	var data_node := _find_node_by_name(field_name)
	if not data_node:
		_send_error("Velocity field '%s' not found" % field_name, request_id)
		return

	var particles := _find_node_by_name(particle_name)
	if not particles or not particles is GPUParticles3D:
		_send_error("Particle system '%s' not found" % particle_name, request_id)
		return

	var points: PackedVector3Array = data_node.get_meta("velocity_points", PackedVector3Array())
	var vectors: PackedVector3Array = data_node.get_meta("velocity_vectors", PackedVector3Array())

	var mat := particles.process_material as ParticleProcessMaterial
	if mat:
		mat.initial_velocity_min = 0.02 * speed
		mat.initial_velocity_max = 0.08 * speed

	# Set emission box extents to cover the velocity field
	var bbox_min: Vector3 = data_node.get_meta("bbox_min", Vector3.ZERO)
	var bbox_max: Vector3 = data_node.get_meta("bbox_max", Vector3.ZERO)
	var extent := bbox_max - bbox_min

	var box := BoxMesh.new()
	box.size = extent
	particles.draw_pass_1 = box

	particles.emitting = true

	_send_response(request_id, {
		"animated": true,
		"particle_system": particle_name,
		"velocity_field": field_name,
		"speed_multiplier": speed,
		"point_count": points.size(),
	})

func _cmd_create_camera(request_id: String, params: Dictionary):
	var pos: Dictionary = params.get("position", {"x": 0, "y": 5, "z": 10})
	var look_at: Dictionary = params.get("look_at", {"x": 0, "y": 0, "z": 0})
	var fov: float = params.get("fov", 75.0)

	var cam := Camera3D.new()
	cam.name = params.get("name", "MCP_Camera")
	cam.position = Vector3(pos.get("x", 0), pos.get("y", 5), pos.get("z", 10))
	cam.look_at(Vector3(look_at.get("x", 0), look_at.get("y", 0), look_at.get("z", 0)))
	cam.fov = fov
	cam.current = true

	# Enable orbit controls via script
	var orbit := Node.new()
	orbit.name = "OrbitControls"
	var script := GDScript.new()
	script.source_code = """extends Node
var rotation_speed := 0.005
var zoom_speed := 1.0
var pan_speed := 0.01

func _input(event):
	var cam := get_parent() as Camera3D
	if not cam: return
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		if Input.is_key_pressed(KEY_ALT):
			cam.position = cam.position.rotated(Vector3.UP, -event.relative.x * rotation_speed)
		else:
			cam.rotate_y(-event.relative.x * rotation_speed)
			cam.rotate_object_local(Vector3.RIGHT, -event.relative.y * rotation_speed)
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			cam.position += cam.global_transform.basis.z * zoom_speed
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			cam.position -= cam.global_transform.basis.z * zoom_speed
"""
	script.reload()
	orbit.set_script(script)
	cam.add_child(orbit)

	var parent := _get_or_create_container("Cameras")
	parent.add_child(cam)

	_send_response(request_id, {
		"created": true,
		"name": cam.name,
		"fov": fov,
		"position": {"x": cam.position.x, "y": cam.position.y, "z": cam.position.z},
	})

func _cmd_add_light(request_id: String, params: Dictionary):
	var light_type: String = params.get("type", "directional")
	var intensity: float = params.get("intensity", 1.0)

	var light: Light3D
	if light_type == "directional":
		light = DirectionalLight3D.new()
		light.position = Vector3(5, 10, 5)
		light.look_at(Vector3.ZERO)
	elif light_type == "ambient":
		# Use environment instead
		var env := Environment.new()
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env.ambient_light_color = Color.WHITE * intensity
		env.ambient_light_energy = intensity
		_send_response(request_id, {"created": true, "type": "ambient", "intensity": intensity})
		return
	else:
		light = OmniLight3D.new()
		var pos: Dictionary = params.get("position", {"x": 5, "y": 5, "z": 5})
		light.position = Vector3(pos.get("x", 5), pos.get("y", 5), pos.get("z", 5))

	light.name = params.get("name", "MCP_Light_" + light_type)
	light.light_energy = intensity

	var parent := _get_or_create_container("Lights")
	parent.add_child(light)

	_send_response(request_id, {"created": true, "name": light.name, "type": light_type, "intensity": intensity})

func _cmd_set_material(request_id: String, params: Dictionary):
	var node_name: String = params.get("node", "")
	var color_hex: String = params.get("color", "#ffffff")
	var roughness: float = params.get("roughness", 0.5)

	var node := _find_node_by_name(node_name)
	if not node or not node is MeshInstance3D:
		_send_error("Mesh node '%s' not found" % node_name, request_id)
		return

	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(color_hex)
	mat.roughness = roughness
	(node as MeshInstance3D).set_surface_override_material(0, mat)

	_send_response(request_id, {"set": true, "node": node_name, "color": color_hex, "roughness": roughness})

func _cmd_import_obj(request_id: String, params: Dictionary):
	var path: String = params.get("path", "")
	var import_name: String = params.get("name", "OBJ_Import")

	if path.is_empty():
		_send_error("Missing path parameter", request_id)
		return

	if not FileAccess.file_exists(path):
		_send_error("File not found: %s" % path, request_id)
		return

	# Godot 4 supports OBJ/MTL via ResourceLoader
	var imported := ResourceLoader.load(path, "", ResourceLoader.CACHE_MODE_IGNORE)
	if not imported:
		_send_error("ResourceLoader failed to load OBJ: %s" % path, request_id)
		return

	# OBJ import may return a PackedScene or an ArrayMesh directly
	var scene_root: Node3D
	if imported is PackedScene:
		scene_root = imported.instantiate() as Node3D
		if not scene_root:
			_send_error("OBJ PackedScene instantiation returned null", request_id)
			return
	elif imported is ArrayMesh:
		var mi := MeshInstance3D.new()
		mi.mesh = imported
		scene_root = mi
	else:
		_send_error("Unsupported OBJ import result type: %s" % imported.get_class(), request_id)
		return

	scene_root.name = import_name

	var scale_vec: float = params.get("scale", 1.0)
	var pos: Dictionary = params.get("position", {"x": 0, "y": 0, "z": 0})
	scene_root.scale = Vector3(scale_vec, scale_vec, scale_vec)
	scene_root.position = Vector3(
		pos.get("x", 0.0), pos.get("y", 0.0), pos.get("z", 0.0)
	)

	var parent := _get_or_create_container("OBJ_Imports")
	parent.add_child(scene_root)

	_send_response(request_id, {
		"imported": true,
		"name": scene_root.name,
	})

func _cmd_export_web(request_id: String, params: Dictionary):
	var output_path: String = params.get("output_path", "user://export/web/index.html")
	# Web export requires export templates to be installed
	# This is a placeholder — full implementation needs OS.shell_exec for godot CLI
	var msg := "Web export requires godot --headless --export-release \"Web\" %s" % output_path
	_send_response(request_id, {"exported": false, "message": msg, "requires_cli": true})

func _cmd_read_scene_tree(request_id: String):
	var tree := _build_scene_tree(get_tree().get_root())
	_send_response(request_id, {"scene_tree": tree, "node_count": _count_nodes(get_tree().get_root())})

func _cmd_set_config(request_id: String, params: Dictionary):
	var section: String = params.get("section", "")
	var key: String = params.get("key", "")
	var value = params.get("value", "")

	if section.is_empty() or key.is_empty():
		_send_error("Missing section or key", request_id)
		return

	# project.godot is an INI-like file
	var cfg := ConfigFile.new()
	var path := "res://project.godot"
	if cfg.load(path) != OK:
		_send_error("Failed to load project.godot", request_id)
		return

	cfg.set_value(section, key, value)
	cfg.save(path)

	_send_response(request_id, {"updated": true, "section": section, "key": key, "value": value})

func _cmd_headless_verify(request_id: String, params: Dictionary):
	var script_path: String = params.get("script", "res://dev/mcp_verify.gd")
	# In headless mode, we can't access EditorInterface
	# This reports whether we're running headless
	_send_response(request_id, {
		"headless": DisplayServer.get_name() == "headless",
		"script_path": script_path,
		"message": "Run: godot --headless --script %s for syntax verification" % script_path,
	})

func _cmd_add_node(request_id: String, params: Dictionary):
	var parent_path: String = params.get("parent", ".")
	var node_type: String = params.get("type", "Node3D")
	var node_name: String = params.get("name", "NewNode")

	var parent := get_tree().get_root().get_node_or_null(NodePath(parent_path))
	if not parent:
		_send_error("Parent node '%s' not found" % parent_path, request_id)
		return

	var node: Node
	match node_type:
		"Node2D": node = Node2D.new()
		"Control": node = Control.new()
		"CanvasLayer": node = CanvasLayer.new()
		"CharacterBody2D": node = CharacterBody2D.new()
		"Node3D": node = Node3D.new()
		"MeshInstance3D": node = MeshInstance3D.new()
		"Camera3D": node = Camera3D.new()
		"Light3D": node = OmniLight3D.new()
		"GPUParticles3D": node = GPUParticles3D.new()
		_: node = Node3D.new()

	node.name = node_name
	parent.add_child(node)

	_send_response(request_id, {"added": true, "path": str(node.get_path()), "type": node_type, "name": node_name})

func _cmd_remove_node(request_id: String, params: Dictionary):
	var node_path: String = params.get("path", "")
	var node := get_tree().get_root().get_node_or_null(NodePath(node_path))
	if not node:
		_send_error("Node '%s' not found" % node_path, request_id)
		return
	node.queue_free()
	_send_response(request_id, {"removed": true, "path": node_path})

func _cmd_modify_node(request_id: String, params: Dictionary):
	# Set a (possibly nested) property on an existing node.
	# params: node (absolute path or plain name), property (e.g. "position:x"), value
	var node_ref: String = params.get("node", "")
	var prop: String = params.get("property", "")
	if node_ref.is_empty() or prop.is_empty():
		_send_error("modify_node requires 'node' and 'property' params", request_id)
		return
	if not params.has("value"):
		_send_error("modify_node requires a 'value' param", request_id)
		return

	var node: Node = get_tree().get_root().get_node_or_null(NodePath(node_ref))
	if not node:
		node = _find_node_by_name(node_ref)
	if not node:
		_send_error("Node '%s' not found (tried path and name lookup)" % node_ref, request_id)
		return

	var value = params.get("value")
	var prop_path := NodePath(prop)
	var previous = node.get_indexed(prop_path)
	node.set_indexed(prop_path, value)
	var applied = node.get_indexed(prop_path)

	_send_response(request_id, {
		"modified": true,
		"node": str(node.get_path()),
		"property": prop,
		"previous": str(previous),
		"value": str(applied),
	})

func _cmd_save_scene(request_id: String, params: Dictionary):
	var path: String = params.get("path", "res://mcp_scene.tscn")
	var scene := PackedScene.new()
	var root := _get_or_create_container("MCP_Scene")
	scene.pack(root)
	var err := ResourceSaver.save(scene, path)
	_send_response(request_id, {"saved": err == OK, "path": path, "error": err})

func _cmd_play_animation(request_id: String, params: Dictionary):
	var root_name: String = params.get("root_name", "")
	var animation_name: String = params.get("animation", "")
	var loop: bool = params.get("loop", true)
	var speed_scale: float = float(params.get("speed_scale", 1.0))

	var search_root: Node = get_tree().get_root()
	if not root_name.is_empty():
		var named := _find_node_by_name(root_name)
		if not named:
			_send_error("Root node not found: %s" % root_name, request_id)
			return
		search_root = named

	var player := _find_animation_player_recursive(search_root)
	if not player:
		_send_error("No AnimationPlayer found under %s" % search_root.name, request_id)
		return

	var library := player.get_animation_library("")
	if library == null and player.get_animation_library_list().size() > 0:
		library = player.get_animation_library(player.get_animation_library_list()[0])

	var available: Array = []
	if library:
		for anim_name in library.get_animation_list():
			available.append(anim_name)

	if animation_name.is_empty():
		_send_response(request_id, {
			"listed": true,
			"root_name": search_root.name,
			"animation_player": player.get_path(),
			"animations": available,
		})
		return

	if library == null or not library.has_animation(animation_name):
		_send_error(
			"Animation not found: %s (available: %s)" % [animation_name, str(available)],
			request_id,
		)
		return

	player.speed_scale = speed_scale
	var anim := library.get_animation(animation_name)
	if anim:
		anim.loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
	player.play(animation_name)

	_send_response(request_id, {
		"playing": true,
		"root_name": search_root.name,
		"animation": animation_name,
		"loop": loop,
		"speed_scale": speed_scale,
		"animation_player": str(player.get_path()),
		"available_animations": available,
	})

# ─── Helpers ──────────────────────────────────────────────────────────

func _load_stl_mesh(path: String) -> ArrayMesh:
	# Godot 4 STL loading:
	# Godot doesn't natively support STL in ResourceLoader,
	# but we can use the .stl import plugin or load as OBJ if converted.
	# For now, this is a placeholder — full STL import needs the godot-mcp
	# server to pre-convert STL to OBJ or GLTF before loading.
	var file := FileAccess.open(path, FileAccess.READ)
	if not file:
		return null

	# Read binary STL header
	var header := file.get_buffer(80)
	var tri_count := file.get_32()

	var mesh := ArrayMesh.new()
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()

	for i in range(tri_count):
		var nx := file.get_float()
		var ny := file.get_float()
		var nz := file.get_float()
		normals.append(Vector3(nx, ny, nz))

		for _j in range(3):
			var vx := file.get_float()
			var vy := file.get_float()
			var vz := file.get_float()
			vertices.append(Vector3(vx, vy, vz))

		file.get_16()  # skip attribute byte count

	file.close()

	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals

	var arr := ArrayMesh.new()
	arr.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return arr

func _get_or_create_container(name: String) -> Node3D:
	var root := get_tree().get_root()
	for child in root.get_children():
		if child.name == name and child is Node3D:
			return child as Node3D
	var container := Node3D.new()
	container.name = name
	root.add_child(container)
	return container

func _find_node_by_name(name: String) -> Node:
	var root := get_tree().get_root()
	return _find_recursive(root, name)

func _find_recursive(node: Node, name: String) -> Node:
	if node.name == name:
		return node
	for child in node.get_children():
		var found := _find_recursive(child, name)
		if found:
			return found
	return null

func _find_animation_player_recursive(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:
		return node as AnimationPlayer
	for child in node.get_children():
		var found := _find_animation_player_recursive(child)
		if found:
			return found
	return null

func _cmd_simulate_input(request_id: String, params: Dictionary):
	var actions: Array = params.get("actions", [])
	if actions.is_empty():
		_send_error("Missing 'actions' array", request_id)
		return

	var instant_results := []
	var timed_actions: Array = []

	for act in actions:
		# --- Action press/release with analog strength ---
		if act.has("action"):
			var name: String = act.get("action", "")
			var strength: float = act.get("strength", 1.0)
			var pressed: bool = act.get("pressed", true)
			if pressed:
				Input.action_press(name, strength)
			else:
				Input.action_release(name)
			instant_results.append({"type": "action", "name": name, "strength": strength, "pressed": pressed})

		# --- Joypad axis motion ---
		elif act.has("joypad") and act["joypad"].has("axis"):
			var jp: Dictionary = act["joypad"]
			var event := InputEventJoypadMotion.new()
			event.device = jp.get("device", 0)
			event.axis = jp["axis"]
			event.axis_value = jp.get("value", 0.0)
			Input.parse_input_event(event)
			instant_results.append({"type": "joypad_motion", "device": event.device, "axis": event.axis, "value": event.axis_value})

		# --- Joypad button press/release ---
		elif act.has("joypad") and act["joypad"].has("button"):
			var jp: Dictionary = act["joypad"]
			var event := InputEventJoypadButton.new()
			event.device = jp.get("device", 0)
			event.button_index = jp["button"]
			event.pressed = jp.get("pressed", true)
			Input.parse_input_event(event)
			instant_results.append({"type": "joypad_button", "device": event.device, "button": event.button_index, "pressed": event.pressed})

		# --- Mouse look (relative motion) ---
		elif act.has("mouse_look"):
			var ml: Dictionary = act["mouse_look"]
			var event := InputEventMouseMotion.new()
			event.relative = Vector2(ml.get("dx", 0), ml.get("dy", 0))
			var vp := get_viewport()
			event.position = vp.get_mouse_position() if vp else Vector2.ZERO
			event.velocity = Vector2.ZERO
			Input.parse_input_event(event)
			instant_results.append({"type": "mouse_look", "dx": ml.get("dx", 0), "dy": ml.get("dy", 0)})

		# --- Mouse button click ---
		elif act.has("mouse_button"):
			var mb: Dictionary = act["mouse_button"]
			var event := InputEventMouseButton.new()
			event.button_index = mb.get("button", 1)
			event.pressed = mb.get("pressed", true)
			var pos: Dictionary = mb.get("position", {})
			event.position = Vector2(pos.get("x", 0.0), pos.get("y", 0.0))
			Input.parse_input_event(event)
			instant_results.append({"type": "mouse_button", "button": event.button_index, "pressed": event.pressed})

		# --- Text input (simulate per-character key events) ---
		elif act.get("type") == "text":
			var text: String = act.get("text", "")
			for ch in text:
				var ev := InputEventKey.new()
				ev.keycode = ch.unicode_at(0)
				ev.unicode = ch.unicode_at(0)
				ev.pressed = true
				Input.parse_input_event(ev)
				var rel := InputEventKey.new()
				rel.keycode = ev.keycode
				rel.unicode = ev.unicode
				rel.pressed = false
				Input.parse_input_event(rel)
			instant_results.append({"type": "text", "text": text, "chars": text.length()})

		# --- Legacy key press/release (backward compat) ---
		elif act.has("key"):
			timed_actions.append(act)

	# Process legacy key events with optional hold timing (sequential awaits)
	var timed_results := []
	for action in timed_actions:
		var key_name: String = action.get("key", "")
		var pressed: bool = action.get("pressed", true)
		var hold_ms: float = action.get("hold_ms", 50.0)
		if key_name.is_empty():
			continue
		var event := InputEventKey.new()
		event.keycode = OS.find_keycode(key_name)
		if event.keycode == 0:
			event.keycode = key_name.unicode_at(0)
		event.pressed = pressed
		event.echo = false
		Input.parse_input_event(event)
		if pressed and hold_ms > 0:
			await get_tree().create_timer(hold_ms / 1000.0).timeout
			var release := InputEventKey.new()
			release.keycode = event.keycode
			release.pressed = false
			Input.parse_input_event(release)
		timed_results.append({"key": key_name, "keycode": event.keycode, "pressed": pressed})

	var all_results := instant_results + timed_results
	_send_response(request_id, {"actions_processed": len(all_results), "results": all_results})


func _cmd_inspect_resource(request_id: String, params: Dictionary):
	var res_path: String = params.get("path", "")
	if res_path.is_empty():
		_send_error("Missing 'path' param (resource path like res://assets/player.tres)", request_id)
		return
	var res = ResourceLoader.load(res_path)
	if not res:
		_send_error("Failed to load resource: %s" % res_path, request_id)
		return

	var result := {"path": res_path, "type": res.get_class()}

	if res is SpriteFrames:
		var sf := res as SpriteFrames
		var anims := []
		for anim_name in sf.get_animation_names():
			anims.append({
				"name": anim_name,
				"frame_count": sf.get_frame_count(anim_name),
				"speed": sf.get_animation_speed(anim_name),
				"loop": sf.get_animation_loop(anim_name),
			})
		result["animation_count"] = anims.size()
		result["animations"] = anims

	elif res is TileSet:
		var ts := res as TileSet
		var sources := []
		for i in ts.get_source_count():
			var src_id := ts.get_source_id(i)
			var src = ts.get_source(src_id)
			var src_info := {"source_id": src_id, "type": src.get_class()}
			if src.has_method("get_tiles_count"):
				src_info["tiles_count"] = src.get_tiles_count()
			sources.append(src_info)
		result["source_count"] = ts.get_source_count()
		result["sources"] = sources

	elif res is Material:
		var mat_info := {}
		if res is StandardMaterial3D:
			var sm := res as StandardMaterial3D
			mat_info["albedo_color"] = "#" + sm.albedo_color.to_html()
			mat_info["roughness"] = sm.roughness
			mat_info["metallic"] = sm.metallic
			mat_info["emission"] = "#" + sm.emission.to_html() if sm.emission_enabled else null
			mat_info["transparency"] = sm.transparency
			mat_info["billboard_mode"] = sm.billboard_mode
		elif res is ShaderMaterial:
			var shm := res as ShaderMaterial
			mat_info["shader_path"] = shm.shader.resource_path if shm.shader else null
			var param_list := shm.get_shader_parameter_list()
			var params_dict := {}
			for p in param_list:
				var val := shm.get_shader_parameter(p.name)
				if val is Color:
					params_dict[p.name] = "#" + val.to_html()
				else:
					params_dict[p.name] = val
			mat_info["parameters"] = params_dict
			mat_info["parameter_count"] = param_list.size()
		else:
			mat_info["material_type"] = res.get_class()
		result["material"] = mat_info

	elif res is Texture2D:
		var tex := res as Texture2D
		result["texture"] = {
			"width": tex.get_width(),
			"height": tex.get_height(),
			"has_mipmaps": tex.has_mipmaps(),
			"format": tex.get_image().get_format() if tex.get_image() else null,
		}

	else:
		# Generic resource: list exposed properties
		var props := []
		for prop in res.get_property_list():
			if prop.usage & PROPERTY_USAGE_EDITOR:
				var pname: String = prop.name
				props.append({"name": pname, "type": prop.type})
		result["property_count"] = props.size()
		result["properties"] = props

	_send_response(request_id, {"resource": result})


func _collect_profile_snapshot() -> Dictionary:
	return {
		"fps": Performance.get_monitor(Performance.TIME_FPS),
		"process_time": Performance.get_monitor(Performance.TIME_PROCESS),
		"physics_time": Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS),
		"memory_static": Performance.get_monitor(Performance.MEMORY_STATIC),
		"memory_dynamic": Performance.get_monitor(Performance.MEMORY_DYNAMIC),
		"objects": Performance.get_monitor(Performance.OBJECT_COUNT),
		"nodes": Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
		"orphan_nodes": Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT),
		"render_draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		"render_primitives": Performance.get_monitor(Performance.RENDER_PRIMITIVES_IN_FRAME),
		"render_video_mem": Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),
		"physics_active": Performance.get_monitor(Performance.PHYSICS_ACTIVE_OBJECTS),
		"physics_collisions": Performance.get_monitor(Performance.PHYSICS_COLLISION_PAIRS),
		"audio_latency": Performance.get_monitor(Performance.AUDIO_OUTPUT_LATENCY),
	}


func _detect_spikes(snapshots: Array) -> Array:
	"""Detect anomalous metrics: values deviating >2 stddev from the window mean."""
	if snapshots.size() < 10:
		return []
	var spikes := []
	var keys := ["process_time", "physics_time", "render_draw_calls", "render_primitives"]
	for key in keys:
		var vals := []
		for s in snapshots:
			if s.has(key):
				vals.append(s[key])
		if vals.size() < 5:
			continue
		var avg := 0.0
		for v in vals:
			avg += v
		avg /= vals.size()
		var variance := 0.0
		for v in vals:
			var d := v - avg
			variance += d * d
		variance /= vals.size()
		var std := sqrt(variance)
		if std < 0.001:
			continue
		var latest := vals[-1]
		if abs(latest - avg) > 2.0 * std:
			spikes.append({"metric": key, "value": latest, "mean": avg, "std": std})
	return spikes


func _cmd_import_splat(request_id: String, params: Dictionary):
	"""Read a compact binary splat file and create a Gaussian-splat rendered scene.

	Binary format: [N:uint32] [x:f32 y:f32 z:f32 r:u8 g:u8 b:u8 a:u8 sx:f32 sy:f32 sz:f32] × N
	Uses the gaussian_splat.gdshader for proper billboarded Gaussian falloff.
	"""
	var binary_path: String = params.get("path", "")
	var node_name: String = params.get("name", "SplatCloud")

	if binary_path.is_empty():
		_send_error("Missing 'path' param", request_id)
		return

	var file := FileAccess.open(binary_path, FileAccess.READ)
	if not file:
		_send_error("Cannot open splat binary: %s" % binary_path, request_id)
		return

	var n := file.get_32()
	if n <= 0 or n > 500000:
		file.close()
		_send_error("Invalid splat count: %d" % n, request_id)
		return

	# Read splat data
	var positions := PackedVector3Array()
	var colors := PackedColorArray()
	var custom_data := PackedVector4Array()
	positions.resize(n)
	colors.resize(n)
	custom_data.resize(n)

	var has_scale := false
	for i in range(n):
		var x := file.get_float()
		var y := file.get_float()
		var z := file.get_float()
		var r := file.get_8()
		var g := file.get_8()
		var b := file.get_8()
		var a := file.get_8()
		positions[i] = Vector3(x, y, z)
		colors[i] = Color(r / 255.0, g / 255.0, b / 255.0, a / 255.0)

		# Try reading scale data (3 floats). EOF-safe.
		var sx := 0.05
		var sy := 0.05
		var sz := 0.05
		if file.get_length() >= file.get_position() + 12:
			sx = file.get_float()
			sy = file.get_float()
			sz = file.get_float()
			has_scale = true
		custom_data[i] = Vector4(sx, sy, sz, 0.0)

	file.close()

	# Load the Gaussian splat shader
	var shader_path := "res://shaders/gaussian_splat.gdshader"
	var shader := ResourceLoader.load(shader_path)
	var mat := ShaderMaterial.new()
	mat.shader = shader
	if not shader:
		# Fallback: simple material if shader not found
		printerr("[MCP-Bridge] Gaussian splat shader not found at %s" % shader_path)

	# Create MultiMesh with instance data
	var multimesh := MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.use_colors = true
	multimesh.custom_data_format = MultiMesh.CUSTOM_DATA_FLOAT_SIZE_4
	multimesh.instance_count = n

	# Unit quad — the shader does the billboarding
	var quad := QuadMesh.new()
	quad.size = Vector2(2.0, 2.0)  # normalized quad [-1, 1]
	quad.flip_faces = false
	quad.material = mat
	multimesh.mesh = quad

	# Set per-instance data
	for i in range(n):
		var t := Transform3D.IDENTITY
		t.origin = positions[i]
		multimesh.set_instance_transform(i, t)
		multimesh.set_instance_color(i, colors[i])
		multimesh.set_instance_custom_data(i, custom_data[i])

	var mi := MultiMeshInstance3D.new()
	mi.name = node_name
	mi.multimesh = multimesh

	var container := _get_or_create_container("Splat_Imports")
	container.add_child(mi)

	_send_response(request_id, {
		"imported": true,
		"name": node_name,
		"splat_count": n,
		"shader": shader != null,
		"scales": has_scale,
	})


func _cmd_validate_meshes(request_id: String):
	var root := get_tree().get_root() if get_tree() else null
	if not root:
		_send_error("No active scene tree", request_id)
		return

	var results := []
	var issues := []
	var total_meshes := 0
	var corrupt_count := 0

	var all_meshes := _find_all_mesh_instances(root)
	for mi in all_meshes:
		total_meshes += 1
		var mesh := mi.mesh
		if not mesh:
			continue
		var mesh_issues := _validate_single_mesh(mi)
		if mesh_issues.size() > 0:
			corrupt_count += 1
			for issue in mesh_issues:
				issues.append(issue)

		results.append({
			"node": mi.name,
			"path": str(mi.get_path()),
			"mesh_type": mesh.get_class(),
			"surface_count": mesh.get_surface_count(),
			"issues": mesh_issues.size(),
		})

	_send_response(request_id, {
		"total_meshes": total_meshes,
		"corrupt_meshes": corrupt_count,
		"total_issues": issues.size(),
		"details": results,
		"issues": issues,
	})


func _find_all_mesh_instances(node: Node) -> Array:
	var result := []
	if node is MeshInstance3D:
		result.append(node)
	for child in node.get_children():
		result.append_array(_find_all_mesh_instances(child))
	return result


func _validate_single_mesh(mi: MeshInstance3D) -> Array:
	var found := []
	var mesh := mi.mesh
	if not mesh:
		return found

	for surf_idx in mesh.get_surface_count():
		var arrays := mesh.surface_get_arrays(surf_idx)
		if arrays.is_empty():
			found.append({"node": mi.name, "surface": surf_idx, "severity": "error", "detail": "Empty surface arrays"})
			continue

		var verts = arrays[Mesh.ARRAY_VERTEX] if arrays.size() > Mesh.ARRAY_VERTEX else null
		var normals = arrays[Mesh.ARRAY_NORMAL] if arrays.size() > Mesh.ARRAY_NORMAL else null
		var indices = arrays[Mesh.ARRAY_INDEX] if arrays.size() > Mesh.ARRAY_INDEX else null

		# Check for NaN/inf in vertices
		if verts is PackedVector3Array:
			for i in verts.size():
				var v := verts[i]
				if isnan(v.x) or isnan(v.y) or isnan(v.z) or is_inf(v.x) or is_inf(v.y) or is_inf(v.z):
					found.append({"node": mi.name, "surface": surf_idx, "severity": "error",
						"detail": "Vertex %d has NaN/inf: (%s, %s, %s)" % [i, v.x, v.y, v.z]})
					if found.size() >= 5:
						return found  # limit per mesh

		# Check for zero-length normals
		if normals is PackedVector3Array:
			for i in normals.size():
				var n := normals[i]
				if n.length_squared() < 0.0001:
					found.append({"node": mi.name, "surface": surf_idx, "severity": "warning",
						"detail": "Normal %d is zero-length" % i})
					break

		# Check for degenerate triangles (zero-area)
		if verts is PackedVector3Array and verts.size() >= 3:
			var step := 3
			var tri_indices := []
			if indices is PackedInt32Array:
				for i in range(0, indices.size(), 3):
					if i + 2 < indices.size():
						tri_indices.append([indices[i], indices[i+1], indices[i+2]])
			else:
				for i in range(0, verts.size(), 3):
					if i + 2 < verts.size():
						tri_indices.append([i, i+1, i+2])

			for tri in tri_indices:
				var a := verts[tri[0]]
				var b := verts[tri[1]]
				var c := verts[tri[2]]
				var cross = (b - a).cross(c - a)
				if cross.length_squared() < 0.0000001:
					found.append({"node": mi.name, "surface": surf_idx, "severity": "warning",
						"detail": "Degenerate triangle at indices %s" % str(tri)})
					break

	return found


func _cmd_profile_snapshot(request_id: String):
	var snap := _collect_profile_snapshot()
	_send_response(request_id, {"snapshot": snap, "enabled": _profile_enabled})


func _cmd_profile_enable(request_id: String, params: Dictionary):
	_profile_enabled = params.get("enabled", true)
	if not _profile_enabled:
		_profile_history.clear()
	_send_response(request_id, {"enabled": _profile_enabled, "history_size": _profile_history.size()})


func _cmd_profile_history(request_id: String):
	var spikes := _detect_spikes(_profile_history)
	var avg_snap := {}
	if _profile_history.size() > 0:
		var keys = _profile_history[0].keys()
		for key in keys:
			var total := 0.0
			for s in _profile_history:
				if s.has(key):
					total += s[key]
			avg_snap[key] = total / _profile_history.size()

	_send_response(request_id, {
		"enabled": _profile_enabled,
		"frames": _profile_history.size(),
		"latest": _profile_history[-1] if _profile_history.size() > 0 else null,
		"average": avg_snap,
		"spikes": spikes,
		"spike_count": spikes.size(),
	})


func _cmd_animation_edit(request_id: String, params: Dictionary):
	var node_ref: String = params.get("node", "")
	var operation: String = params.get("operation", "")
	var anim_name: String = params.get("animation", "")
	if node_ref.is_empty():
		_send_error("Missing 'node' param", request_id)
		return
	var node := get_tree().get_root().get_node_or_null(NodePath(node_ref))
	if not node:
		node = _find_node_by_name(node_ref)
	if not node:
		_send_error("AnimationPlayer not found: %s" % node_ref, request_id)
		return
	if not node is AnimationPlayer:
		_send_error("Node '%s' is not an AnimationPlayer" % node.name, request_id)
		return
	var ap := node as AnimationPlayer
	var lib = ap.get_animation_library("")
	if lib == null and ap.get_animation_library_list().size() > 0:
		lib = ap.get_animation_library(ap.get_animation_library_list()[0])
	if not lib:
		_send_error("No animation library found on '%s'" % node.name, request_id)
		return

	if operation == "list_animations":
		var anims := []
		for name in lib.get_animation_list():
			anims.append(name)
		_send_response(request_id, {"node": node.name, "animations": anims, "count": anims.size()})

	elif operation == "list_tracks":
		if not lib.has_animation(anim_name):
			_send_error("Animation not found: %s" % anim_name, request_id)
			return
		var anim := lib.get_animation(anim_name)
		var tracks := []
		for i in anim.get_track_count():
			var track_info := {
				"index": i,
				"type": anim.track_get_type(i),
				"path": str(anim.track_get_path(i)),
			}
			var interp = anim.track_get_interpolation(i)
			var interp_names = ["NEAREST", "LINEAR", "CUBIC", "LINEAR_ANGLE", "CUBIC_ANGLE"]
			track_info["interpolation"] = interp_names[interp] if interp < interp_names.size() else str(interp)
			track_info["key_count"] = anim.track_get_key_count(i)
			tracks.append(track_info)
		_send_response(request_id, {"node": node.name, "animation": anim_name, "tracks": tracks, "count": tracks.size()})

	elif operation == "list_keyframes":
		if not lib.has_animation(anim_name):
			_send_error("Animation not found: %s" % anim_name, request_id)
			return
		var anim := lib.get_animation(anim_name)
		var track_index: int = params.get("track", 0)
		if track_index < 0 or track_index >= anim.get_track_count():
			_send_error("Track index %d out of range (0-%d)" % [track_index, anim.get_track_count() - 1], request_id)
			return
		var keys := []
		for k in anim.track_get_key_count(track_index):
			var ktime := anim.track_get_key_time(track_index, k)
			var kval := anim.track_get_key_value(track_index, k)
			var ktrans := anim.track_get_key_transition(track_index, k)
			keys.append({"index": k, "time": ktime, "value": str(kval), "transition": ktrans})
		_send_response(request_id, {
			"node": node.name, "animation": anim_name, "track": track_index,
			"keys": keys, "count": keys.size(),
		})

	elif operation == "insert_keyframe":
		if not lib.has_animation(anim_name):
			_send_error("Animation not found: %s" % anim_name, request_id)
			return
		var anim := lib.get_animation(anim_name)
		var track_index: int = params.get("track", -1)
		var time: float = params.get("time", 0.0)
		var value = params.get("value", 0)
		if track_index < 0 or track_index >= anim.get_track_count():
			_send_error("Invalid track index %d" % track_index, request_id)
			return
		var inserted = anim.track_insert_key(track_index, time, value)
		_send_response(request_id, {
			"node": node.name, "animation": anim_name, "track": track_index,
			"time": time, "inserted": inserted,
		})

	elif operation == "remove_keyframe":
		if not lib.has_animation(anim_name):
			_send_error("Animation not found: %s" % anim_name, request_id)
			return
		var anim := lib.get_animation(anim_name)
		var track_index: int = params.get("track", -1)
		var time: float = params.get("time", 0.0)
		if track_index < 0 or track_index >= anim.get_track_count():
			_send_error("Invalid track index %d" % track_index, request_id)
			return
		anim.track_remove_key_at_time(track_index, time)
		_send_response(request_id, {
			"node": node.name, "animation": anim_name, "track": track_index,
			"time": time, "removed": true,
		})

	elif operation == "set_interpolation":
		if not lib.has_animation(anim_name):
			_send_error("Animation not found: %s" % anim_name, request_id)
			return
		var anim := lib.get_animation(anim_name)
		var track_index: int = params.get("track", -1)
		var mode: String = params.get("mode", "linear")
		var interp_map := {"nearest": 0, "linear": 1, "cubic": 2, "linear_angle": 3, "cubic_angle": 4}
		var interp_val = interp_map.get(mode.to_lower(), 1)
		if track_index < 0 or track_index >= anim.get_track_count():
			_send_error("Invalid track index %d" % track_index, request_id)
			return
		anim.track_set_interpolation(track_index, interp_val)
		_send_response(request_id, {
			"node": node.name, "animation": anim_name, "track": track_index,
			"interpolation": mode,
		})

	else:
		_send_error("Unknown animation_edit operation: %s" % operation, request_id)


func _cmd_tilemap_read(request_id: String, params: Dictionary):
	var node_ref: String = params.get("node", "")
	if node_ref.is_empty():
		_send_error("Missing 'node' param", request_id)
		return
	var node := get_tree().get_root().get_node_or_null(NodePath(node_ref))
	if not node:
		node = _find_node_by_name(node_ref)
	if not node:
		_send_error("Node not found: %s" % node_ref, request_id)
		return

	if node is TileMapLayer:
		var tml := node as TileMapLayer
		var used := tml.get_used_cells()
		var cells := []
		for coord in used:
			cells.append({
				"x": coord.x, "y": coord.y,
				"source_id": tml.get_cell_source_id(coord),
				"atlas_coords": {"x": tml.get_cell_atlas_coords(coord).x, "y": tml.get_cell_atlas_coords(coord).y},
				"alternative_tile": tml.get_cell_alternative_tile(coord),
			})
		_send_response(request_id, {
			"node": node.name, "type": "TileMapLayer",
			"cell_count": cells.size(), "cells": cells,
			"cell_size": {"x": tml.tile_set.tile_size.x, "y": tml.tile_set.tile_size.y} if tml.tile_set else null,
			"layers": tml.get_layers_count() if tml.has_method("get_layers_count") else 1,
		})

	elif node is GridMap:
		var gm := node as GridMap
		var used := gm.get_used_cells()
		var cells := []
		for cell in used:
			cells.append({
				"x": cell.x, "y": cell.y, "z": cell.z,
				"item": gm.get_cell_item(cell),
				"orientation": gm.get_cell_item_orientation(cell),
			})
		_send_response(request_id, {
			"node": node.name, "type": "GridMap",
			"cell_count": cells.size(), "cells": cells,
		})

	else:
		_send_error("Node '%s' is not a TileMapLayer or GridMap" % node.name, request_id)


func _cmd_tilemap_edit(request_id: String, params: Dictionary):
	var node_ref: String = params.get("node", "")
	var operation: String = params.get("operation", "set_cell")
	if node_ref.is_empty():
		_send_error("Missing 'node' param", request_id)
		return
	var node := get_tree().get_root().get_node_or_null(NodePath(node_ref))
	if not node:
		node = _find_node_by_name(node_ref)
	if not node:
		_send_error("Node not found: %s" % node_ref, request_id)
		return

	if operation == "set_cell" and node is TileMapLayer:
		var tml := node as TileMapLayer
		var cells: Array = params.get("cells", [])
		var count := 0
		for c in cells:
			var coord := Vector2i(c.get("x", 0), c.get("y", 0))
			var source_id: int = c.get("source_id", 0)
			var ac := c.get("atlas_coords", {"x": 0, "y": 0})
			var atlas := Vector2i(ac.get("x", 0), ac.get("y", 0))
			var alt: int = c.get("alternative_tile", 0)
			tml.set_cell(coord, source_id, atlas, alt)
			count += 1
		_send_response(request_id, {"operation": "set_cell", "node": node.name, "type": "TileMapLayer", "cells_set": count})

	elif operation == "erase_cell" and node is TileMapLayer:
		var tml := node as TileMapLayer
		var coords: Array = params.get("coords", [])
		var count := 0
		for c in coords:
			tml.erase_cell(Vector2i(c.get("x", 0), c.get("y", 0)))
			count += 1
		_send_response(request_id, {"operation": "erase_cell", "node": node.name, "type": "TileMapLayer", "cells_erased": count})

	elif operation == "clear" and (node is TileMapLayer or node is GridMap):
		if node is TileMapLayer:
			(node as TileMapLayer).clear()
		else:
			(node as GridMap).clear()
		_send_response(request_id, {"operation": "clear", "node": node.name, "cleared": true})

	else:
		_send_error("Unsupported operation '%s' for %s" % [operation, node.get_class()], request_id)


func _cmd_read_node(request_id: String, params: Dictionary):
	var node_ref: String = params.get("node", "")
	if node_ref.is_empty():
		_send_error("Missing 'node' param (path or name)", request_id)
		return
	var node := get_tree().get_root().get_node_or_null(NodePath(node_ref))
	if not node:
		node = _find_node_by_name(node_ref)
	if not node:
		_send_error("Node not found: %s" % node_ref, request_id)
		return

	var result := _collect_node_state(node)
	result["path"] = str(node.get_path())
	# List direct children
	var children := []
	for child in node.get_children():
		children.append({"name": child.name, "type": child.get_class()})
	if children.size() > 0:
		result["children"] = children
	_send_response(request_id, {"node": result})


func _cmd_state_digest(request_id: String, params: Dictionary):
	var filter_names: Array = params.get("nodes", [])
	var root := get_tree().get_root() if get_tree() else null
	if not root:
		_send_error("No active scene tree", request_id)
		return

	var result := {}
	if filter_names.is_empty():
		# Collect state for all nodes in mcp_watch group
		var watched := get_tree().get_nodes_in_group("mcp_watch")
		for node in watched:
			result[node.name] = _collect_node_state(node)
	else:
		# Collect state for named nodes (found anywhere in tree)
		for name in filter_names:
			var node_name := str(name)
			var node := _find_node_by_name(node_name)
			if not node:
				result[node_name] = {"error": "node not found"}
			else:
				result[node_name] = _collect_node_state(node)

	_send_response(request_id, {"nodes": result, "count": result.size()})


func _cmd_state_watch_add(request_id: String, params: Dictionary):
	var node_ref: String = params.get("node", "")
	if node_ref.is_empty():
		_send_error("Missing 'node' param (path or name)", request_id)
		return
	var node := get_tree().get_root().get_node_or_null(NodePath(node_ref))
	if not node:
		node = _find_node_by_name(node_ref)
	if not node:
		_send_error("Node not found: %s" % node_ref, request_id)
		return
	node.add_to_group("mcp_watch")
	_send_response(request_id, {"added": true, "node": node.name, "group": "mcp_watch"})


func _cmd_state_watch_remove(request_id: String, params: Dictionary):
	var node_ref: String = params.get("node", "")
	if node_ref.is_empty():
		_send_error("Missing 'node' param (path or name)", request_id)
		return
	var node := get_tree().get_root().get_node_or_null(NodePath(node_ref))
	if not node:
		node = _find_node_by_name(node_ref)
	if not node:
		_send_error("Node not found: %s" % node_ref, request_id)
		return
	node.remove_from_group("mcp_watch")
	_send_response(request_id, {"removed": true, "node": node.name, "group": "mcp_watch"})


func _cmd_game_time_freeze(request_id: String):
	_playtest_state = PlaytestState.FROZEN
	Engine.time_scale = 0
	_send_response(request_id, {"state": "frozen", "time_scale": 0.0})


func _cmd_game_time_unfreeze(request_id: String):
	_playtest_state = PlaytestState.RUNNING
	Engine.time_scale = 1.0
	_send_response(request_id, {"state": "running", "time_scale": 1.0})


func _cmd_game_time_step(request_id: String, params: Dictionary):
	var frames: int = params.get("frames", 1)
	if _playtest_state != PlaytestState.FROZEN:
		_send_error("Must freeze the game clock before stepping (use game_time_freeze)", request_id)
		return

	_step_pending = frames
	_step_until_condition = ""
	_step_until_request_id = ""
	_step_until_counter = 0
	_step_until_timeout = 0
	_playtest_state = PlaytestState.STEPPING
	# time_scale will be set to 1.0 in _process during stepping

	_send_response(request_id, {"stepping": true, "frames": frames})


func _cmd_game_time_step_until(request_id: String, params: Dictionary):
	var condition: String = params.get("condition", "")
	var timeout_frames: int = params.get("timeout_frames", 3600)
	if condition.is_empty():
		_send_error("step_until requires a 'condition' GDScript expression", request_id)
		return
	if _playtest_state != PlaytestState.FROZEN:
		_send_error("Must freeze the game clock first (use game_time_freeze)", request_id)
		return

	_step_until_request_id = request_id
	_step_until_condition = condition
	_step_until_counter = 0
	_step_until_timeout = timeout_frames
	_step_pending = max(timeout_frames, 1)
	_playtest_state = PlaytestState.STEPPING
	# Response is deferred — sent from _process when condition is met or timeout.
	# The Python side blocks on bridge.send() until the response arrives.


func _cmd_generate_procedural_texture(request_id: String, params: Dictionary):
	var texture_type: String = params.get("type", "gradient")
	var width: int = params.get("width", 256)
	var height: int = params.get("height", 256)
	var colors: Array = params.get("colors", ["#ff4444", "#4444ff"])
	var output_path: String = params.get("output_path", "")
	var img := Image.create(width, height, false, Image.FORMAT_RGBA8)

	match texture_type:
		"gradient":
			img.fill(Color(0, 0, 0, 1))
			for y in range(height):
				var t := float(y) / float(height - 1) if height > 1 else 0.0
				var ci := int(t * (colors.size() - 1))
				var cf := t * (colors.size() - 1) - ci
				var c1 := Color(colors[ci] if ci < colors.size() else colors[-1])
				var c2 := Color(colors[min(ci + 1, colors.size() - 1)])
				var c := c1.lerp(c2, cf)
				for x in range(width):
					img.set_pixel(x, y, c)

		"noise":
			var noise := FastNoiseLite.new()
			noise.seed = params.get("seed", randi())
			noise.frequency = params.get("frequency", 0.05)
			for y in range(height):
				for x in range(width):
					var n := noise.get_noise_2d(float(x), float(y)) * 0.5 + 0.5
					var c1 := Color(colors[0])
					var c2 := Color(colors[1] if colors.size() > 1 else colors[0])
					img.set_pixel(x, y, c1.lerp(c2, n))

		"checker":
			var cell_size: int = params.get("cell_size", 32)
			var c1 := Color(colors[0])
			var c2 := Color(colors[1] if colors.size() > 1 else Color.WHITE)
			for y in range(height):
				for x in range(width):
					var cx := int(x / cell_size)
					var cy := int(y / cell_size)
					img.set_pixel(x, y, c1 if (cx + cy) % 2 == 0 else c2)

		"solid":
			var c := Color(colors[0])
			img.fill(c)

		_:
			_send_error("Unknown texture type: " + texture_type, request_id)
			return

	if output_path.is_empty():
		output_path = "user://procedural_%s_%d.png" % [texture_type, Time.get_unix_time_from_system()]
	var save_err := img.save_png(output_path)
	if save_err != OK:
		_send_error("Failed to save texture: error %d" % save_err, request_id)
		return
	_send_response(request_id, {
		"path": output_path,
		"width": width,
		"height": height,
		"texture_type": texture_type,
		"format": "png",
		"colors": colors,
	})


func _cmd_capture_viewport(request_id: String, params: Dictionary):
	var output_path: String = params.get("output_path", "")
	var viewport := get_viewport()
	if not viewport:
		_send_error("No active viewport", request_id)
		return
	var img := viewport.get_texture().get_image()
	if not img:
		_send_error("Failed to capture viewport image", request_id)
		return
	if output_path.is_empty():
		output_path = "user://viewport_capture_%d.png" % Time.get_unix_time_from_system()
	var save_err := img.save_png(output_path)
	if save_err != OK:
		_send_error("Failed to save PNG: error %d" % save_err, request_id)
		return
	_send_response(request_id, {
		"path": output_path,
		"width": img.get_width(),
		"height": img.get_height(),
		"format": "png",
	})


func _collect_node_state(node: Node) -> Dictionary:
	var result := {"name": node.name, "type": node.get_class()}

	# Opt-in custom state via _mcp_state() method
	if node.has_method("_mcp_state"):
		result["mcp_state"] = true
		var custom := node._mcp_state()
		if typeof(custom) == TYPE_DICTIONARY:
			for key in custom:
				result[key] = custom[key]
		return result

	# Default property collection for common node types
	if node is Node3D:
		var n := node as Node3D
		result["position"] = {"x": n.position.x, "y": n.position.y, "z": n.position.z}
		result["rotation_deg"] = {"x": rad_to_deg(n.rotation.x), "y": rad_to_deg(n.rotation.y), "z": rad_to_deg(n.rotation.z)}
		result["scale"] = {"x": n.scale.x, "y": n.scale.y, "z": n.scale.z}
	if node is Node2D:
		var n := node as Node2D
		result["position"] = {"x": n.position.x, "y": n.position.y}
		result["rotation_deg"] = rad_to_deg(n.rotation)
		result["scale"] = {"x": n.scale.x, "y": n.scale.y}
	if node is CanvasItem:
		result["visible"] = (node as CanvasItem).visible
	if node is CharacterBody3D:
		var v := (node as CharacterBody3D).velocity
		result["velocity"] = {"x": v.x, "y": v.y, "z": v.z}
	if node is RigidBody3D:
		var v := (node as RigidBody3D).linear_velocity
		result["velocity"] = {"x": v.x, "y": v.y, "z": v.z}
	if node is CharacterBody2D:
		var v := (node as CharacterBody2D).velocity
		result["velocity"] = {"x": v.x, "y": v.y}
	if node is RigidBody2D:
		var v := (node as RigidBody2D).linear_velocity
		result["velocity"] = {"x": v.x, "y": v.y}
	if node is AnimationPlayer:
		var ap := node as AnimationPlayer
		if ap.is_playing():
			result["current_animation"] = ap.get_current_animation()
			result["speed_scale"] = ap.speed_scale

	return result


func _build_scene_tree(node: Node) -> Dictionary:
	var children: Array = []
	for child in node.get_children():
		children.append(_build_scene_tree(child))
	return {
		"name": node.name,
		"type": node.get_class(),
		"path": str(node.get_path()),
		"children": children,
	}

func _count_nodes(node: Node) -> int:
	var count := 1
	for child in node.get_children():
		count += _count_nodes(child)
	return count

func _send_response(request_id: String, data: Dictionary):
	var msg := {"type": "response", "request_id": request_id, "success": true, "data": data}
	_send_json(msg)

func _send_error(message: String, request_id: String = ""):
	var msg := {"type": "response", "request_id": request_id, "success": false, "error": message}
	_send_json(msg)

func _send_json(data: Dictionary):
	if not _peer:
		return
	var json_str := JSON.stringify(data) + "\n"
	_peer.put_data(json_str.to_utf8_buffer())
