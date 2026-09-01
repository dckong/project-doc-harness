# 文档契约与模板

## 目录

- [最小结构](#最小结构)
- [信息状态](#信息状态)
- [信息角色与耦合度](#信息角色与耦合度)
- [元数据约定](#元数据约定)
- [生命周期](#生命周期)
- [文件契约](#文件契约)
- [迁移规则](#迁移规则)
- [质量评分](#质量评分)

## 最小结构

按项目复杂度选用，不要求一次创建全部文件。

| 工件 | 何时需要 | 权威内容 |
| --- | --- | --- |
| `AGENTS.md` | 所有 AI 参与开发的仓库 | 导航、命令、少量不可违背规则、任务路由 |
| `ARCHITECTURE.md` | 两个以上组件或存在明确依赖边界 | 系统地图、模块职责、依赖方向 |
| `docs/PROJECT_STATE.md` | 跨会话、有活跃计划、多环境或持续运维 | 当前阶段、下一动作、阻塞、环境差异和最近验证的短摘要 |
| `docs/design-docs/` | 存在跨模块设计决策 | 设计动机、约束、决策、替代方案和生命周期 |
| `docs/product-specs/` | 行为由产品意图决定 | 用户行为、验收标准、非目标 |
| `docs/exec-plans/` | 复杂或跨会话任务 | 可恢复的进度、决策、验证、关闭记录和债务 |
| `docs/operations/` | 有部署、外部依赖或运行状态 | 目标环境与实际观测、验证和恢复方式 |
| `docs/generated/` | 模式、API 或依赖信息可自动生成 | 标注来源与生成命令的只读快照 |
| `docs/references/` | 智能体必须离线查阅外部规范 | 经许可落库的稳定参考资料 |
| `docs/QUALITY_SCORE.md` | 大型仓库需要持续补齐知识 | 各域文档覆盖、风险与负责人 |
| `docs/RELIABILITY.md` | 有运行时或运维责任 | SLO、失败模式、可观测性、恢复 |
| `docs/SECURITY.md` | 处理鉴权、数据或发布 | 威胁边界、敏感数据和验证要求 |

`PROJECT_STATE.md` 是状态胶囊，不是新的产品、架构或部署事实源。详细恢复规则见 [resumability.md](resumability.md)。

## 信息状态

文档类型说明事实属于哪里；信息状态说明它多久可能失效：

| 类型 | 示例 | 维护方式 |
| --- | --- | --- |
| 稳定事实 | 使命、边界、架构职责、已实施决策 | 设计变化时复审；链接机械约束 |
| 活跃状态 | 当前阶段、计划、阻塞、技术债 | 任务状态变化时更新；提供明确下一动作 |
| 易变事实 | 部署版本、节点、外部服务、运行配置 | 记录观测日期、环境、验证命令和局限 |

目标、当前实现和实际部署分别记录。不能因为代码存在就宣称服务器已经部署，也不能因为生产在运行就宣称它符合最新产品目标。

## 信息角色与耦合度

初始化结构、迁移旧文档或维护现有文档时，都用以下角色决定信息应放在哪里，以及其他文档如何引用或投影它。同一主题可以合理地出现在多份文档中，关键是每一处承担清晰且有价值的角色：

| 角色 | 作用 | 常见位置 | 维护关系 |
| --- | --- | --- | --- |
| 权威定义（Authority） | 完整定义当前规则、值或契约 | `SECURITY.md`、产品规格、平台契约、运行状态 | 由明确 owner 维护，作为其他文档的主要引用目标 |
| 护栏摘要（Guardrail） | 在任务入口或风险现场提醒读者 | `AGENTS.md`、操作手册、局部开发指南 | 保留足以指导当下动作的短摘要，并链接权威定义 |
| 领域投影（Projection） | 解释同一事实对特定领域的影响 | 架构、设计、可靠性、功能文档 | 聚焦本领域的行为、责任或后果，并链接完整定义 |
| 历史证据（Evidence） | 保存决策、发布、验证当时的事实 | 已完成计划、决策记录、发布记录 | 带日期、版本或环境，服务追溯并链接当前状态 |

可把变更耦合度理解为“事实变化频率 × 需要人工同步的当前文档数量”。设计和维护信息架构时关注以下方向：

- 稳定且高风险的规则适合在入口保留护栏摘要，使智能体在关键动作前获得提醒。
- 高频变化的当前值适合靠近运行 owner；其他文档说明它的意义、影响和查询入口。
- 产品规格描述期望行为，设计文档描述实现与校验路径；两者通过链接形成互补投影。
- 历史计划和发布记录保留当时证据，使过去判断可追溯，同时由当前状态说明现在成立的事实。
- 当一次变化牵动很多当前文档时，复核每处内容是否提供了角色特有的信息价值，并优先收敛同步成本高、变化又频繁的细节。

## 元数据约定

对当前状态、架构、设计、产品、计划、运行、安全和可靠性文档使用 YAML frontmatter：

```yaml
---
doc_type: project-state | architecture | decision | product-spec | plan | tech-debt | operations | reliability | security
status: status-for-this-doc-type
owner: team-or-role
last_reviewed: YYYY-MM-DD
---
```

可选或按类型要求的字段：

- `verified_commit`: 文档最近与之核验的 commit 或明确的工作树标识；`project-state` 必填。
- `observed_at`: 易变运行事实的实际观测日期或时间。
- `environment`: `local`、`test`、`staging`、`production` 或项目定义的环境。
- `supersedes`: 当前文档取代的仓库相对路径。
- `superseded_by`: 取代当前文档的仓库相对路径；`deprecated` 和 `superseded` 必填。
- `generated_from`: 生成输入或命令；出现此字段时不要手工编辑正文。
- `review_trigger`: 触发复审的代码目录、事件或版本。

不要虚构 owner、日期或验证证据。迁移中的未知值可暂时使用 `TBD`，但 `active`、`blocked` 和 `implemented` 文档必须在严格检查前落实真实 owner。`verified_commit` 指向最近实际核验的代码或工作树，不要求它包含随后提交的纯文档修改。

## 生命周期

状态按 `doc_type` 解释，不能混用：

| `doc_type` | 允许状态 | 语义 |
| --- | --- | --- |
| `project-state` | `active` | 当前恢复入口 |
| `architecture`、`product-spec`、`operations`、`reliability`、`security` | `draft`、`active`、`deprecated` | 未确认、当前权威、已失效 |
| `decision` | `proposed`、`implemented`、`rejected`、`superseded` | 待决、已生效、已否决、被取代 |
| `plan` | `active`、`blocked`、`completed`、`cancelled` | 执行中、受阻、完成、取消 |
| `tech-debt` | `active`、`deprecated` | 当前 tracker 或已由替代系统接管 |

权威性规则：

- `active` 和 `implemented` 可以作为当前实现依据。
- `draft` 和 `proposed` 不得被智能体擅自视为已确认需求或设计。
- `blocked` 只表示执行状态，不改变既有产品和架构事实。
- `completed` 和 `cancelled` 是执行历史，不自动拥有当前产品或架构权威。
- `rejected` 保存仍能阻止未来误判的负面知识。
- `deprecated` 和 `superseded` 不再是当前事实，必须通过 `superseded_by` 指向替代来源。

计划目录必须与状态一致：`active/` 只容纳 `active` 或 `blocked`，`completed/` 只容纳 `completed` 或 `cancelled`。

## 文件契约

### `AGENTS.md`

控制在约 100 行并保持稳定：

```markdown
# Repository Guide

## Mission and boundaries
## Commands
## Non-negotiable rules
## Documentation map
## Task routing
## Before finishing
```

“Task routing” 应写成条件导航，例如：修改 API 前读取架构和 API 设计文档；修改结算行为前读取对应产品规格。存在 `docs/PROJECT_STATE.md` 时必须从 Documentation map 链接它。避免塞入所有专题规则。

### `ARCHITECTURE.md`

使用 `doc_type: architecture`，写系统地图而非逐文件说明：

```markdown
# Architecture
## Context and scope
## Components and responsibilities
## Dependency direction
## Data and control flow
## Cross-cutting concerns
## Enforced invariants
## Where to learn more
```

链接可执行约束（lint、测试、模式）。如果架构规则没有任何验证手段，明确标注该风险。`draft` 表示尚不能作为最终架构依据；已确认但仍有局部缺口的当前架构使用 `active`，并显式记录缺口。

### `docs/PROJECT_STATE.md`

使用 `doc_type: project-state`、`status: active` 和 `verified_commit`。正文包含：

```markdown
# Project State
## Current phase
## Now
## Next action
## Blocked or awaiting
## Active work
## Environment divergence
## Last verified
## Do not reopen
```

保持短小，只保存状态摘要和链接。详细模板、触发条件和冷启动验收见 [resumability.md](resumability.md)。

### 设计决策

使用 `doc_type: decision`：

```markdown
# Decision title
## Context
## Goals and non-goals
## Constraints
## Decision or proposal
## Alternatives considered
## Consequences
## Verification
## Related sources
```

`proposed` 说明待决方案、验收和风险；`implemented` 用现在时说明已生效机制；`rejected` 说明仍可能被重新提出的方案为什么不成立；`superseded` 链接新 owner。`design-docs/index.md` 至少列出标题、状态、owner、最近复审日期和链接。

### 产品规格

使用 `doc_type: product-spec`：

```markdown
# Capability name
## User problem
## Desired behavior
## Non-goals
## Acceptance criteria
## Edge cases
## Analytics or observability
## Related implementation
```

验收标准应可测试。不要让产品规格变成当前实现的重复叙述；目标行为与当前实现存在差异时显式链接项目状态或执行计划。

### 执行计划

使用 `doc_type: plan`。活跃计划在长正文之前提供恢复快照：

```markdown
# Outcome
## Resume snapshot
- Current state:
- Next action:
- Blocked by:
- Awaiting:
- Last verified:
  - commit:
  - environment:
  - commands:
  - date:
## Context
## Scope and non-goals
## Milestones
## Progress
## Discoveries
## Decision log
## Validation
## Completion notes
```

进度使用带日期的清单。计划必须允许另一个智能体只依赖仓库内容继续执行。快照更新当前状态，Progress 和 Validation 保留带日期证据。

完成或取消计划时，`Completion notes` 必须包含：

```markdown
### Outcome
### Durable decisions promoted
### Product or architecture updates
### Remaining work transferred
### Rejected alternatives recorded
### Final validation
```

每节提供链接、证据或明确的 `None`。持久结论、未完成工作和否决理由拥有新位置后，才更新项目状态并把计划移动到 `completed/`。详细关闭顺序见 [resumability.md](resumability.md)。

### 技术债务 tracker

使用 `doc_type: tech-debt`。每项包含 `ID`、影响范围、风险、证据、推荐方向、owner、状态和最近复审日期。不要把没有证据的偏好登记成债务。计划关闭时未排期工作必须进入新计划或 tracker，不能只留在 completed plan。

### 运行状态

使用 `doc_type: operations`，区分目标配置和实际观测。易变事实优先包含：

```markdown
## Target state
## Observed state
## Environment divergence
## Verification procedure
## Recovery or rollback
```

frontmatter 使用 `observed_at`、`environment` 和适当的 `verified_commit`。如果无法实时核验，明确写出证据日期和局限，不能把旧快照表述成无条件当前事实。

### 生成文档

文件开头明确：

```markdown
<!-- Generated. Do not edit manually.
Source: path-or-command
Regenerate: exact command
-->
```

CI 应验证生成物未过期；若暂时不能验证，在 `QUALITY_SCORE.md` 登记风险。

## 迁移规则

1. 先建立旧路径到新路径的映射表，并区分当前权威、提案、执行历史和外部参考。
2. 先创建当前状态、索引和交叉链接，再移动正文。
3. 为多处出现的内容标注角色，保留权威定义，并把其他位置整理为面向各自读者的护栏摘要、领域投影或历史证据。
4. 把长计划中的持久决策、当前行为和未完成事项分别提升到正确 owner。
5. 对重要否决方案保留 `rejected` 记录；没有未来防错价值的过程噪声不必迁移。
6. 过时内容标记 `deprecated` 或 `superseded` 并链接替代文档。
7. 更新代码注释、CI、issue 模板和文档中的旧链接。
8. 完成后运行严格检查，并从入口进行冷启动导航验收。

## 质量评分

按领域而不是按文件数量评分：

| 维度 | 检查问题 |
| --- | --- |
| 可发现性 | 能否从 `AGENTS.md` 两次跳转内找到权威信息？ |
| 可恢复性 | 能否确定当前阶段、下一动作、阻塞、环境差异和最近验证？ |
| 正确性 | 文档是否与代码、测试和实际运行行为一致？ |
| 权威性 | 提案、当前事实、执行历史和被取代材料是否明确分离？ |
| 决策连续性 | 已实施和已否决选择能否防止未来重新争论？ |
| 完整性 | 目标、边界、失败模式和验证是否齐备？ |
| 新鲜度 | 是否有真实 owner、复审日期、环境和机械验证？ |
| 可执行性 | 命令是否可复制运行，验收标准是否可测试？ |
| 耦合度 | 信息角色是否清晰，一次变化需要人工同步的当前文档是否保持在合理范围？ |

使用 `good / partial / missing / stale`，并为 `partial`、`missing`、`stale` 记录下一步和 owner。分数用于暴露缺口，不用于美化报表。
