# `systemd` Autograde-Executor for BYTE Grader

## Overview

The `bytegrader-systemd-spawner` is a secure execution environment for running untrusted student notebook submissions in the BYTE Grader autograding system. It uses Linux systemd's transient units and isolation features to execute Jupyter notebooks in a sandboxed environment, providing strong process isolation, resource management, and security boundaries.