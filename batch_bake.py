bl_info = {
    "name": "Batch Bake Addon",
    "author": "Pietro3DArtist",
    "version": (1, 2),
    "blender": (5, 0, 0),
    "location": "Render Properties > Batch Bake",
    "description": "Batch bake from high to low using cage meshes with customizable options.",
    "category": "Bake",
}

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

class BatchBakeProperties(bpy.types.PropertyGroup):
    image_name: bpy.props.StringProperty(name="Image Base Name", default="baked_texture")
    image_format: bpy.props.EnumProperty(
        name="Image Format",
        items=[
            ("PNG", "PNG", ""),
            ("TIFF", "TIFF", ""),
            ("OPEN_EXR", "OpenEXR", ""),
        ],
        default="PNG",
    )
    resolution_x: bpy.props.IntProperty(name="Width", default=2048, min=64)
    resolution_y: bpy.props.IntProperty(name="Height", default=2048, min=64)
    output_path: bpy.props.StringProperty(name="Output Path", subtype='DIR_PATH')
    bake_margin: bpy.props.IntProperty(name="Bake Margin", default=2, min=0)

    collection_low: bpy.props.PointerProperty(name="Low Collection", type=bpy.types.Collection)
    collection_high: bpy.props.PointerProperty(name="High Collection", type=bpy.types.Collection)
    collection_cage: bpy.props.PointerProperty(name="Cage Collection", type=bpy.types.Collection)

    for bt in BAKE_TYPES:
        exec(f"bake_{bt[0]}: bpy.props.BoolProperty(name=\"{bt[1]}\", default=False)")

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

        low_list = list(low_objs.objects)
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

                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = low_obj
                low_obj.select_set(True)
                high_obj.select_set(True)

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
                nt.nodes.active = img_node

                self.report({'INFO'}, f"Baking ({i+1}/{total_meshes}) {low_obj.name} | Channel: {channel}")
                print(f"[{i+1}/{total_meshes}] Baking {low_obj.name} for {channel}")

                bpy.ops.object.bake(
                    type=BAKE_ENUM_MAP[channel],
                    use_cage=True,
                    cage_object=cage_obj.name,
                    margin=props.bake_margin,
                    margin_type='EXTEND'
                )

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

classes = (
    BatchBakeProperties,
    BATCHBAKE_PT_panel,
    BATCHBAKE_OT_execute,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.batch_bake_props = bpy.props.PointerProperty(type=BatchBakeProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.batch_bake_props

if __name__ == "__main__":
    register()
