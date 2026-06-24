# SKILL.md Research Notes

## Definition

A SKILL.md is a structured Markdown file packaged inside a "skill folder"
that gives Claude AI domain-specific workflows, domain knowledge, and
tool-use patterns beyond its general training.

## Core Structure

```
skill/
├── SKILL.md          YAML frontmatter + Markdown instructions
├── scripts/          Executable Python/bash helpers
├── references/       Domain knowledge docs (codes, standards)
└── assets/           Templates, headers, icons
```

## YAML Frontmatter Fields

| Field         | Required | Purpose                              |
|---------------|----------|--------------------------------------|
| name          | ✅        | Identifier shown in available_skills |
| description   | ✅        | Trigger mechanism (most critical)    |
| compatibility | ⬜        | Required Python version or tools     |

## 3-Layer Loading System

```
Layer 1  Metadata (name + description)      Always in context
Layer 2  SKILL.md body                      Loaded when triggered
Layer 3  Scripts / references / assets      Loaded on demand
```

This keeps Claude's context window efficient.

## Triggering

Claude scans the `available_skills` list using each skill's description.
A vague description → skill undertriggers. An explicit description with
named phrases and paraphrases → reliable triggering.

Good description pattern:
- List exact trigger phrases ("SOAP note", "patient report")
- Include paraphrases ("even if they just say 'write up this patient'")
- Specify what NOT to use it for

## Why Healthcare?

| Factor              | Detail                                          |
|---------------------|-------------------------------------------------|
| Documentation load  | 35–55% of clinician time spent on docs          |
| Format requirements | SOAP, ICD-10 codes, HIPAA headers are mandatory |
| Error cost          | Missing fields = patient safety risk            |
| Volume              | Millions of clinical docs per hospital per year |

## Other Industries Where SKILL.md Applies

| Industry  | Example Skill       | Problem Solved                    |
|-----------|---------------------|-----------------------------------|
| Legal     | contract-review     | Clause extraction + risk flags    |
| Finance   | earnings-analysis   | Structured earnings summaries     |
| Education | lesson-plan         | Curriculum-aligned lesson docs    |
| HR        | job-description     | EEOC-compliant JD generation      |
| Ecommerce | product-description | SEO-optimised product copy        |

## Key Design Principles

1. Description = trigger — invest the most effort here
2. SKILL.md body < 500 lines — use sub-files for anything larger
3. Scripts for deterministic tasks — formatting, file generation, validation
4. References for domain knowledge — codes, standards, glossaries
5. Validate before output — never produce incomplete documents
6. No hallucination — state explicitly what Claude must not invent
7. Compliance-first in regulated industries — bake in required headers
