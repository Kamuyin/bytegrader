import React, { useMemo, useCallback, useState } from 'react';
import {
  Card,
  Button,
  ActionSheet,
  FlexBox,
  FlexBoxDirection,
  FlexBoxJustifyContent,
  FlexBoxAlignItems,
  Title,
  Text,
  Icon,
  Select,
  Option,
  MessageBox,
  IllustratedMessage
} from '@ui5/webcomponents-react';
import '@ui5/webcomponents-fiori/dist/illustrations/SimpleTask.js';
import '@ui5/webcomponents-icons/dist/download.js';
import '@ui5/webcomponents-icons/dist/reset.js';
import '@ui5/webcomponents-icons/dist/document.js';
import '@ui5/webcomponents-icons/dist/navigation-left-arrow.js';
import '@ui5/webcomponents-icons/dist/calendar.js';
import '@ui5/webcomponents-icons/dist/overflow.js';
import '@ui5/webcomponents-icons/dist/edit.js';
import '@ui5/webcomponents-icons/dist/delete.js';
import '@ui5/webcomponents-icons/dist/hide.js';
import '@ui5/webcomponents-icons/dist/show.js';
import '@ui5/webcomponents-icons/dist/add.js';
import '@ui5/webcomponents-icons/dist/upload.js';
import '@ui5/webcomponents-icons/dist/status-positive.js';
import '@ui5/webcomponents-icons/dist/refresh.js';
import '@ui5/webcomponents-icons/dist/group-2.js';
import '@ui5/webcomponents-icons/dist/course-book.js';
import '@ui5/webcomponents-icons/dist/activity-individual.js';
import '@ui5/webcomponents-icons/dist/lightbulb.js';
import '@ui5/webcomponents-icons/dist/target-group.js';
import { Assignment, Course } from '../types/api';
import { AssignmentStatusBadge, HiddenBadge, ScoreBadge } from './shared/Badges';
import { DueDateDisplay } from './shared/DueDateDisplay';
import { NotebookList } from './shared/NotebookList';
import { AssignmentActionButtons } from './shared/AssignmentActionButtons';
import { useScrollDetection } from '../hooks/useScrollDetection';
import { SCROLL_THRESHOLD } from '../constants';

export interface AssignmentsListData {
  courseId: string;
  courseTitle: string;
  assignments: Assignment[];
  permissions: { global: string[]; scoped: Record<string, string[]> };
}

export interface AssignmentsListProps {
  currentCourseId?: string;
  data: AssignmentsListData | null;
  coursesData: Course[];
  loading: boolean;
  coursesLoading: boolean;
  fetchingAssignments: Set<string>;
  optimisticUpdates: Record<string, Assignment['status']>;
  fetchingSolutions: Set<string>;
  hasCoursePermission: (courseId: string, permission: string) => boolean;
  hasAssignmentPermission: (assignmentId: string, permission: string) => boolean;
  onCourseChange?: (courseId: string) => void;
  onStartAssignment?: (assignmentId: string) => void;
  onResetAssignment?: (assignmentId: string) => void;
  onSubmitAssignment?: (assignmentId: string) => void;
  onFetchSolutions?: (assignmentId: string) => void;
  onEditAssignment?: (assignmentId: string) => void;
  onDeleteAssignment?: (assignmentId: string) => void;
  onToggleAssignmentVisibility?: (assignmentId: string, isHidden: boolean) => void;
  onCreateAssignment?: () => void;
  onViewSubmissions?: (assignmentId?: string) => void;
  onBackToCourses?: () => void;
  onRefreshAssignments?: () => void;
  submitWarningOpen: boolean;
  selectedAssignmentForSubmit: string | null;
  onSubmitConfirm?: () => void;
  onSubmitCancel?: () => void;
  deleteWarningOpen: boolean;
  selectedAssignmentForDelete: string | null;
  onDeleteConfirm?: () => void;
  onDeleteCancel?: () => void;
}

