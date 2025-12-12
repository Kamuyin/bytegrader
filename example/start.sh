export JUPYTERHUB_SERVICE_PREFIX="/services/bytegrader/"
export JUPYTERHUB_API_TOKEN="1442555d6d82d96fc8a69776f19978e442873859c6a003f7be15e61d669e2e1c"
export JUPYTERHUB_API_URL="http://127.0.0.1:8000/hub/api"
export JUPYTERHUB_SERVICE_NAME="bytegrader"
export JUPYTERHUB_SERVICE_URL="http://0.0.0.0:10101"
export BYTEGRADER_LOG_LEVEL="DEBUG"
#export SENTRY_DSN="http://f816ac1bb0294a7b8dde1e19d509e0d0@127.0.0.1:6060/1"
bytegrader serve --config bytegrader_config.py