import React from 'react';
import { FlexBox, Button } from '@ui5/webcomponents-react';
import { Assignment } from '../../types/api';

interface AssignmentActionButtonsProps {
  assignment: Assignment;
  displayStatus: Assignment['status'];
  isFetching: boolean;
  isSolutionFetching: boolean;
  hasPermission: (permission: string) => boolean;
  onStart: () => void;
  onSubmit: () => void;
  onReset: () => void;
  onFetchSolutions: () => void;
}

export const AssignmentActionButtons: React.FC<AssignmentActionButtonsProps> = ({
  assignment,
  displayStatus,
  isFetching,
  isSolutionFetching,
  hasPermission,
  onStart,
  onSubmit,
  onReset,
  onFetchSolutions
}) => {
  const canFetch = hasPermission('assignment:fetch');
  const canSubmit = hasPermission('assignment:submit');
  const canFetchSolution = hasPermission('assignment:fetch_solution');

  const renderSolutionButton = () => {
    if (!canFetchSolution) return null;
    return (
      <Button
        design="Transparent"
        icon="lightbulb"
        onClick={onFetchSolutions}
        disabled={isSolutionFetching}
        tooltip="Fetch Solutions"
      >
        {isSolutionFetching ? 'Solutions…' : 'Solutions'}
      </Button>
    );
  };

  switch (displayStatus) {
    case 'NOT_STARTED':
      return (
        <FlexBox style={{ gap: '8px', flexWrap: 'wrap' }}>
          <Button
            design="Emphasized"
            icon="download"
            onClick={onStart}
            disabled={isFetching || !canFetch}
          >
            {isFetching ? 'Fetching...' : 'Start Assignment'}
          </Button>
          {renderSolutionButton()}
        </FlexBox>
      );

    case 'IN_PROGRESS':
      return (
        <FlexBox style={{ gap: '8px', flexWrap: 'wrap' }}>
          <Button
            design="Default"
            icon="download"
            onClick={onStart}
            disabled={isFetching || !canFetch}
          >
            {isFetching ? 'Fetching...' : 'Open in JupyterLab'}
          </Button>
          <Button
            design="Emphasized"
            icon="upload"
            onClick={onSubmit}
            disabled={isFetching || !canSubmit}
          >
            {isFetching ? 'Submitting...' : 'Submit'}
          </Button>
          <Button
            design="Transparent"
            icon="reset"
            onClick={onReset}
            disabled={isFetching || !canFetch}
          >
            {isFetching ? 'Resetting...' : 'Reset'}
          </Button>
          {renderSolutionButton()}
        </FlexBox>
      );

    case 'SUBMITTED':
      return (
        <FlexBox style={{ gap: '8px', flexWrap: 'wrap' }}>
          <Button
            design="Default"
            icon="download"
            onClick={onStart}
            disabled={isFetching || !canFetch}
          >
            {isFetching ? 'Fetching...' : 'Open in JupyterLab'}
          </Button>
          {renderSolutionButton()}
        </FlexBox>
      );

    case 'GRADED':
      return (
        <FlexBox style={{ gap: '8px', flexWrap: 'wrap' }}>
          <Button
            design="Default"
            icon="download"
            onClick={onStart}
            disabled={isFetching || !canFetch}
          >
            {isFetching ? 'Fetching...' : 'Open in JupyterLab'}
          </Button>
          <Button
            design="Emphasized"
            icon="upload"
            onClick={onSubmit}
            disabled={isFetching || !canSubmit}
          >
            {isFetching ? 'Submitting...' : 'Submit'}
          </Button>
          {renderSolutionButton()}
        </FlexBox>
      );

    case 'COMPLETED':
      return (
        <FlexBox style={{ gap: '8px', flexWrap: 'wrap' }}>
          <Button
            design="Default"
            icon="download"
            onClick={onStart}
            disabled={isFetching || !canFetch}
          >
            {isFetching ? 'Fetching...' : 'View Assignment'}
          </Button>
          {renderSolutionButton()}
        </FlexBox>
      );

    default:
      return null;
  }
};
