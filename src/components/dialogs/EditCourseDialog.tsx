import React from 'react';
import {
    Button,
    FlexBox,
    FlexBoxDirection,
    FlexBoxJustifyContent,
    FlexBoxAlignItems,
    Text,
    Input,
    Switch,
    Icon,
    Popover
} from '@ui5/webcomponents-react';
import '@ui5/webcomponents-icons/dist/save.js';
import '@ui5/webcomponents-icons/dist/decline.js';
import '@ui5/webcomponents-icons/dist/question-mark.js';
import WidgetModal from './WidgetModal';
import { Course } from '../../types/api';

interface EditCourseDialogProps {
    open: boolean;
    onClose: () => void;
    course: Course | null;
    onSave?: (courseData: Partial<Course>) => void;
}

const EditCourseDialog: React.FC<EditCourseDialogProps> = ({
    open,
    onClose,
    course,
    onSave
}) => {
    const [formData, setFormData] = React.useState({
        title: '',
        lti_id: '',
        active: true
    });

    React.useEffect(() => {
        if (course) {
            setFormData({
                title: course.title || '',
                lti_id: course.lti_id || '',
                active: course.active !== undefined ? course.active : true
            });
        }
    }, [course]);

    const handleSave = () => {
        if (onSave) {
            onSave(formData);
        }
        onClose();
    };

    const handleCancel = () => {
        if (course) {
            setFormData({
                title: course.title || '',
                lti_id: course.lti_id || '',
                active: course.active !== undefined ? course.active : true
            });
        }
        onClose();
    };

    const isFormValid = formData.title.trim() !== '';

    return (
        <>
            <WidgetModal
                open={open}
                onClose={handleCancel}
                title={`Edit Course - ${course?.label || ''}`}
                width="400px"
                footer={
                    <FlexBox
                        justifyContent={FlexBoxJustifyContent.End} 
                        style={{ gap: '8px' }}
                    >
                        <Button
                            design="Transparent"
                            icon="decline"
                            onClick={handleCancel}
                        >
                            Cancel
                        </Button>
                        <Button
                            design="Emphasized"
                            icon="save"
                            onClick={handleSave}
                            disabled={!isFormValid}
                        >
                            Save Changes
                        </Button>
                    </FlexBox>
                }
            >
                <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '16px' }}>

                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '4px' }}>
                        <Text style={{ fontWeight: '600', fontSize: '12px' }}>Course ID</Text>
                        <Input
                            value={course?.label || ''}
                            readonly
                            style={{ backgroundColor: '#f5f5f5' }}
                        />
                        <Text style={{ fontSize: '10px', color: '#666' }}>
                            Course ID cannot be changed
                        </Text>
                    </FlexBox>

                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '2px' }}>
                        <Text style={{ fontWeight: '600', fontSize: '12px' }}>
                            Course Title <span style={{ color: '#e53e3e' }}>*</span>
                        </Text>
                        <Input
                            value={formData.title}
                            onInput={(e: any) => setFormData({ ...formData, title: e.target.value })}
                            placeholder="Enter course title"
                            required
                        />
                    </FlexBox>

                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '2px' }}>
                        <Text style={{ fontWeight: '600', fontSize: '12px' }}>LTI ID</Text>
                        <Input
                            value={formData.lti_id}
                            onInput={(e: any) => setFormData({ ...formData, lti_id: e.target.value })}
                            placeholder="Enter LTI ID"
                        />
                        <Text style={{ fontSize: '10px', color: '#666' }}>
                            Learning Management System integration ID
                        </Text>
                    </FlexBox>

                    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '2px' }}>
                        <Text style={{ fontWeight: '600', fontSize: '12px' }}>Activity Status</Text>
                        <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '6px' }}>
                            <Switch
                                checked={formData.active}
                                onChange={(e: any) => setFormData({ ...formData, active: e.target.checked })}
                            />
                            <Text style={{ fontSize: '12px' }}>
                                {formData.active ? 'Active' : 'Inactive'}
                            </Text>
                        </FlexBox>
                        <Text style={{ fontSize: '10px', color: '#666' }}>
                            {formData.active
                                ? 'Course is accessible to students'
                                : 'Course is not accessible to students'
                            }
                        </Text>
                    </FlexBox>
                </FlexBox>
            </WidgetModal>
        </>
    );
};

export default EditCourseDialog;
