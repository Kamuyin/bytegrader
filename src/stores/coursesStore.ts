import { create } from 'zustand';
import { Course, CoursePermissions } from '../types/api';
import { apiService } from '../services/api';

interface CoursesState {
  courses: Course[];
  permissions: CoursePermissions | null;
  loading: boolean;
  fetchCourses: () => Promise<void>;
  createCourse: (courseData: {
    label: string;
    title: string;
    lti_id: string;
    active: boolean;
  }) => Promise<void>;
  updateCourse: (courseLabel: string, courseData: {
    title?: string;
    lti_id?: string;
    active?: boolean;
  }) => Promise<void>;
  deleteCourse: (courseLabel: string) => Promise<void>;
  reset: () => void;
}

const initialState = {
  courses: [],
  permissions: null,
  loading: false
};

export const useCoursesStore = create<CoursesState>((set, get) => ({
  ...initialState,

  fetchCourses: async () => {
    set({ loading: true });
    try {
      const response = await apiService.courses.getAll();
      if (!response.success) {
        throw new Error(response.error || 'Failed to load courses');
      }
      set({
        courses: response.data?.courses || [],
        permissions: response.data?.permissions || null,
        loading: false
      });
    } catch (err) {
      set({ loading: false });
      throw err;
    }
  },

  createCourse: async (courseData) => {
    const response = await apiService.courses.create(courseData);
    if (!response.success) {
      throw new Error(response.error || 'Failed to create course');
    }
    await get().fetchCourses();
  },

  updateCourse: async (courseLabel, courseData) => {
    const response = await apiService.courses.update(courseLabel, courseData);
    if (!response.success) {
      throw new Error(response.error || 'Failed to update course');
    }
    await get().fetchCourses();
  },

  deleteCourse: async (courseLabel) => {
    await apiService.courses.delete(courseLabel);
    await get().fetchCourses();
  },

  reset: () => set(initialState)
}));
