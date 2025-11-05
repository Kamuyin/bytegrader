from jupyterhub.auth import Authenticator
from jupyterhub.spawner import Spawner
from traitlets import Unicode, Dict, Bool, Any, validate, TraitError
from ltiauthenticator.lti13.auth import LTI13Authenticator
import sys

c = get_config()

c.JupyterHub.ip = "0.0.0.0"
c.JupyterHub.port = 8000

c.ConfigurableHTTPProxy.wait_for_start_timeout = 60

c.JupyterHub.authenticator_class = "ltiauthenticator.lti13.auth.LTI13Authenticator"
c.Authenticator.allow_all = True
c.Authenticator.admin_users = {"2"}

c.LTI13Authenticator.issuer = "http://localhost:7070"
c.LTI13Authenticator.authorize_url = "http://localhost:7070/mod/lti/auth.php"
c.LTI13Authenticator.jwks_endpoint = "http://localhost:7070/mod/lti/certs.php"
c.LTI13Authenticator.client_id = "3IC49Kld4TSZyrD"
c.LTI13Authenticator.enable_auth_state = True

c.JupyterHub.spawner_class = "simple"

c.Application.log_level = "DEBUG"

c.JupyterHub.services = [
    {
        "name": "bytegrader",
        "api_token": "1442555d6d82d96fc8a69776f19978e442873859c6a003f7be15e61d669e2e1c",
        "url": "http://127.0.0.1:10101",
    }
]

c.JupyterHub.load_roles = [
    {
        "name": "user",
        "scopes": [
            "self",
            "access:services!service=bytegrader",
            "read:users:name!user",
            "read:users:groups!user",
            "access:servers!user",
        ],
        "users": ["*"],
    },
    {
        "name": "server",
        "scopes": [
            "access:servers!user",
            "read:users:activity!user",
            "users:activity!user",
            "admin:auth_state!user",
            "access:services!service=bytegrader",
        ],
    },
    {
        "name": "bytegrader-role",
        "scopes": [
            "read:users:name",
            "admin:auth_state",
            "access:services!service=bytegrader",
            "read:users",
            "list:users",
        ],
        "services": ["bytegrader"],
    },
]