import React, { useState, useCallback, useMemo } from 'react';
import {
    Button,
    FlexBox,
    Toolbar,
    Card,
    CardHeader,
    FlexBoxDirection,
    FlexBoxJustifyContent,
    FlexBoxAlignItems,
    Title,
    Text,
    Input,
    TextArea,
    DatePicker,
    MessageStrip,
    Icon,
    Switch,
    BusyIndicator,
    Select,
    Option,
    Dialog,
    Label,
    ToolbarSeparator,
    Panel,
} from '@ui5/webcomponents-react';
import { JupyterFrontEnd } from '@jupyterlab/application';
import '@ui5/webcomponents-icons/dist/product.js';
import '@ui5/webcomponents-icons/dist/hint.js';
import '@ui5/webcomponents-icons/dist/action-settings.js';
import '@ui5/webcomponents-icons/dist/save.js';
import '@ui5/webcomponents-icons/dist/decline.js';
import '@ui5/webcomponents-icons/dist/navigation-right-arrow.js';
import '@ui5/webcomponents-icons/dist/navigation-left-arrow.js';
import '@ui5/webcomponents-icons/dist/open-folder.js';
import '@ui5/webcomponents-icons/dist/process.js';
import '@ui5/webcomponents-icons/dist/detail-view.js';
import '@ui5/webcomponents-icons/dist/folder.js';
import '@ui5/webcomponents-icons/dist/document.js';
import '@ui5/webcomponents-icons/dist/picture.js';
import '@ui5/webcomponents-icons/dist/add-folder.js';
import '@ui5/webcomponents-icons/dist/add-document.js';
import '@ui5/webcomponents-icons/dist/delete.js';
import '@ui5/webcomponents-icons/dist/attachment.js';
import FilePickerDialog from '../dialogs/FilePickerDialog';
import WidgetModal from '../dialogs/WidgetModal';
import ErrorDialog from '../dialogs/ErrorDialog';
import { requestAPI } from '../../utils';
import { GeneratePreviewResponse, APIResponse } from '../../types/api';
import { useErrorHandler } from '../../hooks/useErrorHandler';

// Types
interface FileNode {
    id: string;
    name: string;
    type: 'notebook' | 'asset';
    path: string; // relative path within assignment
    sourcePath: string; // absolute path in JupyterLab
}

interface DirectoryNode {
    id: string;
    name: string;
    type: 'directory';
    path: string;
    children: (DirectoryNode | FileNode)[];
}

type FileSystemNode = DirectoryNode | FileNode;

interface AssignmentData {
    name: string;
    description: string;
    dueDate?: string;
    visible: boolean;
    allowResubmissions: boolean;
    allowLateSubmissions: boolean;
    ltiSyncEnabled: boolean;
    showSolution: SolutionVisibility;
    fileSystem: DirectoryNode;
}

interface CreateAssignmentWizardProps {
    open: boolean;
    onClose: () => void;
    onSave?: (assignmentData: AssignmentData) => void;
    app?: JupyterFrontEnd;
    courseId: string;
}

interface SelectedFile {
    name: string;
    path: string;
}

type WizardStep = 'basic-info' | 'assignment-details' | 'design-assignment' | 'generate-review' | 'review';

type SolutionVisibility = 'never' | 'after-due-date' | 'after-submission' | 'after-completion';

interface StepConfig {
    key: WizardStep;
    title: string;
    icon: string;
}

// Constants
const INITIAL_FILE_SYSTEM: DirectoryNode = {
    id: 'root',
    name: 'assignment',
    type: 'directory',
    path: '',
    children: []
};

const INITIAL_ASSIGNMENT_DATA: AssignmentData = {
    name: '',
    description: '',
    dueDate: '',
    visible: true,
    allowResubmissions: false,
    allowLateSubmissions: false,
    ltiSyncEnabled: false,
    showSolution: 'never',
    fileSystem: INITIAL_FILE_SYSTEM
};

const WIZARD_STEPS: StepConfig[] = [
    { key: 'basic-info', title: 'Basic Information', icon: 'product' },
    { key: 'assignment-details', title: 'Assignment Details', icon: 'hint' },
    { key: 'design-assignment', title: 'Design Assignment', icon: 'action-settings' },
    { key: 'generate-review', title: 'Generate & Review', icon: 'process' },
    { key: 'review', title: 'Final Review', icon: 'save' }
];

const SOLUTION_VISIBILITY_OPTIONS = [
    { value: 'never', label: 'Never', description: 'Solutions are never shown to students' },
    { value: 'after-due-date', label: 'After Due Date', description: 'Solutions are shown after the assignment due date' },
    { value: 'after-submission', label: 'After Submission', description: 'Solutions are shown after student submits their work' },
    { value: 'after-completion', label: 'After Completion', description: 'Solutions are shown after assignment is marked as complete' }
];

// Utility Functions
let idCounter = 0;
const generateId = (): string => `node-${idCounter++}`;

const findNode = (node: FileSystemNode, id: string): FileSystemNode | null => {
    if (node.id === id) return node;
    if (node.type === 'directory') {
        for (const child of node.children) {
            const found = findNode(child, id);
            if (found) return found;
        }
    }
    return null;
};

const addDirectory = (fileSystem: DirectoryNode, parentId: string, name: string): DirectoryNode => {
    const newDir: DirectoryNode = {
        id: generateId(),
        name,
        type: 'directory',
        path: parentId === 'root' ? name : `${findNode(fileSystem, parentId)?.path}/${name}`,
        children: []
    };
    if (parentId === 'root') {
        return { ...fileSystem, children: [...fileSystem.children, newDir] };
    } else {
        const parent = findNode(fileSystem, parentId) as DirectoryNode;
        if (parent && parent.type === 'directory') {
            const updatedParent = { ...parent, children: [...parent.children, newDir] };
            return updateNode(fileSystem, parentId, updatedParent) as DirectoryNode;
        }
        return fileSystem;
    }
};

