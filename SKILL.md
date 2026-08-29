---
name: training-program-skill-factory
description: Use when converting a university talent-training-program PDF into a separate, reviewable professional syllabus Skill, including extraction, validation, anonymization, generation, process metrics, retrospectives, and version updates.
---

# 培养方案到课程大纲 Skill 工厂

将一份培养方案转换为独立的专业课程大纲 Skill。先保留来源事实及其状态，再生成可审核的下游 Skill；课程目标、教学内容、考核方案等来源未提供的内容保持 `待编制`，不补写。

## 选择工作模式

| 请求 | 处理 |
| --- | --- |
| 新建骨架或读取 PDF | scaffold；记录来源、版本和候选状态。读取 [schema](references/schema.md)。 |
| 提取表格或矩阵 | extraction；提取项只能是 `extracted` 或 `needs_review`，直到逐项视觉复核。读取 [schema](references/schema.md)。 |
| 审核现有 JSON | review；先运行 CLI `validate`，再处理错误、警告和未决项。读取 [schema](references/schema.md)。 |
| 生成课程大纲 Skill | downstream generation；以已校验 JSON 生成一个单独、可移动的 Skill。 |
| 去身份化 | anonymization；仅替换获准公开的机构与路径信息，保留官方课程事实。 |
| 复盘或性能记录 | retrospective；把实测耗时、观察到的瓶颈与待验证假设分开记录。 |
| 新旧版本冲突 | version update；保留旧版本，生成新版本与 diff，不覆盖旧 JSON。读取 [schema](references/schema.md)。 |

## 核心合同

- 每次运行都声明来源文件、可见版本标识和发布边界；缺失项写为未提供，不以猜测补齐。
- 官方直接关系、系统派生关系和未解决项分栏呈现。`official_direct` 的课程—指标点、毕业要求—培养目标关系可用于追踪；追踪得到的课程—培养目标关系只能标为 `derived_transitive`，不能回写为官方矩阵。
- 调用 `scripts/curriculum.py validate <program.json>` 成功后，才可说结构化数据“可用”；校验无错误不等于完成视觉复核、事实核验或发布。
- 专业课程目标、周次内容、教材与考核细则若不在输入中，生成的 Skill 必须明确保留 `待编制`。不要用示例夹具回答真实专业课程问题，也不要把夹具当作生成的专业 Skill。
- 复核时保留候选的页码、表格/符号和审核决定。提取器产生的候选不能因自动处理而升格为 `visually_verified`。

## 生成独立的下游 Skill

在输入 JSON 已通过校验、名称和发布边界已明确后，运行：

```powershell
py -3.12 scripts/generate_skill.py <program.json> <output-dir> --skill-name <name> --display-name <display-name> --factory-commit <commit>
```

生成结果应含 `SKILL.md`、`agents/openai.yaml`、`data/program.json`、最小查询/校验运行时和 `generated-from.json`。生成后在输出目录运行 `scripts/curriculum.py validate data/program.json`；下游 Skill 不依赖工厂路径。

## 可读记录

- 详细执行边界见 [workflow](docs/workflow.md)。
- 仅在复盘时读取 [lessons learned](docs/lessons-learned.md)、[pitfalls](docs/pitfalls.md) 和 [performance](docs/performance.md)。
