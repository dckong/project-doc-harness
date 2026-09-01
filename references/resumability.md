# 无记忆智能体恢复契约

## 目录

- [适用条件](#适用条件)
- [信息半衰期](#信息半衰期)
- [项目状态胶囊](#项目状态胶囊)
- [执行计划恢复快照](#执行计划恢复快照)
- [计划关闭事务](#计划关闭事务)
- [冷启动验收](#冷启动验收)

## 适用条件

满足任意条件时，项目需要显式恢复协议：

- 工作跨越多个会话、窗口或智能体；
- `docs/exec-plans/active/` 中存在活跃计划；
- 本地、测试、预发布和生产状态可能不同；
- 项目已经进入持续部署、运营或外部集成阶段；
- 多条工作流并行，下一动作不能从 Git 历史直接推出。

恢复协议不是新的产品或架构事实源。它提供当前状态和链接，使无记忆智能体无需从长计划、提交记录或聊天中重新推导工作位置。

## 信息半衰期

按变化速度选择所有者和验证方式：

| 类型 | 典型内容 | 维护规则 |
| --- | --- | --- |
| 稳定事实 | 使命、边界、架构职责、已实施决策 | 设计改变时更新，以权威文档和机械约束验证 |
| 活跃状态 | 当前阶段、计划、下一动作、阻塞、技术债 | 相关任务状态变化时立即更新 |
| 易变事实 | 部署版本、服务地址、外部依赖、运行配置 | 记录 `observed_at`、环境、验证方法和证据；过期后不得无条件当作当前事实 |

目标、实现和部署是三种不同事实。代码已经实现不证明目标环境已经部署；生产正在运行也不证明它符合最新产品目标。

## 项目状态胶囊

跨会话或复杂项目使用 `docs/PROJECT_STATE.md`：

```markdown
---
doc_type: project-state
status: active
owner: team-or-role
last_reviewed: YYYY-MM-DD
verified_commit: git-commit-or-working-tree-marker
---

# Project State

## Current phase

一句话说明当前阶段。

## Now

只写当前成立的状态摘要并链接权威文档。

## Next action

写一个可以直接执行和验证的最小动作。

## Blocked or awaiting

列出阻塞、依赖对象和决策 owner；没有则写 `None`。

## Active work

链接活跃计划；没有则写 `None`。

## Environment divergence

说明目标、本地、测试、生产之间已知差异并链接运行状态；没有则写 `None`。

## Last verified

记录日期、commit 或工作树标识、环境、命令、结果和局限。

## Do not reopen

链接仍有效的 implemented/rejected 决策；没有则写 `None`。
```

保持在约 100 行或 600 中文字以内。项目状态只保存摘要和链接，不复制规格、架构、部署表或完整进度。`Next action` 不能写 `None`、“继续开发”或没有验收方式的宽泛目标；项目确实处于等待状态时，把等待动作写成可验证的下一动作，例如“等待 owner 确认 X，并在确认后更新 Y”。

以下变化会触发更新：

- 当前阶段或下一动作改变；
- 产生或解除阻塞；
- 活跃计划创建、关闭或转移；
- 发现环境差异；
- 完成新的有效验证；
- 新决策使旧方案不应再被讨论。

## 执行计划恢复快照

每个活跃计划在背景和长日志之前放置：

```markdown
## Resume snapshot

- Current state: 当前已经完成和成立的最小摘要。
- Next action: 下一个可执行、可验收动作。
- Blocked by: 阻塞和解除条件；没有则写 `None`。
- Awaiting: 等待的人或外部输入；没有则写 `None`。
- Last verified:
  - commit: commit 或工作树标识
  - environment: local/test/staging/production
  - commands: 实际运行的命令
  - date: YYYY-MM-DD
```

快照是计划日志的入口，不替代带日期的 Progress、Discoveries、Decision log 和 Validation。状态变化时先更新快照，再追加详细证据。下一动作不能靠阅读整份计划后推断。

## 计划关闭事务

计划只有在持久信息拥有新位置后才算完成。`Completion notes` 至少包含：

```markdown
## Completion notes

### Outcome
最终达成或取消了什么。

### Durable decisions promoted
链接已提升的设计决策；没有则说明为什么没有持久决策。

### Product or architecture updates
链接同步后的产品、架构或运行文档；不适用则写 `None`。

### Remaining work transferred
链接新计划或技术债；没有则写 `None`。

### Rejected alternatives recorded
链接仍能防止未来误判的否决理由；没有则写 `None`。

### Final validation
记录 commit、环境、命令、结果和未覆盖范围。
```

关闭顺序：

1. 从 Decision log 和 Discoveries 识别持久知识；
2. 将当前行为提升到产品、架构、运行文档或 implemented decision；
3. 将未完成工作转入新计划或技术债；
4. 保存仍有未来防错价值的 rejected alternative；
5. 记录最终验证；
6. 更新 `PROJECT_STATE.md` 和活跃计划索引；
7. 修改计划状态并移动到 `completed/`。

`completed/` 是执行历史，不自动拥有当前产品或架构权威。不能让新智能体必须阅读已完成计划才能理解当前设计。

## 冷启动验收

从根 `AGENTS.md` 开始，不使用聊天、个人记忆或未落库材料，验证新智能体能否在两次跳转内回答：

1. 项目使命和非目标是什么？
2. 当前阶段和已经成立的状态是什么？
3. 下一个最小可执行动作是什么？
4. 阻塞是什么，由谁或什么条件解除？
5. 当前产品、架构和运行事实的权威来源在哪里？
6. 目标、本地、测试和生产之间有哪些差异？
7. 上次验证对应哪个 commit、环境、命令和日期？
8. 哪些 implemented/rejected 选择不能在没有新证据时重新打开？

任何答案需要从聊天、提交信息或长篇 completed plan 中推断，都说明恢复协议仍有缺口。
