from nbformat import NotebookNode


def is_task(cell: NotebookNode) -> bool:
    if 'nbgrader' not in cell.metadata:
        return False
    return cell.metadata['nbgrader'].get('task', False)


def is_grade(cell: NotebookNode) -> bool:
    if 'nbgrader' not in cell.metadata:
        return False
    return cell.metadata['nbgrader'].get('grade', False)


def is_solution(cell: NotebookNode) -> bool:
    if 'nbgrader' not in cell.metadata:
        return False
    return cell.metadata['nbgrader'].get('solution', False)


def is_locked(cell: NotebookNode) -> bool:
    if 'nbgrader' not in cell.metadata:
        return False
    elif is_solution(cell):
        return False
    elif is_grade(cell):
        return True
    else:
        return cell.metadata['nbgrader'].get('locked', False)