import { ICellModel } from '@jupyterlab/cells';
import { ReadonlyJSONObject } from '@lumino/coreutils';

const NBGRADER_KEY = 'nbgrader';
export const NBGRADER_SCHEMA_VERSION = 3;

export type GradingCellType =
    | ''
    | 'manual'
    | 'task'
    | 'solution'
    | 'tests'
    | 'readonly';

export interface NbgraderData {
    grade?: boolean;
    grade_id?: string;
    locked?: boolean;
    points?: number;
    schema_version?: number;
    solution?: boolean;
    task?: boolean;
}

export interface CellGradingInfo {
    type: GradingCellType;
    id: string;
    points: number;
    locked: boolean;
}

export function getNbgraderData(cell: ICellModel): NbgraderData | null {
    const raw = cell.getMetadata(NBGRADER_KEY);
    if (raw === undefined || raw === null) {
        return null;
    }
    return raw.valueOf() as NbgraderData;
}

export function setNbgraderData(
    cell: ICellModel,
    data: NbgraderData | null
): void {
    if (data === null) {
        if (cell.getMetadata(NBGRADER_KEY) !== undefined) {
            cell.deleteMetadata(NBGRADER_KEY);
        }
        return;
    }
    cell.setMetadata(NBGRADER_KEY, data as unknown as ReadonlyJSONObject);
}

export function gradingInfoFromMetadata(
    data: NbgraderData | null,
    cellType: string
): CellGradingInfo {
    const empty: CellGradingInfo = { type: '', id: '', points: 0, locked: false };
    if (!data) {
        return empty;
    }

    let type: GradingCellType = '';
    if (data.task) {
        type = 'task';
    } else if (data.solution && data.grade) {
        type = 'manual';
    } else if (data.solution && cellType === 'code') {
        type = 'solution';
    } else if (data.grade && cellType === 'code') {
        type = 'tests';
    } else if (data.locked) {
        type = 'readonly';
    }

    if (
        !data.task &&
        cellType !== 'code' &&
        data.solution !== data.grade &&
        (data.solution || data.grade)
    ) {
        return empty;
    }

    const id = data.grade_id ?? '';
    const points = toFloat(data.points);
    const locked = !data.solution && (isGradable(data) || !!data.locked);

    return { type, id, points, locked };
}

export function metadataFromGradingInfo(
    info: CellGradingInfo
): NbgraderData | null {
    if (info.type === '') {
        return null;
    }

    const isSolution = info.type === 'manual' || info.type === 'solution';
    const isGrade = info.type === 'manual' || info.type === 'tests';
    const isTask = info.type === 'task';
    const locked = isSolution
        ? false
        : isGrade || isTask || info.type === 'tests' || info.type === 'readonly';

    const data: NbgraderData = {
        grade: isGrade,
        grade_id: info.id || '',
        locked,
        schema_version: NBGRADER_SCHEMA_VERSION,
        solution: isSolution,
        task: isTask,
    };

    if (isGrade || isTask) {
        data.points = info.points >= 0 ? info.points : 0;
    }

    return data;
}

export function isGradable(data: NbgraderData): boolean {
    return !!data.grade || !!data.task;
}

export function hasGradingRole(data: NbgraderData | null): boolean {
    if (!data) return false;
    return !!data.grade || !!data.solution || !!data.task || !!data.locked;
}

export function validTypesForCell(
    cellType: string
): { value: GradingCellType; label: string }[] {
    const common: { value: GradingCellType; label: string }[] = [
        { value: '', label: '— None —' },
        { value: 'readonly', label: 'Read-only' },
        { value: 'manual', label: 'Manually graded' },
        { value: 'task', label: 'Task' },
    ];
    if (cellType === 'code') {
        return [
            ...common,
            { value: 'solution', label: 'Autograded solution' },
            { value: 'tests', label: 'Autograder tests' },
        ];
    }
    return common;
}

// Helpers

function toFloat(val: unknown): number {
    if (val == null || val === '') return 0;
    if (typeof val === 'string') return parseFloat(val) || 0;
    if (typeof val === 'number') return val;
    return 0;
}

export function randomGradeId(length = 8): string {
    const chars = 'abcdef0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}
