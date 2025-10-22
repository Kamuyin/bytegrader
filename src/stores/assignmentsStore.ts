import { create } from 'zustand';
import { Assignment, AssignmentPermissions } from '../types/api';
import { apiService } from '../services/api';

interface AssignmentsState {
  assignments: Assignment[];
  permissions: AssignmentPermissions | null;
  currentCourseId: string | null;
  loading: boolean;
  fetchingAssignments: Set<string>;
  fetchingSolutions: Set<string>;
  optimisticUpdates: Record<string, Assignment['status']>;
  fetchAssignments: (courseId: string, preserve?: boolean) => Promise<void>;
  fetchAssignment: (courseId: string, assignmentId: string, solution?: boolean) => Promise<void>;
  submitAssignment: (courseId: string, assignmentId: string) => Promise<void>;
  deleteAssignment: (courseId: string, assignmentId: string) => Promise<void>;
  setOptimisticStatus: (assignmentId: string, status: Assignment['status']) => void;
  addFetchingAssignment: (assignmentId: string) => void;
  removeFetchingAssignment: (assignmentId: string) => void;
  addFetchingSolution: (assignmentId: string) => void;
  removeFetchingSolution: (assignmentId: string) => void;
  reset: () => void;
}

const initialState = {
  assignments: [],
  permissions: null,
  currentCourseId: null,
  loading: false,
  fetchingAssignments: new Set<string>(),
  fetchingSolutions: new Set<string>(),
  optimisticUpdates: {}
};

export const useAssignmentsStore = create<AssignmentsState>((set, get) => ({
  ...initialState,

  fetchAssignments: async (courseId: string, preserve = false) => {
    if (!preserve) {
      set({ loading: true });
    }
    set({ currentCourseId: courseId });
    
    try {
      const response = await apiService.assignments.getAll(courseId);
      if (!response.success) {
        throw new Error(response.error || 'Failed to load assignments');
      }
      
      const transformed: Assignment[] = response.data?.assignments.map((a: any) => ({
        ...a,
        isHidden: !a.visible,
        currentScore: a.submission?.total_score,
        notebooks: a.notebooks?.map((nb: any) => ({
          id: nb.id,
          filename: nb.name,
          maxScore: nb.max_score
        })) || []
      })) || [];
      
      set({
        assignments: transformed,
        permissions: response.data?.permissions || null,
        loading: false
      });
      
      const currentOptimistic = get().optimisticUpdates;
      const validOptimistic: Record<string, Assignment['status']> = {};
      
      transformed.forEach(asg => {
        const opt = currentOptimistic[asg.id];
        if (opt && opt === asg.status) {
          validOptimistic[asg.id] = opt;
        }
      });
      
      set({ optimisticUpdates: validOptimistic });
    } catch (err) {
      if (!preserve) {
        set({ loading: false });
      }
      throw err;
    }
  },

  fetchAssignment: async (courseId: string, assignmentId: string, solution = false) => {
    const response = await apiService.assignments.fetch(courseId, assignmentId, solution);
    if (!response.success && response.error) {
      throw new Error(response.error);
    }
  },

  submitAssignment: async (courseId: string, assignmentId: string) => {
    const response = await apiService.assignments.submit(courseId, assignmentId);
    if (!response.success) {
      throw new Error(response.error || 'Failed to submit assignment');
    }
    
    get().setOptimisticStatus(assignmentId, 'SUBMITTED');
    await get().fetchAssignments(courseId, true);
  },

  deleteAssignment: async (courseId: string, assignmentId: string) => {
    const response = await apiService.assignments.delete(courseId, assignmentId);
    if (!response.success) {
      throw new Error(response.error || 'Failed to delete assignment');
    }
    
    const currentOptimistic = { ...get().optimisticUpdates };
    delete currentOptimistic[assignmentId];
    set({ optimisticUpdates: currentOptimistic });
    
    await get().fetchAssignments(courseId, true);
  },

  setOptimisticStatus: (assignmentId: string, status: Assignment['status']) => {
    set(state => ({
      optimisticUpdates: { ...state.optimisticUpdates, [assignmentId]: status }
    }));
  },

  addFetchingAssignment: (assignmentId: string) => {
    set(state => ({
      fetchingAssignments: new Set(state.fetchingAssignments).add(assignmentId)
    }));
  },

  removeFetchingAssignment: (assignmentId: string) => {
    set(state => {
      const newSet = new Set(state.fetchingAssignments);
      newSet.delete(assignmentId);
      return { fetchingAssignments: newSet };
    });
  },

  addFetchingSolution: (assignmentId: string) => {
    set(state => ({
      fetchingSolutions: new Set(state.fetchingSolutions).add(assignmentId)
    }));
  },

  removeFetchingSolution: (assignmentId: string) => {
    set(state => {
      const newSet = new Set(state.fetchingSolutions);
      newSet.delete(assignmentId);
      return { fetchingSolutions: newSet };
    });
  },

  reset: () => set(initialState)
}));
