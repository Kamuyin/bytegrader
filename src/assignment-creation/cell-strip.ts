import { Cell } from '@jupyterlab/cells';
import { ISignal, Signal } from '@lumino/signaling';
import { Widget, PanelLayout } from '@lumino/widgets';
import {
    CellGradingInfo,
    GradingCellType,
    getNbgraderData,
    gradingInfoFromMetadata,
    metadataFromGradingInfo,
    setNbgraderData,
    randomGradeId,
    validTypesForCell
} from './model';

const CSS = {
    strip: 'bg-cell-strip',
    typeLabel: 'bg-cell-strip-type-label',
    select: 'bg-cell-strip-select',
    idGroup: 'bg-cell-strip-id-group',
    idInput: 'bg-cell-strip-id-input',
    pointsGroup: 'bg-cell-strip-points-group',
    pointsInput: 'bg-cell-strip-points-input',
    label: 'bg-cell-strip-label',
    lockIcon: 'bg-cell-strip-lock',
} as const;


const TYPE_COLORS: Record<GradingCellType, string> = {
    '': 'transparent',
    solution: '#1976d2',
    tests: '#388e3c',
    manual: '#f57c00',
    task: '#7b1fa2',
    readonly: '#757575',
};

export interface CellStripChangeEvent {
    cell: Cell;
    info: CellGradingInfo;
}

// Inline-Toolbar on top of each cell
export class CellStrip extends Widget {
    private _cell: Cell;
    private _selectEl: HTMLSelectElement;
    private _idInputEl: HTMLInputElement;
    private _pointsInputEl: HTMLInputElement;
    private _idGroup: HTMLDivElement;
    private _pointsGroup: HTMLDivElement;
    private _lockIcon: HTMLSpanElement;
    private _changed = new Signal<this, CellStripChangeEvent>(this);
    private _currentInfo: CellGradingInfo;

    constructor(cell: Cell) {
        super();
        this.addClass(CSS.strip);
        this._cell = cell;
        this._currentInfo = this._readInfo();
        this._buildDom();
        this._syncUi();
        this._inject();
    }

    get changed(): ISignal<this, CellStripChangeEvent> {
        return this._changed;
    }

    get info(): CellGradingInfo {
        return this._currentInfo;
    }

    refresh(): void {
        this._currentInfo = this._readInfo();
        this._syncUi();
    }

    dispose(): void {
        if (this.isDisposed) return;
        Signal.clearData(this);
        super.dispose();
    }

    private _buildDom(): void {
        const strip = this.node;

        const typeLabel = document.createElement('span');
        typeLabel.className = CSS.typeLabel;
        typeLabel.textContent = 'Type:';

        this._selectEl = document.createElement('select');
        this._selectEl.className = CSS.select;
        this._populateOptions();
        this._selectEl.addEventListener('change', this._onTypeChange);

        this._idGroup = document.createElement('div');
        this._idGroup.className = CSS.idGroup;
        const idLabel = document.createElement('span');
        idLabel.className = CSS.label;
        idLabel.textContent = 'ID:';
        this._idInputEl = document.createElement('input');
        this._idInputEl.className = CSS.idInput;
        this._idInputEl.type = 'text';
        this._idInputEl.placeholder = 'cell_id';
        this._idInputEl.addEventListener('change', this._onInputChange);
        this._idGroup.appendChild(idLabel);
        this._idGroup.appendChild(this._idInputEl);

        this._pointsGroup = document.createElement('div');
        this._pointsGroup.className = CSS.pointsGroup;
        const ptsLabel = document.createElement('span');
        ptsLabel.className = CSS.label;
        ptsLabel.textContent = 'Points:';
        this._pointsInputEl = document.createElement('input');
        this._pointsInputEl.className = CSS.pointsInput;
        this._pointsInputEl.type = 'number';
        this._pointsInputEl.min = '0';
        this._pointsInputEl.step = '1';
        this._pointsInputEl.addEventListener('change', this._onInputChange);
        this._pointsGroup.appendChild(ptsLabel);
        this._pointsGroup.appendChild(this._pointsInputEl);

        this._lockIcon = document.createElement('span');
        this._lockIcon.className = CSS.lockIcon;
        this._lockIcon.title = 'Cell is locked (student edits will be overwritten)';

        strip.appendChild(typeLabel);
        strip.appendChild(this._selectEl);
        strip.appendChild(this._idGroup);
        strip.appendChild(this._pointsGroup);
        strip.appendChild(this._lockIcon);
    }

    private _populateOptions(): void {
        const cellType = this._cell.model.type;
        const options = validTypesForCell(cellType);
        for (const opt of options) {
            const el = document.createElement('option');
            el.value = opt.value;
            el.textContent = opt.label;
            this._selectEl.appendChild(el);
        }
    }

    private _inject(): void {
        const layout = this._cell.layout as PanelLayout;
        if (layout && layout.insertWidget) {
            layout.insertWidget(0, this);
        } else {
            const node = this._cell.node;
            node.insertBefore(this.node, node.firstChild);
        }
        this._updateBorder();
    }

    private _onTypeChange = (): void => {
        const newType = this._selectEl.value as GradingCellType;
        const prev = this._currentInfo;

        this._currentInfo = {
            type: newType,
            id: newType !== '' ? (prev.id || randomGradeId()) : '',
            points: newType !== '' ? prev.points : 0,
            locked: false,
        };

        this._writeMetadata();
        this._syncUi();
        this._emitChanged();
    };

    private _onInputChange = (): void => {
        this._currentInfo = {
            ...this._currentInfo,
            id: this._idInputEl.value,
            points: parseFloat(this._pointsInputEl.value) || 0,
        };
        this._writeMetadata();
        this._emitChanged();
    };

    private _readInfo(): CellGradingInfo {
        const raw = getNbgraderData(this._cell.model);
        return gradingInfoFromMetadata(raw, this._cell.model.type);
    }

    private _writeMetadata(): void {
        const data = metadataFromGradingInfo(this._currentInfo);
        setNbgraderData(this._cell.model, data);
    }

    private _syncUi(): void {
        const info = this._currentInfo;

        this._selectEl.value = info.type;

        const showId = info.type !== '';
        this._idGroup.style.display = showId ? '' : 'none';
        this._idInputEl.value = info.id;

        const showPoints =
            info.type === 'manual' ||
            info.type === 'tests' ||
            info.type === 'task';
        this._pointsGroup.style.display = showPoints ? '' : 'none';
        this._pointsInputEl.value = info.points.toString();

        const data = metadataFromGradingInfo(info);
        const isLocked = data?.locked ?? false;
        this._lockIcon.textContent = isLocked ? '🔒' : '';
        this._lockIcon.style.display = isLocked ? '' : 'none';

        this._updateBorder();
    }

    private _updateBorder(): void {
        const color = TYPE_COLORS[this._currentInfo.type];
        this._cell.node.style.borderLeft =
            color === 'transparent' ? '' : `4px solid ${color}`;
        if (color === 'transparent') {
            this._cell.node.style.borderLeft = '';
        }
    }

    private _emitChanged(): void {
        this._changed.emit({ cell: this._cell, info: this._currentInfo });
    }
}
