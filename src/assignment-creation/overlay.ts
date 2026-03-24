import { Notebook, NotebookPanel } from '@jupyterlab/notebook';
import { CellStrip, CellStripChangeEvent } from './cell-strip';
import { Cell } from '@jupyterlab/cells';
import { CellList } from '@jupyterlab/notebook/lib/celllist';
import { IObservableList } from '@jupyterlab/observables';
import { ICellModel } from '@jupyterlab/cells';
import { Signal } from '@lumino/signaling';
import { Widget } from '@lumino/widgets';

export class AssignmentOverlay {
    private _panel: NotebookPanel;
    private _pointsLabel: Widget;
    private _strips: Map<Cell, CellStrip> = new Map();
    private _disposed = false;

    constructor(panel: NotebookPanel) {
        this._panel = panel;

        this._pointsLabel = new Widget();
        this._pointsLabel.addClass('bg-assignment-points-label');
        panel.toolbar.addItem('bg-assignment-points', this._pointsLabel);

        for (const cell of panel.content.widgets) {
            this._addStrip(cell);
        }

        panel.model.cells.changed.connect(this._onCellsChanged, this);
        panel.content.activeCellChanged.connect(this._onActiveCellChanged, this);

        this._refreshPoints();
    }

    dispose(): void {
        if (this._disposed) return;
        this._disposed = true;

        this._panel.model?.cells?.changed?.disconnect(this._onCellsChanged, this);
        this._panel.content?.activeCellChanged?.disconnect(this._onActiveCellChanged, this);

        for (const strip of this._strips.values()) {
            strip.dispose();
        }
        this._strips.clear();

        this._pointsLabel.dispose();

        for (const cell of this._panel.content.widgets) {
            cell.node.style.borderLeft = '';
        }

        Signal.clearData(this);
    }

    get isDisposed(): boolean {
        return this._disposed;
    }

    private _addStrip(cell: Cell): void {
        if (this._strips.has(cell)) return;
        const strip = new CellStrip(cell);
        strip.changed.connect(this._onStripChanged, this);
        this._strips.set(cell, strip);
    }

    private _removeStrip(cell: Cell): void {
        const strip = this._strips.get(cell);
        if (strip) {
            strip.dispose();
            this._strips.delete(cell);
        }
    }

    private _onCellsChanged(
        _sender: CellList,
        _args: IObservableList.IChangedArgs<ICellModel>
    ): void {
        const currentCells = new Set(this._panel.content.widgets);
        for (const [cell] of this._strips) {
            if (!currentCells.has(cell)) {
                this._removeStrip(cell);
            }
        }

        if (this._disposed) return;
        for (const cell of this._panel.content.widgets) {
            if (!this._strips.has(cell)) {
                this._addStrip(cell);
            }
        }
        this._refreshPoints();
    }

    private _onActiveCellChanged(_: Notebook, cell: Cell | null): void {
        if (this._disposed || !cell || this._strips.has(cell)) return;
        this._addStrip(cell);
        this._refreshPoints();
    }

    private _onStripChanged(
        _strip: CellStrip,
        _event: CellStripChangeEvent
    ): void {
        this._refreshPoints();
    }

    private _computeTotalPoints(): number {
        let total = 0;
        for (const strip of this._strips.values()) {
            const { type, points } = strip.info;
            if (type === 'tests' || type === 'manual' || type === 'task') {
                total += points;
            }
        }
        return total;
    }

    private _refreshPoints(): void {
        const total = this._computeTotalPoints();
        this._pointsLabel.node.textContent = `Σ ${total} pts`;
    }
}
