import os
import zipfile
import datetime

def zip_project():
    # 1. Name the output file with a timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    zip_filename = f"MediBot_Project_{timestamp}.zip"
    
    # 2. Define what to IGNORE (Crucial!)
    ignore_folders = {
        "medibot_env", "venv", "env", ".git", "__pycache__", 
        ".idea", ".vscode", "node_modules"
    }
    ignore_extensions = {".pyc", ".zip", ".rar"}

    print(f"📦 Packing project into: {zip_filename}...")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through every file in the current directory
        for root, dirs, files in os.walk("."):
            # A. Remove ignored folders from the list so we don't even enter them
            dirs[:] = [d for d in dirs if d not in ignore_folders]
            
            for file in files:
                # B. Skip ignored extensions and the script itself
                if file == zip_filename or file == "packager.py":
                    continue
                if any(file.endswith(ext) for ext in ignore_extensions):
                    continue
                
                # C. Create the path inside the zip
                file_path = os.path.join(root, file)
                print(f"  + Adding: {file}")
                zipf.write(file_path, arcname=os.path.relpath(file_path, "."))

    print(f"\n✅ SUCCESS! Sent '{zip_filename}' to your friend.")
    print("📝 Tell them to run: 'pip install -r requirements.txt' first.")

if __name__ == "__main__":
    zip_project()