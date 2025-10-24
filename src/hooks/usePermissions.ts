import { useCallback } from 'react';
import { useCoursesStore } from '../stores/coursesStore';

export const usePermissions = () => {
  const coursesPermissions = useCoursesStore(state => state.permissions);

  const hasCoursePermission = useCallback(
    (courseId: string, permission: string) => {
      return (
        coursesPermissions?.scoped?.[courseId]?.includes(permission) ||
        coursesPermissions?.global?.includes(permission) ||
        false
      );
    },
    [coursesPermissions]
  );

  const hasGlobalPermission = useCallback(
    (permission: string) => {
      return coursesPermissions?.global?.includes(permission) || false;
    },
    [coursesPermissions]
  );

  return {
    hasCoursePermission,
    hasGlobalPermission
  };
};
