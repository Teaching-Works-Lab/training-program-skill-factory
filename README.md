# 培养方案到课程大纲 Skill 工厂

把高校人才培养方案 PDF 整理为可查询、可复核的结构化数据，并生成一个独立的专业课程大纲 Skill。

本仓库是“转换工厂”，不是某个专业的数据仓库。智能制造工程的成品 Skill 位于 [intelligent-manufacturing-syllabus](https://github.com/Teaching-Works-Lab/intelligent-manufacturing-syllabus)。

它属于 [Teaching Works Lab 课程教学 Skill 体系](https://github.com/Teaching-Works-Lab)：工厂负责生成可审核的专业数据 Skill，课程基座与课程大纲编制由 `course-teaching-workflows` 按需使用这些数据。

## 适合做什么

- 从培养方案建立课程、课程组、培养目标、毕业要求和指标点的数据关系；
- 提取并复核课程体系支撑毕业要求矩阵；
- 查询课程到指标点的官方直接关系，以及经毕业要求追踪到培养目标的派生关系；
- 对学校身份和私有源文件信息进行受控匿名化；
- 生成可独立安装、查询和校验的专业课程大纲 Skill；
- 记录转换耗时、常见问题、适用范围、经验冲突和仍待验证的提速假设。

它不会根据课程名称自动编造课程目标、教材、教学进度或考核权重。来源未提供的课程大纲字段保持 `待编制`。

## 给 AI 的入口

执行任务前先读取 [SKILL.md](SKILL.md)。它定义了工作模式、数据边界和生成合同。

- 读取、提取、审核或更新数据时，再读取 [数据模型说明](references/schema.md)。
- 执行完整转换时参考 [工作流](docs/workflow.md)。
- 复用模板、脚本、命令行参数或确定最小审核范围时，读取 [复用与提速](docs/reuse-and-speed.md)。
- 只有复盘过程时才需要读取 [经验总结](docs/lessons-learned.md)、[常见坑](docs/pitfalls.md) 和 [性能记录](docs/performance.md)。
- 不要把测试夹具当作真实专业数据，也不要把派生追踪写成官方矩阵。

## 快速开始

项目在 Python 3.12 环境完成验证。结构校验使用 `jsonschema`，PDF 矩阵候选提取使用 PyMuPDF；本地 PDF 优先使用 MarkItDown 建立 Markdown 候选，Markdown 导出 DOCX、HTML、PDF 等格式时优先使用 Pandoc。

```powershell
git clone https://github.com/Teaching-Works-Lab/training-program-skill-factory.git
cd training-program-skill-factory

# 查看命令
py -3.12 scripts/curriculum.py --help

# 校验仓库中的合成夹具
py -3.12 scripts/curriculum.py validate tests/fixtures/minimal-program.json
```

生成一个独立专业 Skill：

```powershell
py -3.12 scripts/generate_skill.py `
  <program.json> <output-dir> `
  --skill-name <skill-name> `
  --display-name <display-name> `
  --factory-commit <commit>
```

生成后进入目标目录，独立运行：

```powershell
py -3.12 scripts/curriculum.py validate data/program.json
```

如果作为 Codex Skill 安装，将整个仓库克隆或复制到 `$CODEX_HOME/skills/training-program-skill-factory`；未设置 `CODEX_HOME` 时通常使用 `~/.codex/skills/`。

也可以通过组织 Marketplace 选择安装：

```text
codex plugin marketplace add Teaching-Works-Lab/.github
codex plugin add training-program-skill-factory@teaching-works-lab
```

安装 Plugin 后可显式使用 `$training-program-skill-factory`。工厂生成的专业 Skill 是一个待审核产物，不会因为安装了工厂而自动安装；审核完成后仍需由用户明确选择安装位置或发布方式。

## 最小工作流

1. 本地 PDF 优先用 MarkItDown 转为 Markdown，同时保留原 PDF 作为复杂版面和事实复核来源。
2. 建立候选数据；自动提取结果只能标为 `extracted` 或 `needs_review`。
3. 对复杂表格和矩阵按原 PDF 逐项复核，保存页码、符号和审核决定。
4. 运行 `validate`，分别处理错误、建议性警告和未解决项。
5. 明确公开边界并匿名化获准字段。
6. 生成独立专业 Skill，并在目标目录进行可移植性验证；需要办公格式时再用 Pandoc 导出。
7. 记录本次问题、工具版本、运行条件、处理与证据；分类为通用、条件性、本机特例或待验证，并检查是否与旧经验冲突。

结构校验通过不等于事实审核、视觉复核或培养质量评价完成。

## 复用优先

工厂已经提供下游 Skill 模板、生成器、通用 CLI、JSON Schema 和测试夹具。新专业先复用这些资产，把专业名、数据路径、输出目录和 Skill 身份作为参数输入；不要把课程事实写死到 Python，也不要为一次特殊情况新建配置框架。完整清单、命令示例、提速机制和最小充分审核规则见 [复用与提速](docs/reuse-and-speed.md)。

## 仓库结构

```text
SKILL.md                     AI 执行入口
scripts/curriculum.py        查询、校验、渲染、差异比较等 CLI
scripts/generate_skill.py    下游专业 Skill 生成器
references/                  数据模式与 JSON Schema
templates/syllabus-skill/    最小专业 Skill 模板
docs/                        工作流、复用提速、经验、常见坑和性能记录
tests/                       单元测试、真实 PDF 环境门控烟测和合成夹具
```

## 验证

```powershell
py -3.12 -m pytest -q
```

真实 PDF 测试需要显式提供 `TRAINING_PROGRAM_PDF` 环境变量；没有该变量时相应测试会跳过，而不是假装完成 PDF 复核。

## 证据边界

- `official_direct`：来源中的直接关系；
- `derived_transitive`：由直接关系计算得到的追踪路径；
- `extracted` / `needs_review`：尚未完成视觉确认的候选；
- 校验警告：用于提醒复核，不是课程质量或毕业要求达成结论。

已记录的耗时只代表对应机器、工具版本和文件复杂度下的单次运行，不构成通用速度承诺。
