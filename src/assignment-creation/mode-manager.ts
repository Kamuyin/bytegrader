import { INotebookTracker, NotebookPanel } from '@jupyterlab/notebook';
import { ISignal, Signal } from '@lumino/signaling';
import { AssignmentOverlay } from './overlay';

// Top-level controller for assignment creation 
export class AssignmentModeManager {
    private _active = false;
    private _tracker: INotebookTracker;
    private _overlays = new Map<NotebookPanel, AssignmentOverlay>();
    private _toggled = new Signal<this, boolean>(this);
    private _disposed = false;

    static readonly CSS_MODE_ACTIVE = 'bg-assignment-mode-active';

    constructor(tracker: INotebookTracker) {
        this._tracker = tracker;
        this._tracker.currentChanged.connect(this._onCurrentChanged, this);
    }

    get isActive(): boolean {
        return this._active;
    }

    get toggled(): ISignal<this, boolean> {
        return this._toggled;
    }

    toggle(): boolean {
        if (this._active) {
            this._deactivate();
        } else {
            this._activate();
        }
        return this._active;
    }

    dispose(): void {
        if (this._disposed) return;
        this._disposed = true;
        this._deactivate();
        this._tracker.currentChanged.disconnect(this._onCurrentChanged, this);
        Signal.clearData(this);
    }

    private _activate(): void {
        this._active = true;

        const panel = this._tracker.currentWidget;
        if (panel) {
            this._ensureOverlay(panel);
        }

        this._toggled.emit(true);
    }

    private _deactivate(): void {
        this._active = false;

        for (const [panel, overlay] of this._overlays) {
            panel.node.classList.remove(AssignmentModeManager.CSS_MODE_ACTIVE);
            overlay.dispose();
        }
        this._overlays.clear();

        this._toggled.emit(false);
    }

    private _onCurrentChanged(
        _tracker: INotebookTracker,
        panel: NotebookPanel | null
    ): void {
        if (!this._active) return;
        if (!panel) return;

        this._ensureOverlay(panel);
    }

    private _ensureOverlay(panel: NotebookPanel): void {
        if (this._overlays.has(panel)) return;

        panel.revealed.then(() => {
            if (!this._active) return;
            if (this._overlays.has(panel)) return;

            const overlay = new AssignmentOverlay(panel);
            this._overlays.set(panel, overlay);
            panel.node.classList.add(AssignmentModeManager.CSS_MODE_ACTIVE);

            panel.disposed.connect(() => {
                const ov = this._overlays.get(panel);
                if (ov) {
                    ov.dispose();
                    this._overlays.delete(panel);
                }
            });
        });
    }
}
