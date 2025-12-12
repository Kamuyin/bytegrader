from traitlets import Instance, Bool, Enum, Integer
from traitlets.config import Configurable, Unicode


class DatabaseConfig(Configurable):
    uri = Unicode(
        "sqlite:///bytegrader.db",
        help="Database URI for BYTE Grader."
    ).tag(config=True)
    echo = Bool(False, help="Echo queries to the console for debugging.").tag(config=True)
    asset_path = Unicode(
        "assets",
        help="Path to store assets for the assignments.",
        allow_none=True,
    ).tag(config=True)

    
    """
    on_resubmission = Enum(
        values=["delete", "archive"],
        default_value="delete",
        help="Action to take on resubmission of an assignment. "
             "'delete' will remove the previous submission, 'archive' will keep it for reference."
    )
    """


class LTISyncTaskConfig(Configurable):
    enabled = Bool(
        False,
        help="Enable/disable the LTI sync task."
    ).tag(config=True)
    interval = Unicode(
        "5m",
        help="Interval for the LTI sync task."
    ).tag(config=True)


class LTIConfig(Configurable):
    enabled = Bool(False, help="Enable/disable LTI configuration").tag(config=True)

    lms_url = Unicode(
        "",
        help="LMS URL for LTI integration."
    ).tag(config=True)
    platform = Enum(
        values=["moodle", "canvas"],
        default_value="moodle",
        help="LTI platform type."
    ).tag(config=True)
    client_id = Unicode("", help="LTI client ID for authentication.").tag(config=True)
    token_url = Unicode(
        "",
        help="Token URL for LTI authentication."
    ).tag(config=True)
    key_path = Unicode(
        "",
        help="Path to the private key for LTI authentication."
    ).tag(config=True)
    lti_url = Unicode(
        "",
        help="LTI URL for the application."
    ).tag(config=True)
    nrps_url = Unicode(
        "",
        help="URL for the Names and Roles Provisioning Service (NRPS)."
    ).tag(config=True)

    sync_task = Instance(
        LTISyncTaskConfig, allow_none=True,
    ).tag(config=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.sync_task is None:
            self.sync_task = LTISyncTaskConfig(parent=self)


class AutogradeConfig(Configurable):
    enabled = Bool(
        False,
        help="Enable/disable autograding for assignments."
    ).tag(config=True)
    workers = Integer(
        16,
        help="Number of workers for autograding tasks. "
             "More workers can speed up processing but may require more resources."
    ).tag(config=True)
    cooldown_period = Unicode(  # ! TBD
        "1h",
        help="Cooldown period for autograding after a submission. "
             "Format: <number><unit>, e.g., '1h' for 1 hour, '30m' for 30 minutes."
    ).tag(config=True)
    executor_class = Unicode(
        "",
        help="Class to handle the execution of autograding tasks. ",
        allow_none=True
    ).tag(config=True)


class BYTEGraderConfig(Configurable):
    database = Instance(DatabaseConfig, allow_none=True).tag(config=True)
    lti = Instance(LTIConfig, allow_none=True).tag(config=True)
    autograde = Instance(AutogradeConfig, allow_none=True).tag(config=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.database is None:
            self.database = DatabaseConfig(parent=self)
        if self.lti is None:
            self.lti = LTIConfig(parent=self)
        if self.autograde is None:
            self.autograde = AutogradeConfig(parent=self)
