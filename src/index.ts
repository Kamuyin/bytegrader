import { ILabShell, ILayoutRestorer, JupyterFrontEnd, JupyterFrontEndPlugin } from "@jupyterlab/application";
import { ICommandPalette, MainAreaWidget, WidgetTracker } from "@jupyterlab/apputils";
import { PageConfig } from "@jupyterlab/coreutils";
import { IMainMenu } from '@jupyterlab/mainmenu';
import { INotebookShell } from "@jupyter-notebook/application";
import { INotebookTree } from "@jupyter-notebook/tree";
import { Menu } from '@lumino/widgets';
import { CoursesListWidget } from "./widgets/CoursesListWidget";
import { AssignmentsListWidget } from "./widgets/AssignmentsListWidget";
import { PLUGIN_ID, COMMAND_IDS } from './constants';

const bytegraderPlugin: JupyterFrontEndPlugin<void> = {
    id: PLUGIN_ID,
    autoStart: true,
    requires: [IMainMenu],
    optional: [ICommandPalette, ILabShell, INotebookShell, ILayoutRestorer, INotebookTree],
    activate: (
        app: JupyterFrontEnd,
        mainMenu: IMainMenu,
        palette: ICommandPalette | null,
        labShell: ILabShell | null,
        notebookShell: INotebookShell | null,
        restorer: ILayoutRestorer | null,
        notebookTree: INotebookTree | null
    ) => {

        let isLabEnvironment = false;
        let isNotebookTreePage = false;
        let isNotebookEditPage = false;

        if (labShell) {
            isLabEnvironment = true;
        } else if (notebookShell) {
            const page = PageConfig.getOption('notebookPage');
            if (page === 'tree') {
                isNotebookTreePage = true;
            } else if (page === 'notebooks') {
                isNotebookEditPage = true;
            }
        }

        if (!(isLabEnvironment || isNotebookTreePage || isNotebookEditPage)) {
            console.error('Unsupported environment');
            return;
        }

        const coursesListTracker = new WidgetTracker<MainAreaWidget<CoursesListWidget>>({
            namespace: 'bytegrader-courses-list'
        });

        const assignmentsListTracker = new WidgetTracker<MainAreaWidget<AssignmentsListWidget>>({
            namespace: 'bytegrader-assignments-list'
        });

        let coursesListWidget: MainAreaWidget<CoursesListWidget> | null = null;
        let assignmentsListWidget: MainAreaWidget<AssignmentsListWidget> | null = null;

        app.commands.addCommand(COMMAND_IDS.openCoursesList, {
            label: 'My Courses',
            caption: 'View and manage your courses',
            execute: () => {
                if (!coursesListWidget || coursesListWidget.isDisposed) {
                    const content = new CoursesListWidget(app);
                    coursesListWidget = new MainAreaWidget({ content });
                    coursesListWidget.id = 'bytegrader-courses-list';
                    coursesListWidget.addClass('bytegrader-mainarea-widget');
                    coursesListWidget.title.label = 'My Courses';
                    coursesListWidget.title.caption = 'View and manage your courses';
                    coursesListWidget.title.closable = true;
                }

                if (!coursesListTracker.has(coursesListWidget)) {
                    coursesListTracker.add(coursesListWidget);
                }

                if (!coursesListWidget.isAttached) {
                    if (notebookTree) {
                        notebookTree.addWidget(coursesListWidget);
                        notebookTree.currentWidget = coursesListWidget;
                    } else {
                        app.shell.add(coursesListWidget, 'main');
                    }
                }

                coursesListWidget.content.update();
                app.shell.activateById(coursesListWidget.id);
            }
        });

        app.commands.addCommand(COMMAND_IDS.openAssignmentsList, {
            label: 'Assignment List',
            caption: 'View and manage assignments',
            execute: (args?: any) => {
                const courseId = args?.courseId;
                
                if (!assignmentsListWidget || assignmentsListWidget.isDisposed) {
                    const content = new AssignmentsListWidget(app, courseId);
                    assignmentsListWidget = new MainAreaWidget({ content });
                    assignmentsListWidget.id = 'bytegrader-assignments-list';
                    assignmentsListWidget.addClass('bytegrader-mainarea-widget');
                    
                    assignmentsListWidget.title.label = 'Assignments';
                    
                    assignmentsListWidget.title.caption = 'View and manage assignments';
                    assignmentsListWidget.title.closable = true;
                } else {
                    if (courseId) {
                        assignmentsListWidget.content.setCourse(courseId);
                    }
                }

                if (!assignmentsListTracker.has(assignmentsListWidget)) {
                    assignmentsListTracker.add(assignmentsListWidget);
                }

                if (!assignmentsListWidget.isAttached) {
                    if (notebookTree) {
                        notebookTree.addWidget(assignmentsListWidget);
                        notebookTree.currentWidget = assignmentsListWidget;
                    } else {
                        app.shell.add(assignmentsListWidget, 'main');
                    }
                }

                assignmentsListWidget.content.update();
                app.shell.activateById(assignmentsListWidget.id);
            }
        });

        const bytegraderMenu = new Menu({ commands: app.commands });
        bytegraderMenu.id = 'jp-mainmenu-bytegrader';
        bytegraderMenu.title.label = 'BYTE Grader';

        if (isLabEnvironment || isNotebookTreePage) {
            bytegraderMenu.addItem({
                command: COMMAND_IDS.openCoursesList,
                type: 'command'
            });

            bytegraderMenu.addItem({ 
                command: COMMAND_IDS.openAssignmentsList,
                type: 'command'
            });
        }

        if (bytegraderMenu.items.length > 0) {
            mainMenu.addMenu(bytegraderMenu);
        }

        if (palette && (isLabEnvironment || isNotebookTreePage)) {
            const category = 'BYTE Grader';

            palette.addItem({
                command: COMMAND_IDS.openCoursesList,
                category
            });

            palette.addItem({
                command: COMMAND_IDS.openInstructorTools,
                category
            });
        }

        if (restorer) {
            restorer.restore(coursesListTracker, {
                command: COMMAND_IDS.openCoursesList,
                name: () => 'bytegrader-courses-list'
            });

            restorer.restore(assignmentsListTracker, {
                command: COMMAND_IDS.openAssignmentsList,
                name: () => 'bytegrader-assignments-list'
            });
        }

        console.debug('ByteGrader extension activated successfully!');
        console.debug(`Environment: Lab=${isLabEnvironment}, NotebookTree=${isNotebookTreePage}, NotebookEdit=${isNotebookEditPage}`);
    }
};

export default bytegraderPlugin;
