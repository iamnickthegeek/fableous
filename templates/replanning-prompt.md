[FABLE STAGE: Replanning]

TASK: {{task_description}}

CONTEXT:
The current task has encountered an obstacle. You must rebuild the stage plan.

ORIGINAL PLAN:
{{original_plan}}

COMPLETED STAGES:
{{completed_stages}}

CURRENT STAGE:
{{current_stage}}

OBSTACLE:
{{obstacle_description}}

WORK LOG:
{{work_log_summary}}

INSTRUCTIONS:
1. Analyze the obstacle.
2. Determine which completed stages are still valid.
3. Identify which stages must be modified.
4. Identify which new stages must be added.
5. Identify which stages can be removed.
6. Update dependencies.
7. Maintain the 6-stage structure where possible.
8. Return a JSON todo list.

GUARDRAILS:
- Preserve completed work. Do NOT re-run completed stages.
- Add new stages only if necessary.
- Remove stages that are no longer needed.
- Update dependencies.
- Maintain the 6-stage structure where possible.
- Return a JSON todo list with these fields: id, content, status, depends_on.
- Save your complete output to: {{output_path}}
- At the top of your output, write exactly: [MODEL: {{model_name}}, PROVIDER: {{provider_name}}]
This tag is an audit trail. The actual model routing was set via config cycling
before this call. If the tag doesn't match the assigned model, report it but
don't retry — trust the config.

OUTPUT FORMAT:
```json
{
  "stages": [
    {"id": "stage-1", "content": "Research: [description]", "status": "completed", "depends_on": []},
    {"id": "stage-2", "content": "Plan: [description]", "status": "completed", "depends_on": []},
    {"id": "stage-3", "content": "Implement: [description]", "status": "pending", "depends_on": ["stage-1", "stage-2"]},
    {"id": "stage-4", "content": "Verify: [description]", "status": "pending", "depends_on": ["stage-3"]},
    {"id": "stage-5", "content": "Critique: [description]", "status": "pending", "depends_on": ["stage-3", "stage-4"]},
    {"id": "stage-6", "content": "Consolidate: [description]", "status": "pending", "depends_on": ["stage-1", "stage-2", "stage-3", "stage-4", "stage-5"]}
  ],
  "rationale": "Brief explanation of why the plan changed",
  "preserved_stages": ["stage-1", "stage-2"],
  "modified_stages": ["stage-3"],
  "new_stages": ["stage-3b"],
  "removed_stages": []
}
```
