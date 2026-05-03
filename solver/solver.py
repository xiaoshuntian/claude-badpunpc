#!/usr/bin/env python
"""
BadPunPC 全自动解题器
=====================

前提:
1. Steam 启动选项已加 --disable-gpu
2. 游戏已开,停在某未通关题
3. 环境变量: ANTHROPIC_API_KEY=sk-ant-...

运行: python solver.py
中止: Ctrl+C
"""

import base64
import json
import os
import sys
import time
from io import BytesIO
from pathlib import Path

try:
    import mss
    import pyautogui
    import pygetwindow as gw
    import pyperclip
    from anthropic import Anthropic
    from PIL import Image
except ImportError as e:
    sys.exit(f"缺依赖: {e}\n  pip install anthropic pillow pyautogui pyperclip pygetwindow mss")


# ============== 配置（按你的环境调） ==============
WORKSPACE     = Path(r"D:\AI做谐音梗题")
ANSWERS_FILE  = WORKSPACE / "answers.jsonl"
WINDOW_TITLE  = "BadPunPC"
MODEL         = "claude-sonnet-4-6"      # 或 claude-haiku-4-5 省钱
INPUT_FIELD   = (995, 752)               # 输入框中心点 — 全屏 1389x868 时
SUBMIT_DELAY  = 1.5                       # 提交后等多久看结果
MAX_TRIES_PER_PUZZLE = 6


