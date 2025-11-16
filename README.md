# BYTEGrader

BYTE Grader is an autograding service designed for educational environments. It integrates with JupyterHub and Learning Management Systems through LTI 1.3, providing automated grading capabilities for Jupyter notebooks with support for custom test cases and modular execution environments. It's inspired of [nbgrader](https://github.com/jupyter/nbgrader) which is great but lacks support of LMS synchronization and isolated execution environments for the autograding.

## Overview

BYTEGrader consists of two main components:

- **Backend Service**: A Tornado application that provides RESTful APIs for managing courses, assignments, and submissions with automated grading capabilities
- **JupyterLab Extension**: A TypeScript/React frontend that extends JupyterLab with an interface for instructors and students

The system supports LTI 1.3 integration with platforms like Moodle, allowing grade synchronization and user provisioning through LTI Advantage services (Assignment and Grade Services, Names and Role Provisioning Service).

## Key Features

### Assignment Management

- Create and manage programming assignments with multiple notebook files
- Configure automated tests and grading criteria
- Set due dates, late submission policies, and point allocations
- Allow students to fetch solutions for an assignment with conditions.

### Automated Grading

- Execute student submissions in isolated environments
- Run automated test suites with timeout and resource limits
- Aggregate scores across multiple notebooks and test cases

### LTI 1.3 Integration

- Secure authentication via LTI launch from LMS platforms
- Automatic course and user synchronization through NRPS
- Grade passback to LMS via Assignment and Grade Service (AGS)
- Support for deep linking and resource selection

## Installation

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Database (SQLite, PostgreSQL, etc.)
- JupyterHub

### Setup

1. Install the package

```bash
uv sync
uv pip install -e .
```

2. Set up BYTEGrader configuration
    Please see [example/bytegrader_config.py](example/bytegrader_config.py) for an example configuration.

3. Add the service to JupyterHub (managed or external)

```python
c.JupyterHub.services = [
    {
        "name": "bytegrader",
        "api_token": "1442555d6d82d96fc8a69776f19978e442873859c6a003f7be15e61d669e2e1c", # generate via `openssl rand -hex 32`
        "url": "http://127.0.0.1:10101",
    }
]
```

4. Start the service

```bash
export JUPYTERHUB_SERVICE_PREFIX="/services/bytegrader/"
export JUPYTERHUB_API_TOKEN="1442555d6d82d96fc8a69776f19978e442873859c6a003f7be15e61d669e2e1c"
export JUPYTERHUB_API_URL="http://127.0.0.1:8000/hub/api"
export JUPYTERHUB_SERVICE_NAME="bytegrader"
export JUPYTERHUB_SERVICE_URL="http://0.0.0.0:10101"
export BYTEGRADER_LOG_LEVEL="DEBUG"
bytegrader serve --config bytegrader_config.py
```

### Docker Deployment

WIP, currently broken.

## Usage

### For Instructors

1. **Create a Course**: Navigate to the Courses panel in JupyterLab
2. **Create Assignment Notebooks:**: Notebooks must be created via the `nbgrader` extension. BYTE Grader is compatible with nbgrader's notebooks format.
3. **Create an Assignment**: Use the assignment wizard to configure:
   - Notebook and asset files to include
   - Due dates and late policies
   - Solution policies
4. **Distribute to Students**: Assignment notebooks are automatically preprocessed and distributed
5. **Review Submissions**: View automated grades and provide manual feedback

### For Students

1. **Access Assignments**: Launch JupyterLab via LTI from your LMS
2. **Fetch Assignment**: Open the assignment and get the starter notebook
3. **Complete Work**: Write code in designated solution cells
4. **Submit**: Click submit to send for automated grading
5. **View Results**: See test results after autograding

## Development

### Building the Extension

```bash
jlpm build
```

## Project Structure

```
bytegrader/
├── bytegrader/              # Python backend
│   ├── autograde/          # Grading queue and workers
│   ├── cli/                # Command-line interface
│   ├── config/             # Configuration system
│   ├── core/               # Core models, auth, database
│   ├── extensions/         # JupyterLab server extension
│   ├── handlers/           # Tornado request handlers
│   ├── preprocessors/      # Notebook preprocessors
│   ├── repositories/       # Data access layer
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # Business logic
│   └── tasks/              # Background tasks
├── src/                    # TypeScript frontend
│   ├── components/         # React components
│   ├── hooks/              # Custom React hooks
│   ├── services/           # API client
│   ├── stores/             # State management
│   └── widgets/            # JupyterLab widgets
├── docker/                 # Docker configurations
├── tests/                  # Test suite (TBD)
└── docs/                   # Documentation (TBD)
```

## License

This project is licensed under the BSD 3-Clause License. See the LICENSE file for details.

## Acknowledgments

Developed as part of the BYTE Challenge initiative to enhance computer science education for students.

BYTE Grader builds upon the work of the [nbgrader](https://github.com/jupyter/nbgrader) project. The core project architecture, notebook format, preprocessor patterns, and notebook manipulation strategies were inspired by nbgrader's approach. I am grateful to the nbgrader team for providing their software as open source. Without them this project would have never existed.
