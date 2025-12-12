export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface Course {
    label: string;
    title: string;
    lti_id: string;
    active: boolean;
    progress: number;
    student_count: number | null;
    instructors: string[];
    created_at: string;
}

export interface CoursePermissions {
  global: string[];
  scoped: Record<string, string[]>;
}

export interface CourseListData {
  courses: Course[];
  permissions: CoursePermissions;
}

export type CourseListResponse = APIResponse<CourseListData>;

export interface CourseListDataWithPermissions {
  courses: Course[];
  perms: CoursePermissions;
}

export interface CourseListResponseWithPermissions extends APIResponse<CourseListData> {
  perms: CoursePermissions;
}

export interface ApiNotebook {
  id: string;
  name: string;
  idx: number;
  max_score: number;
}

export interface Notebook {
  id: string;
  filename: string;
  maxScore: number;
}

export interface ApiAssignment {
  id: string;
  name: string;
  description?: string;
  due_date?: string;
  max_score: number;
  visible: boolean;
  created_at: string;
  notebooks: ApiNotebook[];
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'SUBMITTED' | 'GRADED' | 'COMPLETED';
  submission?: AssignmentSubmission;
  allow_resubmission?: boolean;
}

export interface Assignment {
  id: string;
  name: string;
  description?: string;
  due_date?: string;
  max_score: number;
  visible: boolean;
  created_at: string;
  notebooks: Notebook[];
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'SUBMITTED' | 'GRADED' | 'COMPLETED';
  submission?: AssignmentSubmission;
  allow_resubmission?: boolean;
  isHidden?: boolean;
  currentScore?: number;
}

export interface AssignmentSubmission {
  id: string;
  submitted_at?: string;
  status: string;
  is_late: boolean;
  total_score?: number;
  auto_score?: number;
  manual_score?: number;
  needs_manual_grading: boolean;
  graded_at?: string;
  graded_by?: string;
}

export interface AssignmentListData {
  assignments: ApiAssignment[];
}

export type AssignmentListResponse = APIResponse<AssignmentListData>;

export interface AssignmentPermissions {
  global: string[];
  scoped: Record<string, string[]>;
}

export interface AssignmentListDataWithPermissions {
  assignments: ApiAssignment[];
  permissions: AssignmentPermissions;
}

export type AssignmentListResponseWithEnhancedState = APIResponse<AssignmentListDataWithPermissions>;

export interface GeneratePreviewResponseData {
  base_dir: string;
  files: { rel: string; abs: string }[];
}

export type GeneratePreviewResponse = APIResponse<GeneratePreviewResponseData>;