const AssignmentsList: React.FC<AssignmentsListProps> = ({
  currentCourseId,
  data,
  coursesData,
  loading,
  coursesLoading,
  fetchingAssignments,
  optimisticUpdates,
  fetchingSolutions,
  hasCoursePermission,
  hasAssignmentPermission,
  onCourseChange,
  onStartAssignment,
  onResetAssignment,
  onSubmitAssignment,
  onFetchSolutions,
  onEditAssignment,
  onDeleteAssignment,
  onToggleAssignmentVisibility,
  onCreateAssignment,
  onViewSubmissions,
  onBackToCourses,
  onRefreshAssignments,
  submitWarningOpen,
  selectedAssignmentForSubmit,
  onSubmitConfirm,
  onSubmitCancel,
  deleteWarningOpen,
  selectedAssignmentForDelete,
  onDeleteConfirm,
  onDeleteCancel
}) => {
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [menuOpener, setMenuOpener] = useState<HTMLElement | null>(null);
  const { isScrolled, scrollContainerRef } = useScrollDetection(SCROLL_THRESHOLD);

  const selectedAssignmentForSubmitDialog = data?.assignments.find(a => a.id === selectedAssignmentForSubmit);
  const selectedAssignmentForDeleteDialog = data?.assignments.find(a => a.id === selectedAssignmentForDelete);

  const handleMenuClick = useCallback((event: any, assignmentId: string) => {
    event.stopPropagation();
    setMenuOpener(event.target as HTMLElement);
    setOpenMenuId(assignmentId);
  }, []);

  const getTotalScore = useCallback((assignment: Assignment) => {
    return assignment.notebooks.reduce((sum, n) => sum + n.maxScore, 0);
  }, []);

  if (loading || coursesLoading) {
    return (
      <div style={{ height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '16px' }}>
        <Text style={{ fontSize: '18px', color: 'var(--sapNeutralTextColor)' }}>
          {coursesLoading ? 'Loading courses...' : 'Loading assignments...'}
        </Text>
      </div>
    );
  }

  if (!coursesData.length && !coursesLoading) {
    return (
      <div style={{ height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '16px' }}>
        <Icon name="course-book" style={{ fontSize: '48px', color: 'var(--sapNeutralTextColor)' }} />
        <Text style={{ fontSize: '18px', color: 'var(--sapNeutralTextColor)' }}>
          No courses available
        </Text>
      </div>
    );
  }

  if (!currentCourseId || !data) {
    return (
      <div style={{ height: '100%', width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '16px' }}>
        <Icon name="course-book" style={{ fontSize: '48px', color: 'var(--sapNeutralTextColor)' }} />
        <Text style={{ fontSize: '18px', color: 'var(--sapNeutralTextColor)' }}>
          {!currentCourseId ? 'Select a course to view assignments' : 'No assignment data available'}
        </Text>
      </div>
    );
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 10,
          backgroundColor: 'var(--sapBackgroundColor)',
          borderBottom: isScrolled ? '1px solid var(--sapGroup_TitleBorderColor)' : 'none',
          padding: '24px 24px 16px 24px',
          flexShrink: 0,
          width: '100%',
          boxSizing: 'border-box'
        }}
      >
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            width: '100%'
          }}
        >
          <div
            style={{
              width: '100%',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '16px',
              flexWrap: 'wrap'
            }}
          >
            <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '12px', flexWrap: 'wrap' }}>
              <Button
                design="Transparent"
                icon="navigation-left-arrow"
                onClick={onBackToCourses}
                tooltip="Back to Courses"
                style={{ borderRadius: '50%', width: '40px', height: '40px' }}
              />
              <Icon name="course-book" style={{ fontSize: '24px', color: 'var(--sapAccentColor7)' }} />
              <Title style={{ fontSize: '2rem', fontWeight: '600', margin: 0 }}>Assignments</Title>
            </FlexBox>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                flexWrap: 'wrap'
              }}
            >
              {currentCourseId && (
                <Button
                  design="Transparent"
                  icon="refresh"
                  onClick={() => onRefreshAssignments?.()}
                  style={{ borderRadius: '8px' }}
                  tooltip="Refresh Assignments"
                />
              )}
              {currentCourseId && hasCoursePermission(currentCourseId, 'course:view_submissions') && (
                <Button
                  design="Default"
                  icon="group-2"
                  onClick={() => onViewSubmissions?.()}
                  style={{ borderRadius: '8px', fontWeight: '600' }}
                >
                  View All Submissions
                </Button>
              )}
              {currentCourseId && hasCoursePermission(currentCourseId, 'assignment:create') && (
                <Button
                  design="Emphasized"
                  icon="add"
                  onClick={onCreateAssignment}
                  style={{ borderRadius: '8px', fontWeight: '600' }}
                >
                  Create Assignment
                </Button>
              )}
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              flexWrap: 'wrap'
            }}
          >
            <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '8px' }}>
              <Icon name="course-book" style={{ fontSize: '14px', color: 'var(--sapAccentColor7)' }} />
              <Text style={{ fontSize: '14px', color: '#666' }}>Course:</Text>
            </FlexBox>
            <Select
              value={currentCourseId || data.courseId}
              onChange={(e: any) => {
                const val = e.detail?.selectedOption?.getAttribute('value') || e.target.value;
                onCourseChange?.(val);
              }}
              style={{ minWidth: '260px' }}
            >
              {coursesData.map(course => (
                <Option key={course.label} value={course.label}>
                  {course.title} ({course.label})
                </Option>
              ))}
            </Select>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              flexWrap: 'wrap'
            }}
          >
            <Icon name="activity-individual" style={{ fontSize: '14px', color: 'var(--sapAccentColor6)' }} />
            <Text style={{ fontSize: '14px', color: '#666' }}>
              {data.assignments.length} assignment{data.assignments.length !== 1 ? 's' : ''}
            </Text>
          </div>
        </div>
      </header>

      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          padding: '0 24px 24px 24px',
          minHeight: 0,
          minWidth: 0,
          width: '100%',
          boxSizing: 'border-box'
        }}
      >
        <div
          ref={scrollContainerRef}
          data-scroll-container
          style={{
            flex: 1,
            overflowY: data.assignments.length === 0 ? 'hidden' : 'auto',
            overflowX: 'hidden',
            paddingTop: '16px',
            paddingBottom: '8px',
            minHeight: 0,
            position: 'relative'
          }}
        >
          <FlexBox
            direction={FlexBoxDirection.Column}
            style={{
              gap: '16px',
              paddingBottom: data.assignments.length === 0 ? 0 : '16px',
              minHeight: data.assignments.length === 0 ? '100%' : undefined,
              boxSizing: 'border-box'
            }}
          >
            {data.assignments.length === 0 ? (
              <FlexBox
                direction={FlexBoxDirection.Column}
                alignItems={FlexBoxAlignItems.Center}
                justifyContent={FlexBoxJustifyContent.Center}
                style={{ flex: 1, padding: '32px 16px', gap: '16px', boxSizing: 'border-box' }}
              >
                <IllustratedMessage
                  name="SimpleTask"
                  titleText="No assignments available"
                  subtitleText="There are no assignments in this course yet. Check back later or contact your instructor."
                />
              </FlexBox>
            ) : (
              data.assignments.map(assignment => {
                const totalScore = getTotalScore(assignment);
                const displayStatus = optimisticUpdates[assignment.id] || assignment.status;
                const isFetching = fetchingAssignments.has(assignment.id);
                const isSolutionFetching = fetchingSolutions.has(assignment.id);

                return (
                  <Card
                    key={assignment.id}
                    style={{
                      width: '100%',
                      border: '1px solid var(--sapGroup_TitleBorderColor)',
                      borderRadius: '12px',
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)'
                    }}
                    header={
                      <FlexBox
                        justifyContent={FlexBoxJustifyContent.SpaceBetween}
                        alignItems={FlexBoxAlignItems.Center}
                        style={{
                          padding: '16px 20px',
                          backgroundColor: 'var(--sapObjectHeader_Background)',
                          borderRadius: '12px 12px 0 0',
                          borderBottom: '1px solid var(--sapGroup_TitleBorderColor)'
                        }}
                      >
                        <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '12px', flex: 1 }}>
                          <FlexBox
                            alignItems={FlexBoxAlignItems.Center}
                            style={{
                              width: '40px',
                              height: '40px',
                              backgroundColor: 'var(--sapAccentColor7)',
                              borderRadius: '50%',
                              justifyContent: 'center',
                              flexShrink: 0
                            }}
                          >
                            <Icon name="course-book" style={{ fontSize: '18px', color: 'white' }} />
                          </FlexBox>
                          <Title
                            level="H4"
                            style={{
                              fontSize: '18px',
                              fontWeight: '700',
                              color: 'var(--sapGroup_TitleTextColor)',
                              lineHeight: '1.2',
                              margin: 0
                            }}
                          >
                            {assignment.name}
                          </Title>
                        </FlexBox>
                        <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '12px' }}>
                          {assignment.isHidden && <HiddenBadge />}
                          <AssignmentStatusBadge status={displayStatus} />
                          {assignment.currentScore !== undefined && (
                            <ScoreBadge currentScore={assignment.currentScore} totalScore={totalScore} />
                          )}
                          {(hasAssignmentPermission(assignment.id, 'assignment:view_submissions') ||
                            hasAssignmentPermission(assignment.id, 'assignment:edit') ||
                            hasAssignmentPermission(assignment.id, 'assignment:hide') ||
                            hasAssignmentPermission(assignment.id, 'assignment:delete')) && (
                            <Button
                              icon="overflow"
                              design="Transparent"
                              onClick={(e) => handleMenuClick(e, assignment.id)}
                              style={{ borderRadius: '50%', width: '32px', height: '32px' }}
                            />
                          )}
                        </FlexBox>
                      </FlexBox>
                    }
                  >
                    <FlexBox direction={FlexBoxDirection.Column} style={{ padding: '20px', gap: '16px' }}>
                      {assignment.description && (
                        <FlexBox alignItems={FlexBoxAlignItems.Start} style={{ gap: '12px' }}>
                          <Icon
                            name="activity-individual"
                            style={{ fontSize: '16px', color: 'var(--sapAccentColor6)', marginTop: '2px', flexShrink: 0 }}
                          />
                          <Text style={{ fontSize: '15px', color: 'var(--sapTextColor)', lineHeight: '1.5', fontWeight: 400 }}>
                            {assignment.description}
                          </Text>
                        </FlexBox>
                      )}
                      {assignment.due_date && <DueDateDisplay dueDate={assignment.due_date} />}
                      <NotebookList notebooks={assignment.notebooks} />
                      <FlexBox
                        justifyContent={FlexBoxJustifyContent.SpaceBetween}
                        alignItems={FlexBoxAlignItems.Center}
                        style={{
                          padding: '16px',
                          backgroundColor: 'var(--sapObjectHeader_Background)',
                          borderRadius: '8px',
                          border: '1px solid var(--sapGroup_TitleBorderColor)'
                        }}
                      >
                        <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '8px' }}>
                          <Icon name="status-positive" style={{ fontSize: '16px', color: 'var(--sapSuccessColor)' }} />
                          <Text style={{ fontSize: '15px', fontWeight: 700, color: 'var(--sapGroup_TitleTextColor)' }}>
                            Total Score: {totalScore} points
                          </Text>
                        </FlexBox>
                        <AssignmentActionButtons
                          assignment={assignment}
                          displayStatus={displayStatus}
                          isFetching={isFetching}
                          isSolutionFetching={isSolutionFetching}
                          hasPermission={(perm) => hasAssignmentPermission(assignment.id, perm)}
                          onStart={() => onStartAssignment?.(assignment.id)}
                          onSubmit={() => onSubmitAssignment?.(assignment.id)}
                          onReset={() => onResetAssignment?.(assignment.id)}
                          onFetchSolutions={() => onFetchSolutions?.(assignment.id)}
                        />
                      </FlexBox>
                    </FlexBox>
                  </Card>
                );
              })
            )}
          </FlexBox>
        </div>
      </div>

      <ActionSheet open={!!openMenuId} opener={menuOpener || undefined} onClose={() => setOpenMenuId(null)}>
        {openMenuId && (() => {
          const assignment = data.assignments.find(a => a.id === openMenuId);
          if (!assignment) return null;
          return (
            <>
              {hasAssignmentPermission(openMenuId, 'assignment:view_submissions') && (
                <Button
                  icon="group-2"
                  design="Transparent"
                  onClick={() => {
                    setOpenMenuId(null);
                    onViewSubmissions?.(openMenuId);
                  }}
                >
                  View Submissions
                </Button>
              )}
              {hasAssignmentPermission(openMenuId, 'assignment:edit') && (
                <Button
                  icon="edit"
                  design="Transparent"
                  onClick={() => {
                    setOpenMenuId(null);
                    onEditAssignment?.(openMenuId);
                  }}
                >
                  Edit Assignment
                </Button>
              )}
              {hasAssignmentPermission(openMenuId, 'assignment:hide') && (
                <Button
                  icon={assignment.isHidden ? 'show' : 'hide'}
                  design="Transparent"
                  onClick={() => {
                    setOpenMenuId(null);
                    onToggleAssignmentVisibility?.(openMenuId, !assignment.isHidden);
                  }}
                >
                  {assignment.isHidden ? 'Show Assignment' : 'Hide Assignment'}
                </Button>
              )}
              {hasAssignmentPermission(openMenuId, 'assignment:delete') && (
                <Button
                  icon="delete"
                  design="Transparent"
                  onClick={() => {
                    setOpenMenuId(null);
                    onDeleteAssignment?.(openMenuId);
                  }}
                >
                  Delete Assignment
                </Button>
              )}
            </>
          );
        })()}
      </ActionSheet>

      <MessageBox
        open={submitWarningOpen}
        onClose={onSubmitCancel}
        titleText="No Resubmission Allowed"
        type="Warning"
        actions={[
          <Button key="confirm" design="Emphasized" onClick={onSubmitConfirm}>
            Submit Final Answer
          </Button>,
          <Button key="cancel" design="Transparent" onClick={onSubmitCancel}>
            Cancel
          </Button>
        ]}
      >
        <Text style={{ fontSize: '14px', lineHeight: '1.4' }}>
          This assignment <strong>"{selectedAssignmentForSubmitDialog?.name || selectedAssignmentForSubmit}"</strong> does not allow
          resubmission.
          <br />
          Once you submit, you will not be able to make any changes or submit again.
        </Text>
      </MessageBox>

      <MessageBox
        open={deleteWarningOpen}
        onClose={onDeleteCancel}
        titleText="Delete Assignment"
        type="Warning"
        actions={[
          <Button key="delete" design="Negative" onClick={onDeleteConfirm}>
            Delete
          </Button>,
          <Button key="cancel" design="Transparent" onClick={onDeleteCancel}>
            Cancel
          </Button>
        ]}
      >
        <Text style={{ fontSize: '14px', lineHeight: '1.4' }}>
          Are you sure you want to permanently delete assignment{' '}
          <strong>"{selectedAssignmentForDeleteDialog?.name || selectedAssignmentForDelete}"</strong>?
          <br />
          This action cannot be undone and all related submissions will be lost.
        </Text>
      </MessageBox>
    </div>
  );
};

export default AssignmentsList;
