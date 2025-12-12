import React from 'react';
import { Icon, Text } from '@ui5/webcomponents-react';

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ message = 'Loading...' }) => (
  <div
    style={{
      height: '100%',
      width: '100%',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column',
      gap: '16px'
    }}
    role="status"
    aria-live="polite"
  >
    <Icon name="refresh" style={{ fontSize: '48px', color: 'var(--sapAccentColor7)' }} />
    <Text style={{ fontSize: '16px', color: 'var(--sapNeutralTextColor)' }}>{message}</Text>
  </div>
);

interface ErrorStateProps {
  error: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ error, onRetry }) => (
  <div
    style={{
      height: '100%',
      width: '100%',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '16px',
      padding: '24px'
    }}
    role="alert"
    aria-live="assertive"
  >
    <Icon name="error" style={{ fontSize: '48px', color: 'var(--sapErrorColor)' }} />
    <Text style={{ color: 'var(--sapErrorColor)', fontSize: '18px', fontWeight: '600', textAlign: 'center' }}>
      {error}
    </Text>
    {onRetry && (
      <button onClick={onRetry} style={{ marginTop: '8px' }}>
        Retry
      </button>
    )}
  </div>
);
