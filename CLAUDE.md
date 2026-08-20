<!--
更新时间：2026-08-19（北京时间）
生成模型：claude-sonnet-4-6
-->

# CLAUDE.md — macro_report

> Claude Code 兼容入口。完整 AI 协作上下文见 [AGENTS.md](AGENTS.md)。
> 开始任何改动前先读取 `AGENTS.md`，并按其中的服务结构、命令与接口约定执行。

## 语言约定

**所有对话回复必须使用中文**（代码、命令、文件内容本身不受限制）。

## 分支规则（强制，不可绕过）

| 分支 | 规则 |
|---|---|
| `main` | 禁止直接 push；由 CI bot 自动 merge |
| `staging` | 必须 PR，只接受来自 `main` 的 PR |
| `prod` | 必须 PR + 1 人 review，只接受来自 `staging` 的 PR |
| `dev` | 禁止 force push；**唯一允许直接 push 的分支** |

## 本地开发约定

- 本地**只操作 `dev` 分支**，所有提交推送到 `dev`
- 如需隔离开发，基于 `dev` 创建 `feature/*` 分支，PR 合并回 `dev`
- **禁止**在本地 checkout 或 push `main`、`staging`、`prod`
- **改动完成后只执行 `git commit`，不自动 `git push`**；等用户明确确认后再推送

## 关键路径保护（不可绕过）

以下路径受保护，AI **禁止**直接 push，必须开 PR 并由 @linusli-balance 或 @holiyliu-futu 审批后合并：

- `AGENTS.md` / `CLAUDE.md`
- `iac/`（IaC 资源定义）
- `.github/workflows/`（CI/CD 流水线）
- `.gitignore`

**禁止**使用 `--no-verify` 绕过任何 hook，无例外。

## 其他强制约束

- 修改 `iac/` 后必须跑 `tofu fmt` + `tofu validate -backend=false`
- ECS 服务**禁止** `enable_execute_command = true` 或 `ssmmessages:*`
- `aws_ecs_service` **禁止** `lifecycle { ignore_changes = [task_definition] }`
- **新增或修改 `app/api/v1/` 端点、`app/models/schemas.py` 时，必须在同一 commit 内更新 `docs/api.md`**；CI 会检查漏更
- **修改 `app/scripts/<script>.py` 时，必须在同一 commit 内更新对应 `docs/<script>.md`**；两者需保持同步
