import os
import subprocess
import shutil

def build():
    print("🚀 Starting Stand-alone Build Process...")

    # 1. Build Frontend
    print("\n📦 Building Frontend...")
    os.chdir("frontend")
    subprocess.run("npm install && npm run build", shell=True, check=True)
    os.chdir("..")

    # 2. Package with PyInstaller
    print("\n🔨 Packaging with PyInstaller...")
    # We bundle the backend and tell PyInstaller to include the frontend/dist folder
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--name=KIWASCO-Forecasting-System",
        "--add-data=frontend/dist;frontend/dist",
        "--add-data=backend/app;app",
        "backend/app/main.py"
    ]
    
    subprocess.run(" ".join(cmd), shell=True, check=True)

    print("\n✅ Build Complete! Your stand-alone app is in the 'dist' folder.")
    print("You can now run 'KIWASCO-Forecasting-System.exe' without any internet or servers!")

if __name__ == "__main__":
    build()
