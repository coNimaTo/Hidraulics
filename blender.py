"""
interactive_terrain.py
Load terrain into Blender GUI for interactive editing.
Run this from Blender's Scripting workspace.
"""

import bpy
import numpy as np
import os

class TerrainImporter:
    """GUI-friendly terrain importer with interactive controls"""
    
    def __init__(self):
        self.terrain = None
        self.rows = 0
        self.cols = 0
        self.obj = None
        
    def load_terrain(self, filepath):
        """Load terrain from text file"""
        print(f"Loading terrain from {filepath}")
        
        try:
            # Load terrain data
            self.terrain = np.loadtxt(filepath)
            self.rows, self.cols = self.terrain.shape
            
            print(f"✓ Loaded terrain: {self.rows}x{self.cols}")
            print(f"  Height range: {self.terrain.min():.3f} to {self.terrain.max():.3f}")
            
            return True
        except Exception as e:
            print(f"✗ Error loading terrain: {e}")
            return False
    
    def create_mesh(self, height_scale=2.0, name="Terrain"):
        """Create mesh from terrain data"""
        if self.terrain is None:
            print("✗ No terrain data loaded!")
            return None
        
        print(f"Creating mesh with height scale: {height_scale}")
        
        # Clear any existing terrain with same name
        if name in bpy.data.objects:
            old_obj = bpy.data.objects[name]
            bpy.data.objects.remove(old_obj, do_unlink=True)
        
        # Create mesh data
        mesh = bpy.data.meshes.new(name)
        self.obj = bpy.data.objects.new(name, mesh)
        
        # Create vertices
        verts = []
        faces = []
        
        for i in range(self.rows):
            for j in range(self.cols):
                # Create vertex (x, y, height)
                verts.append((j, -i, self.terrain[i, j] * height_scale))
        
        # Create faces (quads)
        for i in range(self.rows - 1):
            for j in range(self.cols - 1):
                v1 = i * self.cols + j
                v2 = i * self.cols + (j + 1)
                v3 = (i + 1) * self.cols + (j + 1)
                v4 = (i + 1) * self.cols + j
                faces.append((v1, v2, v3, v4))
        
        # Build mesh
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        
        # Link to scene
        bpy.context.collection.objects.link(self.obj)
        
        # Select and make active
        bpy.context.view_layer.objects.active = self.obj
        self.obj.select_set(True)
        
        # Apply smooth shading
        bpy.ops.object.shade_smooth()
        
        print(f"✓ Created terrain mesh: {len(verts)} vertices, {len(faces)} faces")
        return self.obj
    
    def add_default_material(self):
        """Add a simple material to the terrain"""
        if self.obj is None:
            return
        
        # Create or get material
        mat_name = "TerrainMaterial"
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
        else:
            mat = bpy.data.materials.new(name=mat_name)
            mat.diffuse_color = (0.3, 0.6, 0.3, 1)  # Green
        
        # Assign material
        if self.obj.data.materials:
            self.obj.data.materials[0] = mat
        else:
            self.obj.data.materials.append(mat)
        
        print("✓ Added default material")
    
    def setup_camera(self):
        """Setup camera to look at terrain"""
        if self.obj is None:
            return
        
        # Create or get camera
        cam_name = "TerrainCamera"
        if cam_name in bpy.data.objects:
            camera = bpy.data.objects[cam_name]
        else:
            bpy.ops.object.camera_add(location=(0, 0, 0))
            camera = bpy.context.object
            camera.name = cam_name
        
        # Position camera
        camera.location = (self.cols/2, -self.rows*2, self.rows)
        camera.rotation_euler = (1.0, 0, 0)  # Look downward
        
        # Make it active camera
        bpy.context.scene.camera = camera
        
        print("✓ Camera setup complete")
    
    def setup_lighting(self):
        """Add basic lighting"""
        # Sun light
        if "Sun" not in bpy.data.objects:
            bpy.ops.object.light_add(type='SUN', location=(10, 10, 20))
            sun = bpy.context.object
            sun.name = "Sun"
            sun.data.energy = 3.0
        
        print("✓ Basic lighting added")
    
    def import_complete(self, filepath, height_scale=2.0):
        """Complete import process"""
        if not self.load_terrain(filepath):
            return False
        
        self.create_mesh(height_scale)
        self.add_default_material()
        self.setup_camera()
        self.setup_lighting()
        
        # Center view on terrain
        bpy.ops.view3d.view_selected()
        
        print("\n" + "="*50)
        print("TERRAIN IMPORT COMPLETE!")
        print("="*50)
        print(f"File: {os.path.basename(filepath)}")
        print(f"Size: {self.rows} x {self.cols}")
        print(f"Object: {self.obj.name}")
        print("\nYou can now:")
        print("1. Switch to Layout tab to see the terrain")
        print("2. Adjust materials in Shader Editor")
        print("3. Modify lighting in the 3D Viewport")
        print("4. Press F12 to render")
        
        return True