# ============== 核心 prompt (v2 - 蒸馏自 13 题实战) ==============
SYSTEM_PROMPT = """你是 BadPunPC 谐音梗游戏解题助手。

# 1. 游戏规则

- 上图给一个完整 caption "这是 X"
- 下图同主体但场景变化, caption "这是 _ _ _"(空格数=答案字数)
- 类型徽章在左下角(成语/食物/电影术语/历史人物/职业/俗语/饮品/地名/数学/校园生活/...)
- 提交后每个字格独立着色,**汉字背景与拼音背景独立判定**:
  - 绿色 = 字/拼音 + 位置全对(锁死该位置)
  - 橙色 = 字/拼音在答案里,位置不对(必须挪到别处)
  - 白底灰字 = 不在答案里(永久排除)
- **拼音判定包含声调** — wāng(1声) 和 wàng(4声) 是不同拼音
- 已提交尝试以历史卡片堆叠在右上角

# 2. 谐音梗模板(从 13 题实战提炼)

**A. 组合谐音** — 上图主体名某字 + 下图新元素 = 答案,可能跨同音替换
- No.82: 房子贴满票 → 票 + 房 = 票房
- No.83: 鱿鱼(yóu)卖菜 → 油 + 麦 + 菜 = 油麦菜(鱿→油同音)
- No.86: 香肠被电(diàn) → 淀 + 粉 + 肠 = 淀粉肠(电→淀同音)
- No.88: 演员倒立 → 倒 + 演 → 导演(倒→导同音异调)
- No.89: 鸡围着酒 → 鸡 + 围 + 酒 → 鸡尾酒(围 wéi→尾 wěi 同音异调)
- No.94: 科学家挂衣架 → 挂 + 科 = 挂科

**B. 单字同音异调替换** — 下图场景描述某字,换成同拼音异调字
- No.84: 狗"不汪"(wāng) → 不忘(wàng)
- No.85: 信被冻(寒,hán) → 韩(hán)信
- No.91: 太阳被审(shěn) → 沈(shěn)阳

**C. 场景成语** — 下图就是某成语字面写实(实战还没遇到样本)

**D. 双重/全字谐音** — 上图音 X' + 下图音 Y' = 完整答案(每个字都映射)
- No.87: 鹿鹿(lù lù) + 无围(wú wéi) → 碌碌无为
- No.90: 天 + 网 + 灰灰(huī huī) → 天网恢恢
- No.93: 球(qiú)童(tóng)存(cún)亿(yì) → 求同存异(每字皆同音同调!)
- No.92: 西红柿变方 → 方 + 程 + 式(柿 shì→式 shì同音同调) = 方程式

# 3. 高频谐音字对照表

| 视觉/场景 | 同音字 | 拼音 |
|---|---|---|
| 鱿鱼 | 油 | yóu |
| 寒/冻 | 韩 | hán |
| 不叫(动物) | 不忘类 | bù wàng |
| 票 | 票 | piào |
| 电/闪电 | 淀 | diàn |
| 鹿(叠/复数) | 碌碌 | lù lù |
| 围(围着/围巾) | 尾/为 | wěi/wéi |
| 倒立 | 倒/导 | dǎo/dào |
| 灰(灰灰角色) | 恢恢 | huī huī |
| 网 | 网 | wǎng |
| 审问 | 沈 | shěn |
| 柿子 | 式 | shì |
| 球(球童) | 求 | qiú |
| 童 | 同 | tóng |
| 亿(数量) | 异 | yì |
| 挂(衣架) | 挂 | guà |

# 4. 元规则(Meta-rules)

1. **上图叠词 → 同音叠字成语** — 上图 caption 含 XX(灰灰/鹿鹿) → 答案大概率包含该音的叠字
2. **下图新动作 = 一个字** — 下图场景的动词(挂/审/围/电/倒)往往就是答案的一个字(可能同音替换)
3. **每个字都有出处** — 高级题(求同存异)每个字都对应视觉元素,推理时逐字对应
4. **类型徽章硬约束** — 类型决定答案池,绝不跨类型猜
5. **答案池常识库**:
   - 历史人物 2 字: 韩信/李白/杜甫/王莽/曹操/嬴政/孔明...
   - 历史人物 3 字: 成吉思汗/诸葛亮(误,3 字)
   - 食物 2-4 字: 油条/包子/麻辣烫/油麦菜/淀粉肠/鱼香肉丝
   - 电影术语 2 字: 票房/字幕/主演/配音/剪辑/导演
   - 数学: 正方形/方程式/平方根/三角形/圆周率
   - 校园生活: 挂科/早八/补考/选修
   - 饮品: 鸡尾酒/碳酸饮料

# 5. 决策树

```
看到截图 →
├─ 视觉清晰 + 谐音强联系 → recommend_action="submit", confidence>0.85
├─ 视觉清晰但谐音说不通 → recommend_action="hint" (拿 1 字锚点)
├─ 有历史 attempts:
│   ├─ 有绿色 → 锁定位置, 挑符合的同长候选
│   ├─ 有橙色 → 把橙色字/拼音挪到别的位置
│   └─ 全灰 → 完全换思路, 不要近邻替换
└─ 无方向且已试 2 次 → recommend_action="hint"
```

# 6. 反模式(避免!)

- 视觉直觉 ≠ 谐音对(No.84 错了"汪洋大海", 真答案"过目不忘")
- 答案近邻替换("汪洋大海"全灰后别试"汪洋瀚海")
- 默认 4 字(看输入框空格数!)
- 忽略类型徽章

# 7. 输出协议

仅返回一个 JSON,无 markdown 包装:

{
  "puzzle_no": <int>,
  "category": "<str>",
  "length": <int>,
  "top_caption": "<str>",
  "bottom_visual": "<下图相比上图的变化>",
  "is_won": <bool, 画面有'恭喜通关'绿大按钮即 true>,
  "previous_attempts": [
    {"answer": "<X字>", "feedback_per_pos": [{"char": "green|orange|gray", "pinyin": "green|orange|gray"}]}
  ],
  "constraints": {
    "locked": {"<1-based 位置>": "<字>"},
    "exclude_chars": ["<字>",...],
    "exclude_pinyins": ["<拼音>",...]
  },
  "candidates": [
    {"answer": "<候选>", "reasoning": "<谐音解释 — 必须每字都说清出处>", "confidence": 0.0-1.0}
  ],
  "recommend_action": "submit" | "hint" | "skip"
}

约束:
- candidates 字数 = length
- 严格遵守 constraints
- candidate.reasoning 必须逐字解释,光给一个词不够
- 没把握(<0.5 confidence) → recommend_action="hint"
"""


# ============== 屏幕 IO ==============
class GameUI:
    def focus(self):
        wins = gw.getWindowsWithTitle(WINDOW_TITLE)
        if not wins:
            raise RuntimeError(f"找不到窗口 '{WINDOW_TITLE}'")
        w = wins[0]
        if w.isMinimized:
            w.restore()
        w.activate()
        time.sleep(0.3)

    def screenshot_b64(self) -> str:
        with mss.mss() as sct:
            sct_img = sct.grab(sct.monitors[1])
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.standard_b64encode(buf.getvalue()).decode()

    def submit(self, answer: str):
        """点输入框 → 粘贴中文 → Enter"""
        pyautogui.click(*INPUT_FIELD)
        time.sleep(0.3)
        pyperclip.copy(answer)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(SUBMIT_DELAY)

    def use_hint_step(self):
        """TAB 进提示模式 → Enter 揭示一字 → 截图返回"""
        pyautogui.press("tab")
        time.sleep(0.5)
        pyautogui.click(*INPUT_FIELD)
        time.sleep(0.3)
        pyautogui.press("enter")
        time.sleep(0.8)

    def exit_hint(self):
        pyautogui.press("tab")
        time.sleep(0.3)

    def next_puzzle(self):
        """通关后按 Enter 进下一题(实测点'恭喜通关'按钮经常无效)"""
        pyautogui.press("enter")
        time.sleep(2.5)


