---
name: project-doc-harness
description: Organize, scaffold, migrate, audit, and maintain repository-local project documentation so memoryless coding agents can recover current state, navigate authoritative sources, continue cross-session work, and avoid design drift. Use for new-project setup, AGENTS.md design, docs/ information architecture, project-state or execution-plan handoff, architecture or product documentation, decision lifecycle, documentation cleanup, doc-gardening, broken-link or freshness audits, and requests such as “为 AI 开发整理项目文档”, “重构仓库文档结构”, or “make this repo agent-friendly”.
metadata:
  version: "1.1.1"
---

# Project Doc Harness

把仓库变成无记忆智能体可查询、可恢复、可验证、可持续维护的记录系统。提供当前状态和权威地图，不制造一本巨型说明书。

## 核心原则

- 将 `AGENTS.md` 保持为短小稳定的入口和任务路由，不把它写成百科全书。
- 将真实知识版本化到仓库中；聊天、个人记忆和外部文档只有落库后才算智能体可见。
- 从入口到当前状态、索引、专题文档逐层展开，按任务加载上下文。
- 明确每类事实的主要权威来源；摘要用领域相关的一句话和链接表达，易变细节集中在最合适的 owner。
- 区分稳定事实、活跃状态和易变运行事实，并让更新频率与验证证据匹配其半衰期。
- 将计划、决策、进度、否决理由和技术债务视为一等工件；完成计划前提升其中的持久知识。
- 优先把可机械判断的规则做成检查；检查结果是证据，不代替产品和设计判断。
- 默认保留已有内容；先盘点、再迁移，未经允许不覆盖或删除文件。

## 信息角色与耦合度

在初始化、迁移和日常维护项目文档时，先为每类信息确定主要落点、owner，以及它在其他文档中的作用。同一主题可以出现在多处，但每一处都应承担清晰的信息角色：

1. **权威定义（Authority）**：完整定义规则、当前值或契约，由明确 owner 维护。
2. **护栏摘要（Guardrail）**：在入口或高风险上下文中提供短提醒，并链接权威定义。
3. **领域投影（Projection）**：说明该事实对本领域的影响，例如产品行为、架构责任或可靠性后果。
4. **历史证据（Evidence）**：记录某次决策、发布或验证当时成立的事实，支持追溯。

设计和维护信息架构时同时考虑变更耦合度：变化越频繁、需要同步的手写位置越多，维护成本和漂移风险越高。优先让每份文档承担清晰角色，让易变细节靠近 owner，让其他文档通过简短上下文和链接保持可发现性。一个事实变化牵动很多当前文档时，重新检查这些位置是否都提供了独立价值。

## 选择工作模式

根据用户目标选择一种或组合使用：

1. **Scaffold**：为新仓库创建最小文档骨架。
2. **Migrate**：盘点散乱文档，提出映射，确认后移动或整合。
3. **Audit**：检查结构、入口、链接、元数据、生命周期、新鲜度和可恢复性。
4. **Garden**：结合当前代码修正文档，提升计划结论，归档历史，登记技术债务。

## 工作流

### 1. 读取仓库约束

先读取仓库根目录及相关子目录的 `AGENTS.md`、贡献指南、构建配置和已有文档索引。确认工作区是否有用户未提交的修改。不要把通用模板凌驾于项目已有规则之上。

### 2. 盘点事实来源与状态

使用 `rg --files` 找出 Markdown、配置、模式、生成物、计划和运行状态文件。为每类信息记录：

- 当前路径、读者以及承担的角色（权威定义、护栏摘要、领域投影或历史证据）；
- 属于稳定事实、活跃状态还是易变事实；
- 是否仍与代码和实际环境一致；
- 主要权威来源、取代关系以及一次变化会牵动的手写位置；
- owner、验证方式、验证环境与最近证据；
- 应保留、整合、提升、归档还是生成。

对旧仓库，先输出迁移映射再做大规模移动。无法由代码验证的产品意图不要自行补造，标记为待确认。

### 3. 设计最小信息架构

默认采用以下结构，但只创建项目真正需要的部分：

```text
AGENTS.md
ARCHITECTURE.md
docs/
├── PROJECT_STATE.md
├── design-docs/
│   ├── index.md
│   └── core-beliefs.md
├── product-specs/
│   └── index.md
├── exec-plans/
│   ├── active/
│   ├── completed/
│   └── tech-debt-tracker.md
├── generated/
├── operations/
├── references/
├── QUALITY_SCORE.md
├── RELIABILITY.md
└── SECURITY.md
```

