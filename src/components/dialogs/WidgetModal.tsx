import React from 'react';
import {
  FlexBox,
  FlexBoxDirection,
  FlexBoxJustifyContent,
  FlexBoxAlignItems,
  Button,
  Title,
  Icon
} from '@ui5/webcomponents-react';
import '@ui5/webcomponents-icons/dist/decline.js';

interface WidgetModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  width?: string;
  height?: string;
  maxWidth?: string;
  maxHeight?: string;
  closable?: boolean;
}

const WidgetModal: React.FC<WidgetModalProps> = ({
  open,
  onClose,
  title,
  children,
  footer,
  width = '500px',
  height = 'auto',
  maxWidth = '90%',
  maxHeight = '90%',
  closable = true
}) => {
  if (!open) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (closable && e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="widget-modal-backdrop"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '16px',
        boxSizing: 'border-box'
      }}
      onClick={handleBackdropClick}
    >
      <div
        className="widget-modal-content"
        style={{
          backgroundColor: 'var(--sapBackgroundColor)',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
          width,
          height,
          maxWidth,
          maxHeight,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          border: '1px solid var(--sapGroup_TitleBorderColor)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--sapGroup_TitleBorderColor)',
            backgroundColor: 'var(--sapObjectHeader_Background)',
            borderRadius: '12px 12px 0 0',
            flexShrink: 0
          }}
        >
          <FlexBox
            justifyContent={FlexBoxJustifyContent.SpaceBetween}
            alignItems={FlexBoxAlignItems.Center}
          >
            <Title
              level="H4"
              style={{
                margin: 0,
                fontSize: '16px',
                fontWeight: '600',
                color: 'var(--sapGroup_TitleTextColor)'
              }}
            >
              {title}
            </Title>
            {closable && (
              <Button
                design="Transparent"
                icon="decline"
                onClick={onClose}
                style={{
                  borderRadius: '50%',
                  width: '32px',
                  height: '32px'
                }}
              />
            )}
          </FlexBox>
        </div>

        {/* Content */}
        <div
          style={{
            flex: 1,
            overflow: 'auto',
            padding: '20px',
            minHeight: 0
          }}
        >
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div
            style={{
              padding: '16px 20px',
              borderTop: '1px solid var(--sapGroup_TitleBorderColor)',
              backgroundColor: 'var(--sapObjectHeader_Background)',
              borderRadius: '0 0 12px 12px',
              flexShrink: 0
            }}
          >
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

export default WidgetModal;
