# BadPunPC 自动解题器

把 Claude 当 solver 调用 Anthropic API 全自动通关。

## 快速开始

```powershell
# 1. 装依赖
cd D:\AI做谐音梗题\solver
pip install -r requirements.txt

# 2. 配置 API key (PowerShell)
$env:ANTHROPIC_API_KEY = "sk-ant-..."
# 或永久设：
# [System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'sk-ant-...', 'User')

# 3. 启动游戏 (Steam启动选项里要有 --disable-gpu)
# 停在某未通关题上

# 4. 跑
python solver.py
```

按 Ctrl+C 随时中止。

## 工作原理

```
循环:
  截图 → base64 → Anthropic API (claude-sonnet-4-6 + 多模态)
                         ↓
                  返回结构化 JSON
                  {puzzle_no, category, candidates, recommend_action, ...}
                         ↓
  程序按 recommend_action 操作:
    submit → click 输入框 + 粘贴中文 + Enter
    hint   → TAB → click → Enter (拿提示)
    skip   → 跳过此题
                         ↓
  再截图 → API 看是不是通关 → 是就 next_puzzle()
```

## 关键文件

- `solver.py` — 主程序
- `requirements.txt` — Python 包
- `../answers.jsonl` — 累积答案库,跨次运行复用
- `../STRATEGY.md` — 解题策略(嵌入在 solver.py 的 SYSTEM_PROMPT 里)
- `../DESIGN.md` — 整体设计

## 调参建议

| 参数 | 在哪 | 说明 |
|---|---|---|
| `MODEL` | solver.py 顶部 | sonnet 准确 / haiku 便宜 5 倍 |
| `INPUT_FIELD` | solver.py 顶部 | 输入框中心坐标,不同分辨率要改 |
| `SUBMIT_DELAY` | solver.py 顶部 | 提交后等多久看结果(慢机器加大) |
| `MAX_TRIES_PER_PUZZLE` | solver.py 顶部 | 最多尝试次数,超过就跳过 |
| `SYSTEM_PROMPT` | solver.py | 解题逻辑都在这,加新经验改这里 |

## 已知问题 / 后续改进

1. **坐标硬编码** — 不同分辨率/缩放比例需要手动调 `INPUT_FIELD`
   - 改进: 用 `cv2.matchTemplate` 找输入框图标自动定位
2. **类型/题号 OCR 误识别** — 偶尔 Claude 把"成语"看成"俗语"
   - 改进: 单独跑 OCR + 字典校正
3. **API 失败无退避** — 网络抖动会直接报错
   - 改进: 加指数退避重试
4. **不验证缓存答案** — KB 命中后不再校验,如果题号被游戏复用会出错
   - 改进: 缓存命中后再发一张截图给 API 校验场景
5. **颜色识别完全依赖 VLM** — 可以本地像素读取省 token
   - 改进: 写个 `read_feedback_colors(img)` 直接从已知坐标读 RGB

## 估算成本

- claude-sonnet-4-6: $3/MTok input + $15/MTok output
- 单次截图 ≈ 1500-2000 tokens(图) + 500 tokens(prompt)
- 单次响应 ≈ 500 tokens
- **每题约 3-5 次调用 ≈ $0.05-0.10**
- 100 题 ≈ $5-10

换 claude-haiku-4-5 (~$0.80/MTok) 可降到 $1-2/100题, 准确率打 9 折。
