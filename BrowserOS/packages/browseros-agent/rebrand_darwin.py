import os

TARGET_DIR = "/Users/joelagyeman/Library/Mobile Documents/com~apple~CloudDocs/Darwin/BrowserOS/packages/browseros-agent/apps/app"
IGNORE_DIRS = {'node_modules', '.git', 'dist', 'build', 'out', '.next', '.wxt'}

def should_skip_line(line: str) -> bool:
    skip_keywords = [
        "import ", "from '", 'from "', "require(", 
        "@browseros", "browseros-agent", "browseros-server",
        "package.json", "https://api.browseros.com"
    ]
    return any(kw in line for kw in skip_keywords)

def replace_in_file(filepath: str):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    modified = False
    new_lines = []
    
    for line in lines:
        if "BrowserOS" in line or "Browser OS" in line:
            if not should_skip_line(line):
                original_line = line
                line = line.replace("BrowserOS", "DARWIN")
                line = line.replace("Browser OS", "DARWIN")
                if line != original_line:
                    modified = True
        new_lines.append(line)
        
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"[+] Rebranded: {filepath}")

def main():
    print("🚀 Starting Optimized DARWIN Rebrand Sequence...")
    for root, dirs, files in os.walk(TARGET_DIR):
        # Extremely fast directory pruning to avoid iCloud crawl timeouts
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
        for file in files:
            if file.endswith((".tsx", ".ts", ".html", ".css", ".md", ".json")):
                filepath = os.path.join(root, file)
                try:
                    replace_in_file(filepath)
                except Exception as e:
                    pass

if __name__ == "__main__":
    main()
