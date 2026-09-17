本文档由 GPT-6 Astra 生成

# Project Doc Harness

**让 AI 编程助手换一个会话，也能从仓库文档接着工作。**

Project Doc Harness 是一个用于整理和维护项目文档的 Agent Skill，附带零第三方依赖的 Python 初始化与检查脚本。它帮助你建立简短的 `AGENTS.md` 入口、清晰的权威来源、可恢复的执行计划，以及有证据支撑的项目状态。

*An agent skill for discoverable, resumable, and maintainable project documentation.*

## 使用方法

安装后，在项目中对 agent 说一句就行：

```text
使用 $project-doc-harness 管理项目文档
```

或：

```text
使用 $project-doc-harness 更新项目文档
```

日常管理或整理项目文档时，agent 通常会根据任务自动调用这个 skill，无需每次手动指定。具体采用哪些文档、如何整理、何时运行检查，都由 agent 结合项目情况处理。

## 它解决什么问题

当开发跨越多个 AI 会话时，项目上下文很容易散落在聊天、旧计划和重复的说明中。新会话不知道做到哪里，旧决策被反复讨论，文档也逐渐偏离实现。

这个 skill 将工作所需的上下文沉淀到仓库：

- **找得到**：从短小的 `AGENTS.md` 出发，按任务找到架构、产品规格和其他权威来源。
- **接得上**：用项目状态和计划顶部的 `Resume snapshot` 记录进度、下一动作、阻塞与验证。
- **分得清**：区分提案、生效规则、目标行为、当前实现、实际部署和历史证据。
- **维护得动**：按需采用文档结构，将易变事实集中维护，用机械检查发现结构和契约问题。

## 适用场景

| 模式 | 适用场景 | 主要工作 |
| --- | --- | --- |
| Scaffold | 新项目需要文档入口 | 创建最小骨架，按需增加专题文档 |
| Migrate | 旧项目文档散乱或重复 | 盘点来源、建立迁移映射、整理导航和正文 |
| Audit | 想知道文档缺口在哪里 | 检查结构、链接、元数据、生命周期和恢复信息 |
| Garden | 项目持续开发，文档需要跟进 | 更新当前状态、提升计划结论、归档历史、记录技术债 |

agent 会根据项目情况选择合适的模式，具体流程见 [SKILL.md](SKILL.md)。

## 安装到 Codex

需要 Git；运行配套脚本需要 **Python 3.9+**，无需 `pip install`。

安装为用户级 skill（以下命令适用于 macOS / Linux 的 shell）：

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/dckong/project-doc-harness.git \
  ~/.agents/skills/project-doc-harness
```

也可以在目标项目根目录中安装，仅供该项目使用：

```bash
mkdir -p .agents/skills
git clone https://github.com/dckong/project-doc-harness.git \
  .agents/skills/project-doc-harness
```

选择一种安装方式即可。Codex 会自动发现这些目录中的 skill；如果没有出现，重启 Codex。目录和发现规则见 [Codex 官方 Skills 文档](https://learn.chatgpt.com/docs/build-skills)。

如果只想使用命令行检查器，也可以将仓库克隆到任意目录，直接运行脚本。

<details>
<summary>可选：手动运行脚本与自定义文档路径</summary>

### 直接使用脚本

需要手动运行或接入 CI 时，可以使用以下命令。日常使用交给 agent 即可。

以下命令在本 skill 仓库的根目录执行。将 `/path/to/your-project` 替换为需要整理的项目路径。

```bash
# 最小初始化：空项目默认只创建 AGENTS.md
python3 scripts/doc_harness.py init --root /path/to/your-project

# 按需增加架构、设计文档和跨会话项目状态
python3 scripts/doc_harness.py init --root /path/to/your-project \
  --with architecture --with design-docs --with-project-state

# 审计；strict 模式会把警告也视为失败
python3 scripts/doc_harness.py check --root /path/to/your-project
python3 scripts/doc_harness.py check --root /path/to/your-project \
  --strict --stale-days 90
```

`init` 保留已有 Markdown，只创建缺失内容；显式选择的工件会保存到目标项目的 `doc-harness.json`。模板中的 TODO / TBD 需要根据真实项目补齐，初始化后可能尚不能通过严格检查。

`check` 退出码：`0` 表示机械检查通过，`1` 表示存在错误或严格模式下的警告，`2` 表示目标根目录或工件配置无效。

### 使用已有文档路径

在目标项目根目录创建 `doc-harness.json`，将采用的工件映射到现有位置：

```json
{
  "artifacts": {
    "architecture": "handbook/system.md",
    "design-docs": "handbook/decisions",
    "project-state": "docs/PROJECT_STATE.md",
    "plans": "docs/exec-plans"
  }
}
```

然后运行 `init` 或 `check`。二者使用同一份配置；声明但缺失的工件会被报告。没有配置时，只识别已存在的默认路径。存在活跃计划时，仍需要项目状态入口。

所有支持的工件角色、文档元数据和生命周期规则见 [文档契约](references/doc-contracts.md)；跨会话交接、等待/空闲状态和计划关闭规则见 [恢复契约](references/resumability.md)。

### 检查器的边界

检查器覆盖所选工件的存在性、入口长度、部分本地文件链接、简单元数据、日期、状态，以及恢复快照和计划关闭的必要字段。

它不会验证外链、链接锚点、完整 YAML、证据真实性或内容是否符合代码与实际部署。frontmatter 仅支持每行 `key: value` 的简单未加引号标量。结构检查通过后，仍需要审阅内容和执行项目自身的验证。

</details>

## 仓库结构

```text
project-doc-harness/
├── SKILL.md                       # AI 助手的工作流程与决策准则
├── README.md                      # 安装与使用指南
├── LICENSE                        # MIT 许可证
├── agents/openai.yaml             # Codex 展示信息与默认提示
├── references/
│   ├── doc-contracts.md           # 文档结构、元数据与生命周期契约
│   └── resumability.md            # 跨会话恢复与计划关闭契约
├── scripts/doc_harness.py         # 初始化与机械检查工具
└── tests/test_doc_harness.py       # 标准库 unittest 测试
```

## 来源与致谢

本 skill 基于以下文章和开源项目整理而成：

- OpenAI 的 [Harness Engineering 文章](https://openai.com/zh-Hans-CN/index/harness-engineering/)
- DeepSeek 的 [deepseek-harness 项目](https://github.com/deepseek-ai/deepseek-harness)

## 许可证

[MIT](LICENSE) · Copyright (c) 2026 dckong
