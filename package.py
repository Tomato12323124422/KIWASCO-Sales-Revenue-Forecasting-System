import os
import subprocess
import shutil
import sys

def build():
    print("🚀 Starting Stand-alone Build Process...")

    # Get absolute paths
    root_dir = os.path.abspath(os.getcwd())
    frontend_dir = os.path.join(root_dir, "frontend")
    backend_dir = os.path.join(root_dir, "backend")

    # 1. Build Frontend — call vite DIRECTLY to avoid npm path-splitting issues
    print(f"\n📦 Building Frontend in: {frontend_dir}")

    # Path to vite executable inside node_modules
    vite_script = os.path.join(frontend_dir, "node_modules", "vite", "bin", "vite.js")

    if not os.path.exists(vite_script):
        print("   > node_modules not found. Running npm install first...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)

    if not os.path.exists(vite_script):
        print(f"❌ Vite not found at: {vite_script}")
        sys.exit(1)

    print("   > Running vite build directly...")
    try:
        # Call node with the vite.js script directly — no shell, no path splitting
        subprocess.run(
            ["node", vite_script, "build"],
            cwd=frontend_dir,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Frontend build failed: {e}")
        sys.exit(1)

    print("   ✔ Frontend built successfully!")

    # 2. Package with PyInstaller
    print("\n🔨 Packaging with PyInstaller...")
    dist_src = os.path.join(frontend_dir, "dist")
    dist_dst  = os.path.join("frontend", "dist")

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--name=KIWASCO-Forecasting-System",
        f"--add-data={dist_src}{os.pathsep}{dist_dst}",
        os.path.join(backend_dir, "app", "main.py")
    ]

    try:
        subprocess.run(cmd, check=True)
        exe_path = os.path.join(root_dir, "dist", "KIWASCO-Forecasting-System.exe")
        print(f"\n✅ Build Complete!")
        print(f"   Your standalone app is at: {exe_path}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Packaging failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
