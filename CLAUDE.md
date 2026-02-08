# CLAUDE.md

AgentSkills-compatible skills collection for openclaw.

## 仓库结构

```
sancho-skills/
├── skills/                     # 技能目录
│   └── <skill-name>/           # 单个技能目录
│       ├── SKILL.md            # 技能定义文件 (必需)
│       └── scripts/            # 辅助脚本目录 (可选)
│           └── *.py            # 脚本文件
├── CLAUDE.md                   # 本文件
└── README.md                   # 项目说明
```

## 开发新 Skill

### 1. 创建目录结构

```bash
mkdir -p skills/<skill-name>/scripts
```

### 2. 编写 SKILL.md

每个 skill 必须包含 `SKILL.md`，格式如下：

```yaml
---
name: skill-name                 # 技能标识名 (kebab-case)
description: Brief description  # 简短描述
metadata:
  openclaw:
    emoji: 🎵                     # 技能图标
    requires:                    # 依赖要求
      bins: ["binary1", "binary2"]  # 所需可执行文件
    install:                     # 安装步骤 (可选)
      - id: "unique-id"
        kind: "brew"             # 安装方式: brew, uv, npm 等
        formula: "package-name"
        bins: ["binary-name"]
        label: "安装说明"
---

# Skill 使用文档

使用 Markdown 编写详细的使用说明、示例命令等。
```

### 3. 添加辅助脚本 (可选)

如需 Python 脚本辅助：

```python
#!/usr/bin/env python3
# skills/<skill-name>/scripts/helper.py

import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL to process")
    args = parser.parse_args()
    # ... 实现逻辑

if __name__ == "__main__":
    main()
```

在 `SKILL.md` 中引用脚本时使用 `{baseDir}` 占位符：

```bash
python {baseDir}/scripts/helper.py "<URL>"
```

## Skill 规范

### 命名约定

- **Skill 目录名**: kebab-case (如 `audio-download`, `image-convert`)
- **Script 文件名**: 描述性功能名 (如 `download.py`, `convert.sh`)
- **SKILL.md 中的 name 字段**: 与目录名一致

### 依赖声明

在 `metadata.openclaw.requires` 中声明：

```yaml
metadata:
  openclaw:
    requires:
      bins: ["yt-dlp", "ffmpeg"]      # 必需的可执行文件
      python_packages: ["requests"]    # Python 依赖 (可选)
```

### 安装配置

提供自动安装选项：

```yaml
metadata:
  openclaw:
    install:
      - id: "brew-install"            # 唯一标识
        kind: "brew"                   # 包管理器: brew, uv, npm, apt 等
        formula: "package-name"        # 包名
        bins: ["binary-name"]          # 提供的可执行文件
        label: "通过 Homebrew 安装"
```

支持的 `kind` 值：
- `brew` - Homebrew 包
- `uv` / `pip` - Python 包
- `npm` - Node.js 包
- `apt` - Debian/Ubuntu 包

## 现有 Skills

| Skill | 描述 | 依赖 |
|-------|------|------|
| [audio-download](skills/audio-download/) | 从 YouTube 和 Twitter/X 下载音频 | yt-dlp, ffmpeg |

## 提交规范

提交信息应清晰描述新增或修改的 skill：

```bash
# 新增 skill
git commit -m "Add <skill-name> skill for <purpose>"

# 更新 skill
git commit -m "Update <skill-name>: <what changed>"
```

## 测试 Skill

在 openclaw 中加载前，本地验证：

1. **验证 YAML 格式**: 确保 `SKILL.md` 的 frontmatter 格式正确
2. **测试脚本**: 直接运行脚本确保功能正常
3. **检查依赖**: 确认所有依赖的二进制文件已安装

## 参考

- AgentSkills 规范
- openclaw 文档
