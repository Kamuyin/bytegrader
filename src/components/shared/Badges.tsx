import React from 'react';
import { FlexBox, FlexBoxAlignItems, Icon, Text } from '@ui5/webcomponents-react';
import { Assignment } from '../../types/api';
import { ASSIGNMENT_STATUS_CONFIG } from '../../constants';

interface AssignmentStatusBadgeProps {
  status: Assignment['status'];
}

export const AssignmentStatusBadge: React.FC<AssignmentStatusBadgeProps> = ({ status }) => {
  const config = ASSIGNMENT_STATUS_CONFIG[status];

  return (
    <FlexBox
      alignItems={FlexBoxAlignItems.Center}
      style={{
        backgroundColor: config.backgroundColor,
        color: config.color,
        padding: '6px 12px',
        borderRadius: '16px',
        fontSize: '12px',
        fontWeight: '600',
        gap: '6px',
        border: `1px solid ${config.color}20`
      }}
    >
      <Icon name={config.icon} style={{ fontSize: '12px' }} />
      <span>{config.text}</span>
    </FlexBox>
  );
};

interface RoleBadgeProps {
  role: 'instructor' | 'student';
}

export const RoleBadge: React.FC<RoleBadgeProps> = ({ role }) => {
  const config = role === 'instructor'
    ? {
        backgroundColor: '#e3f2fd',
        color: '#1976d2',
        text: 'Instructor',
        icon: 'person-placeholder'
      }
    : {
        backgroundColor: '#e8f5e8',
        color: '#388e3c',
        text: 'Student',
        icon: 'person-placeholder'
      };

  return (
    <FlexBox
      alignItems={FlexBoxAlignItems.Center}
      style={{
        backgroundColor: config.backgroundColor,
        color: config.color,
        padding: '6px 12px',
        borderRadius: '16px',
        fontSize: '12px',
        fontWeight: '600',
        gap: '6px',
        border: `1px solid ${config.color}20`
      }}
    >
      <Icon name={config.icon} style={{ fontSize: '12px' }} />
      <span>{config.text}</span>
    </FlexBox>
  );
};

export const InactiveBadge: React.FC = () => (
  <FlexBox
    alignItems={FlexBoxAlignItems.Center}
    style={{
      backgroundColor: '#fff3e0',
      color: '#f57c00',
      border: '1px solid #f57c0020',
      padding: '6px 12px',
      borderRadius: '16px',
      fontSize: '12px',
      fontWeight: '600',
      gap: '6px'
    }}
  >
    <Icon name="hide" style={{ fontSize: '12px' }} />
    <span>Inactive</span>
  </FlexBox>
);

export const HiddenBadge: React.FC = () => (
  <FlexBox
    alignItems={FlexBoxAlignItems.Center}
    style={{
      backgroundColor: '#f5f5f5',
      color: '#757575',
      border: '1px solid #e0e0e0',
      padding: '6px 12px',
      borderRadius: '16px',
      fontSize: '12px',
      fontWeight: '600',
      gap: '6px'
    }}
  >
    <Icon name="hide" style={{ fontSize: '12px' }} />
    <span>Hidden</span>
  </FlexBox>
);

interface ProgressBadgeProps {
  progress: number;
}

export const ProgressBadge: React.FC<ProgressBadgeProps> = ({ progress }) => {
  const config = progress < 30
    ? { color: '#d32f2f', bg: '#ffebee', icon: 'status-negative' }
    : progress < 70
    ? { color: '#f57c00', bg: '#fff3e0', icon: 'status-critical' }
    : { color: '#388e3c', bg: '#e8f5e8', icon: 'complete' };

  return (
    <FlexBox
      alignItems={FlexBoxAlignItems.Center}
      style={{
        backgroundColor: config.bg,
        color: config.color,
        padding: '6px 12px',
        borderRadius: '16px',
        border: `1px solid ${config.color}20`,
        gap: '6px'
      }}
    >
      <Icon name={config.icon} style={{ fontSize: '12px' }} />
      <Text style={{ fontSize: '12px', fontWeight: '600', color: config.color }}>
        {Math.round(progress)}% Complete
      </Text>
    </FlexBox>
  );
};

interface ScoreBadgeProps {
  currentScore: number;
  totalScore: number;
}

export const ScoreBadge: React.FC<ScoreBadgeProps> = ({ currentScore, totalScore }) => {
  const scorePercentage = Math.round((currentScore / totalScore) * 100);
  const isComplete = scorePercentage === 100;

  return (
    <FlexBox
      alignItems={FlexBoxAlignItems.Center}
      style={{
        backgroundColor: isComplete ? '#e8f5e8' : '#f5f5f5',
        color: isComplete ? '#388e3c' : '#666',
        padding: '6px 12px',
        borderRadius: '16px',
        border: `1px solid ${isComplete ? '#388e3c' : '#e0e0e0'}20`,
        gap: '6px'
      }}
    >
      <Icon name="target-group" style={{ fontSize: '12px' }} />
      <Text style={{ fontSize: '13px', fontWeight: '600' }}>
        {currentScore}/{totalScore} ({scorePercentage}%)
      </Text>
    </FlexBox>
  );
};