读取 [references/doc-contracts.md](references/doc-contracts.md) 选择文件契约、元数据和模板。跨会话、有活跃计划、多环境或持续运维的项目还必须读取 [references/resumability.md](references/resumability.md)。不要为不存在的流程创建空洞文档；可在索引中登记“缺失但需要”的条目。

### 4. 写入口地图

将根 `AGENTS.md` 控制在约 100 行，最多 150 行。只保留：

- 项目一句话目标与关键边界；
- 常用构建、测试、格式化和验证命令；
- 不可违反的少量仓库级规则；
- 当前状态、权威文档地图以及按任务选择阅读材料的指引；
- 变更后必须运行的检查。

把架构、产品、可靠性和安全细节放入各自权威文档。为子系统添加局部 `AGENTS.md`，仅当它确实拥有不同命令或约束。

### 5. 建立可恢复的当前状态

跨会话、有活跃计划、多环境或持续运维的项目使用 `docs/PROJECT_STATE.md` 保存短小的状态胶囊。它只回答当前阶段、下一动作、阻塞、活跃工作、环境差异、最近验证和不应重开的决策，并链接各自权威来源。

每个活跃计划在正文顶部维护 `Resume snapshot`。下一动作、阻塞或验证证据变化时同步更新状态胶囊和相关计划；没有活跃工作或阻塞时明确写 `None`，不要让智能体自行猜测。

### 6. 管理文档与计划生命周期

为手写当前状态、架构、设计、产品、计划和运行文档添加 `doc_type`、`status`、`owner`、`last_reviewed` 元数据，并按文档类型使用状态。`draft` 和 `proposed` 不能直接作为已确认实现依据；`deprecated` 与 `superseded` 必须链接替代来源。

完成计划不是简单移动文件。关闭前必须：

1. 将持久决策提升到设计文档或已实施决策；
2. 同步产品、架构和运行状态；
3. 将未完成事项转入新计划或技术债；
4. 保存仍能防止未来误判的重要否决理由；
5. 记录最终 commit、环境、命令和结果；
6. 更新项目状态后再移动到 `completed/`。

### 7. 编码反馈回路

运行脚本初始化缺失结构或执行审计：

```bash
python3 <skill-dir>/scripts/doc_harness.py init --root <repo>
python3 <skill-dir>/scripts/doc_harness.py init --root <repo> --with-project-state
python3 <skill-dir>/scripts/doc_harness.py check --root <repo>
python3 <skill-dir>/scripts/doc_harness.py check --root <repo> --strict --stale-days 90
```

`init` 仅创建缺失文件，不覆盖已有内容；符合可恢复性条件时使用 `--with-project-state`。`check` 检查必需结构、本地链接、入口长度、索引覆盖、元数据、状态与目录一致性、Resume snapshot、计划关闭记录和项目状态；`--strict` 将警告视为失败。项目已有脚本语言或 CI 规范时，可将等价检查原生化并接入 CI。

### 8. 验证并交付

完成文档变更后：

1. 运行 `doc_harness.py check --strict`；
2. 运行仓库自带的文档 lint、链接检查或生成校验；
3. 从 `AGENTS.md` 出发，验证一个无记忆智能体能否确定使命、当前阶段、下一动作、阻塞、权威来源、环境差异、最近验证和不应重开的选择；
4. 检查链接目标与代码和实际环境，而不只检查文件存在；
5. 汇报新增、迁移、提升、归档、仍待人工确认的内容以及实际检查结果。

## 决策准则

- 文档与代码冲突时，以可执行行为为实现证据，修正文档并记录有意的行为差异；不要静默改变产品意图。
- 目标状态、当前实现和实际部署冲突时分别记录，不能用其中一个冒充另一个。
- 同一事实出现在多处时，明确各处承担的角色；让权威定义保持完整，让护栏摘要、领域投影和历史证据各自服务其读者。
- 文档经常失真且规则可自动判断时，增加 lint、结构测试或生成器。
- 只有相关团队能判断的内容必须标注真实 owner；当前权威文档不能以 `TBD` 代替责任归属。
- 只对自动生成文件执行再生成，不手工修改 `docs/generated/` 中声明为生成的内容。
- 不为了达到“完整结构”而复制敏感信息、密钥、聊天记录或受限外部资料。
