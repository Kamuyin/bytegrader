import React, { useEffect, useMemo } from 'react';
import { 
  Avatar, 
  ResponsivePopover,
  FlexBox,
  FlexBoxDirection,
  FlexBoxAlignItems,
  Text,
  Icon,
  Button
} from '@ui5/webcomponents-react';
import '@ui5/webcomponents-icons/dist/person-placeholder.js';
import logo from '../../style/logo.png';
import { useUserStore } from '../stores/userStore';
import ErrorDialog from './dialogs/ErrorDialog';
import { useErrorHandler } from '../hooks/useErrorHandler';

const topBarStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '0 1rem',
  height: '3.5rem',
  backgroundColor: 'var(--sapShell_Background, #354a5f)',
  boxShadow: 'var(--sapContent_Shadow0)',
  color: 'var(--sapShell_Color, #ffffff)',
};

const logoStyle: React.CSSProperties = {
  height: '80%',
  width: 'auto',
};

const TopBar: React.FC = () => {
  const [userMenuOpen, setUserMenuOpen] = React.useState(false);
  const [userMenuOpener, setUserMenuOpener] = React.useState<HTMLElement | null>(null);
  const [hasAttemptedFetch, setHasAttemptedFetch] = React.useState(false);
  
  const userInfo = useUserStore(state => state.userInfo);
  const loading = useUserStore(state => state.loading);
  const fetchUserInfo = useUserStore(state => state.fetchUserInfo);

  const { errorInfo, isErrorDialogOpen, showError, clearError } = useErrorHandler();

  useEffect(() => {
    if (!userInfo && !loading && !hasAttemptedFetch) {
      setHasAttemptedFetch(true);
      fetchUserInfo().catch(err => {
        showError(err, 'Load User Info Error', true);
      });
    }
  }, [userInfo, loading, fetchUserInfo, hasAttemptedFetch, showError]);

  const displayName = useMemo(() => {
    if (loading) return 'Loading...';
    if (!userInfo) return 'User';
    const fullName = `${userInfo.first_name} ${userInfo.last_name}`.trim();
    return fullName || userInfo.username;
  }, [loading, userInfo]);

  const handleProfileClick = (event: any) => {
    setUserMenuOpener(event.currentTarget);
    setUserMenuOpen(true);
  };

  const handleUserMenuClose = () => {
    setUserMenuOpen(false);
  };

  return (
    <>
      <header style={topBarStyle}>
        <img 
          src={logo} 
          alt="ByteGrader Logo" 
          style={logoStyle}
        />
        <Avatar
          colorScheme="Accent6"
          icon="employee"
          onClick={handleProfileClick}
          shape="Circle"
          size="XS"
        />
      </header>
      
      <ResponsivePopover
        open={userMenuOpen}
        opener={userMenuOpener || undefined}
        onClose={handleUserMenuClose}
        placement="Bottom"
      >
        <div style={{ padding: '20px', minWidth: '280px' }}>
          <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '16px' }}>
            {loading ? (
              <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '8px', textAlign: 'center' }}>
                <Text style={{ fontSize: '16px', fontWeight: '600' }}>Loading...</Text>
              </FlexBox>
            ) : (
              <>
                <FlexBox direction={FlexBoxDirection.Column} style={{ gap: '4px', textAlign: 'center' }}>
                  <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '8px', justifyContent: 'center' }}>
                    <Text style={{ fontSize: '16px', fontWeight: '600' }}>{displayName}</Text>
                    {userInfo?.is_admin && (
                      <span 
                        style={{ 
                          backgroundColor: '#fee2e2', 
                          color: '#dc2626',
                          padding: '2px 8px', 
                          borderRadius: '12px', 
                          fontSize: '11px',
                          fontWeight: '500',
                          textTransform: 'uppercase'
                        }}
                      >
                        Admin
                      </span>
                    )}
                  </FlexBox>
                  <Text style={{ fontSize: '14px', color: '#666' }}>
                    @{userInfo?.username || 'user'}
                  </Text>
                </FlexBox>
              </>
            )}
          </FlexBox>
        </div>
      </ResponsivePopover>

      <ErrorDialog
        open={isErrorDialogOpen}
        onClose={clearError}
        title={errorInfo?.title}
        message={errorInfo?.message || ''}
        details={errorInfo?.details}
        closable={errorInfo?.closable ?? true}
        onRetry={async () => {
          try {
            setHasAttemptedFetch(false);
            await fetchUserInfo();
            clearError();
          } catch (err) {
            showError(err, 'Load User Info Error', true);
          }
        }}
      />
    </>
  );
};

export default TopBar;
