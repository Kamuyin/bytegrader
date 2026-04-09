from traitlets import Bool, Dict, Integer, Unicode
from traitlets.config import Configurable


class SystemdExecutorConfig(Configurable):

    user_mode = Bool(
        False,
        help=(
            "Runs systemd commands with --user. Requires an active user session "
            "(e.g., via 'loginctl enable-linger <user>')."
        ),
    ).tag(config=True)

    unit_name_template = Unicode(
        "bytegrader-{job_id}",
        help=(
            "Template for naming transient systemd units. The placeholder "
            "'{job_id}' is substituted with the generated job identifier."
        ),
    ).tag(config=True)

    job_root = Unicode(
        "/var/lib/bytegrader/jobs",
        help="Filesystem root where job bundles are materialised during grading.",
    ).tag(config=True)

    runtime_directory_root = Unicode(
        "/run/bytegrader",
        help="Base directory used for transient runtime files consumed by systemd.",
    ).tag(config=True)

    working_directory = Unicode(
        "/var/lib/bytegrader/work",
        help="Working directory exposed to the runner process inside the unit.",
    ).tag(config=True)

    runner_entrypoint = Unicode(
        "python3 -m bytegrader_systemd.runner",
        help="Command executed by systemd to process a bundle and emit results.",
    ).tag(config=True)

    unit_slice = Unicode(
        default_value="",
        allow_none=True,
        help="Optional systemd slice that should host the transient unit.",
    ).tag(config=True)

    start_timeout = Integer(
        120,
        help="Maximum seconds to wait for the transient service to report completion.",
    ).tag(config=True)

    stop_timeout = Integer(
        30,
        help="Grace period before forcefully tearing down lingering units.",
    ).tag(config=True)

    preserve_job_artifacts = Bool(
        False,
        help="Keep job bundles on disk instead of cleaning them.",
    ).tag(config=True)

    result_filename = Unicode(
        "results.json",
        help="Relative filename storing execution outcomes within the job bundle.",
    ).tag(config=True)

    journal_max_lines = Integer(
        200,
        help="Limit the number of journald log lines captured when a unit fails.",
    ).tag(config=True)

    extra_unit_properties = Dict(
        {},
        help=(
            "Additional systemd unit properties passed to the transient unit. "
        ),
    ).tag(config=True)