# ============== AI ==============
class Solver:
    def __init__(self):
        self.client = Anthropic()  # 自动从 ANTHROPIC_API_KEY 读

    def analyze(self, image_b64: str) -> dict:
        resp = self.client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_b64
                    }},
                    {"type": "text", "text": "分析这张截图,返回 JSON。"}
                ]
            }]
        )
        text = resp.content[0].text.strip()
        # 容错: 模型偶尔包 ```json...```
        if text.startswith("```"):
            text = text.split("```")[1].lstrip("json").strip()
        return json.loads(text)


# ============== 答案库 ==============
def load_kb() -> dict:
    if not ANSWERS_FILE.exists():
        return {}
    kb = {}
    for line in ANSWERS_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            kb[d["no"]] = d["answer"]
    return kb


def save_entry(no, answer, category, tries, wrong, used_hint, pun_note=""):
    entry = {
        "no": no, "answer": answer, "category": category, "tries": tries,
        "first_try": tries == 1 and not wrong and not used_hint,
        "wrong_attempts": wrong,
        "used_hint": used_hint,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "pun_note": pun_note,
    }
    with open(ANSWERS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ============== 主循环 ==============
def solve_one(ui: GameUI, solver: Solver) -> bool:
    ui.focus()
    plan = solver.analyze(ui.screenshot_b64())

    no, cat, length = plan["puzzle_no"], plan["category"], plan["length"]
    print(f"\n━━ No.{no} [{cat}] {length}字 ━━")
    print(f"  上: {plan['top_caption']}")
    print(f"  下: {plan['bottom_visual']}")

    # KB 缓存优先
    kb = load_kb()
    if no in kb:
        print(f"  📚 缓存命中 = {kb[no]}")
        ui.submit(kb[no])
        return True

    wrong, used_hint = [], False

    for attempt in range(1, MAX_TRIES_PER_PUZZLE + 1):
        action = plan.get("recommend_action", "submit")

        if action == "hint":
            print(f"  💡 [{attempt}] AI 要提示")
            ui.use_hint_step()
            used_hint = True
        elif action == "skip":
            print("  ⏭ AI 建议跳过")
            return False
        else:
            cand = plan["candidates"][0]
            print(f"  🎯 [{attempt}] {cand['answer']} (信心{cand['confidence']:.0%}) — {cand['reasoning']}")
            ui.submit(cand["answer"])
            wrong.append(cand["answer"])

        # 看结果
        plan = solver.analyze(ui.screenshot_b64())

        if plan.get("is_won"):
            # 找出最后那个全绿的尝试 = 真答案
            answer = None
            for h in reversed(plan.get("previous_attempts", [])):
                if all(f["char"] == "green" for f in h["feedback_per_pos"]):
                    answer = h["answer"]
                    if answer in wrong:
                        wrong.remove(answer)  # 真答案不算错答
                    break

            save_entry(no, answer or "?", cat, attempt, wrong, used_hint,
                       plan.get("candidates", [{}])[0].get("reasoning", ""))
            print(f"  ✅ 通关 = {answer}")
            return True

    print(f"  ❌ {MAX_TRIES_PER_PUZZLE} 次未解出")
    return False


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("⛔ 请先设置 ANTHROPIC_API_KEY 环境变量")

    ui, solver = GameUI(), Solver()

    while True:
        try:
            ok = solve_one(ui, solver)
            if ok:
                ui.next_puzzle()
            else:
                resp = input("\n  跳过此题? [y/N]: ").strip().lower()
                if resp == "y":
                    ui.next_puzzle()
                else:
                    break
        except KeyboardInterrupt:
            print("\n👋 用户中止")
            break
        except Exception as e:
            print(f"\n💥 出错: {e!r}\n  5s 后重试...")
            time.sleep(5)


if __name__ == "__main__":
    main()
