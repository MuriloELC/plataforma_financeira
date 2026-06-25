---
name: spec-driven-dev
description: >
  Spec-Driven Development (SDD) — write SPEC.md first, derive PLAN.md, execute via
  subagent-driven-development (one fresh subagent per task, spec review + quality review).
  EDD preamble required for AI/ML features. Verification-before-claim required.
  Use for any non-trivial feature, new API endpoint, new data model, or security-sensitive feature.
---

# Spec-Driven Development (SDD) Skill

> Write the spec first. Derive the plan. Execute with fresh subagents. Verify against the spec.

## Core Principle

SDD is the discipline that connects intent to implementation. Without a spec:
- Builders make assumptions that diverge from intent
- Edge cases are discovered in production, not in review
- "Done" is undefined until someone is unhappy

A spec is a contract. A plan is executable instructions derived from that contract. Implementation is provably correct if it satisfies every line of the spec.

---

## The SDD Loop

```
SPEC.md → spec review → PLAN.md (with exec contract) → subagent execution
     ↑                                                        |
     └────────────── verify against spec ←───────────────────┘
```

---

## The Execution Contract (Every PLAN.md Must Start With This)

```markdown
> **For agentic workers:** REQUIRED: Use subagent-driven-development for every task.
> Each task = one fresh subagent. Spec compliance review → code quality review → ✅ done.
> No task is "done" without: passing verification command, reviewer sign-off.
```

This header is non-negotiable. Any PLAN.md without it is incomplete.

---

## Subagent-Driven-Development Protocol

Every task in the plan is executed by a **fresh subagent**:

```
For each task in PLAN.md:
  1. Spawn fresh subagent with:
     - Full task description (file, action, TDD steps, verification, exit criteria)
     - Relevant context (SPEC.md, existing patterns, dependencies from prior tasks)
  2. Subagent executes:
     a. RED: write failing test
     b. GREEN: implement to pass test
     c. Verify: run verification command, confirm expected output
  3. Spec compliance review:
     - Does output match SPEC.md acceptance criteria?
     - Are all edge cases handled?
  4. Code quality review:
     - Type safety, error handling, conventions, no secrets
  5. Mark task ✅ only after both reviews pass
```

**Why fresh subagents?** Context contamination between tasks causes drift. Fresh context = spec-aligned execution every time.

---

## Phase 1: Write SPEC.md

Create `SPEC.md` (or `docs/specs/<feature-name>.md` for organized projects):

```markdown
# Spec: [Feature Name]

**Status**: Draft | Under Review | Approved | Implemented
**Date**: [date]
**Author**: [who]

## Problem Statement
[What problem does this feature solve? Why does it need to exist?]

## User Stories

### Primary
> As a [user type], I want to [do something] so that [I get value].

**Acceptance Criteria**:
- [ ] [Specific, testable criterion]
- [ ] [Specific, testable criterion]

### Secondary (if applicable)
> As a [user type], I want to [do something else].

**Acceptance Criteria**:
- [ ] [Specific, testable criterion]

## Scope

### In Scope
- [What this feature WILL do]

### Out of Scope
- [What this feature will NOT do — equally important]
- [Save this for v2: ...]

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| F1 | [Specific requirement] | Must Have |
| F2 | [Specific requirement] | Must Have |
| F3 | [Specific requirement] | Should Have |
| F4 | [Specific requirement] | Nice to Have |

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Latency (p99) | < 200ms |
| Throughput | 1000 req/s |
| Availability | 99.9% |
| Data retention | 90 days |

## API Contract (if applicable)

### Request
```
POST /api/v1/[resource]
Authorization: Bearer {token}

{
  "field1": "string",
  "field2": 123
}
```

### Response
```
HTTP 201 Created

{
  "id": "uuid",
  "field1": "string",
  "createdAt": "ISO8601"
}
```

### Error Cases
| HTTP Status | When | Response Body |
|------------|------|---------------|
| 400 | Invalid input | `{ "error": "validation_error", "details": [...] }` |
| 401 | Missing/invalid token | `{ "error": "unauthorized" }` |
| 409 | Duplicate resource | `{ "error": "already_exists" }` |

## Data Model

```
Table: [table_name]
- id: UUID (PK)
- [field]: [type] [constraints]
- created_at: TIMESTAMPTZ
- updated_at: TIMESTAMPTZ

