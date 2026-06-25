import os
import zipfile
import json
import shutil
import requests
from datetime import datetime

# ========================== 配置 ==========================
SRC_FOLDER = "."                         # 扫描目录（当前目录）
TMP_DIR = "./_tmp_extract"               # 临时解压目录
OUT_FOLDER = "./fixed_packs"             # 输出目录
BLOCK_HOST = "forgecdn.net"              # 被屏蔽的域名
DELETE_FOLDERS = ["overrides/PCL"]       # 需要删除的文件夹（相对路径）
# =========================================================

# 颜色常量
class LogColor:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    WHITE = "\033[97m"
    RESET = "\033[0m"

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

# ========================== API 批量查询 ==========================
def get_modrinth_versions_by_sha1_batch(sha1_list, timeout=10):
    """
    批量查询 Modrinth API，返回 {sha1: version_object} 映射。
    未找到的哈希，值设为 None。
    """
    if not sha1_list:
        return {}
    # 去重并转为小写
    unique_hashes = list(set([h.lower() for h in sha1_list if h]))
    if not unique_hashes:
        return {}

    url = "https://api.modrinth.com/v2/version_files"
    headers = {"Content-Type": "application/json"}
    payload = {"hashes": unique_hashes, "algorithm": "sha1"}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            # 确保每个请求的哈希都有返回值（即使没有也设为 None）
            result = {}
            for h in unique_hashes:
                result[h] = data.get(h)  # 可能为 None
            return result
        else:
            log_warn(f"批量查询失败，HTTP {resp.status_code}: {resp.text}")
            return {h: None for h in unique_hashes}
    except Exception as e:
        log_error(f"批量查询异常: {e}")
        return {h: None for h in unique_hashes}

