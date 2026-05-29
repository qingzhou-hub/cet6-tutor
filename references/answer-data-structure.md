# 答案数据结构与零填充 Bug

## 数据结构

```python
all_answers = {
  "2023_06_1": {               # exam_key: 年份_月份_套数（月份两位）
    "answers": {
      "Section A":  "NKOMAGDECI\nB",  # 选词填空（15选10，后附题号指示）
      "Section B":  "CGAIFKDMBH\nC",  # 长篇阅读匹配（10题）
      "Section C1": "DAACB\nC",       # 仔细阅读 Passage 1（5题）
      "Section C2": "ABBCD"           # 仔细阅读 Passage 2（5题）
    }
  },
  ...
}
```

## 🐛 月份零填充不匹配（2026-05-20修复）

### 问题

阅读 JSON 的 meta 中 month 存储为 **`"6"`（无前导零）**，而答案 JSON 的 exam_key 使用 **`"06"`（有前导零）**。

```
reading meta:  month = "6"
answer key:    "2023_06_1"     ← 对不上
exam_key 构建： "2023_6_1"     ← 找不到
```

这导致 `submit_reading_answer()` 在月份为 1-9 月的所有题目上返回 "找不到该套答案"。

### 修复

在 `submit_reading_answer()` 中，当 exam_key 未找到时，尝试将月份补零后再次查找：

```python
if exam_key not in all_answers:
    try:
        padded_key = f"{parts[0]}_{int(parts[1]):02d}_{parts[2]}"
        if padded_key in all_answers:
            exam_key = padded_key
    except (ValueError, IndexError):
        pass
```

### 关键文件

| 文件 | 数据 | 月份格式 |
|------|------|---------|
| `data/CET6_Perfect_Fixed.json` | 96篇阅读 | `"6"`（无填充） |
| `data/CET6_Answer.json` | 44套答案 | `"06"`（两位数） |

### 规避

手动批改时直接查 answers JSON：
```python
answers = load_answers()
meta = reading["meta"]
ans_key = f"{meta['year']}_{int(meta['month']):02d}_{meta['set_index']}"
correct_str = answers[ans_key]["answers"]["Section C2"]  # "ABBCD"
```
