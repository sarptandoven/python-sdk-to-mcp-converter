"""authentication support for various sdks."""
import os
from abc import ABC, abstractmethod


class AuthProvider(ABC):
    """base auth provider."""
    
    @abstractmethod
    def can_handle(self, sdk_name):
        """check if this provider handles the sdk."""
        pass
    
    @abstractmethod
    def get_credentials(self):
        """get credentials."""
        pass
    
    @abstractmethod
    def inject(self, kwargs):
        """inject auth into kwargs."""
        pass


class KubernetesAuth(AuthProvider):
    """kubernetes authentication."""
    
    def can_handle(self, sdk_name):
        return sdk_name == "kubernetes"
    
    def get_credentials(self):
        try:
            from kubernetes import config
            config.load_kube_config()
            return {"type": "kubeconfig", "loaded": True}
        except:
            try:
                config.load_incluster_config()
                return {"type": "incluster", "loaded": True}
            except:
                return {"type": "none"}
    
    def inject(self, kwargs):
        # kubernetes client auto-loads config
        return kwargs


class GitHubAuth(AuthProvider):
    """github authentication."""
    
    def can_handle(self, sdk_name):
        return sdk_name == "github"
    
    def get_credentials(self):
        token = os.getenv("GITHUB_TOKEN")
        return {"token": token} if token else {"type": "none"}
    
    def inject(self, kwargs):
        token = os.getenv("GITHUB_TOKEN")
        if token and "auth" not in kwargs:
            kwargs["auth"] = token
        return kwargs


class AzureAuth(AuthProvider):
    """azure authentication."""
    
    def can_handle(self, sdk_name):
        return sdk_name.startswith("azure")
    
    def get_credentials(self):
        try:
            from azure.identity import DefaultAzureCredential
            return {"type": "default_credential"}
        except:
            return {"type": "none"}
    
    def inject(self, kwargs):
        if "credential" not in kwargs:
            try:
                from azure.identity import DefaultAzureCredential
                kwargs["credential"] = DefaultAzureCredential()
            except:
                pass
        return kwargs


class AWSAuth(AuthProvider):
    """aws/boto3 authentication."""
    
    def can_handle(self, sdk_name):
        return sdk_name in ["boto3", "botocore"]
    
    def get_credentials(self):
        # boto3 uses environment variables automatically
        return {"type": "boto_default"}
    
    def inject(self, kwargs):
        # boto3 handles auth automatically
        return kwargs


class GenericAuth(AuthProvider):
    """generic api key authentication."""
    
    def can_handle(self, sdk_name):
        return True  # fallback
    
    def get_credentials(self):
        return {"type": "generic"}
    
    def inject(self, kwargs):
        # try common patterns
        # todo: make this more sophisticated
        return kwargs


class AuthManager:
    """manages authentication providers."""
    
    def __init__(self):
        self.providers = [
            KubernetesAuth(),
            GitHubAuth(),
            AzureAuth(),
            AWSAuth(),
            GenericAuth()  # fallback
        ]
    
    def get_provider(self, sdk_name):
        """get auth provider for sdk."""
        for provider in self.providers:
            if provider.can_handle(sdk_name):
                return provider
        return self.providers[-1]  # fallback
    
    def inject_auth(self, sdk_name, kwargs):
        """inject authentication."""
        provider = self.get_provider(sdk_name)
        return provider.inject(kwargs)
    
    def check_auth(self, sdk_name):
        """check if auth is configured."""
        provider = self.get_provider(sdk_name)
        creds = provider.get_credentials()
        return creds.get("type") != "none"
