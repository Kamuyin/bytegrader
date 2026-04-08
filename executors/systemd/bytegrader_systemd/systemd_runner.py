from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path
from typing import Iterable, Mapping, MutableMapping, Sequence

ENV_KEY_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")


def ensure_private_directory(path: Path) -> Path:

    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    return path


def render_environment_file(directory: Path, unit_name: str, env: Mapping[str, str]) -> Path:

    ensure_private_directory(directory)
    lines: list[str] = []
    for key, value in sorted(env.items()):
        if not ENV_KEY_PATTERN.match(key):
            raise ValueError(f"Environment key '{key}' is not valid")
        lines.append(f"{key}={value}")
    lines.append("")

    env_path = directory / f"{unit_name}.env"
    content = "\n".join(lines)
    env_path.write_text(content, encoding="utf-8")
    os.chmod(env_path, 0o400)
    return env_path


def build_systemd_run_command(
    *,
    unit_name: str,
    exec_cmd: Sequence[str],
    workdir: Path,
    properties: MutableMapping[str, Iterable[str] | str],
    env_file: Path | None = None,
    slice_name: str | None = None,
    user_mode: bool = False,
) -> list[str]:

    cmd: list[str] = ["systemd-run"]
    if user_mode:
        cmd.append("--user")
    cmd.extend([
        "--unit",
        unit_name,
        "--working-directory",
        str(workdir),
    ])

    if slice_name:
        cmd.append(f"--slice={slice_name}")

    mutable_props = dict(properties)
    if env_file:
        env_prop = mutable_props.setdefault("EnvironmentFile", [])
        if isinstance(env_prop, str):
            env_prop = [env_prop]
        env_prop = list(env_prop)
        env_prop.append(str(env_file))
        mutable_props["EnvironmentFile"] = env_prop

    for key, value in mutable_props.items():
        if isinstance(value, str):
            cmd.append(f"--property={key}={value}")
        else:
            for item in value:
                cmd.append(f"--property={key}={item}")

    cmd.extend(exec_cmd)
    return cmd


async def launch_transient_unit(command: Sequence[str]) -> int:

    process = await asyncio.create_subprocess_exec(*command)
    return await process.wait()


async def query_unit_state(unit_name: str, *, user_mode: bool = False) -> str:

    show_cmd = ["systemctl"]
    if user_mode:
        show_cmd.append("--user")
    show_cmd.extend([
        "show",
        unit_name,
        "--property=SubState",
        "--value",
    ])
    process = await asyncio.create_subprocess_exec(
        *show_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await process.communicate()
    if process.returncode != 0:
        return "unknown"
    return stdout.decode().strip() or "unknown"


async def stop_unit(unit_name: str, *, user_mode: bool = False) -> int:

    cmd = ["systemctl"]
    if user_mode:
        cmd.append("--user")
    cmd.extend(["stop", unit_name])
    process = await asyncio.create_subprocess_exec(*cmd)
    return await process.wait()


async def fetch_unit_logs(unit_name: str, lines: int, *, user_mode: bool = False) -> str:

    cmd = ["journalctl"]
    if user_mode:
        cmd.append("--user")
    cmd.extend([
        f"--unit={unit_name}",
        "--no-pager",
        "--output=short",
        f"--lines={lines}",
    ])
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await process.communicate()
    if process.returncode != 0:
        return ""
    return stdout.decode()