Relationships:
- [table] 1:N [other_table] via [foreign_key]
```

**CAP Trade-off**: [CP/AP] — [reason why]

## Security Considerations
- [ ] Authentication required? Which roles?
- [ ] Data validation: what inputs need sanitizing?
- [ ] Rate limiting: what limits are appropriate?
- [ ] Sensitive data: any PII or secrets in this feature?
- [ ] Authorization: can users access other users' data?

## EDD Requirements (AI/ML features only)
- [ ] Capability evals defined (what the AI must do, with pass@3 >= 0.90 threshold)
- [ ] Regression evals defined (what must not break, pass^3 = 1.00)
- [ ] Grader type specified per eval (code/rule/model/human)
- [ ] Eval file path: `.claude/evals/<feature-name>.md`

## Edge Cases

| Case | Expected Behavior |
|------|-------------------|
| Empty input | Return 400 with clear error |
| Concurrent requests | Idempotent or conflict detection |
| DB unavailable | Graceful degradation, clear error |
| [other case] | [expected behavior] |

## Testing Strategy
- **Unit tests**: [What to unit test]
- **Integration tests**: [What flows to test]
- **E2E tests**: [User journeys]
- **Security tests**: [Auth checks, injection attempts]
- **EDD gate** (AI/ML only): capability pass@3 >= 0.90, regression pass^3 = 1.00

## Open Questions
- [ ] [Question that needs answering before implementation]
- [ ] [Dependency on another team/feature]

## Changelog
- [date]: Initial draft
```

---

## Phase 2: Spec Review

Before creating PLAN.md, verify the spec answers:

```
✓ All acceptance criteria are testable (not vague)
✓ Edge cases are covered
✓ Security considerations addressed
✓ Data model is complete with CAP trade-off stated
✓ API contract is fully specified (request + response + errors)
✓ Out-of-scope is explicitly listed
✓ No open questions remain blocking implementation
✓ EDD requirements filled in (AI/ML features only)
```

If any are missing → update the spec first.

---

## Phase 3: PLAN.md (Derived from Spec)

Once spec is approved, derive PLAN.md. Every task must include:

```markdown
# Plan: [Feature Name]
**Spec**: SPEC.md
**Status**: Ready to implement

> **For agentic workers:** REQUIRED: Use subagent-driven-development for every task.
> Each task = one fresh subagent. Spec compliance review → code quality review → ✅ done.

---

[EDD Preamble here if AI/ML feature]

---

### Phase 1: [Name]
Implements: F1, F2 from SPEC.md

#### Task 1.1: [Name]
- **File**: `src/[module]/[file].ts`
- **Action**: [Specific — "Add `createUser(dto: CreateUserDto): Promise<User>` to UserService"]
- **TDD Steps**:
  1. RED: Write failing test in `src/[module]/[file].spec.ts` — test [behavior]
  2. GREEN: Implement `[function]` to make test pass
  3. Commit: `test: add [name] test` then `feat: implement [name]`
- **Verification**: `npm test -- --testPathPattern=[file]` → `Tests: N passed`
- **Exit criteria**: Test passes, function handles [edge case]
- **Dependencies**: None
- **Risk**: Low
```

---

## Phase 4: Subagent Execution

For each task in PLAN.md:

```python
# Pseudo-code for the execution loop
for task in plan.tasks:
    subagent = spawn_fresh_subagent(
        context=task.full_description,
        spec=SPEC.md,
        prior_outputs=completed_tasks
    )
    output = subagent.execute()

    # Review gate 1: spec compliance
    spec_review = review_against_spec(output, SPEC.md, task.acceptance_criteria)
    if not spec_review.passed:
        raise PlanBlocker(f"Task {task.id} fails spec: {spec_review.issues}")

    # Review gate 2: code quality
    quality_review = review_code_quality(output)
    if not quality_review.passed:
        raise PlanBlocker(f"Task {task.id} code quality: {quality_review.issues}")

    task.status = "✅"
```

---

## Phase 5: Verify Against Spec

After all tasks complete, audit the implementation against the original spec:

```bash
# For each acceptance criterion in SPEC.md:
# Run the associated test or verification command
# Confirm output matches expected behavior

# Example:
npm test -- --testPathPattern=auth       # Unit: auth service
npm run test:e2e -- --spec=auth          # E2E: login flows
curl -X POST /api/v1/users -H "..." -d '{"email":"bad"}' | jq .status  # Edge: invalid input
```

Update SPEC.md status to `Implemented` and add the PR number.

---

## When to Use SDD

**Use it for:**
- Any new user-facing feature
- New API endpoints
- New data models
- Significant algorithm changes
- Security-sensitive features
- AI/ML features (EDD preamble required)

**Skip it for:**
- Bug fixes (use the bug report as your spec)
- Refactoring (behavior doesn't change)
- Documentation updates
- Configuration changes
- Trivial single-file changes

---

## SDD Iron Law

```
❌ Do NOT start a task without a spec-compliance review gate
❌ Do NOT mark a task done without running its verification command
❌ Do NOT skip the execution contract header in PLAN.md
❌ Do NOT use the same subagent for multiple independent tasks
❌ Do NOT skip EDD preamble for any AI/ML feature
```
