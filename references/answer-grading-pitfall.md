# 阅读批改 — 历史陷阱与手动打分流程（大部分已修复）

## ✅ 历史 Bug 修复状态

| Bug | 描述 | 修复状态 | 修复日期 |
|-----|------|---------|---------|
| 嵌套答案查找 | section_id 格式不匹配 answers dict 结构 | ✅ 已修复 | 2026-05-19 |
| Section C 键名映射 | "Section C - Passage 1" → "Section C1" | ✅ 已修复 | 2026-05-19 |
| 月份零填充 | month="6" vs month="06" | ✅ 已修复 | 2026-05-20 |

以上 Bug 均已修复。`submit_reading_answer()` 现在支持所有题型，包括 Section C 仔细阅读。



## ✅ 正确手动批改流程

不要用 `submit_reading_answer()`，改用以下步骤：

### 1. 获取正确答案

```python
from engine import load_answers

answers = load_answers()

# 题目来源：2019年12月第2套 Section C Passage 1
# 对应 answer key: "2019_12_2" -> "Section C1"
ans_data = answers["2019_12_2"]["answers"]["Section C1"]  # "CAADB\nC"
correct_list = list(ans_data.strip()[:5])  # ['C', 'A', 'A', 'D', 'B']
```

### 2. Key 映射规则

| 阅读类型 | reading 中的 type 值 | answers 中的 section key |
|---------|---------------------|-------------------------|
| 选词填空 15选10 | `Section A` | `Section A` |
| 长篇阅读匹配 | `Section B` | `Section B` |
| 仔细阅读 Passage 1 | `Section C - Passage 1` | `Section C1` |
| 仔细阅读 Passage 2 | `Section C - Passage 2` | `Section C2` |

### 3. 完整批改示例

```python
from engine import load_answers, load_readings, get_user_data, save_user_data

answers = load_answers()

# 从 reading 的 meta 中获取 year, month, set_index
# meta = reading.get("meta", {}) -> {"year": "2019", "month": "12", "set_index": "2"}
year_month_set = f"{meta['year']}_{meta['month']}_{meta['set_index']}"  # "2019_12_2"

# 确定 section key（C1或C2）
type_str = reading.get("type", "")  # e.g. "Section C - Passage 1"
section_key = type_str.replace("Section C - Passage 1", "Section C1").replace("Section C - Passage 2", "Section C2")

ans_str = answers[year_month_set]["answers"][section_key]
correct = list(ans_str.strip()[:5])  # 只取前5题答案

# 比较用户答案
user_ans = list("DCDAC")
for i, (u, c) in enumerate(zip(user_ans, correct)):
    ok = u.upper() == c.upper()

# 保存为已完成
section_id = f"{year_month_set}_{section_key}"
user = get_user_data()
if section_id not in user.get("doned_readings", []):
    user.setdefault("doned_readings", []).append(section_id)
    user["stats"]["readings_done"] = user["stats"].get("readings_done", 0) + 1
save_user_data(user)
```

### 4. 题目编号

Section C 的题目从 46 开始编号：
- C1 (Passage 1): Q46-Q50
- C2 (Passage 2): Q51-Q55
