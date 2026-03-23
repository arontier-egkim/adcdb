---
name: fullstack-webapp
description: "A full development pipeline where an agent team collaborates to develop fullstack web apps through requirements analysis, design, frontend, backend, testing, and deployment. Use this skill for requests like 'build me a feature', 'web service development', 'add new entity', 'CRUD app', 'build a dashboard', 'REST API development', 'fullstack project'. Also supports feature additions and refactoring for existing codebases."
---

# Fullstack Web App — Fullstack Web App Development Pipeline

An agent team collaborates to develop web apps through the pipeline of requirements → design → frontend → backend → testing → deployment.

## Execution Mode

**Agent Team** — 5 agents communicate directly via SendMessage and cross-verify.

## Agent Composition

| Agent | File | Role | Type |
|-------|------|------|------|
| architect | `.claude/agents/architect.md` | Requirements, architecture, DB, API design | general-purpose |
| frontend-dev | `.claude/agents/frontend-dev.md` | React/Vite/TypeScript frontend implementation | general-purpose |
| backend-dev | `.claude/agents/backend-dev.md` | FastAPI, SQLAlchemy, RDKit, business logic | general-purpose |
| qa-engineer | `.claude/agents/qa-engineer.md` | Test strategy, test code, code review | general-purpose |
| devops-engineer | `.claude/agents/devops-engineer.md` | CI/CD, infrastructure, deployment, monitoring | general-purpose |

## Workflow

### Phase 1: Preparation (performed directly by the orchestrator)

1. Extract from user input:
   - **Feature Description**: Purpose and core features to build
   - **Scope**: New feature / refactoring / bug fix
   - **Existing Code**: Analyze current ADCDB codebase
2. Create `_workspace/` directory at the project root
3. Organize input and save to `_workspace/00_input.md`
4. Analyze existing code to identify extension points
5. Determine **execution mode** based on request scope

### Phase 2: Team Assembly and Execution

| Order | Task | Owner | Dependencies | Deliverables |
|-------|------|-------|-------------|--------------|
| 1 | Architecture Design | architect | None | `01_architecture.md`, `02_api_spec.md`, `03_db_schema.md` |
| 2a | Frontend Development | frontend-dev | Task 1 | Frontend code |
| 2b | Backend Development | backend-dev | Task 1 | Backend code |
| 2c | Deployment Setup | devops-engineer | Task 1 | `05_deploy_guide.md`, CI/CD config |
| 3 | Testing & Review | qa-engineer | Tasks 2a, 2b | `04_test_plan.md`, `06_review_report.md`, test code |

Tasks 2a, 2b, 2c run **in parallel**.

### Phase 3: Integration and Final Deliverables

1. Verify all code and documents
2. Confirm all critical fixes from review have been addressed
3. Report final summary to the user

## Scale-Based Modes

| Request Pattern | Execution Mode | Deployed Agents |
|----------------|---------------|----------------|
| "Build a full feature" | **Full Pipeline** | All 5 |
| "Just build the API" | **Backend Mode** | architect + backend-dev + qa-engineer |
| "Just build the frontend" | **Frontend Mode** | architect + frontend-dev + qa-engineer |
| "Refactor this code" | **Refactoring Mode** | architect + relevant developer + qa-engineer |
| "Just set up deployment" | **DevOps Mode** | devops-engineer alone |

## Error Handling

| Error Type | Strategy |
|-----------|----------|
| Ambiguous requirements | Apply common patterns, document assumptions |
| Build errors | Analyze error logs → relevant developer fixes → QA re-verifies |
| Agent failure | Retry once → proceed without that deliverable if failed |
| Critical issue in review | Request fix → rework → re-verify (max 2 rounds) |

## Agent Extension Skills

| Skill | Target Agent | Role |
|-------|-------------|------|
| `component-patterns` | frontend-dev | React component patterns, state management strategies |
| `api-security-checklist` | backend-dev | OWASP Top 10, auth patterns, security headers |
