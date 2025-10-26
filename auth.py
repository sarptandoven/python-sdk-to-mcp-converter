"""basic authentication support for common sdks."""
import os


def get_auth_for_sdk(sdk_name):
    """return auth config for known sdks."""
    # basic auth providers
    # todo: make this more extensible
    
    if sdk_name == "kubernetes":
        return _kubernetes_auth()
    elif sdk_name == "github":
        return _github_auth()
    elif sdk_name == "azure":
        return _azure_auth()
    else:
        return _generic_auth(sdk_name)


def _kubernetes_auth():
    """load kubernetes config."""
    try:
        from kubernetes import config
        config.load_kube_config()
        return {"type": "kubeconfig"}
    except:
        return {"type": "none"}


def _github_auth():
    """get github token from env."""
    token = os.getenv("GITHUB_TOKEN")
    return {"token": token} if token else {"type": "none"}


def _azure_auth():
    """basic azure credential setup."""
    # todo: implement proper azure auth
    try:
        from azure.identity import DefaultAzureCredential
        return {"credential": DefaultAzureCredential()}
    except:
        return {"type": "none"}


def _generic_auth(sdk_name):
    """try to find api key in env."""
    # look for common patterns
    key_name = f"{sdk_name.upper()}_API_KEY"
    api_key = os.getenv(key_name)
    return {"api_key": api_key} if api_key else {"type": "none"}


def inject_auth(sdk_name, kwargs):
    """inject auth into kwargs for sdk call."""
    auth = get_auth_for_sdk(sdk_name)
    
    # basic injection - needs improvement
    if "token" in auth:
        kwargs["auth"] = auth["token"]
    elif "api_key" in auth:
        kwargs["api_key"] = auth["api_key"]
    
    return kwargs