const addFile = (fileSystem: DirectoryNode, parentId: string, file: { name: string; type: 'notebook' | 'asset'; sourcePath: string }): DirectoryNode => {
    const parentPath = parentId === 'root' ? '' : findNode(fileSystem, parentId)?.path || '';
    const newFile: FileNode = {
        id: generateId(),
        name: file.name,
        type: file.type,
        path: parentPath ? `${parentPath}/${file.name}` : file.name,
        sourcePath: file.sourcePath
    };
    if (parentId === 'root') {
        return { ...fileSystem, children: [...fileSystem.children, newFile] };
    } else {
        const parent = findNode(fileSystem, parentId) as DirectoryNode;
        if (parent && parent.type === 'directory') {
            const updatedParent = { ...parent, children: [...parent.children, newFile] };
            return updateNode(fileSystem, parentId, updatedParent) as DirectoryNode;
        }
        return fileSystem;
    }
};

const removeNode = (fileSystem: DirectoryNode, nodeId: string): DirectoryNode => {
    if (fileSystem.id === nodeId) return fileSystem;
    return {
        ...fileSystem,
        children: fileSystem.children.filter(child => child.id !== nodeId).map(child =>
            child.type === 'directory' ? removeNode(child as DirectoryNode, nodeId) : child
        )
    };
};

const updateNode = (node: FileSystemNode, targetId: string, updatedNode: FileSystemNode): FileSystemNode => {
    if (node.id === targetId) return updatedNode;
    if (node.type === 'directory') {
        return {
            ...node,
            children: node.children.map(child => updateNode(child, targetId, updatedNode))
        };
    }
    return node;
};

const extractNotebooksAndAssets = (fileSystem: DirectoryNode) => {
    const notebooks: { rel: string; abs: string }[] = [];
    const assets: { rel: string; abs: string }[] = [];

    const traverse = (node: FileSystemNode) => {
        if (node.type === 'notebook') {
            notebooks.push({ rel: node.path, abs: (node as FileNode).sourcePath });
        } else if (node.type === 'asset') {
            assets.push({ rel: node.path, abs: (node as FileNode).sourcePath });
        } else if (node.type === 'directory') {
            node.children.forEach(traverse);
        }
    };

    fileSystem.children.forEach(traverse);
    return { notebooks, assets };
};

const hasNotebooks = (fileSystem: DirectoryNode): boolean => {
    return fileSystem.children.some(child => child.type === 'notebook' || (child.type === 'directory' && hasNotebooks(child as DirectoryNode)));
};

