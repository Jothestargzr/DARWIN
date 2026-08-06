import os
import zipfile
import time

ROOT_DIR = '/Users/joelagyeman/Darwin'
OUTPUT_ZIP = '/Users/joelagyeman/Downloads/DARWIN_Full_Repo_With_Git.zip'

EXCLUDE_DIRS = {'DARWIN_DOCX_COPIES', 'DOCX_Documentation'}
EXCLUDE_EXTS = {'.docx', '.zip'}

def main():
    print(f"🚀 Starting Full Repository ZIP Creation...")
    print(f"Source: {ROOT_DIR}")
    print(f"Target: {OUTPUT_ZIP}")
    print("Including: Complete .git history, node_modules, build configs, source files.")
    print("Excluding: DOCX copies & docx documentation.")

    start_time = time.time()
    file_count = 0

    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for dirpath, dirnames, filenames in os.walk(ROOT_DIR):
            # Exclude DOCX folders
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            rel_dir = os.path.relpath(dirpath, ROOT_DIR)

            for f in filenames:
                ext = os.path.splitext(f)[1].lower()
                if ext in EXCLUDE_EXTS:
                    continue

                full_path = os.path.join(dirpath, f)
                rel_path = os.path.normpath(os.path.join(rel_dir, f)) if rel_dir != '.' else f
                
                # Exclude output zip itself if inside
                if full_path == OUTPUT_ZIP:
                    continue

                zf.write(full_path, arcname=os.path.join('DARWIN', rel_path))
                file_count += 1

                if file_count % 1000 == 0:
                    print(f"Packed {file_count} files...")

    elapsed = time.time() - start_time
    size_mb = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)

    print("\n==========================================")
    print("🎉 FULL DARWIN REPO ZIP CREATION COMPLETE!")
    print(f"✅ Total Files Packed: {file_count}")
    print(f"📦 Archive Size: {size_mb:.2f} MB")
    print(f"⏱️ Time Taken: {elapsed:.2f} seconds")
    print(f"📁 Saved to: {OUTPUT_ZIP}")
    print("==========================================")

if __name__ == "__main__":
    main()
