import { useState, useCallback } from 'react';
import { ApiErrorException } from '../utils';

export interface ErrorInfo {
  title: string;
  message: string;
  details?: string;
  closable: boolean;
}

export const useErrorHandler = () => {
  const [errorInfo, setErrorInfo] = useState<ErrorInfo | null>(null);
  const [isErrorDialogOpen, setIsErrorDialogOpen] = useState(false);

  const showError = useCallback((error: Error | unknown, context: string, closable: boolean = true) => {
    let message = 'An unexpected error occurred. Please try again.';
    let details: string | undefined;

    if (error instanceof ApiErrorException) {
      message = error.message || 'The server returned an error.';
      details = `Error Code: ${error.code}${error.request_id ? `\nRequest ID: ${error.request_id}` : ''}`;
    } else if (error instanceof Error) {
      message = error.message;
      details = error.stack;
    } else if (typeof error === 'string') {
      message = error;
    }

    setErrorInfo({
      title: context,
      message,
      details,
      closable
    });
    setIsErrorDialogOpen(true);
  }, []);

  const clearError = useCallback(() => {
    setIsErrorDialogOpen(false);
    setTimeout(() => setErrorInfo(null), 300);
  }, []);

  return {
    errorInfo,
    isErrorDialogOpen,
    showError,
    clearError
  };
};
