<!--
更新时间：2026-08-19（北京时间）
生成模型：claude-sonnet-4-6
-->

# AGENTS.md — macro_report

> **路径约定**：本文件源码路径均相对于 `app/` 目录（仓库根下的 `app/`）。

macro_report 是独立的 ECS Fargate 服务，Python FastAPI，VPC 内通过内网 ALB 访问（`http://macro-report.<env>.bl.internal`，如 dev 为 `macro-report.dev.bl.internal`）。

核心能力（待完善）：

- 业务库 `macro_report` 条件查询
- 用户与 token 鉴权；管理员（`app_user.is_admin`）可管用户与定时脚本
- **定时脚本**：`schedules.yaml` → EventBridge cron → 同集群 `RunTask`（独立 jobs Task Definition），与 API Service 隔离；管理员可在 `/admin/scripts` 手动启停与暂停调度

本地开发说明见 [`app/README.md`](app/README.md)；管理员初始化见 [`docs/admin_roles.md`](docs/admin_roles.md)。

**API 接口文档**：[docs/api.md](docs/api.md)（权威镜像，见下方维护规范）。
**大模型调用规范（强制）**：[docs/llm-call-convention.md](docs/llm-call-convention.md)。

## 双端口与鉴权

进程同时监听两个端口（见 `main.py` / ECS Task Definition）：

| 端口 | 环境变量 | 用途 | 鉴权 |
|---|---|---|---|
| `8000` | `PORT` | 外网 / 页面 / 需 token 的调用 | `Authorization: Bearer <token>` |
| `8080` | `INTERNAL_PORT` | 内网 ALB 监听；VPC 内调用 | **无 token**（由 SG + 内网 ALB 保障） |

- 用户表：`app_user`（含 `is_admin`）；token 表：`auth_token`
- `session`：页面登录后签发的临时 token（默认 8h，登录会撤销该用户旧 session）
- `api`：用户在 `/admin/tokens` 或 `POST /api/v1/auth/tokens` 签发；默认 90 天，最长 365 天
- 公开（外网端口）：`GET /health`、`POST /api/v1/auth/login`、`POST /api/v1/auth/bootstrap`（仅无用户时）、静态页路由
- 管理员专属：用户管理相关接口、`/api/v1/scripts*`（见 `docs/api.md` / `docs/admin_roles.md`）

## 资源命名

- ECS Cluster / Service：`macro-report-<env>`
- Jobs Task Definition：`macro-report-<env>-jobs`
- CloudWatch Log Group：`/ecs/macro-report-<env>`（API）、`/ecs/macro-report-<env>-jobs`（定时脚本）
- EventBridge Rule：`macro-report-<env>-<script>`（由 `app/schedules.yaml` 驱动，IaC `yamldecode` 消费）
- 内网 ALB：`macro-report-<env>-int`（监听 **80** → 鉴权端口；**8080** → 内网无鉴权端口）
- Route53（PHZ）：`macro-report.<env>.bl.internal`
- IAM Roles：`macro-report-<env>-exec`、`-task`、`-events`
- Tofu state key：`app/macro-report/<env>/terraform.tfstate`
- 业务数据库：`macro_report`（共享 meerkat RDS 实例）

## 部署

- 本地开发入口：`uv run python main.py`（API）、`uv run python run_script.py <name>`（脚本）；工作目录必须是 `app/`
- `config.Settings` 对 `ENV` / `PG_HOST` **无代码默认值**，缺一启动失败
- **提交 / 推送默认目标：`dev` 分支**（禁止把功能改动直接 push 到 `staging` / `main`）
- dev：push 到 `dev` 分支 → `deploy-dev.yml` 自动检测变更并部署
- staging：PR main→staging 合并 → `deploy.yml` 触发
- prod：打 `v*` tag → `deploy.yml` 触发
- prod 需 GitHub Environment `production-app` 手动审批

## GitHub Secrets（需在 repo 设置）

| Secret | 用途 |
|---|---|
| `MACRO_REPORT_BOT_TOKEN` | sync-dev-to-main workflow 用 PAT（Classic，repo scope） |

## 脚本文档联动规范

**规则（强制）**：`app/scripts/<script>.py` 有变动时，必须在**同一 commit** 内更新对应 `docs/<script>.md`。

调度权威源：`app/schedules.yaml`（改 cron / enabled / 增删脚本时同步更新该文件；IaC 不在 TF 变量写死 schedule）。

---

## 大模型调用规范（强制）

凡涉及大模型（工作台试运行、定时脚本、新增 API/脚本）：

1. 业务侧只做：校验 → 拼装**客户问题** → 选用已发布 `prompt_bundle` + `llm_configs` → 调用共用执行层 → 回写业务结果。
2. **禁止**在业务脚本内自建多 Agent、自建 tool 循环、或绕过 `llm_configs` 直连模型厂商。
3. 多 Agent / 原文可溯源 / Skills tools 等执行策略，统一在提示词工作台与 `services/prompt_test_runner.py` 演进。

权威细则见 [docs/llm-call-convention.md](docs/llm-call-convention.md)。

---

## API 文档维护规范

**规则（强制，CI 强制执行）**：`app/api/v1/` 或 `app/models/schemas.py` 有变动时，必须在**同一 commit** 内更新 `docs/api.md`，否则 PR 将被 CI 卡住。

## app ↔ 基础设施边界

- 应用接入只读 SSM 派生，不硬编码账号 ID / ARN / VPC ID
- 不直接修改 `infra` IaC
- 本仓 `iac/` 仅管理本应用资源（ECS / ALB / EventBridge / IAM 等）；改动后须 `tofu fmt` + `tofu validate -backend=false`