// Component
const CreateAssignmentWizard: React.FC<CreateAssignmentWizardProps> = ({
    open,
    onClose,
    onSave,
    app,
    courseId
}) => {
    // State
    const [currentStep, setCurrentStep] = useState<WizardStep>('basic-info');
    const [assignmentData, setAssignmentData] = useState<AssignmentData>(INITIAL_ASSIGNMENT_DATA);
    const [filePickerOpen, setFilePickerOpen] = useState(false);
    const [addType, setAddType] = useState<'notebook' | 'asset' | null>(null);
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generationComplete, setGenerationComplete] = useState(false);
    const [previewData, setPreviewData] = useState<any | null>(null);
    const [newDirName, setNewDirName] = useState('');
    const [dirDialogOpen, setDirDialogOpen] = useState(false);

    const { errorInfo, isErrorDialogOpen, showError, clearError } = useErrorHandler();

    const currentStepIndex = useMemo(
        () => WIZARD_STEPS.findIndex(step => step.key === currentStep),
        [currentStep]
    );

    const isFirstStep = currentStepIndex === 0;
    const isLastStep = currentStepIndex === WIZARD_STEPS.length - 1;

    // Handlers
    const startNotebookGeneration = useCallback(async () => {
        setIsGenerating(true);
        setGenerationComplete(false);
        setPreviewData(null);
        try {
            const { notebooks, assets } = extractNotebooksAndAssets(assignmentData.fileSystem);
            const response = await requestAPI<GeneratePreviewResponse>(
                'bytegrader/generate_assignment',
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ notebooks, assets })
                }
            );
            if (response.success && response.data) {
                setPreviewData(response.data);
                setGenerationComplete(true);
            } else {
                throw new Error(response.error || 'Preview generation failed');
            }
        } catch (error) {
            showError(error, 'Generate Preview Error', true);
            setGenerationComplete(false);
        } finally {
            setIsGenerating(false);
        }
    }, [assignmentData.fileSystem, showError]);

    const handleNext = useCallback(() => {
        if (!isLastStep) {
            const nextStepIndex = currentStepIndex + 1;
            const nextStep = WIZARD_STEPS[nextStepIndex].key;
            if (nextStep === 'generate-review') {
                setCurrentStep(nextStep);
                startNotebookGeneration();
            } else {
                setCurrentStep(nextStep);
            }
        }
    }, [isLastStep, currentStepIndex, startNotebookGeneration]);

    const openNotebooksInJupyterLab = useCallback(async () => {
        if (!previewData?.base_dir || !app) {
            app?.commands.execute('apputils:notify', {
                message: 'No preview data available or JupyterLab unavailable',
                type: 'warning'
            });
            return;
        }
        try {
            await app.commands.execute('filebrowser:open-path', { path: previewData.base_dir });
            app.commands.execute('apputils:notify', {
                message: 'Preview notebooks opened in JupyterLab!',
                type: 'success'
            });
        } catch (error) {
            app.commands.execute('apputils:notify', {
                message: 'Failed to open notebooks in JupyterLab',
                type: 'error'
            });
        }
    }, [previewData, app]);

    const handlePrevious = useCallback(() => {
        if (!isFirstStep) {
            const prevStepIndex = currentStepIndex - 1;
            setCurrentStep(WIZARD_STEPS[prevStepIndex].key);
        }
    }, [isFirstStep, currentStepIndex]);

    const handleAddDirectory = useCallback(() => {
        setDirDialogOpen(true);
    }, []);

    const handleDirDialogClose = useCallback(() => {
        setDirDialogOpen(false);
        setNewDirName('');
    }, []);

    const handleDirNameChange = useCallback((e: any) => {
        setNewDirName(e.target.value);
    }, []);

    const handleCreateDirectory = useCallback(() => {
        if (newDirName.trim()) {
            const parentId = selectedNodeId && findNode(assignmentData.fileSystem, selectedNodeId)?.type === 'directory' ? selectedNodeId : 'root';
            setAssignmentData(prev => ({
                ...prev,
                fileSystem: addDirectory(prev.fileSystem, parentId, newDirName.trim())
            }));
            handleDirDialogClose();
        }
    }, [newDirName, selectedNodeId, assignmentData.fileSystem, handleDirDialogClose]);

    const handleAddNotebooks = useCallback(() => {
        setAddType('notebook');
        setFilePickerOpen(true);
    }, []);

    const handleAddAssets = useCallback(() => {
        setAddType('asset');
        setFilePickerOpen(true);
    }, []);

    const handleFilesSelected = useCallback((files: SelectedFile[]) => {
        if (!addType) return;
        const parentId = selectedNodeId && findNode(assignmentData.fileSystem, selectedNodeId)?.type === 'directory' ? selectedNodeId : 'root';
        setAssignmentData(prev => {
            let updatedFileSystem = prev.fileSystem;
            files.forEach(file => {
                updatedFileSystem = addFile(updatedFileSystem, parentId, {
                    name: file.name,
                    type: addType,
                    sourcePath: file.path
                });
            });
            return { ...prev, fileSystem: updatedFileSystem };
        });
        setAddType(null);
        setFilePickerOpen(false);
    }, [selectedNodeId, addType, assignmentData.fileSystem]);

    const handleRemoveNode = useCallback((nodeId: string) => {
        setAssignmentData(prev => ({
            ...prev,
            fileSystem: removeNode(prev.fileSystem, nodeId)
        }));
        if (selectedNodeId === nodeId) {
            setSelectedNodeId(null);
        }
    }, [selectedNodeId]);

    const resetForm = useCallback(() => {
        setAssignmentData(INITIAL_ASSIGNMENT_DATA);
        setCurrentStep('basic-info');
        setFilePickerOpen(false);
        setAddType(null);
        setSelectedNodeId(null);
        setIsGenerating(false);
        setGenerationComplete(false);
        setPreviewData(null);
    }, []);

    const handleCancel = useCallback(() => {
        resetForm();
        onClose();
    }, [resetForm, onClose]);

    const handleFinalize = useCallback(async () => {
        const { notebooks, assets } = extractNotebooksAndAssets(assignmentData.fileSystem);
        const payload = {
            name: assignmentData.name,
            description: assignmentData.description,
            due_date: assignmentData.dueDate || null,
            visible: assignmentData.visible,
            allow_resubmission: assignmentData.allowResubmissions,
            allow_late_submission: assignmentData.allowLateSubmissions,
            show_solutions: assignmentData.showSolution.replace(/-/g, '_'),
            lti_sync: assignmentData.ltiSyncEnabled,
            notebooks,
            assets
        };
        try {
            const response = await requestAPI<APIResponse<any>>(
                `bytegrader/courses/${courseId}/assignments/create`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                }
            );
            if (response.success) {
                await app?.commands.execute('apputils:notify', {
                  message: 'Assignment created successfully!',
                  type: 'success'
                });
                onSave && onSave(assignmentData);
                handleCancel();
            } else {
                throw new Error(response.error || 'Assignment creation failed');
            }
        } catch (error) {
            showError(error, 'Create Assignment Error', true);
        }
    }, [assignmentData, courseId, app, onSave, handleCancel, showError]);

    // Step Validation
    const isStepValid = useMemo(() => {
        switch (currentStep) {
            case 'basic-info':
                return assignmentData.name.trim() !== '';
            case 'assignment-details':
                return true;
            case 'design-assignment':
                return hasNotebooks(assignmentData.fileSystem);
            case 'generate-review':
                return generationComplete;
            case 'review':
                return assignmentData.name.trim() !== '' && hasNotebooks(assignmentData.fileSystem);
            default:
                return false;
        }
    }, [currentStep, assignmentData.name, assignmentData.fileSystem, generationComplete]);

    // Input Handlers
    const handleNameChange = useCallback((e: any) => {
        setAssignmentData(prev => ({ ...prev, name: e.target.value }));
    }, []);

    const handleDescriptionChange = useCallback((e: any) => {
        setAssignmentData(prev => ({ ...prev, description: e.target.value }));
    }, []);

    const handleDueDateChange = useCallback((e: any) => {
        const dateValue = e.target.value;
        let isoDate: string;
        try {
            isoDate = new Date(dateValue).toISOString();
        } catch {
            isoDate = dateValue;
        }
        setAssignmentData(prev => ({ ...prev, dueDate: isoDate }));
    }, []);

    const handleAllowResubmissionsChange = useCallback((e: any) => {
        setAssignmentData(prev => ({ ...prev, allowResubmissions: e.target.checked }));
    }, []);

    const handleAllowLateSubmissionsChange = useCallback((e: any) => {
        setAssignmentData(prev => ({ ...prev, allowLateSubmissions: e.target.checked }));
    }, []);

    const handleLtiSyncChange = useCallback((e: any) => {
        setAssignmentData(prev => ({ ...prev, ltiSyncEnabled: e.target.checked }));
    }, []);

    const handleShowSolutionChange = useCallback((e: any) => {
        setAssignmentData(prev => ({ ...prev, showSolution: e.detail.selectedOption.value }));
    }, []);

    const handleTreeItemClick = useCallback((nodeId: string) => {
        setSelectedNodeId(nodeId);
    }, []);

    const renderTreeItems = useCallback((nodes: FileSystemNode[]): React.ReactNode[] => {
        return nodes.map(node => (
            <div key={node.id} style={{ cursor: 'pointer' }}>
                <FlexBox
                    alignItems={FlexBoxAlignItems.Center}
                    style={{
                        gap: '0.5rem',
                        padding: '0.25rem 0.5rem',
                        backgroundColor: selectedNodeId === node.id ? 'var(--sapSelectedColor)' : 'transparent',
                        borderRadius: '0.25rem'
                    }}
                    onClick={() => handleTreeItemClick(node.id)}
                >
                    <Icon
                        name={node.type === 'directory' ? 'folder' : node.type === 'notebook' ? 'document' : 'attachment'}
                        style={{ fontSize: '1rem' }}
                    />
                    <Text style={{ fontSize: '0.875rem' }}>{node.name}</Text>
                </FlexBox>
                {node.type === 'directory' && node.children.length > 0 && (
                    <div style={{ marginLeft: '1rem', borderLeft: '1px solid var(--sapContent_ForegroundBorderColor)', paddingLeft: '0.5rem' }}>
                        {renderTreeItems(node.children)}
                    </div>
                )}
            </div>
        ));
    }, [selectedNodeId, handleTreeItemClick]);

    const selectedNode = useMemo(() => {
        return selectedNodeId ? findNode(assignmentData.fileSystem, selectedNodeId) : null;
    }, [selectedNodeId, assignmentData.fileSystem]);

    const renderReviewTreeItems = useCallback((nodes: FileSystemNode[]): React.ReactNode[] => {
        return nodes.map(node => (
            <div key={node.id}>
                <FlexBox alignItems={FlexBoxAlignItems.Center} style={{
                    gap: '0.5rem',
                    marginBottom: '0.25rem',
                    padding: '0.25rem 0'
                }}>
                    <Icon
                        name={node.type === 'directory' ? 'folder' : node.type === 'notebook' ? 'document' : 'attachment'}
                        style={{ fontSize: '0.875rem', color: 'var(--sapContent_IconColor)' }}
                    />
                    <Text style={{ fontSize: '0.875rem' }}>
                        {node.name}
                        {node.type === 'directory' ? '/' : ''}
                    </Text>
                    {node.type !== 'directory' && (
                        <Text style={{ fontSize: '0.75rem', color: 'var(--sapContent_LabelColor)' }}>
                            ({node.type})
                        </Text>
                    )}
                </FlexBox>
                {node.type === 'directory' && node.children.length > 0 && (
                    <div style={{ marginLeft: '1rem', paddingLeft: '0.5rem', borderLeft: '1px solid var(--sapContent_ForegroundBorderColor)' }}>
                        {renderReviewTreeItems(node.children)}
                    </div>
                )}
            </div>
        ));
    }, []);

    const renderStepContent = useMemo(() => {
        switch (currentStep) {
            case 'basic-info':
                return (
                    <div style={{ display: 'flex', minHeight: '250px', flexDirection: 'column', gap: '20px' }}>
                        <Title level="H3">1. Basic Information</Title>
                        <MessageStrip>
                            The Assignment Creation Wizard will guide you through setting up a new assignment.
                        </MessageStrip>
                        <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '16px' }}>
                            <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '6px' }}>
                                <Text style={{ fontWeight: '600', fontSize: '14px' }}>
                                    Assignment Name <span style={{ color: '#e53e3e' }}>*</span>
                                </Text>
                                <Input
                                    value={assignmentData.name}
                                    onInput={handleNameChange}
                                    placeholder="Enter assignment name..."
                                    required
                                    style={{ width: '100%' }}
                                />
                            </FlexBox>
                            <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '12px' }}>
                                <Text style={{ fontWeight: '600', fontSize: '14px' }}>Assignment Settings</Text>
                                <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '12px' }}>
                                    <Switch
                                        checked={assignmentData.allowResubmissions}
                                        onChange={handleAllowResubmissionsChange}
                                    />
                                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '2px' }}>
                                        <Text style={{ fontWeight: '500' }}>Allow Resubmissions</Text>
                                        <Text style={{ fontSize: '12px', color: '#666' }}>
                                            Students can resubmit their work
                                        </Text>
                                    </FlexBox>
                                </FlexBox>
                                <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '12px' }}>
                                    <Switch
                                        checked={assignmentData.allowLateSubmissions}
                                        onChange={handleAllowLateSubmissionsChange}
                                    />
                                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '2px' }}>
                                        <Text style={{ fontWeight: '500' }}>Allow Late Submissions</Text>
                                        <Text style={{ fontSize: '12px', color: '#666' }}>
                                            Students can submit after the due date
                                        </Text>
                                    </FlexBox>
                                </FlexBox>
                                <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '12px' }}>
                                    <Switch
                                        checked={assignmentData.ltiSyncEnabled}
                                        onChange={handleLtiSyncChange}
                                    />
                                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '2px' }}>
                                        <Text style={{ fontWeight: '500' }}>LTI Synchronization</Text>
                                        <Text style={{ fontSize: '12px', color: '#666' }}>
                                            Sync grades with LMS
                                        </Text>
                                    </FlexBox>
                                </FlexBox>
                                <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '8px' }}>
                                    <Text style={{ fontWeight: '500' }}>Show Solution</Text>
                                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '6px' }}>
                                        <Select
                                            value={assignmentData.showSolution}
                                            onChange={handleShowSolutionChange}
                                            style={{ width: '300px' }}
                                        >
                                            {SOLUTION_VISIBILITY_OPTIONS.map(option => (
                                                <Option key={option.value} value={option.value}>
                                                    {option.label}
                                                </Option>
                                            ))}
                                        </Select>
                                        <Text style={{ fontSize: '12px', color: '#666' }}>
                                            {SOLUTION_VISIBILITY_OPTIONS.find(opt => opt.value === assignmentData.showSolution)?.description}
                                        </Text>
                                    </FlexBox>
                                </FlexBox>
                            </FlexBox>
                        </FlexBox>
                    </div>
                );

            case 'assignment-details':
                return (
                    <div style={{ display: 'flex', minHeight: '250px', flexDirection: 'column', gap: '20px' }}>
                        <Title level="H3">2. Assignment Details</Title>
                        <Text style={{ color: '#666' }}>
                            Provide additional details about the assignment. Both fields are optional.
                        </Text>
                        <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '16px' }}>
                            <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '6px' }}>
                                <Text style={{ fontWeight: '600', fontSize: '14px' }}>Description</Text>
                                <TextArea
                                    value={assignmentData.description}
                                    onInput={handleDescriptionChange}
                                    placeholder="Enter assignment description..."
                                    rows={4}
                                    style={{ width: '100%' }}
                                />
                            </FlexBox>
                            <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '6px' }}>
                                <Text style={{ fontWeight: '600', fontSize: '14px' }}>Due Date</Text>
                                <DatePicker
                                    value={assignmentData.dueDate}
                                    onChange={handleDueDateChange}
                                    placeholder="Select due date..."
                                    style={{ width: '300px' }}
                                />
                            </FlexBox>
                        </FlexBox>
                    </div>
                );

            case 'design-assignment':
                return (
                    <FlexBox direction={FlexBoxDirection.Column} style={{ height: '100%', gap: '1rem' }}>
                        <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.5rem' }}>
                            <Title level="H3">3. Design Assignment</Title>
                            <Text style={{ color: 'var(--sapContent_LabelColor)' }}>
                                Create the assignment structure by organizing notebooks and assets into directories.
                                Select a directory to add files into it, or add to the root level.
                            </Text>
                        </FlexBox>

                        <Panel
                            headerText="Assignment Structure"
                            collapsed={false}
                            style={{ flex: 1 }}
                        >
                            <FlexBox direction={FlexBoxDirection.Column} style={{ height: '100%' }}>
                                <Toolbar design="Transparent" style={{ marginBottom: '1rem' }}>
                                    <Button
                                        icon="add-folder"
                                        tooltip="Create New Directory"
                                        onClick={handleAddDirectory}
                                    >
                                        New Directory
                                    </Button>
                                    <ToolbarSeparator />
                                    <Button
                                        icon="add-document"
                                        tooltip="Add Jupyter Notebooks"
                                        onClick={handleAddNotebooks}
                                    >
                                        Add Notebooks
                                    </Button>
                                    <Button
                                        icon="attachment"
                                        tooltip="Add Asset Files"
                                        onClick={handleAddAssets}
                                    >
                                        Add Assets
                                    </Button>
                                    <ToolbarSeparator />
                                    <Button
                                        icon="delete"
                                        design="Negative"
                                        tooltip="Delete Selected Item"
                                        disabled={!selectedNodeId || selectedNodeId === 'root'}
                                        onClick={() => selectedNodeId && handleRemoveNode(selectedNodeId)}
                                    >
                                        Delete
                                    </Button>
                                </Toolbar>

                                <FlexBox direction={FlexBoxDirection.Row} style={{ flex: 1, gap: '1rem' }}>
                                    <Card style={{ flex: 2, minHeight: '400px' }}>
                                        <CardHeader titleText="File Structure" />
                                        <div style={{ padding: '1rem', height: '350px', overflow: 'auto' }}>
                                            <div style={{
                                                border: '1px solid var(--sapContent_ForegroundBorderColor)',
                                                borderRadius: '0.5rem',
                                                backgroundColor: 'var(--sapList_Background)',
                                                overflow: 'hidden'
                                            }}>
                                                <div
                                                    style={{
                                                        padding: '0.75rem 1rem',
                                                        borderBottom: '1px solid var(--sapContent_ForegroundBorderColor)',
                                                        cursor: 'pointer',
                                                        backgroundColor: selectedNodeId === 'root' ? 'var(--sapSelectedColor)' : 'var(--sapList_HeaderBackground)'
                                                    }}
                                                    onClick={() => handleTreeItemClick('root')}
                                                >
                                                    <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '0.5rem' }}>
                                                        <Icon name="folder" style={{ fontSize: '1.125rem', color: 'var(--sapContent_IconColor)' }} />
                                                        <Text style={{ fontSize: '1rem', fontWeight: '600' }}>{assignmentData.fileSystem.name}/</Text>
                                                        <Text style={{ fontSize: '0.75rem', color: 'var(--sapContent_LabelColor)' }}>(assignment root)</Text>
                                                    </FlexBox>
                                                </div>

                                                <div style={{ padding: '0.5rem' }}>
                                                    {assignmentData.fileSystem.children.length === 0 ? (
                                                        <FlexBox
                                                            direction={FlexBoxDirection.Column}
                                                            alignItems={FlexBoxAlignItems.Center}
                                                            justifyContent={FlexBoxJustifyContent.Center}
                                                            style={{ height: '200px', gap: '1rem' }}
                                                        >
                                                            <Icon name="folder" style={{ fontSize: '2.5rem', color: 'var(--sapContent_NonInteractiveIconColor)' }} />
                                                            <Text style={{ color: 'var(--sapContent_LabelColor)', textAlign: 'center', fontSize: '0.875rem' }}>
                                                                Empty assignment directory<br />
                                                                Click the "Add Notebooks" or "Add Assets" buttons above to get started
                                                            </Text>
                                                        </FlexBox>
                                                    ) : (
                                                        <div style={{ paddingLeft: '1rem' }}>
                                                            {renderTreeItems(assignmentData.fileSystem.children)}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </Card>

                                    <Card style={{ flex: 1, minHeight: '400px' }}>
                                        <CardHeader titleText="Selection Details" />
                                        <div style={{ padding: '1rem' }}>
                                            {selectedNode ? (
                                                <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '1rem' }}>
                                                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.5rem' }}>
                                                        <Text style={{ fontWeight: '600' }}>Selected Item</Text>
                                                        <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '0.5rem' }}>
                                                            <Icon name={selectedNode.type === 'directory' ? 'folder' : selectedNode.type === 'notebook' ? 'document' : 'attachment'} />
                                                            <Text>{selectedNode.name}</Text>
                                                        </FlexBox>
                                                    </FlexBox>

                                                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.5rem' }}>
                                                        <Text style={{ fontWeight: '600' }}>Type</Text>
                                                        <Text style={{ textTransform: 'capitalize' }}>{selectedNode.type}</Text>
                                                    </FlexBox>

                                                    {selectedNode.type !== 'directory' && (
                                                        <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.5rem' }}>
                                                            <Text style={{ fontWeight: '600' }}>Path in Assignment</Text>
                                                            <Text style={{ fontSize: '0.875rem', fontFamily: 'monospace' }}>
                                                                {selectedNode.path || '/'}
                                                            </Text>
                                                        </FlexBox>
                                                    )}

                                                    {selectedNode.type !== 'directory' && (
                                                        <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.5rem' }}>
                                                            <Text style={{ fontWeight: '600' }}>Source Location</Text>
                                                            <Text style={{ fontSize: '0.875rem', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                                                                {(selectedNode as FileNode).sourcePath}
                                                            </Text>
                                                        </FlexBox>
                                                    )}

                                                    {selectedNode.type === 'directory' && (
                                                        <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.5rem' }}>
                                                            <Text style={{ fontWeight: '600' }}>Contents</Text>
                                                            <Text>{selectedNode.children.length} item(s)</Text>
                                                        </FlexBox>
                                                    )}
                                                </FlexBox>
                                            ) : selectedNodeId === 'root' ? (
                                                <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '1rem' }}>
                                                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.5rem' }}>
                                                        <Text style={{ fontWeight: '600' }}>Selected Item</Text>
                                                        <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '0.5rem' }}>
                                                            <Icon name="folder" />
                                                            <Text>Assignment Root</Text>
                                                        </FlexBox>
                                                    </FlexBox>

                                                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.5rem' }}>
                                                        <Text style={{ fontWeight: '600' }}>Type</Text>
                                                        <Text>Root Directory</Text>
                                                    </FlexBox>

                                                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.5rem' }}>
                                                        <Text style={{ fontWeight: '600' }}>Contents</Text>
                                                        <Text>{assignmentData.fileSystem.children.length} item(s)</Text>
                                                    </FlexBox>
                                                </FlexBox>
                                            ) : (
                                                <FlexBox
                                                    direction={FlexBoxDirection.Column}
                                                    alignItems={FlexBoxAlignItems.Center}
                                                    justifyContent={FlexBoxJustifyContent.Center}
                                                    style={{ height: '200px', gap: '1rem' }}
                                                >
                                                    <Icon name="detail-view" style={{ fontSize: '2rem', color: 'var(--sapContent_NonInteractiveIconColor)' }} />
                                                    <Text style={{ color: 'var(--sapContent_LabelColor)', textAlign: 'center' }}>
                                                        Select an item in the tree<br />to view its details
                                                    </Text>
                                                </FlexBox>
                                            )}
                                        </div>
                                    </Card>
                                </FlexBox>

                                {assignmentData.fileSystem.children.length > 0 && !hasNotebooks(assignmentData.fileSystem) && (
                                    <MessageStrip design="Critical" style={{ marginTop: '1rem' }}>
                                        At least one notebook file is required to create an assignment.
                                    </MessageStrip>
                                )}
                            </FlexBox>
                        </Panel>
                    </FlexBox>
                );

            case 'generate-review':
                return (
                    <div style={{ display: 'flex', minHeight: '300px', flexDirection: 'column', gap: '20px' }}>
                        <Title level="H3">4. Generate & Review Notebooks</Title>
                        {isGenerating ? (
                            <FlexBox direction={FlexBoxDirection.Column} alignItems={FlexBoxAlignItems.Center} style={{ gap: '24px', justifyContent: 'center', minHeight: '250px' }}>
                                <BusyIndicator active delay={1000} size="M" />
                                <Text style={{ fontSize: '16px', color: '#666', textAlign: 'center' }}>
                                    Generating student versions of the selected notebooks...
                                </Text>
                            </FlexBox>
                        ) : generationComplete && previewData ? (
                            <div>
                                <FlexBox direction={FlexBoxDirection.Column} alignItems={FlexBoxAlignItems.Center} style={{ gap: '16px', marginBottom: '24px', padding: '20px', backgroundColor: '#f0f9f0', borderRadius: '8px', border: '1px solid #4caf50' }}>
                                    <Icon name="process" style={{ fontSize: '32px', color: '#4caf50' }} />
                                    <Text style={{ fontSize: '16px', fontWeight: '600', color: '#4caf50' }}>
                                        Preview generated successfully!
                                    </Text>
                                    <Text style={{ fontSize: '14px', color: '#666', textAlign: 'center' }}>
                                        {previewData.files.length} files processed.
                                    </Text>
                                </FlexBox>
                                <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '16px' }}>
                                    <Text style={{ fontWeight: '600', fontSize: '16px' }}>Processed Notebooks</Text>
                                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '6px', marginLeft: '32px' }}>
                                            {previewData.files.map(file => (
                                                <Text key={file.rel} style={{ fontSize: '13px' }}>
                                                    • {file.rel}
                                                </Text>
                                            ))}
                                    </FlexBox>
                                    <MessageStrip>
                                        <Text>
                                            <strong>Optional:</strong> Review the generated notebooks in JupyterLab.
                                        </Text>
                                    </MessageStrip>
                                    <FlexBox justifyContent={FlexBoxJustifyContent.Center} style={{ marginTop: '12px' }}>
                                        <Button
                                            design="Default"
                                            icon="open-folder"
                                            onClick={openNotebooksInJupyterLab}
                                            style={{ minWidth: '180px' }}
                                        >
                                            Open in JupyterLab
                                        </Button>
                                    </FlexBox>
                                </FlexBox>
                            </div>
                        ) : null}
                    </div>
                );

            case 'review':
                return (
                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '1.5rem' }}>
                        <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.5rem' }}>
                            <Title level="H3">5. Final Review</Title>
                            <Text style={{ color: 'var(--sapContent_LabelColor)' }}>
                                Review your assignment configuration before creating the assignment.
                            </Text>
                        </FlexBox>

                        <FlexBox direction={FlexBoxDirection.Row} style={{ gap: '1.5rem' }}>
                            <Card style={{ flex: 1 }}>
                                <CardHeader titleText="Assignment Information" />
                                <div style={{ padding: '1rem' }}>
                                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.75rem' }}>
                                        <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.25rem' }}>
                                            <Text style={{ fontWeight: '600', fontSize: '0.875rem' }}>Name</Text>
                                            <Text style={{ fontSize: '0.875rem' }}>{assignmentData.name}</Text>
                                        </FlexBox>

                                        {assignmentData.description && (
                                            <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.25rem' }}>
                                                <Text style={{ fontWeight: '600', fontSize: '0.875rem' }}>Description</Text>
                                                <Text style={{ fontSize: '0.875rem' }}>{assignmentData.description}</Text>
                                            </FlexBox>
                                        )}

                                        {assignmentData.dueDate && (
                                            <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.25rem' }}>
                                                <Text style={{ fontWeight: '600', fontSize: '0.875rem' }}>Due Date</Text>
                                                <Text style={{ fontSize: '0.875rem' }}>
                                                    {new Date(assignmentData.dueDate).toLocaleDateString()}
                                                </Text>
                                            </FlexBox>
                                        )}
                                    </FlexBox>
                                </div>
                            </Card>

                            <Card style={{ flex: 1 }}>
                                <CardHeader titleText="Settings" />
                                <div style={{ padding: '1rem' }}>
                                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.75rem' }}>
                                        <FlexBox justifyContent={FlexBoxJustifyContent.SpaceBetween} alignItems={FlexBoxAlignItems.Center}>
                                            <Text style={{ fontSize: '0.875rem' }}>Allow Resubmissions</Text>
                                            <Icon
                                                name={assignmentData.allowResubmissions ? "accept" : "decline"}
                                                style={{
                                                    color: assignmentData.allowResubmissions ? 'var(--sapPositiveColor)' : 'var(--sapNegativeColor)',
                                                    fontSize: '1rem'
                                                }}
                                            />
                                        </FlexBox>

                                        <FlexBox justifyContent={FlexBoxJustifyContent.SpaceBetween} alignItems={FlexBoxAlignItems.Center}>
                                            <Text style={{ fontSize: '0.875rem' }}>Allow Late Submissions</Text>
                                            <Icon
                                                name={assignmentData.allowLateSubmissions ? "accept" : "decline"}
                                                style={{
                                                    color: assignmentData.allowLateSubmissions ? 'var(--sapPositiveColor)' : 'var(--sapNegativeColor)',
                                                    fontSize: '1rem'
                                                }}
                                            />
                                        </FlexBox>

                                        <FlexBox justifyContent={FlexBoxJustifyContent.SpaceBetween} alignItems={FlexBoxAlignItems.Center}>
                                            <Text style={{ fontSize: '0.875rem' }}>LTI Synchronization</Text>
                                            <Icon
                                                name={assignmentData.ltiSyncEnabled ? "accept" : "decline"}
                                                style={{
                                                    color: assignmentData.ltiSyncEnabled ? 'var(--sapPositiveColor)' : 'var(--sapNegativeColor)',
                                                    fontSize: '1rem'
                                                }}
                                            />
                                        </FlexBox>

                                        <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.25rem' }}>
                                            <Text style={{ fontWeight: '600', fontSize: '0.875rem' }}>Show Solution</Text>
                                            <Text style={{ fontSize: '0.875rem' }}>
                                                {SOLUTION_VISIBILITY_OPTIONS.find(opt => opt.value === assignmentData.showSolution)?.label}
                                            </Text>
                                        </FlexBox>
                                    </FlexBox>
                                </div>
                            </Card>
                        </FlexBox>

                        <Card>
                            <CardHeader titleText="Assignment Structure" />
                            <div style={{ padding: '1rem' }}>
                                <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '0.5rem', marginBottom: '1rem' }}>
                                    <Text style={{ fontSize: '0.875rem', color: 'var(--sapContent_LabelColor)' }}>
                                        {extractNotebooksAndAssets(assignmentData.fileSystem).notebooks.length} notebooks, {extractNotebooksAndAssets(assignmentData.fileSystem).assets.length} assets
                                    </Text>
                                </FlexBox>

                                {assignmentData.fileSystem.children.length === 0 ? (
                                    <FlexBox
                                        direction={FlexBoxDirection.Column}
                                        alignItems={FlexBoxAlignItems.Center}
                                        justifyContent={FlexBoxJustifyContent.Center}
                                        style={{ height: '100px', gap: '0.5rem' }}
                                    >
                                        <Icon name="folder" style={{ fontSize: '2rem', color: 'var(--sapContent_NonInteractiveIconColor)' }} />
                                        <Text style={{ color: 'var(--sapContent_LabelColor)', fontSize: '0.875rem' }}>
                                            No files added to this assignment
                                        </Text>
                                    </FlexBox>
                                ) : (
                                    <FlexBox direction={FlexBoxDirection.Column}>
                                        <FlexBox alignItems={FlexBoxAlignItems.Center} style={{
                                            gap: '0.5rem',
                                            marginBottom: '0.5rem',
                                            padding: '0.25rem',
                                            backgroundColor: 'var(--sapList_HeaderBackground)',
                                            borderRadius: '0.25rem'
                                        }}>
                                            <Icon name="folder" style={{ fontSize: '0.875rem' }} />
                                            <Text style={{ fontSize: '0.875rem', fontWeight: '600' }}>
                                                {assignmentData.fileSystem.name}/
                                            </Text>
                                            <Text style={{ fontSize: '0.75rem', color: 'var(--sapContent_LabelColor)' }}>
                                                (root)
                                            </Text>
                                        </FlexBox>

                                        <div style={{ marginLeft: '0.5rem', borderLeft: '1px solid var(--sapContent_ForegroundBorderColor)', paddingLeft: '0.5rem' }}>
                                            {renderReviewTreeItems(assignmentData.fileSystem.children)}
                                        </div>
                                    </FlexBox>
                                )}
                            </div>
                        </Card>
                    </FlexBox>
                );

            default:
                return null;
        }
    }, [currentStep, assignmentData, isGenerating, generationComplete, previewData, handleAddDirectory, handleAddNotebooks, handleAddAssets, handleRemoveNode, openNotebooksInJupyterLab, handleNameChange, handleAllowResubmissionsChange, handleAllowLateSubmissionsChange, handleLtiSyncChange, handleShowSolutionChange, handleDescriptionChange, handleDueDateChange]);

    return (
        <>
            <WidgetModal
                open={open}
                onClose={handleCancel}
                title="Create Assignment"
                width="80vw"
                height="80vh"
                maxWidth="900px"
                maxHeight="90vh"
                footer={
                    <FlexBox justifyContent={FlexBoxJustifyContent.End} style={{ gap: '8px' }}>
                        <Button design="Transparent" icon="decline" onClick={handleCancel}>
                            Cancel
                        </Button>
                        <Button
                            design="Default"
                            icon="navigation-left-arrow"
                            onClick={handlePrevious}
                            disabled={isFirstStep}
                        >
                            Previous
                        </Button>
                        {isLastStep ? (
                            <Button
                                design="Emphasized"
                                icon="save"
                                onClick={handleFinalize}
                                disabled={!isStepValid}
                            >
                                Create Assignment
                            </Button>
                        ) : (
                            <Button
                                design="Emphasized"
                                icon="navigation-right-arrow"
                                onClick={handleNext}
                                disabled={!isStepValid}
                            >
                                Next
                            </Button>
                        )}
                    </FlexBox>
                }
            >
                <FlexBox justifyContent={FlexBoxJustifyContent.Center} style={{ marginBottom: '32px', flexShrink: 0 }}>
                    <FlexBox style={{ gap: '8px' }}>
                        {WIZARD_STEPS.map((step, index) => (
                            <FlexBox key={step.key} alignItems={FlexBoxAlignItems.Center} style={{ gap: '4px' }}>
                                <FlexBox
                                    alignItems={FlexBoxAlignItems.Center}
                                    justifyContent={FlexBoxJustifyContent.Center}
                                    style={{
                                        width: '32px',
                                        height: '32px',
                                        borderRadius: '50%',
                                        backgroundColor: index <= currentStepIndex ? '#0070f3' : '#e0e0e0',
                                        color: index <= currentStepIndex ? 'white' : '#666',
                                        fontSize: '12px',
                                        fontWeight: '600'
                                    }}
                                >
                                    {index + 1}
                                </FlexBox>
                                <Text
                                    style={{
                                        fontSize: '12px',
                                        color: index === currentStepIndex ? '#0070f3' : '#666',
                                        fontWeight: index === currentStepIndex ? '600' : '400'
                                    }}
                                >
                                    {step.title}
                                </Text>
                                {index < WIZARD_STEPS.length - 1 && (
                                    <div
                                        style={{
                                            width: '24px',
                                            height: '2px',
                                            backgroundColor: index < currentStepIndex ? '#0070f3' : '#e0e0e0',
                                            margin: '0 8px'
                                        }}
                                    />
                                )}
                            </FlexBox>
                        ))}
                    </FlexBox>
                </FlexBox>
                <div style={{ flex: 1, overflow: 'auto', paddingBottom: '16px' }}>
                    {renderStepContent}
                </div>
            </WidgetModal>

            <FilePickerDialog
                open={filePickerOpen}
                onClose={() => setFilePickerOpen(false)}
                onFilesSelected={handleFilesSelected}
                multiSelect={true}
                fileTypes={addType === 'notebook' ? ['.ipynb'] : []}
                title={addType === 'notebook' ? 'Select Notebook Files' : 'Select Asset Files'}
            />

            <Dialog
                open={dirDialogOpen}
                onClose={handleDirDialogClose}
                header={<Title level="H4">Create New Directory</Title>}
                footer={
                    <FlexBox justifyContent={FlexBoxJustifyContent.End} style={{ gap: '8px', padding: '8px' }}>
                        <Button design="Default" onClick={handleDirDialogClose}>Cancel</Button>
                        <Button design="Emphasized" onClick={handleCreateDirectory} disabled={!newDirName.trim()}>
                            Create
                        </Button>
                    </FlexBox>
                }
            >
                <FlexBox direction={FlexBoxDirection.Column} style={{ padding: '16px', gap: '12px' }}>
                    <Label>Directory Name</Label>
                    <Input
                        value={newDirName}
                        onInput={handleDirNameChange}
                        placeholder="Enter directory name..."
                        style={{ width: '100%' }}
                    />
                </FlexBox>
            </Dialog>

            <ErrorDialog
                open={isErrorDialogOpen}
                onClose={clearError}
                title={errorInfo?.title}
                message={errorInfo?.message || ''}
                details={errorInfo?.details}
                closable={errorInfo?.closable ?? true}
                onRetry={async () => {
                    if (errorInfo?.title?.includes('Generate Preview')) {
                        await startNotebookGeneration();
                        clearError();
                    } else if (errorInfo?.title?.includes('Create Assignment')) {
                        await handleFinalize();
                    }
                }}
            />
        </>
    );
};

export default CreateAssignmentWizard;
