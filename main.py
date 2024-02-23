from cement import App, Controller, ex
import numpy as np
import trimesh
import tarfile
import os
import tempfile
import shutil

class MyBaseController(Controller):
    class Meta:
        label = 'base'
        arguments=[
            (['-l', '--length'], {'help': 'Internal length of the box', 'type': float}),
            (['-w', '--width'], {'help': 'Internal width of the box', 'type': float}),
            (['-H', '--height'], {'help': 'Internal height of the box', 'type': float}),
            (['-t', '--thickness'], {'help': 'Wall thickness', 'type': float, 'default': 2.0}),
            (['-o', '--overlap'], {'help': 'Lid overlap', 'type': float, 'default': 2.0}),
            (['-lh', '--lid_height'], {'help': 'Lid height', 'type': float, 'default': 5.0}),
        ]

    @ex(help='create box with lid')
    def _default(self):
        """Create a 3D box with a lid based on provided dimensions."""
        # Extracting the user-provided dimensions from the command line
        length = self.app.pargs.length
        width = self.app.pargs.width
        height = self.app.pargs.height
        thickness = self.app.pargs.thickness
        overlap = self.app.pargs.overlap
        lid_height = self.app.pargs.lid_height

        # Ensure all required dimensions are provided
        if length is None or width is None or height is None:
            print("Please provide the internal length, width, and height of the box.")
            return

        # Create temporary directory for STL files
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Generate STL files in the temporary directory
            file_basename = f"box_{length}x{width}x{height}"
            create_full_box_with_lid(tmpdirname, length, width, height, thickness, overlap, lid_height)

            file_basename = f"box_{length}x{width}x{height}"  # Ensure this base name format is correct
            files_to_include = [
                os.path.join(tmpdirname, f'box_base_{length}x{width}x{height}.stl'),
                os.path.join(tmpdirname, f'box_lid_{length}x{width}x{height}.stl'),
                os.path.join(tmpdirname, 'README.txt')
            ]

            # Create a README.txt file
            with open(files_to_include[-1], 'w') as readme:
                readme.write("Box and Lid STL files created with specified dimensions.\n")
                readme.write(f"Length: {length}, Width: {width}, Height: {height}\n")
                readme.write(f"Wall Thickness: {thickness}, Lid Overlap: {overlap}, Lid Height: {lid_height}\n")

            # Ensure the archive directory exists
            archive_dir = 'archive'
            if not os.path.exists(archive_dir):
                os.makedirs(archive_dir)

            # Create the tar.gz file in the archive directory
            output_filename = os.path.join(archive_dir, f'{file_basename}.tar.gz')
            create_tar_gz(output_filename, files_to_include)
            for file in files_to_include:
                shutil.move(file, archive_dir)
    
def create_tar_gz(output_filename, files):
    with tarfile.open(output_filename, "w:gz") as tar:
        for file in files:
            tar.add(file, arcname=os.path.basename(file))
            # os.remove(file)  # Delete the file after adding it to the archive
        print(f"Created and archived {output_filename}")

def create_full_box_with_lid(tmpdirname, internal_length, internal_width, internal_height, wall_thickness=2.0, lid_overlap=2.0, lid_height=5.0):
    # File names include dimensions for clarity
    base_filename = f'box_base_{internal_length}x{internal_width}x{internal_height}.stl'
    lid_filename = f'box_lid_{internal_length}x{internal_width}x{internal_height}.stl'
    
    # External dimensions for the base
    external_length = internal_length + 2 * wall_thickness
    external_width = internal_width + 2 * wall_thickness
    base_height = internal_height + wall_thickness  # Base height includes bottom thickness

    # Create and export the full box base
    base_outer = trimesh.creation.box((external_length, external_width, base_height))
    base_inner = trimesh.creation.box((internal_length, internal_width, internal_height))
    base_inner.apply_translation((wall_thickness - 2, wall_thickness - 2, wall_thickness / 2))
    box_base = base_outer.difference(base_inner)
    box_base.export(os.path.join(tmpdirname, base_filename))

    # External dimensions for the lid, accounting for overlap
    lid_external_length = external_length + 2 * lid_overlap
    lid_external_width = external_width + 2 * lid_overlap
    lid_total_height = lid_height  # Total height of the lid, no need to add wall thickness here for cavity creation

    # Create the full lid outer part
    lid_outer = trimesh.creation.box((lid_external_length, lid_external_width, lid_total_height))

    # Dimensions for the inner cavity of the lid, matching the external dimensions of the base for a snug fit
    lid_inner_length = external_length + 0.15 # Same as base external length for snug fit
    lid_inner_width = external_width + 0.15 # Same as base external width for snug fit 
    lid_inner_height = lid_height - (wall_thickness / 2)  # Height of the cavity inside the lid

    # Create the cavity inside the lid by subtracting a box that matches the outer dimensions of the base
    lid_inner = trimesh.creation.box((lid_inner_length, lid_inner_width, lid_inner_height))
    lid_inner.apply_translation((lid_overlap - 2, lid_overlap - 2, wall_thickness / 2))  # Position the inner lid cavity correctly within the outer lid

    # Subtract the inner lid from the outer lid to create the lid with cavity
    box_lid = lid_outer.difference(lid_inner)
    box_lid.export(os.path.join(tmpdirname, lid_filename))

    # Print paths of the exported files
    print(f"Exported box base to {os.path.join(tmpdirname, base_filename)}")
    print(f"Exported box lid to {os.path.join(tmpdirname, lid_filename)}")



class MyApp(App):
    class Meta:
        label = 'myapp'
        base_controller = 'base'
        handlers = [MyBaseController]

if __name__ == '__main__':
    with MyApp() as app:
        app.run()
