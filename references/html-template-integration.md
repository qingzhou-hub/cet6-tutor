# 听力 HTML 模板集成说明

## 架构

听力功能使用以下模式生成含内嵌音频的 HTML：

1. `engine.py::generate_listening_html()` 读取 `listening_questions_v3.json` + MP3
2. 将 MP3 编码为 Base64 嵌入 HTML
3. 用 `data/listening_template.html` 作为模板（`TEMPLATE_DIR` 指向 `data/`）
4. 替换占位符 `{{year}}`, `{{sections}}`, `{{answers}}` 等
5. 输出完整自包含 HTML（双击即可用浏览器打开）

## ⚠️ 已知陷阱

### Radio 按钮必须绑定 onclick

`listening_template.html` 的 JS 使用 `currentAnswers` 对象（`{qNum: "A"}`）跟踪用户选择。
`checkAnswer()` 函数读取 `currentAnswers[i]` 来判题。

**如果 radio 按钮没有 `onclick="selectOption(qn, 'letter')"`，则 `currentAnswers` 永远为空，点击"核对答案"会显示所有题目未选答案。**

`engine.py` 中生成 radio 的代码必须为每个选项添加 onclick：

```python
sections_html += f'''
<label><input type="radio" name="q_{qn}" value="{letter}" 
             onclick="selectOption({qn}, \\'{letter}\\')">
  <span class="opt-letter">{letter}.</span>
  <span>{escape_html(txt)}</span>
</label>'''
```

⚠️ **关于 `\\'` 三层转义**（非常容易搞错，请仔细看）：

| 层级 | 实际内容 | 说明 |
|---|---|---|
| Python f-string 源码 | `\\'` | `\\` → `\`（反斜杠），`'` → 单引号 |
| 渲染到 HTML 属性值 | `\'A\'` | 反斜杠 + 单引号 + A + 反斜杠 + 单引号 |
| HTML 解析器提取 | `selectOption(1, \'A\')` | 双引号属性值内的内容原样提取 |
| JavaScript 解析 | `selectOption(1, 'A')` | `\'` 是 JS 转义的单引号，最终为字符串 `'A'` |

**常见错误：** 如果误写成 `onclick="selectOption({qn}, '{letter}')"`（少了一个反斜杠），则 Python f-string 渲染为 `onclick="selectOption(1, 'A')"` — 这其实也能在 JS 中正确解析（单引号在双引号属性内是合法字符）。**真正的破坏性错误**是完全遗漏了整个 onclick 属性。

简单记忆：保持现有写法 `\\'{letter}\\'` 不要动。验证方法：grep 生成后的 HTML 确认 `onclick="selectOption(1, 'A')"` 格式正确。

### MP3 文件按需下载

MP3 文件 4-5MB 每个，按需从 GitHub 原始仓库 `CET-6听力/` 目录下载。
缓存到 `data/mp3/`，不会重复下载。首次生成某套听力时会下载对应 MP3（耗时 5-15 秒）。

### 模板替换顺序

模板替换必须按此顺序，避免 `replace()` 污染后续内容：
1. `{{year}}`, `{{month}}`, `{{set_num}}`, `{{total}}` — 纯文本
2. `{{audio_player}}` — HTML 片段（含 audio 标签 + base64 data）
3. `{{audio_note}}` — 纯文本
4. `{{sections}}` — 巨大 HTML 块
5. `{{answer_preview}}` — HTML 片段
6. `{{answers}}` — 纯字母字符串（25个字母如 "ACABDCDB..."）
7. `{{result_key}}` — 纯文本

### 标准答案格式

`listening_questions_v3.json` 中 `answers` 字段是 `{"1": "A", "2": "C", ...}` 格式。
生成 `{{answers}}` 时需要转为纯字符串 `"AC..."`。
