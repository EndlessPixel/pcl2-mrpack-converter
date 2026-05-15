import os
import zipfile
import json
import shutil
SRC_FOLDER = "."
TMP_DIR = "./_tmp_extract"
OUT_FOLDER = "./fixed_packs"
BLOCK_HOST = "forgecdn.net"
def clear_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)
def process_mrpack(zip_path, out_name):
    clear_dir(TMP_DIR)
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(TMP_DIR)
    except:
        return
    json_path = os.path.join(TMP_DIR, "modrinth.index.json")
    if not os.path.exists(json_path):
        return
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "files" in data:
        for item in data["files"]:
            if "downloads" in item:
                # 只删除 forgecdn 链接
                item["downloads"] = [
                    link for link in item["downloads"]
                    if BLOCK_HOST not in link
                ]
            else:
                item["downloads"] = []
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    out_path = os.path.join(OUT_FOLDER, f"{out_name}.mrpack")
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(TMP_DIR):
            for file in files:
                full = os.path.join(root, file)
                arc = os.path.relpath(full, TMP_DIR)
                zf.write(full, arc)
def main():
    clear_dir(OUT_FOLDER)

    for fname in os.listdir(SRC_FOLDER):
        lower = fname.lower()
        if not lower.endswith((".zip", ".mrpack")):
            continue
        full_path = os.path.join(SRC_FOLDER, fname)
        name = os.path.splitext(fname)[0]
        process_mrpack(full_path, name)
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
if __name__ == "__main__":
    main()