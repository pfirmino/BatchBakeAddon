import bpy
from .batch_bake import BAKE_TYPES, BATCHBAKE_PT_panel, BATCHBAKE_OT_execute

bl_info = {
    "name": "Batch Bake Addon",
    "author": "Pietro3DArtist",
    "version": (1, 2, 1),
    "blender": (5, 0, 0),
    "location": "Render Properties > Batch Bake",
    "description": "Batch bake from high to low using cage meshes with customizable options.",
    "category": "Bake",
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

    bake_diffuse: bpy.props.BoolProperty(name="Diffuse", default=False)
    bake_metallic: bpy.props.BoolProperty(name="Metallic", default=False)
    bake_specular_tint: bpy.props.BoolProperty(name="Specular Tint", default=False)
    bake_roughness: bpy.props.BoolProperty(name="Roughness", default=False)
    bake_emission: bpy.props.BoolProperty(name="Emissive", default=False)
    bake_sheen_tint: bpy.props.BoolProperty(name="Sheen Tint", default=False)
    bake_normal: bpy.props.BoolProperty(name="Normal", default=False)
    bake_height: bpy.props.BoolProperty(name="Height", default=False)

classes = (
    BatchBakeProperties,
    BATCHBAKE_PT_panel,
    BATCHBAKE_OT_execute,
)

def register():
    registered = []
    try:
        for cls in classes:
            bpy.utils.register_class(cls)
            registered.append(cls)
        bpy.types.Scene.batch_bake_props = bpy.props.PointerProperty(type=BatchBakeProperties)
    except Exception:
        for cls in reversed(registered):
            try:
                bpy.utils.unregister_class(cls)
            except Exception:
                pass
        raise

def unregister():
    if hasattr(bpy.types.Scene, "batch_bake_props"):
        del bpy.types.Scene.batch_bake_props
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

if __name__ == "__main__":
    register()
