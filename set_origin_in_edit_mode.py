import bpy
import bmesh
from mathutils import Vector


# Meta Info
# https://wiki.blender.org/wiki/Process/Addons/Guidelines/metainfo

bl_info = {
    "name": "Set Origin in Edit Mode",
    "description": "Adds a `Set Origin to Selected` option to the right-click menu in Edit Mode",
    "author": "Christopher Kumm",
    "version": (0, 1),
    # TODO: Test the minimum version
    "blender": (2, 93, 0),
    "location": "View3D (Edit Mode) > right-click > Set Origin to Selected",
    "warning": "",  # used for warning icon and text in add-ons panel
    "wiki_url": "https://github.com/ChrisCrossCrash/SetOriginInEditMode",
    "tracker_url": "https://github.com/ChrisCrossCrash/SetOriginInEditMode/issues",
    "support": "COMMUNITY",
    "category": "Object",
}


def get_avg_location(*verts: bmesh.types.BMVert):
    """Return the average location of one or more vertices."""
    result = Vector((0, 0, 0))
    for v in verts:
        result += v.co
    result /= len(verts)
    return result


def set_3d_cursor_to_active_verts(context):
    """Moves the object origin to the average location of the vertices selected in edit mode."""

    # FIXME: Undoing this action takes 3 or more undos when it should take one. Also, it can't be fully re-done
    #  after it has been undone.

    edit_object = context.edit_object
    mesh = edit_object.data
    bm = bmesh.from_edit_mesh(mesh)

    # active_verts are the vertices that are selected in edit mode.
    active_verts = [v for v in bm.verts if v.select]

    if not len(active_verts):
        # TODO: Find a more graceful way of informing the user than raising an exception.
        raise Exception("You must select at least one vertex to change the object origin.")

    # Make a copy of the 3D cursor location so that we can set it back after using it.
    cursor_start = context.scene.cursor.location.copy()

    rotation = edit_object.rotation_euler
    scale = edit_object.scale

    avg_location = get_avg_location(*active_verts)

    # Apply the rotation and scale to avg_location. This makes it possible to add avg_location to the
    # object location in the world space to get the average location relative to the world origin.
    avg_location.rotate(rotation)
    avg_location *= scale

    # Move the 3D cursor to the average location (relative to the world origin).
    bpy.context.scene.cursor.location = edit_object.location + avg_location

    # Switch to object mode, set the object origin to the 3D cursor location, then switch back to edit mode.
    # (I call this trick the "Fastest Gun in the West")
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.mode_set(mode='EDIT')

    # Move the 3D cursor back to its starting location.
    context.scene.cursor.location = cursor_start


# noinspection PyMethodMayBeStatic
class SET_ORIGIN_IN_EDIT_MODE_OT_main_operator(bpy.types.Operator):
    """Moves the object origin to the average location of the vertices selected in edit mode."""
    bl_idname = "set_origin_in_edit_mode.main_operator"
    bl_label = "Set Origin to Selected"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    # noinspection PyUnusedLocal
    def execute(self, context):
        set_3d_cursor_to_active_verts(context)
        return {'FINISHED'}


# noinspection PyUnusedLocal
def draw_menu_item(self, context):
    layout = self.layout
    layout.operator("set_origin_in_edit_mode.main_operator")


def register():
    bpy.utils.register_class(SET_ORIGIN_IN_EDIT_MODE_OT_main_operator)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(draw_menu_item)


def unregister():
    bpy.utils.unregister_class(SET_ORIGIN_IN_EDIT_MODE_OT_main_operator)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(draw_menu_item)


if __name__ == "__main__":
    register()
