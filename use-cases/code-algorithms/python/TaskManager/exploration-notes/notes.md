# Exploration Notes — Task Manager Codebase

Working notes tracking my discovery process: initial guesses, what I actually found, and how I used AI prompts to verify and correct my understanding. Organized by exercise part.

---

## Part 1: Understanding Project Structure

### Initial exploration (before AI)
Top-level files found in `use-cases/code-algorithms/python/TaskManager`:
```
tests/
.gitignore
README.md
cli.py
models.py
storage.py
task_list_merge.py
task_manager.py
task_parser.py
task_priority.py
```

### My initial guesses (before opening any file contents)
- Guessed this was some kind of task-tracking app, possibly with a web framework (Folder structure patterns common to web apps)
- Wasn't sure what technologies were used
- Assumed `.gitignore` was a file extension, not a Git config file
- No `requirements.txt` present, which was a hint the project might not use third-party dependencies

### Applied "Understanding Project Structure and Technology Stack" prompt
Went file by file, forming a hypothesis about each one's purpose from its name, then opening it to confirm or correct.

### What I actually found
| File      | My guess                  |            Confirmed reality 
|---        |---                        |----------------------------|
| `cli.py`  | Probably the interface    | Confirmed — argparse-based                          CLI, entry point (` name__ == "__main__"`) |
| `task_manager.py` | Core logic | Confirmed — `TaskManager` class, orchestrates storage + validation |
| `models.py` | Data entities | Confirmed — `Task`, `TaskStatus`, `TaskPriority` |
| `storage.py` | Persistence | Confirmed — `TaskStorage`, JSON file read/write, CRUD |
| `task_parser.py` | Guessed: file/export parsing | **Wrong** — actually parses free-text shorthand into a `Task` object |
| `task_priority.py` | Guessed: duplicate of the enum | **Wrong** — a separate weighted importance-scoring algorithm, unused by the CLI |
| `task_list_merge.py` | No strong guess | Turned out to be a two-way sync/conflict-resolution algorithm, also unused by the CLI |

### Misconceptions corrected
- `task_parser.py` is about parsing **user input text**, not files
- Two whole modules (`task_priority.py`, `task_list_merge.py`) implement real features that aren't connected to the CLI at all — this wasn't obvious from file names or a quick skim

### Entry point identified
`cli.py` — confirmed via the `if __name__ == "__main__": main()` block.

### Architecture pattern identified
Clean layered architecture:
```
cli.py  →  task_manager.py  →  storage.py  →  models.py
(interface)  (business logic)  (persistence)  (domain model)
```
No web framework, no database, no third-party dependencies — pure Python standard library.

---

## Part 2: Finding Feature Implementation (Task Export to CSV)

### Initial search
Searched the project for "csv" and "export" — nothing found, confirming this is genuinely new functionality.

### Hypothesis (before confirming)
Guessed the export feature belongs in `storage.py`, since it's likely already responsible for serializing task data.

### Applied "Finding Feature Implementation Locations" prompt
Opened `storage.py` and `task_parser.py` to check.

### What I found
- `storage.py` — confirmed home for export. Already has `TaskEncoder`/`TaskDecoder` classes converting `Task` objects to/from JSON, plus a `TaskStorage` class with `save()`/`load()` and query methods like `get_all_tasks()`, `get_overdue_tasks()`.
- `task_parser.py` — **not** related to export at all (see misconception above). It's an input-side feature (free text → `Task`), not an output-side one.

### Implementation plan
- Add `export_to_csv(self, filepath)` method to `TaskStorage`, reusing `get_all_tasks()` and Python's built-in `csv` module
- Reuse the same field-flattening logic `TaskEncoder` already does (enums → `.value`, datetimes → `.isoformat()`)
- Add a new CLI subcommand in `cli.py` to expose it
- Add a test in `tests/` mirroring how `save()`/`load()` are tested

---

## Part 3: Understanding Domain Model

### Initial guesses (before opening `models.py`)
Expected a `Task` class plus `TaskStatus` and `TaskPriority` as enums, based on naming conventions common in task-tracking apps.

### Applied "Understanding Domain Models and Business Concepts" prompt

### What I found in `models.py`
- **`TaskPriority`** (Enum): `LOW=1, MEDIUM=2, HIGH=3, URGENT=4` — numeric values suggest ordering/comparison
- **`TaskStatus`** (Enum): `TODO, IN_PROGRESS, REVIEW, DONE` — string values. No `ABANDONED` value exists yet.
- **`Task`** (class):
  - Fields: `id` (UUID), `title`, `description`, `priority`, `status` (always starts `TODO`), `created_at`, `updated_at`, `due_date`, `completed_at`, `tags`
  - Methods: `update(**kwargs)`, `mark_as_done()`, `is_overdue()`

### Glossary
| Term | Meaning |
|---|---|
| `TODO` | Not yet started |
| `IN_PROGRESS` | Actively being worked on |
| `REVIEW` | Done but awaiting approval |
| `DONE` | Completed |
| `is_overdue()` | True if `due_date` is in the past AND status isn't `DONE` (doesn't factor in priority) |

### Questions for the team
- Should `REVIEW` status count as overdue if due date passes?
- Why can't `status` be set at task creation (always starts at `TODO`)?

---

## Part 4: Practical Application — Overdue/Abandoned Rule

**Rule:** Tasks overdue for more than 7 days should be automatically marked as abandoned, unless high priority.

### Files to modify
- `models.py` — add `ABANDONED` to `TaskStatus`; add `should_be_abandoned()` method to `Task`
- `task_manager.py` — add `abandon_overdue_tasks()` orchestration method
- `cli.py` — decide whether this runs automatically or via a new explicit command

### Draft implementation sketch
```python
# models.py — new method on Task
def should_be_abandoned(self):
    if not self.due_date or self.status == TaskStatus.DONE:
        return False
    days_overdue = (datetime.now() - self.due_date).days
    return days_overdue > 7 and self.priority != TaskPriority.HIGH
```

```python
# task_manager.py — new orchestration method
def abandon_overdue_tasks(self):
    abandoned_count = 0
    for task in self.storage.get_all_tasks():
        if task.should_be_abandoned():
            task.status = TaskStatus.ABANDONED
            task.updated_at = datetime.now()
            abandoned_count += 1
    self.storage.save()
    return abandoned_count
```

### Open questions before implementing
- Does "high priority" exempt only `HIGH`, or also `URGENT` (which ranks above `HIGH`)?
- Should this run on every CLI invocation, on a schedule, or only via an explicit command?
- Are `REVIEW`-status tasks eligible for abandonment?
- Should abandonment be reversible?

---

## Reflection

- **Most helpful prompt:** the Feature Location prompt (Part 2) — it directly corrected a wrong assumption about `task_parser.py` and confirmed the right file for new functionality.
- **What I'd do differently next time:** open files in dependency order (entry point first, then trace outward) rather than assuming a file's purpose from its name alone.
- **Still unsure about:** whether `task_list_merge.py` and `task_priority.py` are planned features awaiting a CLI hook, or leftover/experimental code — need to ask the team.
