# Workflow Core Export Landing Checklist: curated-core-v1

## Summary
- status: warn
- source_ref: 9b8a55234db835dea2ee00be18bede8546c02d0d
- profile_status: active
- selected_path_count_at_source_ref: 19
- ready_include_patterns: 9
- worktree_only_include_patterns: 17
- missing_include_patterns: 0

## Purpose
first actual exportable workflow-core profile before mutable skill-state split completion

## Ready In Source Ref

- [x] .agent/workflows/**
  Action: No action required for this release candidate.
  Matched paths: .agent/workflows/AGENT_ENTRY.md, .agent/workflows/dev-team.md, .agent/workflows/references/README.md, .agent/workflows/references/coordinator_research_skill_trigger_checklist.md, .agent/workflows/references/engineer_skill_trigger_checklist.md, .agent/workflows/references/workflow_skill_trigger_design_principles.md, .agent/workflows/references/workflow_skill_trigger_index.md
- [x] .agent/VScode_system/**
  Action: No action required for this release candidate.
  Matched paths: .agent/VScode_system/Ivy_Coordinator.md, .agent/VScode_system/chat_instructions_ivy_house_rules.md, .agent/VScode_system/prompt_dev.md, .agent/VScode_system/tool_sets.md
- [x] .agent/roles/coordinator.md
  Action: No action required for this release candidate.
  Matched paths: .agent/roles/coordinator.md
- [x] .agent/roles/planner.md
  Action: No action required for this release candidate.
  Matched paths: .agent/roles/planner.md
- [x] .agent/roles/engineer.md
  Action: No action required for this release candidate.
  Matched paths: .agent/roles/engineer.md
- [x] .agent/roles/qa.md
  Action: No action required for this release candidate.
  Matched paths: .agent/roles/qa.md
- [x] .agent/skills/schemas/**
  Action: No action required for this release candidate.
  Matched paths: .agent/skills/schemas/code_reviewer_output.schema.json, .agent/skills/schemas/git_stats_reporter_output.schema.json, .agent/skills/schemas/github_explorer_output.schema.json, .agent/skills/schemas/manifest_updater_output.schema.json, .agent/skills/schemas/plan_validator_output.schema.json, .agent/skills/schemas/skills_evaluator_output.schema.json, .agent/skills/schemas/test_runner_output.schema.json
- [x] .agent/templates/handoff_template.md
  Action: No action required for this release candidate.
  Matched paths: .agent/templates/handoff_template.md
- [x] doc/plans/Idx-000_plan.template.md
  Action: No action required for this release candidate.
  Matched paths: doc/plans/Idx-000_plan.template.md

## Present Only In Working Tree

- [ ] core_ownership_manifest.yml
  Action: Land these paths into the next release candidate before export.
  Matched paths: core_ownership_manifest.yml
- [ ] .agent/runtime/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/runtime/scripts/devcontainer/post_create.sh, .agent/runtime/scripts/portable_smoke/workflow_core_smoke.py, .agent/runtime/scripts/sendtext_bridge_client.py, .agent/runtime/scripts/vscode/install_terminal_orchestrator.sh, .agent/runtime/scripts/vscode/install_terminal_tooling.sh, .agent/runtime/scripts/vscode/workflow_preflight_check.py, .agent/runtime/scripts/vscode/workflow_preflight_fallback.py, .agent/runtime/scripts/vscode/workflow_preflight_pty.py, .agent/runtime/scripts/workflow_core_contracts.py, .agent/runtime/scripts/workflow_core_export_landing_checklist.py, .agent/runtime/scripts/workflow_core_export_materialize.py, .agent/runtime/scripts/workflow_core_manifest.py, .agent/runtime/scripts/workflow_core_projection.py, .agent/runtime/scripts/workflow_core_release_create.py, .agent/runtime/scripts/workflow_core_release_precheck.py, .agent/runtime/scripts/workflow_core_release_publish_notes.py, .agent/runtime/scripts/workflow_core_sync_apply.py, .agent/runtime/scripts/workflow_core_sync_precheck.py, .agent/runtime/scripts/workflow_core_sync_verify.py, .agent/runtime/tools/vscode_terminal_fallback/README.md, .agent/runtime/tools/vscode_terminal_fallback/extension.js, .agent/runtime/tools/vscode_terminal_fallback/package.json, .agent/runtime/tools/vscode_terminal_pty/README.md, .agent/runtime/tools/vscode_terminal_pty/codex_pty_bridge.py, .agent/runtime/tools/vscode_terminal_pty/extension.js, .agent/runtime/tools/vscode_terminal_pty/package.json
- [ ] .agent/roles/security.md
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/roles/security.md
- [ ] .agent/skills/code-reviewer/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/skills/code-reviewer/SKILL.md, .agent/skills/code-reviewer/references/review_checklist.md, .agent/skills/code-reviewer/scripts/code_reviewer.py
- [ ] .agent/skills/doc-generator/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/skills/doc-generator/SKILL.md, .agent/skills/doc-generator/scripts/doc_generator.py
- [ ] .agent/skills/test-runner/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/skills/test-runner/SKILL.md, .agent/skills/test-runner/scripts/test_runner.py
- [ ] .agent/skills/plan-validator/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/skills/plan-validator/SKILL.md, .agent/skills/plan-validator/scripts/plan_validator.py
- [ ] .agent/skills/git-stats-reporter/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/skills/git-stats-reporter/SKILL.md, .agent/skills/git-stats-reporter/scripts/git_stats_reporter.py
- [ ] .agent/skills/skills-evaluator/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/skills/skills-evaluator/SKILL.md, .agent/skills/skills-evaluator/scripts/skills_evaluator.py
- [ ] .agent/skills/project-planner/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/skills/project-planner/SKILL.md, .agent/skills/project-planner/references/estimation-and-risk.md, .agent/skills/project-planner/references/planning-framework.md, .agent/skills/project-planner/references/task-sizing-and-dependencies.md
- [ ] .agent/skills/deep-research/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/skills/deep-research/SKILL.md, .agent/skills/deep-research/references/research-process.md, .agent/skills/deep-research/references/source-policy-and-output.md
- [ ] .agent/skills/fact-checker/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/skills/fact-checker/SKILL.md, .agent/skills/fact-checker/references/verdict-and-context.md, .agent/skills/fact-checker/references/verification-process.md
- [ ] .agent/skills/refactor/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/skills/refactor/SKILL.md, .agent/skills/refactor/references/refactor-python.md, .agent/skills/refactor/references/refactor-smells.md, .agent/skills/refactor/references/refactor-typescript-javascript.md, .agent/skills/refactor/references/refactor-workflow.md
- [ ] .agent/skills/python-expert/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/skills/python-expert/SKILL.md, .agent/skills/python-expert/references/python-correctness.md, .agent/skills/python-expert/references/python-performance.md, .agent/skills/python-expert/references/python-style-and-documentation.md, .agent/skills/python-expert/references/python-type-safety.md
- [ ] .agent/skills/typescript-expert/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/skills/typescript-expert/SKILL.md, .agent/skills/typescript-expert/references/typescript-api-and-testing.md, .agent/skills/typescript-expert/references/typescript-javascript-core.md, .agent/skills/typescript-expert/references/typescript-react-patterns.md
- [ ] .agent/skills/security-review-helper/**
  Action: Land these paths into the next release candidate before export.
  Matched paths: .agent/skills/security-review-helper/SKILL.md, .agent/skills/security-review-helper/references/security_checklist.md
- [ ] doc/logs/Idx-000_log.template.md
  Action: Land these paths into the next release candidate before export.
  Matched paths: doc/logs/Idx-000_log.template.md

## Still Missing

- None

## Deferred By Design

- [ ] .agent/skills/_shared/**
  Reason: shared helpers still resolve canonical runtime-written skill state inside the core tree
- [ ] .agent/skills/github-explorer/**
  Reason: writes audit log and INDEX.md while the mutable split remains incomplete
- [ ] .agent/skills/skill-converter/**
  Reason: updates INDEX.md inside the core tree
- [ ] .agent/skills/manifest-updater/**
  Reason: writes the canonical shared skill manifest inside the core tree
- [ ] .agent/skills/codex-collaboration-bridge/**
  Reason: not yet curated into the first-wave portable workflow surface
- [ ] .agent/skills/explore-cli-tool/**
  Reason: not yet curated into the first-wave portable workflow surface
- [ ] .agent/skills/persistent-terminal/**
  Reason: not yet curated into the first-wave portable workflow surface

## Contract Violations

- None

## Notes

- export profile still has landing gaps before the next clean release ref can be exported
- first actual export profile favors workflow-required, self-contained packages over toolchain packages coupled to shared mutable state
- curated-core-v1 is intentionally narrower than final managed ownership while split_required items remain open
