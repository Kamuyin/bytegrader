import React, { useEffect, useState } from 'react';
import { ThemeProvider } from '@ui5/webcomponents-react';
import { setTheme } from '@ui5/webcomponents-base/dist/config/Theme';
import { reRenderAllUI5Elements } from '@ui5/webcomponents-base/dist/Render';
import '@ui5/webcomponents-react/dist/Assets';

const THEME_MAPPING = {
  'JupyterLab Light': 'sap_horizon',
  'JupyterLab Dark': 'sap_horizon_dark',
  'JupyterLab High Contrast Light': 'sap_horizon_hcb',
  'JupyterLab High Contrast Dark': 'sap_horizon_hcw'
} as const;

function detectJupyterLabTheme(): string {
  const themeNameOnBody = document.body?.getAttribute('data-jp-theme-name');
  const themeNameOnHtml = document.documentElement.getAttribute('data-jp-theme-name');
  const themeName = themeNameOnBody || themeNameOnHtml;
  
  if (themeName) {
    return themeName;
  }
  
  const isLightOnBody = document.body?.getAttribute('data-jp-theme-light');
  const isLightOnHtml = document.documentElement.getAttribute('data-jp-theme-light');
  const isLight = isLightOnBody || isLightOnHtml;
  
  if (isLight === 'true') {
    return 'JupyterLab Light';
  } else if (isLight === 'false') {
    return 'JupyterLab Dark';
  }
  
  const computedStyle = getComputedStyle(document.documentElement);
  const backgroundColor = computedStyle.getPropertyValue('--jp-layout-color0').trim();
  
  const isDarkBackground = backgroundColor && (
    backgroundColor.includes('rgb(33') ||
    backgroundColor.includes('#21') ||
    backgroundColor.includes('#1e') ||
    backgroundColor.includes('#2d') ||
    backgroundColor.includes('rgb(24') ||
    backgroundColor.includes('rgb(30') ||
    backgroundColor.includes('#111') ||
    backgroundColor.includes('#000') ||
    backgroundColor.includes('rgb(0,') ||
    backgroundColor.includes('rgb(17,') ||
    (backgroundColor.startsWith('#') && backgroundColor.length === 4 && 
     parseInt(backgroundColor.substring(1, 2), 16) < 8)
  );
  
  return isDarkBackground ? 'JupyterLab Dark' : 'JupyterLab Light';
}

function mapToUI5Theme(jupyterLabTheme: string): string {
  return THEME_MAPPING[jupyterLabTheme as keyof typeof THEME_MAPPING] || 'sap_horizon';
}

export const JupyterLabThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentTheme, setCurrentTheme] = useState(() => {
    const jupyterTheme = detectJupyterLabTheme();
    return mapToUI5Theme(jupyterTheme);
  });

  useEffect(() => {
    setTheme(currentTheme);
    
    setTimeout(() => {
      reRenderAllUI5Elements({ themeAware: true });
    }, 0);

    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && 
            (mutation.attributeName === 'data-jp-theme-light' || 
             mutation.attributeName === 'data-jp-theme-name' ||
             mutation.attributeName === 'class')) {
          
          const newJupyterTheme = detectJupyterLabTheme();
          const newUI5Theme = mapToUI5Theme(newJupyterTheme);
          
          if (newUI5Theme !== currentTheme) {
            setCurrentTheme(newUI5Theme);
            setTheme(newUI5Theme);
            
            setTimeout(() => {
              reRenderAllUI5Elements({ themeAware: true });
            }, 0);
          }
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-jp-theme-light', 'data-jp-theme-name', 'class'],
      attributeOldValue: true
    });
    
    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ['class', 'data-jp-theme-light', 'data-jp-theme-name'],
      attributeOldValue: true
    });

    return () => {
      observer.disconnect();
    };
  }, [currentTheme]);

  return (
    <ThemeProvider>
      {children}
    </ThemeProvider>
  );
};

export default JupyterLabThemeProvider;
