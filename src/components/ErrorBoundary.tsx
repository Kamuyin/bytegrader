import React from 'react';

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends React.Component<React.PropsWithChildren<{}>, State> {
  constructor(props: {}) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('UI render error', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: '1rem',
            textAlign: 'center',
            color: '#900'
          }}
        >
          <h2>Something went wrong.</h2>
          <p>Please reload the page or try again later.</p>
        </div>
      );
    }
    return this.props.children;
  }
}
