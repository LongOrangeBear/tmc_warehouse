import os
import sys
import shutil
import subprocess
from pathlib import Path

def run_command(command):
    print(f"Running: {command}")
    subprocess.check_call(command, shell=True)

def main():
    print("Starting build process...")
    
    # Check for PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        run_command(f"{sys.executable} -m pip install pyinstaller")

    # Define paths
    root_dir = Path(__file__).parent
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"
    
    # Clean previous builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
        
    # Build Client
    print("\nBuilding Client...")
    # --noconsole for GUI, --onefile or --onedir? 
    # --onedir is better for debugging and faster startup usually, but --onefile is requested as "exe files".
    # However, with config files, --onedir is often easier to manage.
    # Let's go with --onedir for now as it's more robust for assets, but user asked for "exe files".
    # I'll do --onedir and name the folder "TMC_Client".
    
    # Note: We need to include 'common' and 'client' and 'server' packages.
    # PyInstaller usually finds them if in path.
    
    client_cmd = (
        f"pyinstaller --noconfirm --onedir --windowed --name TMC_Client "
        f"--add-data \"config{os.pathsep}config\" "  # Include config in the bundle (optional, but good)
        f"--hidden-import=common "
        f"--hidden-import=client "
        f"client/src/main_client.py"
    )
    run_command(client_cmd)
    
    # Build Server
    print("\nBuilding Server...")
    # Server needs console usually to see logs, or maybe not. Let's keep console for server.
    server_cmd = (
        f"pyinstaller --noconfirm --onedir --console --name TMC_Server "
        f"--add-data \"config{os.pathsep}config\" "
        f"--hidden-import=common "
        f"--hidden-import=server "
        f"--hidden-import=uvicorn "
        f"server/src/main_server.py"
    )
    run_command(server_cmd)
    
    # Copy external resources if needed (like if we want config to be editable outside)
    # We put config INSIDE the bundle with --add-data above.
    # But our code looks for config NEXT to the exe as well.
    
    # Let's create a "Release" folder
    release_dir = dist_dir / "Release"
    release_dir.mkdir(exist_ok=True)
    
    # Move built apps to Release
    shutil.move(dist_dir / "TMC_Client", release_dir / "TMC_Client")
    shutil.move(dist_dir / "TMC_Server", release_dir / "TMC_Server")
    
    # Copy config to Release root so it's editable
    shutil.copytree(root_dir / "config", release_dir / "config", dirs_exist_ok=True)
    
    # Create data dir
    (release_dir / "data").mkdir(exist_ok=True)
    
    print(f"\nBuild complete! Files are in {release_dir}")
    print("You can zip the 'Release' folder and move it to another computer.")

if __name__ == "__main__":
    main()
