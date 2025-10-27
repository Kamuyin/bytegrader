import React, { useEffect, useMemo, useCallback, useState } from 'react';
import {
    Card, Button, ActionSheet, FlexBox, FlexBoxDirection, FlexBoxJustifyContent, FlexBoxAlignItems,
    Title, Text, ProgressIndicator, CheckBox, Icon, IllustratedMessage
} from '@ui5/webcomponents-react';
import '@ui5/webcomponents-icons/dist/overflow.js';
import '@ui5/webcomponents-icons/dist/group.js';
import '@ui5/webcomponents-icons/dist/edit.js';
import '@ui5/webcomponents-icons/dist/delete.js';
import '@ui5/webcomponents-icons/dist/status-positive.js';
import '@ui5/webcomponents-icons/dist/hide.js';
import '@ui5/webcomponents-icons/dist/error.js';
import '@ui5/webcomponents-icons/dist/refresh.js';
import '@ui5/webcomponents-icons/dist/course-book.js';
import '@ui5/webcomponents-icons/dist/task.js';
import '@ui5/webcomponents-icons/dist/person-placeholder.js';
import '@ui5/webcomponents-fiori/dist/illustrations/EmptyList.js';
import EnrollmentsDialog from './dialogs/EnrollmentsDialog';
import EditCourseDialog from './dialogs/EditCourseDialog';
import CreateCourseDialog from './dialogs/CreateCourseDialog';
import ConfirmationDialog from './dialogs/ConfirmationDialog';
import ErrorDialog from './dialogs/ErrorDialog';
import { Course } from '../types/api';
import { useCoursesStore } from '../stores/coursesStore';
import { usePermissions } from '../hooks/usePermissions';
import { useErrorHandler } from '../hooks/useErrorHandler';
import { RoleBadge, InactiveBadge, ProgressBadge } from './shared/Badges';
import { LoadingState } from './shared/LoadingStates';

interface CoursesListPageProps {
    onCreateCourse?: () => void;
    onEditCourse?: (courseId: string) => void;
    onDeleteCourse?: (courseId: string) => void;
    onCourseClick?: (courseId: string) => void;
}

