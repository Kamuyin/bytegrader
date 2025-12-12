import React from 'react';
import { Button, Text } from '@ui5/webcomponents-react';
import '@ui5/webcomponents-icons/dist/error.js';
import '@ui5/webcomponents-icons/dist/message-error.js';
import WidgetModal from './WidgetModal';

export interface ErrorDialogProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  message: string;
  details?: string;
  onRetry?: () => void;
  closable?: boolean;
}

const ErrorDialog: React.FC<ErrorDialogProps> = ({
  open,
  onClose,
  title = 'Error',
  message,
  details,
  onRetry,
  closable = true
}) => {
  const handleRetry = async () => {
    if (onRetry) {
      await onRetry();
    }
  };

  const handleClose = () => {
    if (closable) {
      onClose();
    }
  };

  return (
    <WidgetModal
      open={open}
      onClose={handleClose}
      title={title}
      width="460px"
      maxWidth="520px"
      closable={closable}
      footer={
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          {onRetry && (
            <Button design="Emphasized" onClick={handleRetry}>
              Retry
            </Button>
          )}
          {closable && (
            <Button design="Transparent" onClick={handleClose}>
              Close
            </Button>
          )}
        </div>
      }
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <div style={{ flex: 1 }}>
            <Text style={{ fontSize: '14px', lineHeight: '1.5', color: 'var(--sapTextColor)' }}>
              {message}
            </Text>
          </div>
        </div>
        {details && (
          <details style={{ marginTop: '8px' }}>
            <summary style={{ cursor: 'pointer', fontSize: '13px', color: 'var(--sapContent_LabelColor)', fontWeight: '600' }}>
              Details
            </summary>
            <div
              style={{
                marginTop: '8px',
                padding: '12px',
                backgroundColor: 'var(--sapGroup_ContentBackground)',
                borderRadius: '4px',
                fontSize: '12px',
                fontFamily: 'monospace',
                wordBreak: 'break-word',
                maxHeight: '200px',
                overflow: 'auto',
                border: '1px solid var(--sapGroup_TitleBorderColor)'
              }}
            >
              {details}
            </div>
          </details>
        )}
        {
          /*
          {!closable && (
            <div
              style={{
                marginTop: '8px',
                padding: '8px 12px',
                backgroundColor: 'var(--sapErrorBackground)',
                borderRadius: '4px',
                fontSize: '13px',
                color: 'var(--sapErrorColor)',
                border: '1px solid var(--sapErrorBorderColor)'
              }}
            >
              <strong>Note:</strong> This operation is required to continue. Please retry or contact support if the issue persists.
            </div>
          )}
          */
        }
      </div>
    </WidgetModal>
  );
};

export default ErrorDialog;
