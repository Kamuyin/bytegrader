import React from 'react';
import { FlexBox, FlexBoxAlignItems, Icon, Text } from '@ui5/webcomponents-react';

interface DueDateDisplayProps {
  dueDate?: string;
}

export const DueDateDisplay: React.FC<DueDateDisplayProps> = ({ dueDate }) => {
  if (!dueDate) return null;

  const date = new Date(dueDate);
  const now = new Date();
  const isOverdue = date < now;

  return (
    <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '4px' }}>
      <Icon name="calendar" style={{ fontSize: '12px', color: isOverdue ? '#d32f2f' : '#666' }} />
      <Text style={{ fontSize: '12px', color: isOverdue ? '#d32f2f' : '#666', fontWeight: isOverdue ? '600' : '400' }}>
        Due: {date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
        {isOverdue && ' (Overdue)'}
      </Text>
    </FlexBox>
  );
};
