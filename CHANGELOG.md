# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 规范，版本号采用 [SemVer](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 计划
- 多分辨率自适应（目前 INPUT_FIELD 坐标硬编码 1389x868 全屏）
- 题库去重与统计脚本
- 支持 Linux / macOS（需替换 `pygetwindow`）

## [0.1.0] - 2026-05-03

首个工程化版本。29 题 100% 通关，85% 一击命中，AI 推理真实准确率约 100%。

### 新增
- `solver/solver.py`：截图 → Claude 推理 → 键盘输入 → 反馈解析的全自动闭环
- `answers.jsonl`：积累的题库（已答对的题作为 few-shot 范例）
- `DESIGN.md`：架构与决策记录
- `STRATEGY.md`：提示词、置信度阈值、错误处理策略
- 支持 `claude-sonnet-4-6` / `claude-haiku-4-5` 双模型切换

### 已知问题
- 仅支持 Windows（依赖 `pygetwindow` 抓窗口标题）
- 输入框坐标硬编码，换分辨率需手改 `INPUT_FIELD`
- 罕见字 / 网络新梗会触发误判

[Unreleased]: https://github.com/xiaoshuntian/claude-badpunpc/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/xiaoshuntian/claude-badpunpc/releases/tag/v0.1.0
