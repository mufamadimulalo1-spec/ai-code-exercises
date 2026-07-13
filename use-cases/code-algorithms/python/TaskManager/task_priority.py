from datetime import datetime

from models import TaskStatus, TaskPriority

def calculate_task_score(task):
    """
    Calculate a numeric priority score for a task, combining its priority
    level, due date urgency, current status, tags, and recency of last
    update into one comparable value. Higher scores mean the task should
    be worked on sooner. Powers sort_tasks_by_importance and
    get_top_priority_tasks.

    Parameters:
        task (Task): Expected attributes:
            - priority (TaskPriority): LOW=1, MEDIUM=2, HIGH=4, URGENT=6
              point multipliers (x10 for the base score). An unrecognized
              or missing priority silently contributes 0 rather than
              raising an error -- this can mask bad task data.
            - due_date (datetime | None): If set, contributes a flat
              bonus based on days remaining: overdue +35, due today +20,
              due within 2 days +15, due within a week +10, further out
              +0. Note: `.days` on a timedelta truncates toward negative
              infinity, so a task overdue by only a few hours already
              registers as -1 day, not 0 -- the +35 bonus triggers
              immediately on becoming overdue, with no same-day grace
              period.
            - status (TaskStatus): DONE subtracts 50; REVIEW subtracts
              15; TODO/IN_PROGRESS have no effect.
            - tags (list[str]): A flat +8 bonus if ANY of "blocker",
              "critical", or "urgent" appears -- the bonus does not scale
              with how many of the three match.
            - updated_at (datetime): +5 bonus if updated less than a day
              ago. Assumed to always be a valid past timestamp; a
              future-dated value would still pass this check.

    Returns:
        int: The computed score. NOT clamped to any range -- e.g. a DONE,
        LOW-priority task with no due date scores 10 - 50 = -40. Fine for
        sorting, but a negative number could look like a bug if ever
        shown to a user directly.

    Raises:
        AttributeError: If `task` is missing any of the expected
            attributes.
        TypeError: If `due_date` or `updated_at` isn't a datetime when
            subtracted against datetime.now().

    Example:
        >>> from datetime import datetime, timedelta
        >>> task = Task(
        ...     title="Fix login bug",
        ...     priority=TaskPriority.HIGH,
        ...     due_date=datetime.now() + timedelta(days=1),
        ... )
        >>> task.tags = ["urgent"]
        >>> calculate_task_score(task)
        63

    Suggested improvements: extract magic numbers (35, 20, 15, 10, 50,
    8, 5...) into named constants; clamp the score to a non-negative
    minimum if ever displayed to users; raise/log on an invalid
    `priority` instead of silently defaulting to 0; consider scaling
    the tag bonus with the number of matching tags if that's the
    intended behavior.
    """
    # Base priority weights
    priority_weights = {
        TaskPriority.LOW: 1,
        TaskPriority.MEDIUM: 2,
        TaskPriority.HIGH: 4,
        TaskPriority.URGENT: 6
    }

    # Calculate base score from priority
    score = priority_weights.get(task.priority, 0) * 10

    # Add due date factor (higher score for tasks due sooner)
    if task.due_date:
        days_until_due = (task.due_date - datetime.now()).days
        if days_until_due < 0:  # Overdue tasks
            score += 35
        elif days_until_due == 0:  # Due today
            score += 20
        elif days_until_due <= 2:  # Due in next 2 days
            score += 15
        elif days_until_due <= 7:  # Due in next week
            score += 10

    # Reduce score for tasks that are completed or in review
    if task.status == TaskStatus.DONE:
        score -= 50
    elif task.status == TaskStatus.REVIEW:
        score -= 15

    # Boost score for tasks with certain tags
    if any(tag in ["blocker", "critical", "urgent"] for tag in task.tags):
        score += 8

    # Boost score for recently updated tasks
    days_since_update = (datetime.now() - task.updated_at).days
    if days_since_update < 1:
        score += 5

    return score

def sort_tasks_by_importance(tasks):
    """Sort tasks by calculated importance score (highest first)."""
    task_scores = [(calculate_task_score(task), task) for task in tasks]
    # Use key parameter to tell sorted() to only compare the scores (first element of tuple)
    sorted_tasks = [task for _, task in sorted(task_scores, key=lambda x: x[0], reverse=True)]
    return sorted_tasks

def get_top_priority_tasks(tasks, limit=5):
    """Return the top N priority tasks."""
    sorted_tasks = sort_tasks_by_importance(tasks)
    return sorted_tasks[:limit]