# ====================================================================
# GUI PANEL for Blender (Appears in 3D Viewport sidebar)
# ====================================================================

import bpy
from bpy.types import Panel, Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, FloatProperty

class IMPORT_OT_terrain(Operator, ImportHelper):
    """Operator to import terrain from text file"""
    bl_idname = "import.terrain_data"
    bl_label = "Import Terrain"
    bl_description = "Load terrain height data from text file"
    
    # Filter for text files
    filter_glob: StringProperty(
        default="*.txt",
        options={'HIDDEN'},
    )
    
    # File path property
    filepath: StringProperty(
        name="File Path",
        description="Path to terrain data file",
        maxlen=1024,
        default="",
    )
    
    # Height scale property
    height_scale: FloatProperty(
        name="Height Scale",
        description="Scale factor for terrain height",
        default=50.0,
        min=0.1,
        max=50.0,
    )
    
    def execute(self, context):
        """Execute the import operation"""
        importer = TerrainImporter()
        success = importer.import_complete(self.filepath, self.height_scale)
        
        if success:
            self.report({'INFO'}, f"Terrain imported successfully!")
            # Force viewport update
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        else:
            self.report({'ERROR'}, "Failed to import terrain")
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        """Open file browser"""
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class VIEW3D_PT_terrain_importer(Panel):
    """Panel in 3D Viewport sidebar for terrain import"""
    bl_label = "Terrain Importer"
    bl_idname = "VIEW3D_PT_terrain_importer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Terrain"
    
    def draw(self, context):
        layout = self.layout
        
        # Import button
        col = layout.column(align=True)
        col.operator("import.terrain_data", text="Import Terrain", icon='IMPORT')
        
        # Quick actions if terrain exists
        terrain_obj = None
        for obj in bpy.data.objects:
            if "Terrain" in obj.name:
                terrain_obj = obj
                break
        
        if terrain_obj:
            box = layout.box()
            box.label(text="Terrain Actions", icon='MODIFIER')
            
            row = box.row()
            row.operator("object.shade_smooth", text="Smooth")
            row.operator("object.shade_flat", text="Flat")
            
            box.operator("view3d.view_selected", text="Focus View")
            
            # Material buttons
            box.label(text="Materials:", icon='MATERIAL')
            row = box.row()
            row.operator("terrain.add_height_material", text="Height Map")
            # row.operator("terrain.add_rock_material", text="Rock")

# ====================================================================
# Additional operators for terrain manipulation
# ====================================================================

