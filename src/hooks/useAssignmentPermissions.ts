import { useCallback } from 'react';
import { useAssignmentsStore } from '../stores/assignmentsStore';

export const useAssignmentPermissions = () => {
  const permissions = useAssignmentsStore(state => state.permissions);

  const hasAssignmentPermission = useCallback(
    (assignmentId: string, permission: string) => {
      return (
        permissions?.scoped?.[assignmentId]?.includes(permission) ||
        permissions?.global?.includes(permission) ||
        false
      );
    },
    [permissions]
  );

  return { hasAssignmentPermission };
};
