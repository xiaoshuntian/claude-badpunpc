# 贡献指南

欢迎 issue / PR！这是个个人玩票项目，规则尽量轻。

## 报 bug / 提需求

走 [Issues](https://github.com/xiaoshuntian/claude-badpunpc/issues)，模板会带你填关键信息。最好附上：
- 你跑的题号 / 截图
- `solver_log.md` 的相关片段
- Claude 的原始返回（如果是推理出错）

## 开发环境

```bash
git clone https://github.com/xiaoshuntian/claude-badpunpc.git
cd claude-badpunpc/solver
python -m venv .venv
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # macOS/Linux（注意：solver 目前只支持 Windows）
pip install -r requirements.txt
pip install ruff               # 提交前 lint 用
```

需要环境变量 `ANTHROPIC_API_KEY`。

## 代码规范

- Python 用 [ruff](https://docs.astral.sh/ruff/) lint + format，提交前跑 `ruff check . && ruff format .`
- 行长 100，字符串首选双引号
- 不写无意义的 docstring；模块顶部的"为什么"注释欢迎补

## 提交信息

[Conventional Commits](https://www.conventionalcommits.org/zh-hans/v1.0.0/)：

```
feat: 加多分辨率自适应
fix: 修罕见字截断
docs: 补 DESIGN.md 的 retry 章节
refactor: 把提示词拆到独立文件
chore: 升级 anthropic 到 0.42
```

## PR 流程

1. fork → 起新分支：`git checkout -b feat/xxx`
2. 改完跑一次 `ruff check`，本地能跑通 solver
3. 写清楚改了啥、为啥改、怎么验证
4. 提 PR，等 CI 通过

## 不接受的 PR

- 分发游戏内容（题库截图、官方答案表）
- 反检测 / 绕过游戏机制的"作弊"功能 —— 本项目定位是 AI 推理实验，不是外挂
- 加无关的依赖或抽象层（请先开 issue 讨论）

## 行为准则

互相尊重，对事不对人。脏话斗嘴留给游戏里。
