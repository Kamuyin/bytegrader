export const PLUGIN_ID = '@bytechallenge/bytegrader:main';

export const COMMAND_IDS = {
  openCoursesList: 'bytegrader:open-courses-list',
  openAssignmentsList: 'bytegrader:open-assignments-list',
  openInstructorTools: 'bytegrader:open-instructor-tools',
  openStudentDashboard: 'bytegrader:open-student-dashboard'
} as const;

export const ASSIGNMENT_STATUS = {
  NOT_STARTED: 'NOT_STARTED',
  IN_PROGRESS: 'IN_PROGRESS',
  SUBMITTED: 'SUBMITTED',
  GRADED: 'GRADED',
  COMPLETED: 'COMPLETED'
} as const;

export const ASSIGNMENT_STATUS_CONFIG = {
  NOT_STARTED: {
    backgroundColor: '#e3f2fd',
    color: '#1976d2',
    text: 'Not Started',
    icon: 'task'
  },
  IN_PROGRESS: {
    backgroundColor: '#fff3e0',
    color: '#f57c00',
    text: 'In Progress',
    icon: 'status-critical'
  },
  SUBMITTED: {
    backgroundColor: '#f3e5f5',
    color: '#7b1fa2',
    text: 'Submitted',
    icon: 'status-inactive'
  },
  GRADED: {
    backgroundColor: '#fff8e1',
    color: '#f9a825',
    text: 'Graded',
    icon: 'status-negative'
  },
  COMPLETED: {
    backgroundColor: '#e8f5e8',
    color: '#388e3c',
    text: 'Completed',
    icon: 'complete'
  }
} as const;

export const ROLE_BADGE_CONFIG = {
  instructor: {
    backgroundColor: '#e3f2fd',
    color: '#1976d2',
    text: 'Instructor',
    icon: 'person-placeholder'
  },
  student: {
    backgroundColor: '#e8f5e8',
    color: '#388e3c',
    text: 'Student',
    icon: 'person-placeholder'
  }
} as const;

export const SOLUTION_VISIBILITY_OPTIONS = [
  {
    value: 'never',
    label: 'Never',
    description: 'Solutions are never shown to students'
  },
  {
    value: 'after-due-date',
    label: 'After Due Date',
    description: 'Solutions are shown after the assignment due date'
  },
  {
    value: 'after-submission',
    label: 'After Submission',
    description: 'Solutions are shown after student submits their work'
  },
  {
    value: 'after-completion',
    label: 'After Completion',
    description: 'Solutions are shown after assignment is marked as complete'
  }
] as const;

export const WIZARD_STEPS = [
  { key: 'basic-info', title: 'Basic Information', icon: 'product' },
  { key: 'assignment-details', title: 'Assignment Details', icon: 'hint' },
  { key: 'design-assignment', title: 'Design Assignment', icon: 'action-settings' },
  { key: 'generate-review', title: 'Generate & Review', icon: 'process' },
  { key: 'review', title: 'Final Review', icon: 'save' }
] as const;

export const SCROLL_THRESHOLD = 20;
