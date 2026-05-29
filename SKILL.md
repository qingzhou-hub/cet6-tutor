---
name: cet6-tutor
description: "🎓 六级金牌私教 - 英语六级备考助手（阅读真题/听力练习/艾宾浩斯背单词）"
version: 1.3.0
author: Hermes Agent
category: education
tags: [cet6, english, exam, vocabulary, listening, reading]
---

# 🎓 六级金牌私教 (CET-6 Tutor)

六级备考全能助手！内置真题库、听力练习、艾宾浩斯记忆引擎。

## 快速使用

发以下指令给我即可：

### 📖 阅读真题
| 指令 | 说明 |
|------|------|
| `来篇阅读` | 随机抽一篇六级阅读真题 |
| `阅读答案 ABCDE...` | 提交答案并批改（按题目顺序写答案） |
| `查答案` | 查看当前阅读解析 |

### 🎧 听力练习
| 指令 | 说明 |
|------|------|
| `来套听力` | 随机抽一套六级听力真题，生成含音频的HTML文件发给你 |
| `听力答案 ABCD...` | 提交听力答案批改 |
| `听力跳过` | 跳过当前听力题 |

### 📝 单词背诵 (艾宾浩斯记忆)
| 指令 | 说明 |
|------|------|
| `加生词 [单词] [释义]` | 添加生词到词库（例如：加生词 abandon 放弃） |
| `今日复习` | 获取今天需要复习的单词 |
| `记住 [单词]` | 复习时说我记住了（调整下次复习间隔） |
| `忘了 [单词]` | 复习时说我没记住（缩短复习周期） |
| `斩 [单词]` | 永久掌握该单词（不再复习） |
| `今日新词` | 从已做阅读中提取生词推荐 |
| `查单词 [单词]` | 从真题库中查找单词例句 |
| `我的词库` | 查看学习统计 |

### ⚙️ 其他
| 指令 | 说明 |
|------|------|
| `使用文档` | 显示此帮助 |

## 数据

- 📚 **阅读真题**: 96篇完整六级阅读，涵盖2018-2025年真题
- 🎧 **听力真题**: 27套完整听力试题
- 📝 **答案库**: 44套标准答案

## 文件结构

```
cet6-tutor/
├── SKILL.md                              # 本文件
├── scripts/engine.py                     # 核心引擎（阅读/听力/单词/HTML生成）
├── references/
│   ├── html-template-integration.md      # HTML模板集成说明和陷阱
│   └── answer-grading-pitfall.md         # 阅读批改bug及手动打分流程
├── templates/
│   └── listening_template.html           # 旧占位文件（实际使用 data/ 下的模板）
├── data/
│   ├── CET6_Perfect_Fixed.json           # 96篇阅读真题
│   ├── CET6_Answer.json                  # 44套答案
│   ├── listening_questions_v3.json       # 27套听力题
│   ├── listening_template.html           # ✅ 听力HTML模板（TEMPLATE_DIR 指向这里）
│   ├── metadata.yaml                     # 插件元数据
│   └── mp3/                              # 自动下载的MP3音频缓存
├── user_data/                            # 用户学习数据（自动生成）
└── temp/                                 # 生成的HTML文件（自动生成）
```

## 开发笔记

### 引擎架构

`engine.py` 负责：
1. **数据加载** — 读取 JSON 题库
2. **阅读模块** — 随机抽题、提交批改
3. **听力模块** — 生成含 Base64 音频的自包含 HTML
4. **单词模块** — 艾宾浩斯记忆引擎（7级状态 + 动态间隔）

### 已知陷阱

- **submit_reading_answer 答案查找 Bug（已修复 2026-05-19）**: `submit_reading_answer(section_id)` 原来直接用 `section_id` 作为顶级键查找答案 JSON，但答案 JSON 结构是嵌套的：`answers["2019_12_2"]["answers"]["Section C1"]`。已修复为自动解析 section_id（格式 `2019_12_2_Section C - Passage 1`），提取 exam_key 和 section_name，并将 section_name 映射到答案键（如 `Section C - Passage 1` → `Section C1`）。同时支持正则提取答案字符串中的有效字母（忽略尾部的 `\nB`、`\nC` 等元信息）。
- **答案数据结构**：详见 `references/answer-data-structure.md`。
- **月份零填充 Bug（2026-05-20 已修复）**: 阅读 JSON 的 month 值为 `"6"`（无前导零），但答案 JSON 的 exam_key 使用 `"06"`。`submit_reading_answer()` 已补丁为自动尝试补零，避免月份 1-9 月的题目报 "找不到答案"。

- **`submit_reading_answer()` 键名不匹配**: 该函数直接查 answer dict 的顶层 key，但答案数据是嵌套结构 `{"YEAR_MONTH_SET": {"answers": {"Section C1": "CAADB\nC", ...}}}`，而 reading 的 section_id 格式为 `2019_12_2_Section C - Passage 1` 不匹配。**所有 Section C（仔细阅读）批改必须手动进行**，详见 `references/answer-grading-pitfall.md`。

- **Radio onclick 绑定**: 听力 HTML 依赖 `selectOption()` JS 函数跟踪用户选择。生成 radio 按钮时必须添加 `onclick="selectOption(qn, 'letter')"`，否则"核对答案"无效。详见 `references/html-template-integration.md`。验证方法：生成后 grep `onclick="selectOption` 计数应为 `题数×4`。
- **TEMPLATE_DIR 路径**: `load_listening_template()` 从 `TEMPLATE_DIR / "listening_template.html"` 读取模板。`TEMPLATE_DIR` 当前指向 `data/`（不是 `templates/`），因为实际模板文件在 `data/listening_template.html`。如果新增模板文件记得同步修改路径。
- **MP3 按需下载**: 首次听某套题时从 GitHub 下载 4-5MB MP3，缓存到 `data/mp3/`。
- **模板替换顺序**: 先替换纯文本占位符，再替换 HTML 片段。`{{answers}}` 是 25 个字母的纯字符串。
