import React from 'react';
import { FlexBox, FlexBoxDirection, FlexBoxJustifyContent, FlexBoxAlignItems, Icon, Text } from '@ui5/webcomponents-react';
import { Notebook } from '../../types/api';

interface NotebookListProps {
  notebooks: Notebook[];
}

export const NotebookList: React.FC<NotebookListProps> = ({ notebooks }) => {
  return (
    <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '8px' }}>
      <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '8px' }}>
        <Icon name="document" style={{ fontSize: '14px', color: 'var(--sapAccentColor8)' }} />
        <Text style={{ fontSize: '13px', color: 'var(--sapGroup_TitleTextColor)', fontWeight: 700 }}>
          Notebooks ({notebooks.length}):
        </Text>
      </FlexBox>
      <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '4px', marginLeft: '22px' }}>
        {notebooks.map((nb, idx) => (
          <FlexBox
            key={nb.id}
            justifyContent={FlexBoxJustifyContent.SpaceBetween}
            alignItems={FlexBoxAlignItems.Center}
            style={{
              padding: '8px 12px',
              backgroundColor: idx % 2 === 0 ? 'var(--sapList_AlternatingBackground)' : 'var(--sapList_Background)',
              borderRadius: '8px',
              border: '1px solid var(--sapList_BorderColor)'
            }}
          >
            <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '8px' }}>
              <Icon name="document" style={{ fontSize: '14px', color: 'var(--sapAccentColor3)' }} />
              <Text style={{ fontSize: '13px', fontWeight: 500, color: 'var(--sapTextColor)' }}>
                {nb.filename}
              </Text>
            </FlexBox>
            <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '4px' }}>
              <Icon name="target-group" style={{ fontSize: '12px', color: 'var(--sapAccentColor1)' }} />
              <Text style={{ fontSize: '12px', fontWeight: 700, color: 'var(--sapAccentColor1)' }}>
                {nb.maxScore} pts
              </Text>
            </FlexBox>
          </FlexBox>
        ))}
      </FlexBox>
    </FlexBox>
  );
};
