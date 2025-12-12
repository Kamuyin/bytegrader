import React from 'react';
import {
  Button,
  FlexBox,
  FlexBoxDirection,
  FlexBoxJustifyContent,
  FlexBoxAlignItems,
  Text,
  Table,
  TableHeaderRow,
  TableHeaderCell,
  TableRow,
  TableCell,
  Input,
  Select,
  Option,
  Icon,
  Popover
} from '@ui5/webcomponents-react';
import '@ui5/webcomponents-icons/dist/add.js';
import '@ui5/webcomponents-icons/dist/edit.js';
import '@ui5/webcomponents-icons/dist/delete.js';
import '@ui5/webcomponents-icons/dist/save.js';
import '@ui5/webcomponents-icons/dist/decline.js';
import '@ui5/webcomponents-icons/dist/question-mark.js';
import WidgetModal from './WidgetModal';
import { Course } from '../../types/api';

interface Enrollment {
  id: string;
  username: string;
  fullName: string;
  email: string;
  role: 'instructor' | 'student';
  enrolledDate: string;
}

interface EnrollmentsDialogProps {
  open: boolean;
  onClose: () => void;
  course: Course | null;
  userRole?: 'instructor' | 'student';
}

// TODO: Unimplemented!!! (but also not necessary yet)
const EnrollmentsDialog: React.FC<EnrollmentsDialogProps> = ({
  open,
  onClose,
  course,
  userRole = 'student'
}) => {
  const [enrollments, setEnrollments] = React.useState<Enrollment[]>([]);
  const [newEnrollment, setNewEnrollment] = React.useState({
    username: '',
    fullName: '',
    email: '',
    role: 'student' as 'instructor' | 'student'
  });
  const [editingEnrollment, setEditingEnrollment] = React.useState<string | null>(null);
  const [ltiWarningOpen, setLtiWarningOpen] = React.useState(false);
  const [ltiWarningOpener, setLtiWarningOpener] = React.useState<HTMLElement | null>(null);

  // Mock enrollment data
  const mockEnrollments: Enrollment[] = [
    {
      id: '1',
      username: 'alice.johnson',
      fullName: 'Alice Johnson',
      email: 'alice.johnson@university.edu',
      role: 'instructor',
      enrolledDate: '2024-01-15'
    },
    {
      id: '2',
      username: 'bob.smith',
      fullName: 'Bob Smith',
      email: 'bob.smith@university.edu',
      role: 'student',
      enrolledDate: '2024-02-01'
    },
    {
      id: '3',
      username: 'carol.williams',
      fullName: 'Carol Williams',
      email: 'carol.williams@university.edu',
      role: 'student',
      enrolledDate: '2024-02-03'
    },
    {
      id: '4',
      username: 'david.brown',
      fullName: 'David Brown',
      email: 'david.brown@university.edu',
      role: 'student',
      enrolledDate: '2024-02-05'
    }
  ];

  React.useEffect(() => {
    if (open && course) {
      setEnrollments(mockEnrollments);
    }
  }, [open, course]);

  const handleAddEnrollment = () => {
    if (newEnrollment.username && newEnrollment.fullName && newEnrollment.email) {
      const enrollment: Enrollment = {
        id: Date.now().toString(),
        ...newEnrollment,
        enrolledDate: new Date().toISOString().split('T')[0]
      };
      setEnrollments([...enrollments, enrollment]);
      setNewEnrollment({ username: '', fullName: '', email: '', role: 'student' });
    }
  };

  const handleDeleteEnrollment = (enrollmentId: string) => {
    setEnrollments(enrollments.filter(e => e.id !== enrollmentId));
  };

  const handleEditEnrollment = (enrollmentId: string, field: string, value: string) => {
    setEnrollments(enrollments.map(e => 
      e.id === enrollmentId ? { ...e, [field]: value } : e
    ));
  };

  const handleLtiWarningClick = (event: any) => {
    setLtiWarningOpener(event.target);
    setLtiWarningOpen(true);
  };

  return (
    <>
      <style>
        {`  
          .full-space-dialog::part(content) {
            padding: 0 !important;
            margin: 0 !important;
            width: 100% !important;
            height: 100% !important;
          }
        `}
      </style>
      <WidgetModal
        open={open}
        onClose={onClose}
        title={`Manage Enrollments - ${course?.title || ''}`}
        width="80%"
        maxWidth="1200px"
        height="80%"
        footer={
          <FlexBox justifyContent={FlexBoxJustifyContent.End}>
            <Button design="Emphasized" onClick={onClose}>
              Close
            </Button>
          </FlexBox>
        }
      >
        <FlexBox direction={FlexBoxDirection.Column} style={{ height: '100%' }}>
        <FlexBox direction={FlexBoxDirection.Column} style={{ marginBottom: '16px', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
          <FlexBox alignItems={FlexBoxAlignItems.Center} justifyContent={FlexBoxJustifyContent.SpaceBetween} style={{ marginBottom: '8px' }}>
            <Text style={{ fontWeight: '600', fontSize: '14px' }}>Add New Enrollment</Text>
          </FlexBox>
          <FlexBox style={{ gap: '8px', flexWrap: 'wrap' }}>
            <Input
              placeholder="Username"
              value={newEnrollment.username}
              onInput={(e) => setNewEnrollment({ ...newEnrollment, username: e.target.value })}
              style={{ width: '140px' }}
            />
            <Input
              placeholder="Full Name"
              value={newEnrollment.fullName}
              onInput={(e) => setNewEnrollment({ ...newEnrollment, fullName: e.target.value })}
              style={{ width: '180px' }}
            />
            <Input
              placeholder="Email"
              value={newEnrollment.email}
              onInput={(e) => setNewEnrollment({ ...newEnrollment, email: e.target.value })}
              style={{ width: '200px' }}
            />
            <Select
              value={newEnrollment.role}
              onChange={(e) => setNewEnrollment({ ...newEnrollment, role: e.detail.selectedOption.value as 'instructor' | 'student' })}
              style={{ width: '120px' }}
            >
              <Option value="student">Student</Option>
              <Option value="instructor">Instructor</Option>
            </Select>
            <Button 
              design="Emphasized" 
              icon="add"
              onClick={handleAddEnrollment}
              disabled={!newEnrollment.username || !newEnrollment.fullName || !newEnrollment.email}
              style={{ padding: '0 12px' }}
            >
              Add
            </Button>
          </FlexBox>
        </FlexBox>

        <FlexBox direction={FlexBoxDirection.Column} style={{ flex: 1, overflow: 'hidden' }}>
          <FlexBox alignItems={FlexBoxAlignItems.Center} justifyContent={FlexBoxJustifyContent.SpaceBetween} style={{ marginBottom: '12px' }}>
            <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '8px' }}>
              <Text style={{ fontWeight: '600', fontSize: '16px' }}>Current Enrollments</Text>
              <Icon
                name="question-mark"
                style={{
                  fontSize: '12px',
                  color: '#0070f3',
                  cursor: 'help'
                }}
                onClick={handleLtiWarningClick}
              />
            </FlexBox>
            <Text style={{ fontSize: '14px', color: '#666' }}>({enrollments.length} enrolled)</Text>
          </FlexBox>
          <div style={{ 
            overflow: 'auto', 
            flex: 1, 
            border: '1px solid #d1d5db', 
            borderRadius: '6px',
            backgroundColor: 'white'
          }}>
            <Table 
              style={{ 
                width: '100%'
              }}
              headerRow={
                <TableHeaderRow sticky>
                  <TableHeaderCell minWidth="120px">
                    <span style={{ fontWeight: '600', fontSize: '14px' }}>Username</span>
                  </TableHeaderCell>
                  <TableHeaderCell minWidth="150px">
                    <span style={{ fontWeight: '600', fontSize: '14px' }}>Full Name</span>
                  </TableHeaderCell>
                  <TableHeaderCell minWidth="200px">
                    <span style={{ fontWeight: '600', fontSize: '14px' }}>Email</span>
                  </TableHeaderCell>
                  <TableHeaderCell minWidth="100px">
                    <span style={{ fontWeight: '600', fontSize: '14px' }}>Role</span>
                  </TableHeaderCell>
                  <TableHeaderCell minWidth="100px">
                    <span style={{ fontWeight: '600', fontSize: '14px' }}>Enrolled</span>
                  </TableHeaderCell>
                  <TableHeaderCell minWidth="120px" width="120px">
                    <span style={{ fontWeight: '600', fontSize: '14px' }}>Actions</span>
                  </TableHeaderCell>
                </TableHeaderRow>
              }
            >
              {enrollments.map((enrollment, index) => (
                <TableRow 
                  key={enrollment.id}
                  style={{ 
                    backgroundColor: index % 2 === 0 ? '#ffffff' : '#fafafa'
                  }}
                >
                  <TableCell>
                    {editingEnrollment === enrollment.id ? (
                      <Input
                        value={enrollment.username}
                        onInput={(e) => handleEditEnrollment(enrollment.id, 'username', e.target.value)}
                        style={{ width: '100%' }}
                      />
                    ) : (
                      <span style={{ fontSize: '14px', fontWeight: '500' }}>{enrollment.username}</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {editingEnrollment === enrollment.id ? (
                      <Input
                        value={enrollment.fullName}
                        onInput={(e) => handleEditEnrollment(enrollment.id, 'fullName', e.target.value)}
                        style={{ width: '100%' }}
                      />
                    ) : (
                      <span style={{ fontSize: '14px' }}>{enrollment.fullName}</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {editingEnrollment === enrollment.id ? (
                      <Input
                        value={enrollment.email}
                        onInput={(e) => handleEditEnrollment(enrollment.id, 'email', e.target.value)}
                        style={{ width: '100%' }}
                      />
                    ) : (
                      <span style={{ fontSize: '14px', color: '#6b7280' }}>{enrollment.email}</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {editingEnrollment === enrollment.id ? (
                      <Select
                        value={enrollment.role}
                        onChange={(e) => handleEditEnrollment(enrollment.id, 'role', e.detail.selectedOption.value || 'student')}
                        style={{ width: '100%' }}
                      >
                        <Option value="student">Student</Option>
                        <Option value="instructor">Instructor</Option>
                      </Select>
                    ) : (
                      <span 
                        style={{ 
                          backgroundColor: enrollment.role === 'instructor' ? '#dbeafe' : '#dcfce7', 
                          color: enrollment.role === 'instructor' ? '#1e40af' : '#166534',
                          padding: '4px 10px', 
                          borderRadius: '16px', 
                          fontSize: '12px',
                          fontWeight: '500',
                          textTransform: 'capitalize',
                          display: 'inline-block'
                        }}
                      >
                        {enrollment.role}
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    <span style={{ fontSize: '14px', color: '#6b7280' }}>{enrollment.enrolledDate}</span>
                  </TableCell>
                  <TableCell>
                    <FlexBox style={{ gap: '4px' }}>
                      {editingEnrollment === enrollment.id ? (
                        <>
                          <Button 
                            design="Positive" 
                            icon="save"
                            onClick={() => setEditingEnrollment(null)}
                            style={{ fontSize: '11px', padding: '4px', minWidth: '32px' }}
                            tooltip="Save"
                          />
                          <Button 
                            design="Transparent" 
                            icon="decline"
                            onClick={() => setEditingEnrollment(null)}
                            style={{ fontSize: '11px', padding: '4px', minWidth: '32px' }}
                            tooltip="Cancel"
                          />
                        </>
                      ) : (
                        <>
                          <Button 
                            design="Transparent" 
                            icon="edit"
                            onClick={() => setEditingEnrollment(enrollment.id)}
                            style={{ fontSize: '11px', padding: '4px', minWidth: '32px' }}
                            tooltip="Edit"
                          />
                          <Button 
                            design="Negative" 
                            icon="delete"
                            onClick={() => handleDeleteEnrollment(enrollment.id)}
                            style={{ fontSize: '11px', padding: '4px', minWidth: '32px' }}
                            tooltip="Delete"
                          />
                        </>
                      )}
                    </FlexBox>
                  </TableCell>
                </TableRow>
              ))}
            </Table>
          </div>
        </FlexBox>
        </FlexBox>
    </WidgetModal>

    <Popover
      open={ltiWarningOpen}
      opener={ltiWarningOpener || undefined}
      onClose={() => setLtiWarningOpen(false)}
      placement="Top"
    >
      <div style={{ padding: '12px', maxWidth: '320px' }}>
        <Text style={{ fontSize: '12px', fontWeight: '600', marginBottom: '6px' }}>
          LTI Synchronization Warning
        </Text>
        <Text style={{ fontSize: '11px', color: '#666', lineHeight: '1.4' }}>
          Changes made to enrollments may be overridden by the LTI synchronization task when enabled. 
          LTI sync automatically manages enrollments based on your Learning Management System (LMS) data.
        </Text>
      </div>
    </Popover>
    </>
  );
};

export default EnrollmentsDialog;
