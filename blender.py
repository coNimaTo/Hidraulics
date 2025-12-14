"""
render_terrain.py
Blender script to create realistic 3D renders of terrain data.
This script loads height data from a text file and creates a photorealistic render
with proper lighting, shadows, and materials to visualize terrain features like ravines.
"""

import bpy
import numpy as np

def create_realistic_terrain(terrain_file="terrain.txt", output_file="terrain_render.png"):
    """
    Main function to create a photorealistic terrain render in Blender.
    
    Parameters:
    -----------
    terrain_file : str
        Path to the text file containing height data (space-separated matrix)
    output_file : str
        Path where the rendered image will be saved
    """
    
    # ====================================================================
    # STEP 1: Clean the Blender scene
    # ====================================================================
    print("Cleaning scene...")
    # Select all objects in the scene
    bpy.ops.object.select_all(action='SELECT')
    # Delete all objects to start with a clean scene
    bpy.ops.object.delete()
    
    # ====================================================================
    # STEP 2: Load terrain data from text file
    # ====================================================================
    print(f"Loading terrain data from {terrain_file}...")
    # Load the terrain matrix (space-separated values)
    terrain = np.loadtxt(terrain_file)
    # Get dimensions of the terrain
    rows, cols = terrain.shape
    print(f"Terrain dimensions: {rows} rows × {cols} columns")
    print(f"Height range: {terrain.min():.3f} to {terrain.max():.3f}")
    
    # ====================================================================
    # STEP 3: Create the terrain mesh
    # ====================================================================
    print("Creating terrain mesh...")
    
    # List to store all vertices (points in 3D space)
    verts = []
    # List to store all faces (polygons connecting vertices)
    faces = []
    
    # Create vertices from terrain data
    # Each point in the matrix becomes a vertex at position (x, y, height)
    for i in range(rows):
        for j in range(cols):
            # Vertex format: (x, y, z)
            # - j: x-coordinate (column index)
            # - i: y-coordinate (row index, negative so +y is up in Blender)
            # - terrain[i, j] * 2: z-coordinate (height, scaled for visibility)
            verts.append((j, -i, terrain[i, j] * 2))
    
    # Create faces (quads) connecting adjacent vertices
    # Each face connects 4 vertices to form a square
    for i in range(rows - 1):
        for j in range(cols - 1):
            # Calculate indices for the 4 corners of each quad
            v1 = i * cols + j          # Top-left vertex
            v2 = i * cols + (j + 1)    # Top-right vertex
            v3 = (i + 1) * cols + (j + 1)  # Bottom-right vertex
            v4 = (i + 1) * cols + j        # Bottom-left vertex
            
            # Create a face connecting these 4 vertices (in counter-clockwise order)
            faces.append((v1, v2, v3, v4))
    
    # ====================================================================
    # STEP 4: Create Blender mesh object
    # ====================================================================
    print("Creating Blender mesh object...")
    # Create a new mesh data block
    mesh = bpy.data.meshes.new("Terrain")
    # Create a new object using the mesh
    obj = bpy.data.objects.new("Terrain", mesh)
    # Link the object to the current collection (makes it visible)
    bpy.context.collection.objects.link(obj)
    
    # Fill the mesh with our vertices and faces
    mesh.from_pydata(verts, [], faces)
    # Update the mesh with the new data
    mesh.update()
    
    # ====================================================================
    # STEP 5: Apply smooth shading for realistic appearance
    # ====================================================================
    print("Applying smooth shading...")
    # Make the terrain object active
    bpy.context.view_layer.objects.active = obj
    # Select the terrain object
    obj.select_set(True)
    # Apply smooth shading (softens edges between faces)
    bpy.ops.object.shade_smooth()
    
    # ====================================================================
    # STEP 6: Add subdivision surface for smoother geometry
    # ====================================================================
    print("Adding subdivision surface modifier...")
    # Add a subdivision surface modifier to smooth the geometry
    bpy.ops.object.modifier_add(type='SUBSURF')
    # Set subdivision levels (more levels = smoother but heavier)
    obj.modifiers["Subdivision"].levels = 2  # Viewport quality
    obj.modifiers["Subdivision"].render_levels = 3  # Render quality
    
    # ====================================================================
    # STEP 7: Create realistic material for the terrain
    # ====================================================================
    print("Creating terrain material...")
    # Create a new material
    mat = bpy.data.materials.new(name="TerrainMaterial")
    # Enable node-based shading (required for advanced materials)
    mat.use_nodes = True
    # Clear default nodes
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # --------------------------------------------------------
    # Create material nodes for height-based coloring
    # --------------------------------------------------------
    
    # 1. Principled BSDF shader - modern physically-based shader
    shader = nodes.new(type='ShaderNodeBsdfPrincipled')
    shader.location = (0, 0)
    # Configure shader properties
    shader.inputs['Roughness'].default_value = 0.8  # Matte surface
    shader.inputs['Specular'].default_value = 0.2   # Low reflectivity
    
    # 2. Color Ramp node - maps height to color
    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (-400, 0)
    
    # Configure color stops based on elevation:
    # Each element represents a color at a specific height (0-1)
    
    # Element 0: Deep water (lowest elevation)
    color_ramp.color_ramp.elements[0].color = (0.2, 0.4, 0.8, 1)  # Deep blue
    color_ramp.color_ramp.elements[0].position = 0.0
    
    # Element 1: Sand/beach
    color_ramp.color_ramp.elements[1].color = (0.8, 0.7, 0.4, 1)  # Sandy brown
    color_ramp.color_ramp.elements[1].position = 0.2
    
    # Add new element: Grass/forest
    grass_elem = color_ramp.color_ramp.elements.new(position=0.5)
    grass_elem.color = (0.3, 0.6, 0.3, 1)  # Green
    
    # Add new element: Rock/mountain
    rock_elem = color_ramp.color_ramp.elements.new(position=0.8)
    rock_elem.color = (0.5, 0.4, 0.3, 1)  # Brown-gray
    
    # Add new element: Snow (highest elevation)
    snow_elem = color_ramp.color_ramp.elements.new(position=1.0)
    snow_elem.color = (1, 1, 1, 1)  # White
    
    # 3. Geometry node - provides vertex information
    geometry = nodes.new(type='ShaderNodeNewGeometry')
    geometry.location = (-600, 0)
    
    # 4. Separate XYZ node - extracts Z (height) coordinate
    separate_xyz = nodes.new(type='ShaderNodeSeparateXYZ')
    separate_xyz.location = (-400, -200)
    
    # 5. Output node - final material output
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (200, 0)
    
    # --------------------------------------------------------
    # Connect the nodes
    # --------------------------------------------------------
    links = mat.node_tree.links
    
    # Connect geometry position to separate XYZ
    links.new(geometry.outputs['Position'], separate_xyz.inputs[0])
    
    # Connect Z coordinate to color ramp
    links.new(separate_xyz.outputs[2], color_ramp.inputs[0])
    
    # Connect color ramp to shader base color
    links.new(color_ramp.outputs[0], shader.inputs[0])
    
    # Connect shader to output
    links.new(shader.outputs[0], output.inputs[0])
    
    # --------------------------------------------------------
    # Add surface detail (bump mapping)
    # --------------------------------------------------------
    print("Adding surface detail...")
    # Noise texture for micro-surface detail
    noise_texture = nodes.new(type='ShaderNodeTexNoise')
    noise_texture.location = (-400, -400)
    noise_texture.inputs['Scale'].default_value = 50.0  # Texture scale
    
    # Bump node to create the illusion of small surface variations
    bump = nodes.new(type='ShaderNodeBump')
    bump.location = (-200, -400)
    bump.inputs['Strength'].default_value = 0.1  # How pronounced the bumps are
    
    # Connect noise to bump to shader normal
    links.new(noise_texture.outputs[0], bump.inputs[2])
    links.new(bump.outputs[0], shader.inputs[22])  # Normal input
    
    # Apply the material to the terrain object
    obj.data.materials.append(mat)
    
    # ====================================================================
    # STEP 8: Setup lighting for dramatic shadows in ravines
    # ====================================================================
    print("Setting up lighting...")
    
    # 1. Sun light (main directional light - like real sun)
    bpy.ops.object.light_add(type='SUN', location=(10, 10, 20))
    sun = bpy.context.object
    sun.data.energy = 5.0  # Light intensity
    # Set sun angle: lower angle = longer shadows (better for showing ravines)
    sun.rotation_euler = (0.8, 0, 0.5)  # (x, y, z) rotation in radians
    
    # 2. Fill light (softens harsh shadows)
    bpy.ops.object.light_add(type='AREA', location=(-10, -10, 15))
    fill_light = bpy.context.object
    fill_light.data.energy = 2.0  # Softer light
    fill_light.data.size = 5.0    # Larger light source = softer shadows
    
    # ====================================================================
    # STEP 9: Setup camera for optimal viewing
    # ====================================================================
    print("Setting up camera...")
    # Add camera to scene
    bpy.ops.object.camera_add(location=(cols/2, -rows*1.5, rows/2))
    camera = bpy.context.object
    # Point camera downward to see terrain
    camera.rotation_euler = (1.1, 0, 0)  # (x, y, z) - x controls look-down angle
    
    # Make this camera the active scene camera
    bpy.context.scene.camera = camera
    
    # ====================================================================
    # STEP 10: Setup world/environment
    # ====================================================================
    print("Setting up environment...")
    # Get the scene's world settings
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    # Enable node-based world settings
    world.use_nodes = True
    # Get the background node
    env = world.node_tree.nodes['Background']
    # Set sky color
    env.inputs['Color'].default_value = (0.8, 0.9, 1, 1)  # Light blue sky
    env.inputs['Strength'].default_value = 0.5  # Sky brightness
    
    # Add atmospheric mist/fog (enhances depth perception)
    bpy.context.scene.render.use_mist = True
    bpy.context.scene.mist_settings.start = 0  # Where fog begins
    bpy.context.scene.mist_settings.depth = rows * 2  # How far fog reaches
    bpy.context.scene.mist_settings.falloff = 'QUADRATIC'  # How fog fades
    
    # ====================================================================
    # STEP 11: Configure render settings
    # ====================================================================
    print("Configuring render settings...")
    # Use Cycles render engine (ray-tracing for realistic shadows)
    bpy.context.scene.render.engine = 'CYCLES'
    
    # Set render quality
    bpy.context.scene.cycles.samples = 128  # More samples = better quality but slower
    bpy.context.scene.cycles.preview_samples = 32  # Viewport samples
    
    # Enable denoising (cleans up noise in shadows)
    bpy.context.scene.cycles.use_denoising = True
    
    # Set output resolution
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.resolution_percentage = 100  # 100% of resolution
    
    # Set output file format
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.image_settings.color_mode = 'RGB'
    bpy.context.scene.render.image_settings.color_depth = '8'
    
    # Set output file path
    bpy.context.scene.render.filepath = output_file
    
    # ====================================================================
    # STEP 12: Render the scene
    # ====================================================================
    print(f"Rendering to {output_file}...")
    print("This may take a few minutes depending on terrain size...")
    
    # Perform the render
    bpy.ops.render.render(write_still=True)
    
    print("=" * 50)
    print("RENDER COMPLETE!")
    print(f"Image saved to: {output_file}")
    print("=" * 50)
    
    # Print some tips for improvement
    print("\nTips for better ravine visibility:")
    print("1. Lower the sun angle: sun.rotation_euler = (0.3, 0, 0)")
    print("2. Increase height scale: terrain[i, j] * 3 (instead of * 2)")
    print("3. Reduce fill light: fill_light.data.energy = 1.0")
    print("4. Move camera closer to ground")

# ====================================================================
# Main execution
# ====================================================================
if __name__ == "__main__":
    # You can customize these paths:
    terrain_file = "terrain.txt"      # Your terrain data file
    output_file = "terrain_render.png"  # Where to save the render
    
    # Run the terrain creation function
    create_realistic_terrain(terrain_file, output_file)
    
    # Optional: Keep Blender open after rendering (for GUI mode)
    # Comment out if running in background mode
    # print("Script complete. Close Blender or check the rendered image.")