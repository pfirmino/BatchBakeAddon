import bpy
import os

BAKE_TYPES = [
    ("diffuse", "Diffuse", ""),
    ("metallic", "Metallic", ""),
    ("specular_tint", "Specular Tint", ""),
    ("roughness", "Roughness", ""),
    ("emission", "Emissive", ""),
    ("sheen_tint", "Sheen Tint", ""),
    ("normal", "Normal", ""),
    ("height", "Height", ""),
]

BAKE_ENUM_MAP = {
    "diffuse": "DIFFUSE",
    "metallic": "GLOSSY",  # Approximate
    "specular_tint": "GLOSSY",  # Approximate
    "roughness": "ROUGHNESS",
    "emission": "EMIT",
    "sheen_tint": "GLOSSY",  # Approximate
    "normal": "NORMAL",
    "height": "POSITION",  # Approximate
}


class BATCHBAKE_PT_panel(bpy.types.Panel):
    bl_label = "Batch Bake"
    bl_idname = "BATCHBAKE_PT_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'

    def draw(self, context):
        props = context.scene.batch_bake_props
        layout = self.layout

        layout.prop(props, "image_name")
        layout.prop(props, "image_format")

        row = layout.row()
        row.prop(props, "resolution_x")
        row.prop(props, "resolution_y")

        layout.prop(props, "output_path")
        layout.prop(props, "bake_margin")

        layout.prop(props, "collection_low")
        layout.prop(props, "collection_high")
        layout.prop(props, "collection_cage")

        layout.label(text="Bake Channels:")
        for bt in BAKE_TYPES:
            layout.prop(props, f"bake_{bt[0]}", text=bt[1])

        layout.operator("batchbake.execute", icon="RENDER_STILL")

class BATCHBAKE_OT_execute(bpy.types.Operator):
    bl_idname = "batchbake.execute"
    bl_label = "Start Baking"

    def execute(self, context):
        props = context.scene.batch_bake_props
        wm = context.window_manager
        high_objs = props.collection_high
        low_objs = props.collection_low
        cage_objs = props.collection_cage

        if not (high_objs and low_objs and cage_objs):
            self.report({'ERROR'}, "Missing one or more selected collections: high, low, cage")
            return {'CANCELLED'}

        to_bake = [bt[0] for bt in BAKE_TYPES if getattr(props, f"bake_{bt[0]}")]
        if not to_bake:
            self.report({'ERROR'}, "No bake channels selected")
            return {'CANCELLED'}

        low_list = [obj for obj in low_objs.objects if obj.type == 'MESH']
        if not low_list:
            self.report({'ERROR'}, "No mesh objects found in low collection")
            return {'CANCELLED'}

        total_meshes = len(low_list)
        wm.progress_begin(0, total_meshes * len(to_bake))

        step = 0

        for channel in to_bake:
            img = bpy.data.images.new(
                name=f"{props.image_name}_{channel}",
                width=props.resolution_x,
                height=props.resolution_y,
                alpha=True,
                float_buffer=True if props.image_format == "OPEN_EXR" else False
            )
            img.generated_type = 'BLANK'
            img.generated_color = (0.0, 0.0, 0.0, 0.0)
            img.use_alpha = True
            img.alpha_mode = 'STRAIGHT'
            img.colorspace_settings.name = 'Raw'
            img.use_fake_user = True
            img.file_format = props.image_format
            img.pixels.foreach_set([0.0] * len(img.pixels))

            for i, low_obj in enumerate(low_list):
                name_base = low_obj.name.removesuffix(".low")
                high_obj = high_objs.objects.get(f"{name_base}.high")
                cage_obj = cage_objs.objects.get(f"{name_base}.cage")

                if not high_obj or not cage_obj:
                    self.report({'WARNING'}, f"Missing pair for {low_obj.name}")
                    step += 1
                    wm.progress_update(step)
                    continue

                # Save render visibility of all relevant objects
                visibility_cache = {}
                for obj in list(low_objs.objects) + list(high_objs.objects) + list(cage_objs.objects):
                    visibility_cache[obj] = obj.hide_render
                    obj.hide_render = True

                # Enable only current set
                low_obj.hide_render = False
                high_obj.hide_render = False
                cage_obj.hide_render = False

                if bpy.ops.object.mode_set.poll():
                    bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.select_all(action='DESELECT')
                low_obj.select_set(True)
                high_obj.select_set(True)
                bpy.context.view_layer.objects.active = low_obj
                bpy.context.view_layer.update()

                mat = low_obj.data.materials[0] if low_obj.data.materials else None
                if not mat:
                    mat = bpy.data.materials.new(name="BakeMat")
                    low_obj.data.materials.append(mat)

                if not mat.node_tree:
                    mat.use_nodes = True

                nt = mat.node_tree
                img_node = nt.nodes.get("BakedImage") or nt.nodes.new("ShaderNodeTexImage")
                img_node.name = "BakedImage"
                img_node.image = img
                for node in nt.nodes:
                    node.select = False
                img_node.select = True
                nt.nodes.active = img_node

                self.report({'INFO'}, f"Baking ({i+1}/{total_meshes}) {low_obj.name} | Channel: {channel}")
                print(f"[{i+1}/{total_meshes}] Baking {low_obj.name} for {channel}")

                result = bpy.ops.object.bake(
                    type=BAKE_ENUM_MAP[channel],
                    target='IMAGE_TEXTURES',
                    save_mode='INTERNAL',
                    use_selected_to_active=True,
                    use_cage=True,
                    cage_object=cage_obj.name,
                    margin=props.bake_margin,
                    margin_type='EXTEND',
                    use_clear=False
                )
                print(f"Bake op result: {result}")

                # Restore original visibility
                for obj, visibility in visibility_cache.items():
                    obj.hide_render = visibility
                
                step += 1
                wm.progress_update(step)

            img.filepath_raw = os.path.join(props.output_path, f"{props.image_name}_{channel}.{props.image_format.lower()}")
            img.file_format = props.image_format
            img.save()

        wm.progress_end()
        self.report({'INFO'}, "Baking complete.")
        return {'FINISHED'}

