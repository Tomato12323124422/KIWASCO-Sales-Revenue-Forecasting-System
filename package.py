import os
import subprocess
import shutil
import sys

def build():
    print("🚀 Starting Stand-alone Build Process...")
    
    # Get absolute paths to avoid confusion with spaces/special characters
    root_dir = os.path.abspath(os.getcwd())
    frontend_dir = os.path.join(root_dir, "frontend")
    backend_dir = os.path.join(root_dir, "backend")

    # 1. Build Frontend
    print(f"\n📦 Building Frontend in: {frontend_dir}")
    os.chdir(frontend_dir)
    
    # Use shell=True with triple quotes for Windows path safety
    try:
        print("   > Running npm install...")
        subprocess.run('npm install', shell=True, check=True)
        print("   > Running npm run build...")
        subprocess.run('npm run build', shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Frontend build failed: {e}")
        sys.exit(1)
    
    os.chdir(root_dir)

    # 2. Package with PyInstaller
    print("\n🔨 Packaging with PyInstaller...")
    
    # Define data files with quotes for Windows
    # Syntax: "source;destination"
    frontend_data = f"{os.path.join(frontend_dir, 'dist')}{os.pathsep}{os.path.join('frontend', 'dist')}"
    backend_data = f"{os.path.join(backend_dir, 'app')}{os.pathsep}app"
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--name=KIWASCO-Forecasting-System",
        f"--add-data={frontend_data}",
        f"--add-data={backend_data}",
        os.path.join(backend_dir, "app", "main.py")
    ]
    
    print(f"   > Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Build Complete! Your stand-alone app is in the 'dist' folder.")
        print("Path: " + os.path.join(root_dir, "dist", "KIWASCO-Forecasting-System.exe"))
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Packaging failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