const CoursesListPage: React.FC<CoursesListPageProps> = ({
    onCreateCourse,
    onEditCourse,
    onDeleteCourse,
    onCourseClick
}) => {
    const courses = useCoursesStore(state => state.courses);
    const loading = useCoursesStore(state => state.loading);
    const fetchCourses = useCoursesStore(state => state.fetchCourses);
    const createCourse = useCoursesStore(state => state.createCourse);
    const updateCourse = useCoursesStore(state => state.updateCourse);
    const deleteCourse = useCoursesStore(state => state.deleteCourse);

    const { hasCoursePermission, hasGlobalPermission } = usePermissions();
    const { errorInfo, isErrorDialogOpen, showError, clearError } = useErrorHandler();

    const [openPopover, setOpenPopover] = useState<string | null>(null);
    const [popoverOpener, setPopoverOpener] = useState<HTMLElement | null>(null);
    const [enrollmentsDialogOpen, setEnrollmentsDialogOpen] = useState(false);
    const [selectedCourseForEnrollments, setSelectedCourseForEnrollments] = useState<string | null>(null);
    const [editCourseDialogOpen, setEditCourseDialogOpen] = useState(false);
    const [selectedCourseForEdit, setSelectedCourseForEdit] = useState<string | null>(null);
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
    const [selectedCourseForDelete, setSelectedCourseForDelete] = useState<string | null>(null);
    const [createCourseDialogOpen, setCreateCourseDialogOpen] = useState(false);
    const [showInactiveCourses, setShowInactiveCourses] = useState(false);

    useEffect(() => {
        fetchCourses().catch(err => {
            showError(err, 'Load Courses Error', false);
        });
    }, [fetchCourses, showError]);

    const filteredCourses = useMemo(() =>
        courses.filter(course => course.active !== false || showInactiveCourses),
        [courses, showInactiveCourses]
    );

    const getRoleBadgeForCourse = useCallback((course: Course) => {
        const isInstructor = hasCoursePermission(course.label, 'course:edit') ||
                            hasCoursePermission(course.label, 'course:delete') ||
                            hasCoursePermission(course.label, 'assignment:create');
        return <RoleBadge role={isInstructor ? 'instructor' : 'student'} />;
    }, [hasCoursePermission]);

    const activeCourseCount = useMemo(() =>
        courses.filter(course => course.active !== false).length,
        [courses]
    );

    const inactiveCourseCount = useMemo(() =>
        courses.filter(course => course.active === false).length,
        [courses]
    );

    const handleCourseClick = useCallback((course: Course) =>
        onCourseClick?.(course.label),
        [onCourseClick]
    );

    const handleMenuClick = useCallback((event: any, courseLabel: string) => {
        event.stopPropagation();
        setPopoverOpener(event.currentTarget as HTMLElement);
        setOpenPopover(courseLabel);
    }, []);

    const handleMenuItemClick = useCallback((action: 'edit' | 'delete' | 'enrollments', courseLabel: string) => {
        setOpenPopover(null);
        if (action === 'edit') {
            setSelectedCourseForEdit(courseLabel);
            setEditCourseDialogOpen(true);
        } else if (action === 'delete') {
            setSelectedCourseForDelete(courseLabel);
            setDeleteConfirmOpen(true);
        } else {
            setSelectedCourseForEnrollments(courseLabel);
            setEnrollmentsDialogOpen(true);
        }
    }, []);

    const handleSaveCourse = useCallback(async (courseData: Partial<Course>) => {
        if (selectedCourseForEdit) {
            try {
                await updateCourse(selectedCourseForEdit, courseData);
            } catch (err) {
                showError(err, 'Update Course Error', true);
            }
        }
    }, [updateCourse, selectedCourseForEdit, showError]);

    const handleCreateCourse = useCallback(async (courseData: {
        label: string;
        title: string;
        lti_id: string;
        active: boolean;
    }) => {
        try {
            await createCourse(courseData);
        } catch (err) {
            showError(err, 'Create Course Error', true);
        }
    }, [createCourse, showError]);

    const handleDeleteConfirm = useCallback(async () => {
        if (selectedCourseForDelete) {
            try {
                await deleteCourse(selectedCourseForDelete);
                setDeleteConfirmOpen(false);
                setSelectedCourseForDelete(null);
            } catch (err) {
                showError(err, 'Delete Course Error', true);
            }
        }
    }, [deleteCourse, selectedCourseForDelete, showError]);

    const handleDeleteCancel = useCallback(() => {
        setDeleteConfirmOpen(false);
        setSelectedCourseForDelete(null);
    }, []);

    const handleCreateCourseClick = useCallback(() => {
        setCreateCourseDialogOpen(true);
    }, []);

    const selectedCourse = courses.find(c => c.label === selectedCourseForEnrollments);
    const selectedCourseForEditDialog = courses.find(c => c.label === selectedCourseForEdit);
    const selectedCourseForDeleteDialog = courses.find(c => c.label === selectedCourseForDelete);

    if (loading) {
        return <LoadingState message="Loading courses..." />;
    }

    return (
        <div
            style={{
                height: '100%',
                width: '100%',
                display: 'flex',
                flexDirection: 'column',
                overflowX: 'hidden',
                overflowY: 'hidden',
                minHeight: 0,
                minWidth: 0,
                position: 'relative'
            }}
            role="main"
            aria-label="Courses list"
        >
            <header
                style={{
                    position: 'sticky',
                    top: 0,
                    zIndex: 10,
                    backgroundColor: 'var(--sapBackgroundColor)',
                    borderBottom: '1px solid var(--sapGroup_TitleBorderColor)',
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
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            gap: '16px',
                            flexWrap: 'wrap',
                            width: '100%'
                        }}
                    >
                        <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '12px', minWidth: 0 }}>
                            <Icon name="course-book" style={{ fontSize: '24px', color: 'var(--sapAccentColor7)', flexShrink: 0 }} />
                            <Title style={{ fontSize: '2rem', fontWeight: '600', margin: 0, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                My Courses
                            </Title>
                        </FlexBox>
                        {hasGlobalPermission('course:create') && (
                            <Button
                                design="Emphasized"
                                onClick={handleCreateCourseClick}
                                style={{ borderRadius: '8px', fontWeight: '600' }}
                            >
                                Create Course
                            </Button>
                        )}
                    </div>

                    <div
                        style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            gap: '16px',
                            flexWrap: 'wrap',
                            width: '100%'
                        }}
                    >
                        <div
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '16px',
                                flexWrap: 'wrap'
                            }}
                        >
                            <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '8px' }}>
                                <Icon name="status-positive" style={{ fontSize: '14px', color: 'var(--sapSuccessColor)' }} />
                                <Text style={{ fontSize: '14px', color: '#666' }}>
                                    {activeCourseCount} active course{activeCourseCount !== 1 ? 's' : ''}
                                </Text>
                            </FlexBox>
                            {inactiveCourseCount > 0 && (
                                <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '8px' }}>
                                    <Icon name="hide" style={{ fontSize: '14px', color: 'var(--sapCriticalColor)' }} />
                                    <Text style={{ fontSize: '14px', color: '#666' }}>{inactiveCourseCount} inactive</Text>
                                </FlexBox>
                            )}
                        </div>

                        {inactiveCourseCount > 0 && (
                            <CheckBox
                                checked={showInactiveCourses}
                                onChange={(e) => setShowInactiveCourses(e.target.checked)}
                                text="Show inactive courses"
                            />
                        )}
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
                    data-scroll-container
                    style={{
                        flex: 1,
                        overflowY: filteredCourses.length === 0 ? 'hidden' : 'auto',
                        overflowX: 'hidden',
                        paddingTop: '16px',
                        paddingBottom: '8px',
                        minHeight: 0,
                        minWidth: 0
                    }}
                >
                    {filteredCourses.length === 0 ? (
                        <div style={{ flex: 1, width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px', padding: '24px' }}>
                            <IllustratedMessage 
                                name="EmptyList"
                                titleText={showInactiveCourses ? 'No courses found' : 'No active courses found'}
                                subtitleText={showInactiveCourses ? 'There are no courses available at the moment.' : 'You don\'t have any active courses. Check the "Show inactive courses" option to see all courses.'}
                            />
                        </div>
                    ) : (
                        <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '16px', paddingBottom: '16px', width: '100%', minWidth: 0 }}>
                            {filteredCourses.map((course) => (
                                <Card
                                    key={course.label}
                                    onClick={() => handleCourseClick(course)}
                                    role="button"
                                    tabIndex={0}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' || e.key === ' ') {
                                            e.preventDefault();
                                            handleCourseClick(course);
                                        }
                                    }}
                                    aria-label={`Open course ${course.title}`}
                                    style={{
                                        cursor: 'pointer',
                                        width: '100%',
                                        maxWidth: '100%',
                                        minWidth: 0,
                                        opacity: course.active === false ? 0.85 : 1,
                                        border: '1px solid var(--sapGroup_TitleBorderColor)',
                                        borderRadius: '12px',
                                        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
                                        boxSizing: 'border-box'
                                    }}
                                    header={
                                        <FlexBox
                                            justifyContent={FlexBoxJustifyContent.SpaceBetween}
                                            alignItems={FlexBoxAlignItems.Center}
                                            style={{
                                                padding: '16px 20px',
                                                backgroundColor: 'var(--sapObjectHeader_Background)',
                                                borderRadius: '12px 12px 0 0',
                                                borderBottom: '1px solid var(--sapGroup_TitleBorderColor)',
                                                minWidth: 0,
                                                overflow: 'hidden'
                                            }}
                                        >
                                            <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '12px', flex: 1, minWidth: 0, overflow: 'hidden' }}>
                                                <FlexBox
                                                    alignItems={FlexBoxAlignItems.Center}
                                                    style={{
                                                        width: '40px',
                                                        height: '40px',
                                                        backgroundColor: hasCoursePermission(course.label, 'course:edit')
                                                            ? 'var(--sapAccentColor1)'
                                                            : 'var(--sapAccentColor8)',
                                                        borderRadius: '50%',
                                                        justifyContent: 'center',
                                                        flexShrink: 0
                                                    }}
                                                >
                                                    <Icon name="course-book" style={{ fontSize: '18px', color: 'white' }} />
                                                </FlexBox>
                                                <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '4px', flex: 1, minWidth: 0, overflow: 'hidden' }}>
                                                    <Title
                                                        level="H4"
                                                        style={{
                                                            fontSize: '18px',
                                                            fontWeight: '700',
                                                            color: 'var(--sapGroup_TitleTextColor)',
                                                            lineHeight: '1.2',
                                                            margin: '0',
                                                            overflow: 'hidden',
                                                            textOverflow: 'ellipsis',
                                                            whiteSpace: 'nowrap',
                                                            maxWidth: '100%'
                                                        }}
                                                    >
                                                        {course.title}
                                                    </Title>
                                                    <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '6px' }}>
                                                        <Icon name="task" style={{ fontSize: '12px', color: '#666' }} />
                                                        <Text style={{ fontSize: '13px', color: '#666', fontWeight: '500' }}>
                                                            Course ID: {course.label}
                                                        </Text>
                                                    </FlexBox>
                                                </FlexBox>
                                            </FlexBox>
                                            <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '12px', flexShrink: 0, flexWrap: 'wrap' }}>
                                                {getRoleBadgeForCourse(course)}
                                                {course.active === false && <InactiveBadge />}
                                                <ProgressBadge progress={course.progress} />
                                                {hasCoursePermission(course.label, 'course:edit') && (
                                                    <Button
                                                        icon="overflow"
                                                        design="Transparent"
                                                        onClick={(event) => handleMenuClick(event, course.label)}
                                                        aria-label={`More actions for ${course.title}`}
                                                        style={{ borderRadius: '50%', width: '32px', height: '32px' }}
                                                    />
                                                )}
                                            </FlexBox>
                                        </FlexBox>
                                    }
                                >
                                    <FlexBox direction={FlexBoxDirection.Column} style={{ padding: '20px', gap: '16px' }}>
                                        <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '8px' }}>
                                            <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '8px' }}>
                                                <Icon name="status-positive" style={{ fontSize: '14px', color: 'var(--sapAccentColor6)' }} />
                                                <Text style={{ fontSize: '13px', color: 'var(--sapGroup_TitleTextColor)', fontWeight: '700' }}>
                                                    Course Progress
                                                </Text>
                                            </FlexBox>
                                            <ProgressIndicator
                                                value={course.progress}
                                                valueState={course.progress < 30 ? 'Negative' : course.progress < 70 ? 'Critical' : 'Positive'}
                                                style={{ height: '8px', borderRadius: '4px' }}
                                            />
                                        </FlexBox>
                                        <FlexBox justifyContent={FlexBoxJustifyContent.SpaceBetween} alignItems={FlexBoxAlignItems.Center} style={{ gap: '16px' }}>
                                            <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '8px', flex: 1 }}>
                                                <Icon name="person-placeholder" style={{ fontSize: '14px', color: '#666' }} />
                                                <Text style={{ fontSize: '13px', color: '#666', fontWeight: '500' }}>
                                                    {course.instructors.join(', ')}
                                                </Text>
                                            </FlexBox>
                                            {course.student_count !== null && (
                                                <FlexBox
                                                    alignItems={FlexBoxAlignItems.Center}
                                                    style={{
                                                        backgroundColor: 'var(--sapAccentColor1)',
                                                        color: 'white',
                                                        padding: '8px 16px',
                                                        borderRadius: '20px',
                                                        gap: '6px'
                                                    }}
                                                >
                                                    <Icon name="group" style={{ fontSize: '14px' }} />
                                                    <Text style={{ fontSize: '14px', fontWeight: '700' }}>Students: {course.student_count}</Text>
                                                </FlexBox>
                                            )}
                                        </FlexBox>
                                    </FlexBox>
                                </Card>
                            ))}
                        </FlexBox>
                    )}
                </div>
            </div>

            <ActionSheet open={!!openPopover} opener={popoverOpener || undefined} onClose={() => setOpenPopover(null)} aria-label="Course actions menu">
                {openPopover && hasCoursePermission(openPopover, 'course:enrollments') && (
                    <Button icon="group" design="Transparent" onClick={() => openPopover && handleMenuItemClick('enrollments', openPopover)}>
                        Enrollments
                    </Button>
                )}
                {openPopover && hasCoursePermission(openPopover, 'course:edit') && (
                    <Button icon="edit" design="Transparent" onClick={() => openPopover && handleMenuItemClick('edit', openPopover)}>
                        Edit
                    </Button>
                )}
                {openPopover && hasCoursePermission(openPopover, 'course:delete') && (
                    <Button icon="delete" design="Transparent" onClick={() => openPopover && handleMenuItemClick('delete', openPopover)}>
                        Delete
                    </Button>
                )}
            </ActionSheet>

            <EnrollmentsDialog
                open={enrollmentsDialogOpen}
                onClose={() => setEnrollmentsDialogOpen(false)}
                course={selectedCourse || null}
                userRole={selectedCourse ? (hasCoursePermission(selectedCourse.label, 'course:edit') ? 'instructor' : 'student') : 'student'}
            />
            <CreateCourseDialog
                open={createCourseDialogOpen}
                onClose={() => setCreateCourseDialogOpen(false)}
                onSave={handleCreateCourse}
            />
            <EditCourseDialog
                open={editCourseDialogOpen}
                onClose={() => {
                    setEditCourseDialogOpen(false);
                    setSelectedCourseForEdit(null);
                }}
                course={selectedCourseForEditDialog || null}
                onSave={handleSaveCourse}
            />
            <ConfirmationDialog
                open={deleteConfirmOpen}
                onClose={handleDeleteCancel}
                onConfirm={handleDeleteConfirm}
                title="Delete Course"
                message={`Are you sure you want to delete the course "${selectedCourseForDeleteDialog?.title || selectedCourseForDelete}"?\n\nThis action cannot be undone and will permanently remove the course and all associated data.`}
                confirmText="Delete"
                cancelText="Cancel"
                confirmDesign="Negative"
                type="Warning"
            />
            
            <ErrorDialog
                open={isErrorDialogOpen}
                onClose={clearError}
                title={errorInfo?.title}
                message={errorInfo?.message || ''}
                details={errorInfo?.details}
                closable={errorInfo?.closable ?? true}
                onRetry={async () => {
                    try {
                        await fetchCourses();
                        clearError();
                    } catch (err) {
                        showError(err, 'Load Courses Error', false);
                    }
                }}
            />
        </div>
    );
};

export default CoursesListPage;