class TERRAIN_OT_add_height_material(Operator):
    """Add height-based color material"""
    bl_idname = "terrain.add_height_material"
    bl_label = "Add Height Material"
    
    def execute(self, context):
        # Find terrain object
        terrain_obj = None
        for obj in bpy.data.objects:
            if "Terrain" in obj.name:
                terrain_obj = obj
                break
        
        if not terrain_obj:
            self.report({'WARNING'}, "No terrain object found")
            return {'CANCELLED'}
        
        # Create node-based material
        mat = bpy.data.materials.new(name="Terrain_Height")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        # Add nodes
        output = nodes.new(type='ShaderNodeOutputMaterial')
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        color_ramp = nodes.new(type='ShaderNodeValToRGB')
        separate = nodes.new(type='ShaderNodeSeparateXYZ')
        geometry = nodes.new(type='ShaderNodeNewGeometry')
        
        # Position nodes
        output.location = (300, 0)
        bsdf.location = (100, 0)
        color_ramp.location = (-100, 0)
        separate.location = (-300, 0)
        geometry.location = (-500, 0)
        
        # Connect nodes
        links = mat.node_tree.links
        links.new(geometry.outputs['Position'], separate.inputs[0])
        links.new(separate.outputs[2], color_ramp.inputs[0])
        links.new(color_ramp.outputs[0], bsdf.inputs[0])
        links.new(bsdf.outputs[0], output.inputs[0])
        
        # Setup color ramp
        color_ramp.color_ramp.elements[0].color = (0.1, 0.2, 0.8, 1)  # Water
        color_ramp.color_ramp.elements[1].color = (0.3, 0.6, 0.3, 1)  # Grass
        
        # Assign material
        terrain_obj.data.materials.clear()
        terrain_obj.data.materials.append(mat)
        
        self.report({'INFO'}, "Height-based material added")
        return {'FINISHED'}


class TERRAIN_OT_quick_render(Operator):
    """Quick render from current view"""
    bl_idname = "terrain.quick_render"
    bl_label = "Quick Render"
    
    def execute(self, context):
        # Setup quick render settings
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.samples = 64  # Quick render
        bpy.context.scene.render.resolution_x = 1280
        bpy.context.scene.render.resolution_y = 720
        
        # Render
        bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)
        
        self.report({'INFO'}, "Rendering...")
        return {'FINISHED'}

# ====================================================================
# Registration and main execution
# ====================================================================

def register():
    """Register operators and panel"""
    bpy.utils.register_class(IMPORT_OT_terrain)
    bpy.utils.register_class(VIEW3D_PT_terrain_importer)
    bpy.utils.register_class(TERRAIN_OT_add_height_material)
    bpy.utils.register_class(TERRAIN_OT_quick_render)
    print("Terrain Importer registered!")

def unregister():
    """Unregister operators and panel"""
    bpy.utils.unregister_class(IMPORT_OT_terrain)
    bpy.utils.unregister_class(VIEW3D_PT_terrain_importer)
    bpy.utils.unregister_class(TERRAIN_OT_add_height_material)
    bpy.utils.unregister_class(TERRAIN_OT_quick_render)
    print("Terrain Importer unregistered!")

# ====================================================================
# Simple direct import function (without GUI panel)
# ====================================================================

def quick_import_terrain(filepath="terrain.txt", height_scale=2.0):
    """
    Quick function to import terrain without GUI panel.
    Run this directly from Blender's Python console.
    """
    importer = TerrainImporter()
    success = importer.import_complete(filepath, height_scale)
    
    if success:
        print("✓ Terrain imported successfully!")
        print("Switch to Layout tab to see it.")
    else:
        print("✗ Failed to import terrain")
    
    return success


# ====================================================================
# Main execution - Choose your method
# ====================================================================

if __name__ == "__main__":
    # METHOD 1: Register GUI panel (keeps it available in Blender)
    register()
    
    # METHOD 2: Direct import (uncomment and modify as needed)
    # quick_import_terrain("C:/path/to/your/terrain.txt", height_scale=2.0)
    
    print("\n" + "="*50)
    print("TERRAIN IMPORTER READY!")
    print("="*50)
    print("\nTo import terrain:")
    print("1. Go to 3D Viewport")
    print("2. Press N to open sidebar")
    print("3. Click 'Terrain' tab")
    print("4. Click 'Import Terrain' button")
    print("\nOR run from Python console:")
    print("quick_import_terrain('terrain.txt', 2.0)")