# ========================== 核心处理函数 ==========================
def process_mrpack(zip_path, out_name):
    log_info(f"开始处理模组包：{os.path.basename(zip_path)}")
    clear_dir(TMP_DIR)

    # 解压
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(TMP_DIR)
        log_debug("压缩包解压完成")
    except Exception as e:
        log_error(f"解压失败：{str(e)}")
        return

    # 删除指定文件夹
    for del_folder in DELETE_FOLDERS:
        del_path = os.path.join(TMP_DIR, del_folder)
        if os.path.exists(del_path):
            shutil.rmtree(del_path)
            log_info(f"已删除目录：{del_folder}")
        else:
            log_debug(f"目录不存在，跳过删除：{del_folder}")

    # 定位索引文件
    json_path = os.path.join(TMP_DIR, "modrinth.index.json")
    if not os.path.exists(json_path):
        log_warn("未找到模组索引文件，跳过处理")
        return

    log_debug("读取模组索引配置")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 处理 files 数组
    if "files" not in data:
        log_warn("索引中无 files 字段，无需处理")
    else:
        # 第一步：扫描并收集被屏蔽的条目
        candidates = []  # 元素: (索引, sha1, path)
        to_remove_indices = []  # 记录需要移除的索引
        processed_mods = []  # 用于生成报告

        for idx, item in enumerate(data["files"]):
            path = item.get("path", "")
            # 如果 path 属于要删除的文件夹，直接跳过（后续会整体删除）
            if any(path.startswith(folder) for folder in DELETE_FOLDERS):
                continue

            downloads = item.get("downloads", [])
            if any(BLOCK_HOST in link for link in downloads):
                sha1 = item.get("hashes", {}).get("sha1")
                if sha1:
                    candidates.append((idx, sha1.lower(), path))
                else:
                    # 没有 SHA1，无法查询，直接移除
                    log_warn(f"条目 {path} 缺少 SHA1，无法查询 Modrinth，将被移除")
                    processed_mods.append({
                        "file": os.path.basename(path),
                        "homepage": None,
                        "status": "removed (no SHA1)"
                    })
                    to_remove_indices.append(idx)
            # 否则保持不变

        # 第二步：批量查询 SHA1
        if candidates:
            sha1_list = [c[1] for c in candidates]
            version_map = get_modrinth_versions_by_sha1_batch(sha1_list)
            # 处理每个候选
            for idx, sha1, path in candidates:
                version_obj = version_map.get(sha1)
                if version_obj and "files" in version_obj and version_obj["files"]:
                    # 提取下载链接（通常取第一个文件）
                    new_downloads = [f.get("url") for f in version_obj["files"] if "url" in f]
                    if new_downloads:
                        # 替换 downloads
                        data["files"][idx]["downloads"] = new_downloads
                        project_id = version_obj.get("project_id")
                        homepage = f"https://modrinth.com/project/{project_id}" if project_id else None
                        processed_mods.append({
                            "file": os.path.basename(path),
                            "homepage": homepage,
                            "status": "replaced"
                        })
                        log_info(f"已替换下载链接: {os.path.basename(path)}")
                        continue
                # 如果到达这里，说明未找到或无效，移除该条目
                log_warn(f"未在 Modrinth 找到 {os.path.basename(path)}，将其从索引移除")
                processed_mods.append({
                    "file": os.path.basename(path),
                    "homepage": None,
                    "status": "removed (not found on Modrinth)"
                })
                to_remove_indices.append(idx)

        # 第三步：移除所有标记为删除的条目（倒序，避免索引变化）
        if to_remove_indices:
            # 排序并倒序
            for idx in sorted(to_remove_indices, reverse=True):
                del data["files"][idx]
            log_info(f"从索引中移除了 {len(to_remove_indices)} 个条目")

        # 写回索引
        log_debug("写入修改后的索引文件")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 生成 ATTRIBUTION.txt
        if processed_mods:
            attrib_path = os.path.join(TMP_DIR, "ATTRIBUTION.txt")
            with open(attrib_path, "w", encoding="utf-8") as f:
                f.write("本整合包中以下模组的下载链接已从 forgecdn 替换为 Modrinth（若未找到则移除）：\n")
                f.write("说明：移除的模组如果仍在 overrides 目录中，安装时不会丢失，但需要手动补充归属信息。\n\n")
                for mod in processed_mods:
                    f.write(f"- {mod['file']}\n")
                    if mod['status'] == "replaced":
                        if mod.get('homepage'):
                            f.write(f"  项目主页：{mod['homepage']}\n")
                        else:
                            f.write("  项目主页：替换成功但未获取到项目ID\n")
                    else:
                        f.write(f"  状态：{mod['status']}\n")
                    f.write("\n")
            log_info(f"已生成处理记录：ATTRIBUTION.txt (位于临时目录)")

    # 重新打包
    out_path = os.path.join(OUT_FOLDER, f"{out_name}.mrpack")
    log_info(f"重新打包输出：{os.path.basename(out_path)}")
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(TMP_DIR):
            for file in files:
                full = os.path.join(root, file)
                arc = os.path.relpath(full, TMP_DIR)
                zf.write(full, arc)
    log_success(f"模组包 {out_name} 处理完成")

    # 清理临时目录（可选，为了调试可以注释掉）
    shutil.rmtree(TMP_DIR)

# ========================== 主程序 ==========================
def main():
    log_info("程序启动，初始化输出目录")
    clear_dir(OUT_FOLDER)

    # 扫描当前目录下的压缩包
    file_list = []
    for fname in os.listdir(SRC_FOLDER):
        lower = fname.lower()
        if lower.endswith((".zip", ".mrpack")):
            file_list.append(fname)

    if not file_list:
        log_warn("当前目录未检测到可处理压缩包")
        return

    log_info(f"共扫描到 {len(file_list)} 个待处理文件")
    for fname in file_list:
        full_path = os.path.join(SRC_FOLDER, fname)
        name = os.path.splitext(fname)[0]
        process_mrpack(full_path, name)

    log_success("全部任务执行完毕")

if __name__ == "__main__":
    print("=" * 60)
    log_info("正在准备程序...")
    log_info("正在进行初始化...")
    log_success("初始化完成")
    print("=" * 60)
    main()