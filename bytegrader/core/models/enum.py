import enum


class UserRole(enum.Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"


class CellType(enum.Enum):
    CODE = "code"
    MARKDOWN = "markdown"


class ShowSolutionsOption(enum.Enum):
    NEVER = "never"
    ALWAYS = "always"
    AFTER_DUE = "after_due_date"
    AFTER_SUBMISSION = "after_submission"
    AFTER_COMPLETION = "after_completion"


class SubmissionStatus(enum.Enum):
    SUBMITTED = "submitted"
    GRADED = "graded"
    ARCHIVED = "archived"