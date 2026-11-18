# 文档契约与模板

## 目录

- [最小结构](#最小结构)
- [工件选择与路径映射](#工件选择与路径映射)
- [信息状态](#信息状态)
- [信息角色与耦合度](#信息角色与耦合度)
- [元数据约定](#元数据约定)
- [新鲜度契约](#新鲜度契约)
- [生命周期](#生命周期)
- [文件契约](#文件契约)
- [迁移规则](#迁移规则)
- [机械检查与内容审阅](#机械检查与内容审阅)
- [质量评分](#质量评分)

## 最小结构

按项目复杂度选用所需工件。以下路径是默认约定，允许映射到项目已有的等价位置。

| 工件 | 何时需要 | 权威内容 |
| --- | --- | --- |
| `AGENTS.md` | 所有 AI 参与开发的仓库 | 导航、命令、少量不可违背规则、任务路由 |
| `ARCHITECTURE.md` | 两个以上组件或存在明确依赖边界 | 系统地图、模块职责、依赖方向 |
| `docs/PROJECT_STATE.md` | 跨会话、有活跃计划、多环境或持续运维 | 项目阶段、工作优先级、跨任务阻塞和计划入口；必要的环境与验证摘要 |
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

## 工件选择与路径映射

`AGENTS.md` 是唯一无条件要求的入口。其余工件按上表的适用条件选择，初始化和检查共用仓库根目录的 `doc-harness.json`：

```json
{
  "artifacts": {
    "architecture": "handbook/system.md",
    "design-docs": "handbook/decisions",
    "plans": "docs/exec-plans",
    "project-state": "docs/PROJECT_STATE.md"
  }
}
```

- 对象中列出的角色表示已采用；路径必须位于仓库内。文件角色指向文件，目录角色指向目录。
- 初始化和检查采用清单中声明的角色。清单内的文件或目录缺失时报错，缺口保留到补齐时。
- 支持的文件角色：`architecture`、`project-state`、`tech-debt`、`quality`、`reliability`、`security`。
- 支持的目录角色：`design-docs`、`product-specs`、`plans`、`operations`、`generated`、`references`。设计与产品目录需要 `index.md`；计划目录下需要 `active/index.md` 与 `completed/index.md`。
- `plans` 和 `tech-debt` 分别选择。项目有活跃计划时，必须同时维护 `project-state`。
- 路径映射保留元数据、状态和必要章节的契约。项目已有其他内部格式时，让检查器读取原格式。

首次采用默认路径时，可以运行 `init --root <repo> --with architecture --with design-docs`；`--with` 可重复使用，选择会写入配置，后续 `check` 无需重复参数。自定义路径时先写配置，再运行 `init`；生成的导航链接会按目标位置调整。已有正文和其中的链接仍需按迁移映射核对。

没有配置时，脚本按已存在的默认路径识别可选工件；空仓库默认只初始化 `AGENTS.md`。这种兼容模式无法发现整个可选工件被删除，或自动识别非默认路径，因此正式接入 CI、采用自定义路径或需要检查缺失工件时应提交配置。

选择设计文档目录时先生成索引，有原则或决策需要记录时再创建 `core-beliefs.md`。初始化只创建缺失的 Markdown，保留已有 Markdown。显式 `--with` 会更新配置。已有 `AGENTS.md` 缺少项目状态链接时，按 `ACTION_REQUIRED` 补上链接。用项目事实填写模板中的 TODO/TBD。

## 信息状态

文档类型说明事实属于哪里；信息状态说明它多久可能失效：

| 类型 | 示例 | 维护方式 |
| --- | --- | --- |
| 稳定事实 | 使命、边界、架构职责、已实施决策 | 设计变化时复审；链接机械约束 |
| 活跃状态 | 当前阶段、计划、阻塞、技术债 | 任务状态变化时更新；提供明确下一动作 |
| 易变事实 | 部署版本、节点、外部服务、运行配置 | 记录观测日期、环境、验证命令和局限 |

产品目标引用已批准的规格或决定，实现状态引用代码和测试，部署状态引用目标环境的运行记录。

## 信息角色与耦合度

初始化结构、迁移旧文档或维护现有文档时，都用以下角色决定信息应放在哪里，以及其他文档如何引用或投影它。同一主题可以合理地出现在多份文档中，关键是每一处承担清晰且有价值的角色：

| 角色 | 作用 | 常见位置 | 维护关系 |
| --- | --- | --- | --- |
| 权威定义（Authority） | 完整定义当前规则、值或契约 | `SECURITY.md`、产品规格、平台契约、运行状态 | 由明确负责人维护，作为其他文档的主要引用目标 |
| 护栏摘要（Guardrail） | 在任务入口或风险现场提醒读者 | `AGENTS.md`、操作手册、局部开发指南 | 保留足以指导当下动作的短摘要，并链接权威定义 |
| 领域投影（Projection） | 解释同一事实对特定领域的影响 | 架构、设计、可靠性、功能文档 | 聚焦本领域的行为、责任或后果，并链接完整定义 |
| 历史证据（Evidence） | 保存决策、发布、验证当时的事实 | 已完成计划、决策记录、发布记录 | 带日期、版本或环境，服务追溯并链接当前状态 |

可把变更耦合度理解为“事实变化频率 × 需要人工同步的当前文档数量”。设计和维护信息架构时关注以下方向：

- 稳定且高风险的规则适合在入口保留护栏摘要，使智能体在关键动作前获得提醒。
- 高频变化的当前值保存在运行负责人维护的权威来源中；其他文档说明它的意义、影响和查询入口。
- 产品规格描述期望行为，设计文档描述实现与校验路径；两者通过链接形成互补投影。
- 历史计划和发布记录保留当时证据，使过去判断可追溯，同时由当前状态说明现在成立的事实。
- 当一次变化牵动很多当前文档时，复核每处内容是否提供了角色特有的信息价值，并优先收敛同步成本高、变化又频繁的细节。

## 元数据约定

`owner` 表示负责维护或确认内容的人、团队或角色；主要权威来源通过文件路径或链接另行标注。

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

- `verified_commit`: 文档最近与之核验的 commit 或明确的工作树标识；`project-state` 必填，未核验时明确写 `Unknown` 并在 `Last verified` 说明局限。
- `observed_at`: 易变运行事实的实际观测日期或时间。
- `environment`: `local`、`test`、`staging`、`production` 或项目定义的环境。
- `supersedes`: 当前文档取代的仓库相对路径。
- `superseded_by`: 取代当前文档的仓库相对文件路径；`superseded` 必填，`deprecated` 有替代来源时填写。
- `deprecation_reason`: 退役原因，所有 `deprecated` 文档必填。
- `generated_from`: 生成输入或命令；出现此字段时不要手工编辑正文。
- `review_trigger`: 触发复审的代码目录、事件或版本；由内容审阅判断是否触发。
- `review_after_days`: 正整数，按风险设置当前文档的复审或任务状态检查周期；未设置时使用 `--stale-days`。
- `updated_at`: 计划或项目状态最近一次实质进展更新的日期；与 `last_reviewed` 的含义不同。
- `observation_max_age_days`: 正整数，设置 `observed_at` 的有效期；未设置时使用 `--stale-days`。
- `work_status`: 项目状态的工作状态，`active`、`waiting` 或 `idle`；独立于文档生命周期 `status: active`。旧文档省略时按工作活跃处理。

owner、日期和验证证据按实际情况填写。迁移中的未知值可暂时使用 `TBD`，但 `active`、`blocked`、`accepted` 和 `implemented` 文档必须在严格检查前落实真实 owner。`verified_commit` 指向最近实际核验的代码或工作树，不要求它包含随后提交的纯文档修改。

## 新鲜度契约

- `last_reviewed` 只在实际复审后更新。当前文档按 `review_after_days` 或默认周期检查；设计、依赖或风险发生变化时即使尚未到期也应复审。
- 活跃计划和项目状态有实质进展时更新 `updated_at`。检查器用它计算状态的年龄，旧文档缺少该字段时使用 `last_reviewed`。
- 取得新的运行观测时更新 `observed_at`，由 `observation_max_age_days` 指定有效期。日期可用日历日期或 ISO 8601 时间。脚本按日检查，小时级有效期由项目工具检查。
- `completed`、`cancelled`、`rejected`、`superseded`、`deprecated` 保留历史日期。检查器验证日期格式和必要契约。若当前规则仍引用这项历史判断，在引用处注明适用条件，条件变化时复审。
- 对尚未核实的事实填 `Unknown`，检查器会提示证据缺口。已确认没有填 `None`，不适用填 `Not applicable`。必填的负责人、替代文档或日期按各自字段契约填写。

## 生命周期

各类文档的状态与含义如下。

| `doc_type` | 允许状态 | 语义 |
| --- | --- | --- |
| `project-state` | `active` | 当前恢复入口 |
| `architecture`、`product-spec`、`operations`、`reliability`、`security` | `draft`、`active`、`deprecated` | 未确认、当前权威、已失效 |
| `decision` | `proposed`、`accepted`、`implemented`、`rejected`、`superseded` | 待决、已批准待实施、已落地、已否决、被取代 |
| `plan` | `active`、`blocked`、`completed`、`cancelled` | 执行中、受阻、完成、取消 |
| `tech-debt` | `active`、`deprecated` | 当前 tracker 或已退役（可有替代系统） |

权威性规则：

- 生效的产品规格定义目标行为。`accepted` 表示决策已获批准，`implemented` 需要实施证据，部署情况查目标环境的运行记录。
- `draft` 和 `proposed` 分别标记草案和待审提案。
- 计划的 `active`、`blocked` 描述执行进度，项目状态的 `active` 标记当前恢复入口。
- `completed` 和 `cancelled` 保存执行历史。仍然有效的产品与架构决定归入相应权威文档。
- `rejected` 保存仍能阻止未来误判的负面知识。
- `superseded` 不再是当前事实，必须通过 `superseded_by` 指向替代文件。`deprecated` 记录 `deprecation_reason`；功能下线或规范撤销可以没有后继文档，有后继时再提供链接。

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

“Task routing” 应写成条件导航，例如：修改 API 前读取架构和 API 设计文档；修改结算行为前读取对应产品规格。存在项目状态工件时必须从 Documentation map 链接其实际路径。避免塞入所有专题规则。

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

使用 `doc_type: project-state`、`status: active`、`work_status` 和 `verified_commit`。正文包含：

```markdown
# Project State
## Current phase
## Now
## Next action
## Blocked or awaiting
## Active work
## Environment divergence
## Last verified
## Decisions and review conditions
```

`Decisions and review conditions` 链接既有决策，摘要其适用前提和重审触发条件；旧标题 `Do not reopen` 仍可被检查器识别，维护时逐步采用新标题。

有活跃计划时，`Next action` 指向当前优先计划的快照，`Last verified` 链接影响项目判断的验证记录，不逐项复制任务字段。无计划时可在此直接维护下一动作和验证。等待或空闲时增加 `Resume when` 章节。详细模板、触发条件和冷启动验收见 [resumability.md](resumability.md)。

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

`proposed` 说明待决方案、验收和风险；`accepted` 记录批准依据并链接实施计划，明确标为待实施；`implemented` 用现在时说明已生效机制并链接验证证据；`rejected` 说明仍可能被重新提出的方案为什么不成立；`superseded` 链接替代文档。`design-docs/index.md` 至少列出标题、状态、owner、最近复审日期和链接。

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
- Resume when: blocked 计划必填；active 计划可省略
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

进度使用带日期的清单。计划快照记录任务状态、下一动作、阻塞和最近验证，Progress 和 Validation 保留带日期的证据，项目状态链接相应快照。`blocked` 计划在 `Resume when` 写明解除阻塞的条件，在 `Next action` 写恢复后的动作。尚未核实的事实填 `Unknown` 并注明核验位置。

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

使用 `doc_type: tech-debt`。每项包含 `ID`、影响范围、风险、证据、推荐方向、owner、状态和最近复审日期。只登记有证据支持的债务。计划关闭时未排期工作必须进入新计划或 tracker。

### 运行状态

使用 `doc_type: operations`，区分目标配置和实际观测。易变事实优先包含：

```markdown
## Target state
## Observed state
## Environment divergence
## Verification procedure
## Recovery or rollback
```

frontmatter 使用 `observed_at`、`environment` 和适当的 `verified_commit`。已有快照尚待复核时，注明原观测时间和待核实的内容。

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

已有迁移授权覆盖的移动、整合和链接修复直接执行；仅对超出授权范围或可能丢失无法判断去留的信息请求确认。

1. 先建立旧路径到新路径的映射表，并区分当前权威、提案、执行历史和外部参考。
2. 先创建当前状态、索引和交叉链接，再移动正文。
3. 为多处出现的内容标注角色，保留权威定义，并把其他位置整理为面向各自读者的护栏摘要、领域投影或历史证据。
4. 把长计划中的持久决策、当前行为和未完成事项分别提升到对应权威文档、执行计划或技术债记录，并明确负责人。
5. 对重要否决方案保留 `rejected` 记录；没有未来防错价值的过程噪声不必迁移。
6. 退役内容标记 `deprecated` 并记录原因；被取代内容标记 `superseded` 并链接替代文件。
7. 更新代码注释、CI、issue 模板和文档中的旧链接。
8. 完成后运行严格检查，并从入口进行冷启动导航验收。

## 机械检查与内容审阅

下表列出 `check` 检查的项目，以及内容审阅时需要回答的问题。

| 机械检查实际覆盖 | 仍需内容审阅或项目工具验证 |
| --- | --- |
| 已选工件的路径、入口长度、必要章节或字段存在 | 目录是否适用、入口是否足以恢复工作、内容是否有意义 |
| 支持的 Markdown 内联本地文件链接目标是否存在 | 锚点、引用式链接、外链、链接所指内容是否权威；正则识别还可能把示例当作真实链接 |
| 索引是否出现同目录 Markdown 文件名 | 是否是有效导航链接，索引状态与负责人是否和正文一致 |
| 简单平面 frontmatter 的字段、状态、路径与日期约束 | 完整 YAML 语法、真实责任归属、复审是否发生、观测是否可信 |
| 快照与关闭记录的必要字段/章节、空值及部分占位值 | 下一动作是否可执行，关闭证据是否充分，持久结论是否完成提升 |
| 当前记录的日期年龄、显式等待/空闲条件字段 | 变更事件是否触发复审，运行事实是否仍成立，目标/实现/部署是否一致 |

内置 frontmatter 解析器读取每行 `key: value` 形式的简单未加引号标量。使用更丰富 YAML 或不同 Markdown 语法时，采用相应解析器。`--strict` 将警告计为失败。`Unknown` 标记的事实留待取得证据后更新。

审阅发现冲突时，列出目标、实现和部署的依据。文档过时则更新说明，实现有误或迁移未完成则按任务授权处理。原因待定时记录差异和确认人。

## 质量评分

按领域而不是按文件数量评分：

| 维度 | 检查问题 |
| --- | --- |
| 可发现性 | 能否从 `AGENTS.md` 两次跳转内找到权威信息？ |
| 可恢复性 | 能否确定当前阶段、下一动作、阻塞、环境差异和最近验证？ |
| 正确性 | 文档是否与代码、测试和实际运行行为一致？ |
| 权威性 | 提案、当前事实、执行历史和被取代材料是否明确分离？ |
| 决策连续性 | 是否保留既有结论、适用前提和重审条件，避免重复争论并允许新证据触发重审？ |
| 完整性 | 目标、边界、失败模式和验证是否齐备？ |
| 新鲜度 | 是否有真实 owner、复审日期、环境和机械验证？ |
| 可执行性 | 命令是否可复制运行，验收标准是否可测试？ |
| 耦合度 | 信息角色是否清晰，一次变化需要人工同步的当前文档是否保持在合理范围？ |

使用 `good / partial / missing / stale`，并为 `partial`、`missing`、`stale` 记录下一步和 owner。评分应如实反映缺口及后续工作。
