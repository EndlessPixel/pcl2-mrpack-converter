# PCL2-to-Modrinth

[![Python 3.x](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![GitHub license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/EndlessPixel/pcl2-mrpack-converter.svg?style=flat&label=Stars)](https://github.com/EndlessPixel/pcl2-mrpack-converter/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/EndlessPixel/pcl2-mrpack-converter.svg?style=flat&label=Issues)](https://github.com/EndlessPixel/pcl2-mrpack-converter/issues)

> 一键把 PCL2 导出的混合源整合包，转换成 Modrinth 可直接上传的标准 mrpack 格式

---

## ✨ 项目背景
PCL2 导出的整合包默认是 **CurseForge + Modrinth 混合源** 的 mrpack 格式，直接上传 Modrinth 会因为包含 forgecdn 等非 Modrinth 源链接而校验失败。

网上大部分工具只支持纯 CurseForge 包转 Modrinth，**唯独 PCL2 这种混合包没有现成工具**，所以我写了这个脚本解决这个痛点。

---

## 📦 功能特点
- 批量处理 `.mrpack` / `.zip` 格式的整合包
- 自动移除 `forgecdn.net` 等无效/防盗链下载链接
- 保留 Modrinth 原生下载源，生成符合 Modrinth 标准的 mrpack 文件
- 轻量无依赖，纯 Python 脚本，开箱即用

---

## 🚀 使用方法

### 1. 准备环境
确保你的电脑安装了 Python 3.x：
```bash
python --version
```

### 2. 运行脚本
1. 把脚本和你的 `.mrpack` 文件放在同一个文件夹里
2. 运行脚本：
```bash
python fix_mrpack.py
```

### 3. 查看结果
处理好的文件会自动输出到 `./fixed_packs/` 文件夹里，直接上传 Modrinth 即可。

---

## 📝 工作原理
1. 解压 mrpack 文件，读取 `modrinth.index.json`
2. 过滤掉所有包含 `forgecdn.net` 的下载链接
3. 重新打包成标准 mrpack 文件
4. 输出干净、可直接通过 Modrinth 校验的整合包

---

## 📌 注意事项
- 脚本只修改下载链接，不会删除任何文件
- 请确保你的整合包中包含 Modrinth 源的下载链接，否则脚本处理后可能会丢失下载源
- 处理前建议备份原始文件

---

## 📄 License
MIT