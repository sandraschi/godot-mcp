shader_type spatial;
render_mode blend_mix, unshaded, cull_disabled, depth_draw_opaque;

// 3D Gaussian Splatting shader for MultiMeshInstance3D.
// Each instance is a billboarded quad with Gaussian falloff alpha.
// Instance color = splat RGB, Instance custom = (scale_x, scale_y, scale_z, _)

// 2D screen-space covariance (approximate: use uniform scale per axis)
// and apply the 3D→2D Gaussian projection for proper perspective scaling
uniform float global_scale : hint_range(0.0, 5.0) = 1.0;
uniform float falloff_strength : hint_range(1.0, 20.0) = 8.0;

varying vec2 v_uv;

void vertex() {
    // Splat world position from instance transform
    vec3 splat_pos = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;

    // Billboard vectors (camera-facing)
    vec3 cam_pos = CAMERA_POSITION_WORLD;
    vec3 forward = normalize(cam_pos - splat_pos);
    vec3 up = CAMERA_DIRECTION_UP_WORLD;
    vec3 right = normalize(cross(forward, up));
    up = cross(right, forward);

    // Per-instance scale from custom data (log-scale → linear in Python)
    vec3 splat_scale = INSTANCE_CUSTOM.xyz * global_scale;

    // The quad mesh vertices are at corners of a unit quad centered at origin.
    // VERTEX is in local space; we reconstruct the billboard offset.
    // Map VERTEX.xy → [-0.5, 0.5] range for centering
    vec2 offset_uv = VERTEX.xy;

    // Compute screen-space quad size accounting for perspective.
    // Larger splats far away should appear smaller.
    float view_dist = length(cam_pos - splat_pos);
    float perspective = view_dist / max(view_dist, 1.0);

    // Billboard offset with per-axis scale
    vec3 billboard_offset = right * offset_uv.x * splat_scale.x
                          + up * offset_uv.y * splat_scale.y;

    vec3 world_vertex = splat_pos + billboard_offset;
    VERTEX = (VIEW_MATRIX * vec4(world_vertex, 1.0)).xyz;
    v_uv = offset_uv;
}

void fragment() {
    // Gaussian falloff: distance from center of billboard
    float dist = length(v_uv);
    float alpha = exp(-dist * dist * falloff_strength);

    // Discard near-zero alpha for depth writing
    if (alpha < 0.01) discard;

    ALBEDO = COLOR.rgb;
    ALPHA = COLOR.a * alpha;

    // Emit weak light for glow effect on bright splats
    EMISSION = COLOR.rgb * 0.15;
}
