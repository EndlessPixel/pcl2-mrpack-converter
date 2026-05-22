import os
import zipfile
import json
import shutil
from datetime import datetime

# 颜色常量
class LogColor:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    WHITE = "\033[97m"
    RESET = "\033[0m"

SRC_FOLDER = "."
TMP_DIR = "./_tmp_extract"
OUT_FOLDER = "./fixed_packs"
BLOCK_HOST = "forgecdn.net"
DELETE_FOLDERS = [
    os.path.join("overrides", "PCL"),
]

# 带时间戳的日志函数
def get_time():
    return datetime.now().strftime("%H:%M:%S")

def log_info(msg):
    print(f"[{get_time()}] {LogColor.BLUE}[INFO] {msg}{LogColor.RESET}")

def log_debug(msg):
    print(f"[{get_time()}] {LogColor.WHITE}[DEBUG] {msg}{LogColor.RESET}")

def log_warn(msg):
    print(f"[{get_time()}] {LogColor.YELLOW}[WARNING] {msg}{LogColor.RESET}")

def log_error(msg):
    print(f"[{get_time()}] {LogColor.RED}[ERROR] {msg}{LogColor.RESET}")

def log_success(msg):
    print(f"[{get_time()}] {LogColor.GREEN}[SUCCESS] {msg}{LogColor.RESET}")

def clear_dir(path):
    log_debug(f"清理目录：{path}")
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)

def process_mrpack(zip_path, out_name):
    log_info(f"开始处理模组包：{os.path.basename(zip_path)}")
    clear_dir(TMP_DIR)
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(TMP_DIR)
        log_debug("压缩包解压完成")
    except Exception as e:
        log_error(f"解压失败：{str(e)}")
        return

    for del_folder in DELETE_FOLDERS:
        del_path = os.path.join(TMP_DIR, del_folder)
        if os.path.exists(del_path):
            shutil.rmtree(del_path)
            log_info(f"已删除目录：{del_folder}")
        else:
            log_debug(f"目录不存在，跳过删除：{del_folder}")

    json_path = os.path.join(TMP_DIR, "modrinth.index.json")
    if not os.path.exists(json_path):
        log_warn("未找到模组索引文件，跳过处理")
        return

    log_debug("读取模组索引配置")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    filter_cnt = 0
    if "files" in data:
        for item in data["files"]:
            if "downloads" in item:
                old_len = len(item["downloads"])
                item["downloads"] = [
                    link for link in item["downloads"]
                    if BLOCK_HOST not in link
                ]
                filter_cnt += old_len - len(item["downloads"])
            else:
                item["downloads"] = []
    log_info(f"过滤 {filter_cnt} 条非法下载链接")

    log_debug("写入修改后的索引文件")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    out_path = os.path.join(OUT_FOLDER, f"{out_name}.mrpack")
    log_info(f"重新打包输出：{os.path.basename(out_path)}")
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(TMP_DIR):
            for file in files:
                full = os.path.join(root, file)
                arc = os.path.relpath(full, TMP_DIR)
                zf.write(full, arc)
    log_success(f"模组包 {out_name} 处理完成")

def main():
    log_info("程序启动，初始化输出目录")
    clear_dir(OUT_FOLDER)

    file_list = []
    for fname in os.listdir(SRC_FOLDER):
        lower = fname.lower()
        if not lower.endswith((".zip", ".mrpack")):
            continue
        file_list.append(fname)

    if not file_list:
        log_warn("当前目录未检测到可处理压缩包")
        return
    log_info(f"共扫描到 {len(file_list)} 个待处理文件")

    for fname in file_list:
        full_path = os.path.join(SRC_FOLDER, fname)
        name = os.path.splitext(fname)[0]
        process_mrpack(full_path, name)

    if os.path.exists(TMP_DIR):
        log_debug("清理临时缓存目录")
        shutil.rmtree(TMP_DIR)
    log_success("全部任务执行完毕")

if __name__ == "__main__":
    print("=" * 60)
    log_info("正在准备程序...")
    log_info("正在进行初始化...")
    log_success("初始化完成")
    print("=" * 60)
    main()