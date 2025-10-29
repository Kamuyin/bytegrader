import React from 'react';
import {
  FlexBox,
  FlexBoxJustifyContent,
  FlexBoxAlignItems,
  Button,
  Text,
  Icon
} from '@ui5/webcomponents-react';
import '@ui5/webcomponents-icons/dist/warning.js';
import WidgetModal from './WidgetModal';

interface ConfirmationDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  confirmDesign?: 'Emphasized' | 'Negative' | 'Positive' | 'Transparent';
  type?: 'Warning' | 'Error' | 'Information';
}

const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  open,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmDesign = 'Emphasized',
  type = 'Warning'
}) => {
  const getTypeConfig = () => {
    switch (type) {
      case 'Error':
        return {
          icon: 'warning',
          iconColor: 'var(--sapNegativeColor)',
          backgroundColor: '#fef7f7'
        };
      case 'Warning':
        return {
          icon: 'warning',
          iconColor: 'var(--sapCriticalColor)',
          backgroundColor: '#fffdf5'
        };
      case 'Information':
        return {
          icon: 'information',
          iconColor: 'var(--sapInformationColor)',
          backgroundColor: '#f5f9ff'
        };
      default:
        return {
          icon: 'warning',
          iconColor: 'var(--sapCriticalColor)',
          backgroundColor: '#fffdf5'
        };
    }
  };

  const typeConfig = getTypeConfig();

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <WidgetModal
      open={open}
      onClose={onClose}
      title={title}
      width="400px"
      footer={
        <FlexBox justifyContent={FlexBoxJustifyContent.End} style={{ gap: '8px' }}>
          <Button design="Transparent" onClick={onClose}>
            {cancelText}
          </Button>
          <Button design={confirmDesign} onClick={handleConfirm}>
            {confirmText}
          </Button>
        </FlexBox>
      }
    >
      <FlexBox
        alignItems={FlexBoxAlignItems.Start}
        style={{
          gap: '12px',
          padding: '16px',
          backgroundColor: typeConfig.backgroundColor,
          borderRadius: '8px',
          border: `1px solid ${typeConfig.iconColor}20`
        }}
      >
        <Icon
          name={typeConfig.icon}
          style={{
            fontSize: '20px',
            color: typeConfig.iconColor,
            flexShrink: 0,
            marginTop: '2px'
          }}
        />
        <Text style={{ fontSize: '14px', lineHeight: '1.4', whiteSpace: 'pre-line' }}>
          {message}
        </Text>
      </FlexBox>
    </WidgetModal>
  );
};

export default ConfirmationDialog;
