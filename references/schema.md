# 结构化培养方案数据约定

本说明对应 `references/program.schema.json`。在摄入、审核或版本更新时读取；普通课程查询只使用已生成 Skill 中的 `data/program.json`。

## 稳定实体 ID

`program`、培养目标、毕业要求、指标点、课程和课程组均以字符串 `id` 标识。ID 是关系端点与 diff 的稳定键；标题变化不应更改既有 ID。指标点如有明确 `graduation_requirement_id`，追踪时以该字段为准。

## 关系与证据

| 关系类型 | 含义 | 直接或派生 |
| --- | --- | --- |
| `requirement_supports_objective` | 毕业要求指向培养目标 | 可为官方直接关系 |
| `course_supports_indicator` | 课程或课程组指向指标点 | 可为官方直接关系 |
| `curriculum_sequence_link` | 已明确的课程先后关系 | 可为官方直接关系 |
| 课程到培养目标追踪结果 | 经指标点和毕业要求得到 | 仅 `derived_transitive`，不写回官方关系 |

每条持久化关系都有 `provenance`：`source_kind`、`source_file_hash`、`source_page`、`source_table`、`source_symbol`、`verification_status` 与 `note`。`source_kind=official_direct` 仅表示输入来源直接陈述；`derived_transitive` 仅用于运行时推导。候选的 `verification_status` 至少区分 `extracted`、`needs_review`、`visually_verified` 和 `rejected`；只有可追溯的视觉审核决定可使用 `visually_verified`。

## 课时与课程组

课程 `hours` 可含 `lecture_hours`、`experiment_hours`、`practice_hours` 与 `total_hours`。数值 `0` 是已知的零；`null` 是未知，不能参加精确合计或被替换成零。`course_groups` 保存官方类别或选课组及 `course_ids`；组行不是拆分到每门成员课的许可。

## 下游课程大纲链

`来源 PDF → extracted/needs_review 候选 → 视觉审核 → program.json → CLI validate → 生成的专业 Skill → 课程查询/大纲编制`。

链条末端只提供官方字段、直接关系和明确标记的派生追踪。输入未提供的课程目标、教学进度或考核细则应继续显示为 `待编制`。
