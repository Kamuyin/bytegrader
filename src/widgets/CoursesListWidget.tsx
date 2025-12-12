import { JupyterFrontEnd } from "@jupyterlab/application";
import { ReactWidget } from "@jupyterlab/apputils";
import { ErrorBoundary } from "../components/ErrorBoundary";
import React from 'react';
import TopBar from '../components/TopBar';
import CoursesListPage from '../components/CoursesListPage';
import { JupyterLabThemeProvider } from '../utils/themeSync';
import { COMMAND_IDS } from '../constants';

const CoursesPage: React.FC<{ app: JupyterFrontEnd }> = ({ app }) => {
  const handleCourseClick = async (courseId: string) => {
    await app.commands.execute(COMMAND_IDS.openAssignmentsList, { courseId });
  };

  return (
    <div style={{ 
      height: '100%', 
      width: '100%',
      display: 'flex', 
      flexDirection: 'column',
      overflow: 'hidden',
      minHeight: 0,
      minWidth: 0,
      position: 'relative'
    }}>
      <div style={{ 
        position: 'relative',
        height: '3rem',
        flexShrink: 0,
        zIndex: 100
      }}>
        <TopBar />
      </div>
      
      <div style={{ 
        flex: 1, 
        overflow: 'hidden',
        minHeight: 0,
        minWidth: 0,
        width: '100%'
      }}>
        <CoursesListPage onCourseClick={handleCourseClick} />
      </div>
    </div>
  );
};

export class CoursesListWidget extends ReactWidget {
  private app: JupyterFrontEnd;

  constructor(app: JupyterFrontEnd) {
    super();
    this.app = app;
    this.addClass('bytegrader-courses-list-widget');
    this.title.label = 'Courses';
    this.title.closable = true;
  }

  render(): JSX.Element {
    return (
      <ErrorBoundary>
        <JupyterLabThemeProvider>
          <CoursesPage app={this.app} />
        </JupyterLabThemeProvider>
      </ErrorBoundary>
    );
  }
}