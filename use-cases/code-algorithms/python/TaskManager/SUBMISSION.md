# Understanding the Task Manager Codebase — Submission

**Project:** Task Manager (Python implementation)
**Repo path:** `use-cases/code-algorithms/python/TaskManager`

## 1. Initial vs. Final Understanding

**Initial understanding (before exploring):**
Based only on folder/file names, my early guesses were cautious — I assumed this was some kind of task-tracking application, likely with a CLI, but wasn't sure whether it used a web framework, a database, or third-party libraries. I also wasn't sure what `task_parser.py` did — I initially guessed it might x file parsing (e.g. for import/export), and that `.gitignore` was some kind of file extension rather than a Git configuration file.

**Final understanding (after exploring with AI prompts):**
The project is a **pure Python 3, standard-library-only CLI application** with no framework and no database — persistence is a single flat JSON file. It follows a clean **layered architecture**:

- `cli.py` — argparse-based CLI, the entry point (`if __name__ == "__main__"`)
- `task_manager.py` — business logic / orchestration layer (`TaskManager` class)
- `models.py` — domain model (`Task`, `TaskStatus`, `TaskPriority`)
- `storage.py` — persistence layer (`TaskStorage`, JSON read/write, CRUD, filtering)
- `task_parser.py` — converts free-text shorthand (e.g. `"Buy milk @shopping !2 #tomorrow"`) into a `Task` object — **not** a file/export parser, correcting my initial guess
- `task_list_merge.py` — a two-way sync/conflict-resolution algorithm for reconciling local vs. remote task lists
- `task_priority.py` — a weighted importance-scoring algorithm for ranking tasks

**Biggest surprise:** two entire modules (`task_list_merge.py` and `task_priority.py`) implement real, non-trivial features that are **not wired into the CLI at all**. Skimming file names alone would never have revealed this — it only became clear by actually opening each file and comparing it against my hypothesis.

## 2. Most Valuable Insights, By Prompt

**Prompt 1 — Understanding Project Structure and Technology Stack:**
Helped me quickly rule out assumptions (no framework, no database, no dependencies) and gave me a reliable method — hypothesize per file, then verify — for building an accurate map of the codebase instead of guessing from names alone.

**Prompt 2 — Finding Feature Implementation Locations:**
Directly corrected a misconception (`task_parser.py`) and confirmed `storage.py` as the natural home for a new CSV export feature, since it's already the single place responsible for serializing `Task` objects.

**Prompt 3 — Understanding Domain Models and Business Concepts:**
Surfaced the exact fields and methods on `Task` (`is_overdue()`, `mark_as_done()`) needed to reason about business rules, and made clear that `TaskStatus` currently has no `ABANDONED` value — a direct input into Part 4.

## 3. Approach to Implementing the New Business Rule

**Rule:** *Tasks overdue for more than 7 days should be automatically marked as abandoned, unless they are high priority.*

**Files to modify:**
- `models.py` — add `ABANDONED` to `TaskStatus`; add a `should_be_abandoned()` method to `Task`, mirroring the existing style of `is_overdue()`
- `task_manager.py` — add an orchestration method (e.g. `abandon_overdue_tasks()`) that loops over all tasks, applies the rule, and saves changes
- `cli.py` — decide whether this runs automatically or via an explicit new command

**Open questions for the team before implementing:**
- Does "high priority" exempt only `HIGH`, or also `URGENT` (which ranks above `HIGH`)?
- Should this check run on every CLI invocation, on a schedule, or only via an explicit command?
- Are `REVIEW`-status tasks eligible for abandonment, or only `TODO`/`IN_PROGRESS`?
- Should abandonment be reversible?

## 4. Strategies for Approaching Unfamiliar Codebases (Future Reference)

- Skim structure first, but **don't trust file names alone** — two "hidden" feature modules here were completely invisible from the outside.
- Form a hypothesis *before* opening each file, then compare — this made incorrect assumptions (like `task_parser.py`) obvious and memorable, rather than silently absorbing a wrong mental model.
- Trace the entry point first (`cli.py`), then follow one call chain all the way down (CLI → Manager → Storage → Model) to understand layering, rather than reading files in isolation.
- Flag anything that looks unused or unconnected (like `task_list_merge.py`) as a question for the team rather than assuming it's dead code — it may be a planned feature or used elsewhere.
