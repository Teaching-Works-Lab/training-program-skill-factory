---
name: {{SKILL_NAME}}
description: Use when answering reviewable course-outline questions from the bundled verified training-program data; keep official fields, derived traces, and unresolved syllabus content separate.
---

# {{DISPLAY_NAME}}

本 Skill 使用 `data/program.json` 中的培养方案数据回答课程与关系查询。课程目标、教学内容、进度、教材和考核细则仅在来源明确提供时输出；其他内容保持 `待编制`。

## 查询与校验

```powershell
py -3.12 scripts/curriculum.py validate data/program.json
py -3.12 scripts/curriculum.py query data/program.json --course <课程代码或名称> --format markdown
```

查询结果中，课程—指标点关系是官方直接关系；课程—培养目标关系是通过指标点和毕业要求得到的派生追踪，不能作为官方矩阵单元格或课程成效结论。

## 编制边界

- 保留来源中的课程名称、代码、学分、学时、学期、关系与 provenance。
- 对未提供的课程目标和大纲内容写 `待编制`，并说明需要的来源或审核。
- 不将校验通过、支持关系数量或派生路径表述为培养质量、学习成效或审核完成。
