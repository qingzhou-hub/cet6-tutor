"""
CET-6 核心引擎 - 阅读/单词/听力/HTML生成
"""
import json, os, random, re, base64, time, urllib.request
from datetime import datetime, date
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent / "data"
USER_DIR = Path(__file__).parent.parent / "user_data"
TEMP_DIR = Path(__file__).parent.parent / "temp"
TEMPLATE_DIR = Path(__file__).parent.parent / "data"
MP3_DIR = BASE_DIR / "mp3"
USER_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
MP3_DIR.mkdir(exist_ok=True)

GITHUB_RAW = "https://raw.githubusercontent.com/202704948-design/astrbot_plugin_cet6/master"

# ====== 数据加载 ======
def load_readings():
    with open(BASE_DIR / "CET6_Perfect_Fixed.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_answers():
    with open(BASE_DIR / "CET6_Answer.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_listenings():
    with open(BASE_DIR / "listening_questions_v3.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_listening_template():
    path = TEMPLATE_DIR / "listening_template.html"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None

# ====== 用户数据 ======
def get_user_data(user_id="default"):
    path = USER_DIR / f"{user_id}.json"
    default = {
        "vocab": {}, "doned_readings": [], "doned_listenings": [],
        "mastered": [], "custom_dict": {},
        "stats": {"words_learned": 0, "words_mastered": 0, "readings_done": 0, "listenings_done": 0}
    }
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return {**default, **json.load(f)}
    return default

def save_user_data(data, user_id="default"):
    path = USER_DIR / f"{user_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ====== MP3 下载 ======
def ensure_mp3(mp3_filename):
    """下载MP3文件（如果本地没有）"""
    path = MP3_DIR / mp3_filename
    if path.exists():
        return str(path)
    url = f"{GITHUB_RAW}/CET-6%E5%90%AC%E5%8A%9B/{mp3_filename}"
    try:
        print(f"📥 下载MP3: {mp3_filename}...")
        urllib.request.urlretrieve(url, path)
        print(f"✅ 下载完成: {mp3_filename}")
        return str(path)
    except Exception as e:
        print(f"❌ MP3下载失败: {e}")
        return None

def escape_html(text):
    if not text: return ''
    return (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;').replace("'", '&#39;'))

# ====== 听力模块（HTML生成）======
def generate_listening_html(session_key, user_id="default"):
    """生成听力HTML文件（含内嵌音频）"""
    listenings = load_listenings()
    info = listenings.get(session_key)
    if not info:
        return None, "找不到该套听力"

    meta = info.get("meta", {})
    sections = info.get("sections", {})
    answers = info.get("answers", {})
    total = info.get("total", 25)
    year = meta.get("year", "")
    month = meta.get("month", "")
    set_num = meta.get("set_num", "")
    mp3_file = meta.get("mp3_file", "")

    # 内嵌MP3音频
    mp3_path = ensure_mp3(mp3_file)
    if mp3_path and os.path.exists(mp3_path):
        with open(mp3_path, "rb") as f:
            mp3_b64 = base64.b64encode(f.read()).decode("utf-8")
        audio_html = f'<audio id="audioPlayer" class="audio-player" controls preload="metadata"><source src="data:audio/mpeg;base64,{mp3_b64}" type="audio/mpeg"></audio>'
        audio_note = "🎵 音频已嵌入，点击播放即可"
    else:
        audio_html = '<p style="color:#c62828;">⚠️ 音频文件暂不可用</p>'
        audio_note = ""

    # 生成题目HTML
    sections_html = ""
    sec_order = {"A": "长对话", "B": "短文理解", "C": "讲座/讲话"}
    sec_ranges = {"A": (1, 9), "B": (9, 16), "C": (16, 26)}

    for sec_key in ["A", "B", "C"]:
        sec_data = sections.get(sec_key, {})
        questions = sec_data.get("questions", [])
        if not questions:
            continue
        q_start, q_end = sec_ranges[sec_key]
        sections_html += f'''
<div class="section">
    <div class="section-header">
        <h2>📻 Section {sec_key}: {sec_order[sec_key]}</h2>
        <div class="info">Q{q_start}-{q_end-1} | 共{len([q for q in questions if q_start <= q.get("q_num", 0) < q_end])}题</div>
    </div>'''
        for q in questions:
            qn = q.get("q_num", 0)
            if not (q_start <= qn < q_end):
                continue
            opts = q.get("options", {})
            sections_html += f'''
    <div class="question-item">
        <div class="q-header"><span class="q-num">Q{qn}</span><span class="q-note">[听力原题]</span></div>
        <div class="options">'''
            for letter in ["A", "B", "C", "D"]:
                txt = opts.get(letter, "")
                if txt:
                    sections_html += f'''
            <label><input type="radio" name="q_{qn}" value="{letter}" onclick="selectOption({qn}, \'{letter}\')"><span class="opt-letter">{letter}.</span><span>{escape_html(txt)}</span></label>'''
            sections_html += "</div></div>"
        sections_html += "</div>"

    # 答案预览 + 正确答案字符串
    answer_preview = "".join(f'<span class="q-mark">Q{i}:?</span>' for i in range(1, total + 1))
    correct_str = "".join(answers.get(str(i), "_") for i in range(1, total + 1))

    # 加载模板
    template = load_listening_template()
    if not template:
        # 极简兜底模板
        template = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>六级听力</title><style>
body{font-family:sans-serif;padding:20px;background:#f5f5f5;max-width:800px;margin:0 auto}
.audio-player{width:100%;margin:12px 0}
.section{background:#fff;border-radius:10px;padding:20px;margin:16px 0}
.question-item{padding:10px 0;border-bottom:1px solid #eee}
.options label{display:block;padding:6px 10px;margin:4px 0}
.btn{padding:12px 28px;background:#1e3a5f;color:#fff;border:none;border-radius:8px;cursor:pointer}
.result{display:none;background:#fff;padding:20px;border-radius:10px;margin-top:16px}
</style></head><body>
<div style="background:#1e3a5f;color:#fff;padding:20px;border-radius:10px;text-align:center;margin-bottom:20px">
<h1>🎧 六级听力真题</h1><p>{{year}}年{{month}}月 · 第{{set_num}}套 · 共{{total}}题</p>
{{audio_player}}<p>{{audio_note}}</p></div>
{{sections}}
<div style="text-align:center;margin-top:20px">
<button class="btn" onclick="grade()">📊 提交批改</button></div>
<div id="result" class="result"></div>
<script>
const ans="{{answers}}".split("");
function grade(){let s=0,d=[];
for(let i=0;i<{{total}};i++){let v=(document.querySelector('input[name="q_'+(i+1)+'"]:checked')||{}).value||'_';
let o=v===ans[i];if(o)s++;d.push('<div>'+(o?'✅':'❌ 你的'+v+'→'+ans[i])+'</div>')}
let r=document.getElementById('result');r.style.display='block';
r.innerHTML='<h3>得分: '+s+'/'+{{total}}+'</h3>'+d.join('')}
</script></body></html>"""

    html = (template.replace("{{year}}", str(year)).replace("{{month}}", str(month))
            .replace("{{set_num}}", str(set_num)).replace("{{total}}", str(total))
            .replace("{{audio_player}}", audio_html).replace("{{audio_note}}", audio_note)
            .replace("{{sections}}", sections_html).replace("{{answer_preview}}", answer_preview)
            .replace("{{answers}}", correct_str).replace("{{result_key}}", session_key))

    # 保存HTML
    ts = int(time.time())
    fname = TEMP_DIR / f"听力_{year}_{month}_第{set_num}套_{user_id}_{ts}.html"
    with open(fname, "w", encoding="utf-8") as f:
        f.write(html)
    return str(fname), None

# ====== 阅读模块 ======
def reading_id(r):
    m = r.get("meta", {})
    return f"{m.get('year','')}_{m.get('month','')}_{m.get('set_index','')}_{r.get('type','')}"

def get_next_reading(user_id="default"):
    readings = load_readings()
    user = get_user_data(user_id)
    doned = set(user.get("doned_readings", []))
    available = [(r, reading_id(r)) for r in readings if reading_id(r) not in doned]
    if not available:
        return None, "🎉 所有阅读都已做完！"
    chosen, rid = random.choice(available)
    chosen["_id"] = rid
    return chosen, None

def submit_reading_answer(section_id, user_answers, user_id="default"):
    """
    提交阅读答案并批改。
    
    section_id 格式由 reading_id() 生成，例如：
      "2019_12_2_Section C - Passage 1"
      "2019_12_2_Section B"
      "2019_12_2_Section A"
    
    答案 JSON 结构为嵌套字典：answers["2019_12_2"]["answers"]["Section C1"]
    本函数自动解析 section_id 并映射到对应的答案键。
    """
    all_answers = load_answers()
    
    # 解析 section_id: 提取 exam_key (前3段) 和 section_name (剩余部分)
    parts = section_id.split("_", 3)  # ["2019","12","2","Section C - Passage 1"]
    if len(parts) < 4:
        return None, f"section_id 格式错误: {section_id}"
    exam_key = f"{parts[0]}_{parts[1]}_{parts[2]}"
    section_name = parts[3]
    
    if exam_key not in all_answers:
        # 月份补零: reading meta month="6", answer key month="06"
        try:
            padded_key = f"{parts[0]}_{int(parts[1]):02d}_{parts[2]}"
            if padded_key in all_answers:
                exam_key = padded_key
            else:
                return None, f"找不到该套答案: {exam_key}"
        except (ValueError, IndexError):
            return None, f"找不到该套答案: {exam_key}"
    
    exam_data = all_answers[exam_key]
    section_answers = exam_data.get("answers", {})
    
    # 映射 section_name 到答案键
    # "Section C - Passage 1" -> "Section C1"
    # "Section C - Passage 2" -> "Section C2"
    # "Section B"             -> "Section B"
    # "Section A"             -> "Section A"
    answer_key = section_name
    if " - " in section_name:
        base, num = section_name.split(" - ", 1)
        if "Passage" in num:
            num_part = num.replace("Passage ", "")
            answer_key = f"{base}{num_part}"
    
    if answer_key not in section_answers:
        return None, f"找不到该题答案: {exam_key}/{answer_key} (原始: {section_name})"
    
    correct_raw = section_answers[answer_key].strip()
    # 某些答案末尾有 '\nB' 或 '\nC' 表示该套第几题，只取前面的实际答案
    match = re.match(r'^([A-Z]+)', correct_raw, re.IGNORECASE)
    if match:
        correct = list(match.group(1).upper())
    else:
        correct = list(correct_raw.upper())
    
    results = []; score = 0; total = len(correct)
    start_num = 1
    for p, label in [("A", 26), ("B", 36), ("C", 46)]:
        if p in section_name.upper(): start_num = label; break
    for i, c in enumerate(correct):
        ua = user_answers[i] if i < len(user_answers) else ""
        ok = ua.upper() == c.upper()
        if ok: score += 1
        results.append({"num": start_num + i, "user": ua.upper(), "correct": c.upper(), "pass": ok})
    user = get_user_data(user_id)
    if section_id not in user["doned_readings"]:
        user["doned_readings"].append(section_id)
        user["stats"]["readings_done"] += 1
    save_user_data(user, user_id)
    return {"score": score, "total": total, "percent": round(score/total*100, 1), "results": results}, None

# ====== 单词模块（艾宾浩斯）====== 
def add_word(word, meaning, user_id="default"):
    user = get_user_data(user_id)
    if word in user["mastered"]: return f"'{word}' 已经在永久掌握名单中了"
    status = user["vocab"].get(word, {})
    status["meaning"] = meaning
    status["status"] = 0
    status["next_review"] = date.today().isoformat()
    status["interval"] = 1; status["ease"] = 2.5
    user["vocab"][word] = status
    user["stats"]["words_learned"] = len(user["vocab"])
    save_user_data(user, user_id)
    return f"✅ 已添加: {word} - {meaning}"

def get_review_words(user_id="default", count=5):
    user = get_user_data(user_id)
    today = date.today().isoformat()
    due = [(w, i) for w, i in user["vocab"].items()
           if i.get("next_review", "") <= today and w not in user["mastered"]]
    due.sort(key=lambda x: x[1].get("next_review", ""))
    return due[:count]

def review_word(word, remembered, user_id="default"):
    user = get_user_data(user_id)
    if word not in user["vocab"]: return "单词不在词库中"
    info = user["vocab"][word]
    if remembered:
        info["status"] = min(info["status"] + 1, 6)
        info["ease"] = min(info["ease"] + 0.15, 3.0)
    else:
        info["status"] = max(info["status"] - 2, 0)
        info["ease"] = max(info["ease"] - 0.2, 1.3)
    info["interval"] = max(1, int(info["interval"] * info["ease"]))
    from datetime import timedelta
    info["next_review"] = (date.today() + timedelta(days=info["interval"])).isoformat()
    user["vocab"][word] = info
    save_user_data(user, user_id)
    snames = ["🥚待定", "📉模糊", "📈清晰", "🧠记住", "🛡️牢固", "🌟掌握", "👑精通"]
    return f"{'✅ 记住了！' if remembered else '❌ 没记住'} 状态: {snames[info['status']]}  下次复习: {info['next_review']}"

def kill_word(word, user_id="default"):
    user = get_user_data(user_id)
    if word in user["vocab"]: del user["vocab"][word]
    if word not in user["mastered"]:
        user["mastered"].append(word)
        user["stats"]["words_mastered"] = len(user["mastered"])
    save_user_data(user, user_id)
    return f"⚔️ '{word}' 已被斩杀！永久掌握！👑"

def get_stats(user_id="default"):
    user = get_user_data(user_id)
    s = user["stats"]
    return f"""📊 我的学习统计
━━━━━━━━━━━━━━
📖 已做阅读: {s['readings_done']} 篇
🎧 已做听力: {s['listenings_done']} 套
📝 词库单词: {len(user['vocab'])} 个
🏆 已掌握: {s['words_mastered']} 个
📅 今日复习: {len(get_review_words(user_id))} 个"""

if __name__ == "__main__":
    print("=== CET-6 引擎测试 ===")
    print(f"阅读: {len(load_readings())}篇")
    print(f"答案: {len(load_answers())}套")
    print(f"听力: {len(load_listenings())}套")
    sid, _ = get_next_reading()
    print(f"阅读示例: {reading_id(sid) if sid else 'N/A'}")
    # 测试听力HTML生成
    listenings = load_listenings()
    if listenings:
        key = list(listenings.keys())[0]
        html_path, err = generate_listening_html(key)
        if html_path:
            print(f"听力HTML生成成功: {html_path}")
        else:
            print(f"听力HTML生成失败: {err}")
    print("✅ 引擎就绪")
