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
    Icon
} from '@ui5/webcomponents-react';
import '@ui5/webcomponents-icons/dist/add.js';
import '@ui5/webcomponents-icons/dist/decline.js';
import WidgetModal from './WidgetModal';

interface CreateCourseData {
    label: string;
    title: string;
    lti_id: string;
    active: boolean;
}

interface CreateCourseDialogProps {
    open: boolean;
    onClose: () => void;
    onSave?: (courseData: CreateCourseData) => void;
}

const CreateCourseDialog: React.FC<CreateCourseDialogProps> = ({
    open,
    onClose,
    onSave
}) => {
    const [formData, setFormData] = React.useState<CreateCourseData>({
        label: '',
        title: '',
        lti_id: '',
        active: true
    });

    React.useEffect(() => {
        if (open) {
            setFormData({
                label: '',
                title: '',
                lti_id: '',
                active: true
            });
        }
    }, [open]);

    const handleSave = () => {
        if (onSave) {
            onSave(formData);
        }
        onClose();
    };

    const handleCancel = () => {
        setFormData({
            label: '',
            title: '',
            lti_id: '',
            active: true
        });
        onClose();
    };

    const isFormValid = formData.label.trim() !== '' && 
                       formData.title.trim() !== '' && 
                       formData.lti_id.trim() !== '';

    return (
        <WidgetModal
            open={open}
            onClose={handleCancel}
            title="Create New Course"
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
                        icon="add"
                        onClick={handleSave}
                        disabled={!isFormValid}
                    >
                        Create Course
                    </Button>
                </FlexBox>
            }
        >
            <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '16px' }}>

                <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '4px' }}>
                    <Text style={{ fontWeight: '600', fontSize: '12px' }}>
                        Course ID <span style={{ color: '#e53e3e' }}>*</span>
                    </Text>
                    <Input
                        value={formData.label}
                        onInput={(e: any) => setFormData({ ...formData, label: e.target.value })}
                        placeholder="Enter course ID (e.g., CS101)"
                        required
                    />
                    <Text style={{ fontSize: '10px', color: '#666' }}>
                        Unique identifier for the course
                    </Text>
                </FlexBox>

                <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '4px' }}>
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

                <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '4px' }}>
                    <Text style={{ fontWeight: '600', fontSize: '12px' }}>
                        LTI ID <span style={{ color: '#e53e3e' }}>*</span>
                    </Text>
                    <Input
                        value={formData.lti_id}
                        onInput={(e: any) => setFormData({ ...formData, lti_id: e.target.value })}
                        placeholder="Enter LTI ID"
                        required
                    />
                    <Text style={{ fontSize: '10px', color: '#666' }}>
                        Learning Management System integration ID
                    </Text>
                </FlexBox>

                <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '4px' }}>
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
                            ? 'Course will be accessible to students'
                            : 'Course will not be accessible to students'
                        }
                    </Text>
                </FlexBox>
            </FlexBox>
        </WidgetModal>
    );
};

export default CreateCourseDialog;
