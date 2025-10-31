import { JupyterFrontEnd } from "@jupyterlab/application";
import { ReactWidget } from "@jupyterlab/apputils";
import React, { useEffect, useState, useCallback } from 'react';
import { ErrorBoundary } from '../components/ErrorBoundary';
import CreateAssignmentWizard from "../components/wizards/CreateAssignmentWizard";
import AssignmentsList, { AssignmentsListData } from "../components/AssignmentsList";
import TopBar from "../components/TopBar";
import ErrorDialog from "../components/dialogs/ErrorDialog";
import { JupyterLabThemeProvider } from '../utils/themeSync';
import { useCoursesStore } from '../stores/coursesStore';
import { useAssignmentsStore } from '../stores/assignmentsStore';
import { usePermissions } from '../hooks/usePermissions';
import { useAssignmentPermissions } from '../hooks/useAssignmentPermissions';
import { useErrorHandler } from '../hooks/useErrorHandler';
import { COMMAND_IDS } from '../constants';

const AssignmentsPage: React.FC<{ initialCourseId?: string; app?: JupyterFrontEnd }> = ({ initialCourseId, app }) => {
    const [currentCourseId, setCurrentCourseId] = useState(initialCourseId || '');
    const [createWizardOpen, setCreateWizardOpen] = useState(false);
    const [submitWarningOpen, setSubmitWarningOpen] = useState(false);
    const [selectedAssignmentForSubmit, setSelectedAssignmentForSubmit] = useState<string | null>(null);
    const [deleteWarningOpen, setDeleteWarningOpen] = useState(false);
    const [selectedAssignmentForDelete, setSelectedAssignmentForDelete] = useState<string | null>(null);

    const courses = useCoursesStore(state => state.courses);
    const coursesLoading = useCoursesStore(state => state.loading);
    const fetchCourses = useCoursesStore(state => state.fetchCourses);

    const assignments = useAssignmentsStore(state => state.assignments);
    const assignmentsPermissions = useAssignmentsStore(state => state.permissions);
    const loading = useAssignmentsStore(state => state.loading);
    const fetchingAssignments = useAssignmentsStore(state => state.fetchingAssignments);
    const fetchingSolutions = useAssignmentsStore(state => state.fetchingSolutions);
    const optimisticUpdates = useAssignmentsStore(state => state.optimisticUpdates);
    const fetchAssignments = useAssignmentsStore(state => state.fetchAssignments);
    const fetchAssignment = useAssignmentsStore(state => state.fetchAssignment);
    const submitAssignment = useAssignmentsStore(state => state.submitAssignment);
    const deleteAssignment = useAssignmentsStore(state => state.deleteAssignment);
    const setOptimisticStatus = useAssignmentsStore(state => state.setOptimisticStatus);
    const addFetchingAssignment = useAssignmentsStore(state => state.addFetchingAssignment);
    const removeFetchingAssignment = useAssignmentsStore(state => state.removeFetchingAssignment);
    const addFetchingSolution = useAssignmentsStore(state => state.addFetchingSolution);
    const removeFetchingSolution = useAssignmentsStore(state => state.removeFetchingSolution);

    const { hasCoursePermission } = usePermissions();
    const { hasAssignmentPermission } = useAssignmentPermissions();
    const { errorInfo, isErrorDialogOpen, showError, clearError } = useErrorHandler();

    useEffect(() => {
        if (initialCourseId) setCurrentCourseId(initialCourseId);
    }, [initialCourseId]);

    useEffect(() => {
        fetchCourses().catch(err => {
            showError(err, 'Load Courses Error', false);
        });
    }, [fetchCourses, showError]);

    useEffect(() => {
        if (currentCourseId) {
            fetchAssignments(currentCourseId).catch(err => {
                showError(err, 'Load Assignments Error', false);
            });
        }
    }, [currentCourseId, fetchAssignments, showError]);

    useEffect(() => {
        if (!currentCourseId && courses.length > 0) {
            setCurrentCourseId(courses[0].label);
        }
    }, [currentCourseId, courses]);

    const data: AssignmentsListData | null = currentCourseId
        ? {
              courseId: currentCourseId,
              courseTitle: currentCourseId,
              assignments,
              permissions: assignmentsPermissions || { global: [], scoped: {} }
          }
        : null;

    const handleCourseChange = useCallback((courseId: string) => {
        setCurrentCourseId(courseId);
    }, []);

    const handleStartAssignment = useCallback(async (id: string) => {
        if (!currentCourseId) return;
        const assignment = assignments.find(a => a.id === id);
        const status = optimisticUpdates[id] || assignment?.status;

        if (status && status !== 'NOT_STARTED') {
            try {
                await app?.commands.execute('filebrowser:open-path', {
                    path: `courses/${currentCourseId}/${id}`
                });
            } catch (e: any) {
                console.error('Failed to open assignment path', e);
            }
            return;
        }

        addFetchingAssignment(id);
        try {
            await fetchAssignment(currentCourseId, id);
            setOptimisticStatus(id, 'IN_PROGRESS');
            await fetchAssignments(currentCourseId);
            try {
                await app?.commands.execute('filebrowser:open-path', {
                    path: `courses/${currentCourseId}/${id}`
                });
            } catch (e: any) {
                console.error('Fetched but failed to open assignment path', e);
            }
        } catch (e: any) {
            showError(e, 'Start Assignment Error', true);
        } finally {
            removeFetchingAssignment(id);
        }
    }, [currentCourseId, assignments, optimisticUpdates, app, fetchAssignment, fetchAssignments, addFetchingAssignment, removeFetchingAssignment, setOptimisticStatus, showError]);

    const handleBackToCourses = useCallback(async () => {
        if (app) await app.commands.execute(COMMAND_IDS.openCoursesList);
    }, [app]);

    const handleSubmitAssignment = useCallback(async (id: string, force = false) => {
        if (!currentCourseId) return;
        const assignment = assignments.find(a => a.id === id);
        if (!assignment) return;

        const firstSubmission = !assignment.submission;
        if (!force && firstSubmission && assignment.allow_resubmission === false) {
            setSelectedAssignmentForSubmit(id);
            setSubmitWarningOpen(true);
            return;
        }

        try {
            await submitAssignment(currentCourseId, id);
            setSubmitWarningOpen(false);
            setSelectedAssignmentForSubmit(null);
            try {
                await app?.commands.execute('apputils:notify', {
                    message: 'Assignment submitted successfully',
                    type: 'success'
                });
            } catch {}
        } catch (e: any) {
            showError(e, 'Submit Assignment Error', true);
        }
    }, [currentCourseId, assignments, app, submitAssignment, showError]);

    const handleDeleteAssignment = useCallback(async (id: string, force = false) => {
        if (!currentCourseId) return;
        if (!force) {
            setSelectedAssignmentForDelete(id);
            setDeleteWarningOpen(true);
            return;
        }

        try {
            await deleteAssignment(currentCourseId, id);
            setDeleteWarningOpen(false);
            setSelectedAssignmentForDelete(null);
            try {
                await app?.commands.execute('apputils:notify', {
                    message: 'Assignment deleted',
                    type: 'success'
                });
            } catch {}
        } catch (e: any) {
            showError(e, 'Delete Assignment Error', true);
        }
    }, [currentCourseId, app, deleteAssignment, showError]);

    const handleFetchSolutions = useCallback(async (id: string) => {
        if (!currentCourseId) return;
        addFetchingSolution(id);
        try {
            await fetchAssignment(currentCourseId, id, true);
            try {
                await app?.commands.execute('filebrowser:open-path', {
                    path: `courses/${currentCourseId}/${id}/solution`
                });
            } catch {}
            try {
                await app?.commands.execute('apputils:notify', {
                    message: 'Solutions fetched',
                    type: 'success'
                });
            } catch {}
        } catch (e: any) {
            showError(e, 'Fetch Solutions Error', true);
        } finally {
            removeFetchingSolution(id);
        }
    }, [currentCourseId, app, fetchAssignment, addFetchingSolution, removeFetchingSolution, showError]);

    const handleRefreshAssignments = useCallback(() => {
        if (currentCourseId) {
            fetchAssignments(currentCourseId, true).catch(err => {
                showError(err, 'Refresh Assignments Error', true);
            });
        }
    }, [currentCourseId, fetchAssignments, showError]);

    return (
        <div
            style={{
                height: '100%',
                width: '100%',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                minHeight: 0,
                minWidth: 0,
                position: 'relative'
            }}
        >
            <div style={{ position: 'relative', height: '3rem', flexShrink: 0, zIndex: 100 }}>
                <TopBar />
            </div>
            <div style={{ flex: 1, overflow: 'hidden', minHeight: 0, minWidth: 0, width: '100%' }}>
                <AssignmentsList
                    currentCourseId={currentCourseId}
                    data={data}
                    coursesData={courses}
                    loading={loading}
                    coursesLoading={coursesLoading}
                    fetchingAssignments={fetchingAssignments}
                    optimisticUpdates={optimisticUpdates}
                    hasCoursePermission={hasCoursePermission}
                    hasAssignmentPermission={hasAssignmentPermission}
                    onCourseChange={handleCourseChange}
                    onStartAssignment={handleStartAssignment}
                    onResetAssignment={(id) => {
                        console.log('Reset', id);
                    }}
                    onSubmitAssignment={handleSubmitAssignment}
                    onFetchSolutions={handleFetchSolutions}
                    onEditAssignment={(id) => {
                        console.log('Edit assignment', id);
                    }}
                    onDeleteAssignment={handleDeleteAssignment}
                    onToggleAssignmentVisibility={(id, hidden) => {
                        console.log('Toggle visibility', id, hidden);
                    }}
                    onCreateAssignment={() => setCreateWizardOpen(true)}
                    onViewSubmissions={(id) => {
                        console.log('View submissions', id);
                    }}
                    onBackToCourses={handleBackToCourses}
                    onRefreshAssignments={handleRefreshAssignments}
                    fetchingSolutions={fetchingSolutions}
                    submitWarningOpen={submitWarningOpen}
                    selectedAssignmentForSubmit={selectedAssignmentForSubmit}
                    deleteWarningOpen={deleteWarningOpen}
                    selectedAssignmentForDelete={selectedAssignmentForDelete}
                    onSubmitConfirm={() => {
                        if (selectedAssignmentForSubmit) handleSubmitAssignment(selectedAssignmentForSubmit, true);
                    }}
                    onSubmitCancel={() => {
                        setSubmitWarningOpen(false);
                    }}
                    onDeleteConfirm={() => {
                        if (selectedAssignmentForDelete) handleDeleteAssignment(selectedAssignmentForDelete, true);
                    }}
                    onDeleteCancel={() => {
                        setDeleteWarningOpen(false);
                        setSelectedAssignmentForDelete(null);
                    }}
                />
            </div>
            <CreateAssignmentWizard
                open={createWizardOpen}
                onClose={() => setCreateWizardOpen(false)}
                onSave={(assignmentData) => {
                    console.log('Save assignment', assignmentData);
                    setCreateWizardOpen(false);
                    if (currentCourseId) {
                        fetchAssignments(currentCourseId).catch(err => {
                            showError(err, 'Load Assignments Error', false);
                        });
                    }
                }}
                app={app}
                courseId={currentCourseId}
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
                        if (currentCourseId) {
                            await fetchAssignments(currentCourseId);
                        } else {
                            await fetchCourses();
                        }
                        clearError();
                    } catch (err) {
                        const wasListingError = errorInfo?.title?.includes('Load Courses') || errorInfo?.title?.includes('Load Assignments');
                        showError(err, errorInfo?.title || 'Error', !wasListingError);
                    }
                }}
            />
        </div>
    );
};

export class AssignmentsListWidget extends ReactWidget {
    private app: JupyterFrontEnd;
    private courseId?: string;

    constructor(app: JupyterFrontEnd, courseId?: string) {
        super();
        this.app = app;
        this.courseId = courseId;
        this.addClass('bytegrader-assignments-list-widget');
        this.title.label = 'Assignments';
        this.title.caption = 'View and manage assignments';
        this.title.closable = true;
    }

    setCourse(courseId: string): void {
        this.courseId = courseId;
        this.title.label = `Assignments - ${courseId}`;
        this.update();
    }

    render(): JSX.Element {
        return (
            <ErrorBoundary>
                <JupyterLabThemeProvider>
                    <AssignmentsPage initialCourseId={this.courseId} app={this.app} />
                </JupyterLabThemeProvider>
            </ErrorBoundary>
        );
    }
}
