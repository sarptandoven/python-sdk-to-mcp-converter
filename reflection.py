"""discover methods from python modules."""
import inspect
import importlib
from safety import is_dangerous


# SDK-specific configuration for complex SDKs
SDK_CONFIGS = {
    "kubernetes": {
        "submodules": ["kubernetes.client"],
        "client_classes": ["CoreV1Api"],  # limit to 1 main class for OpenAI's 128 tool limit
        "max_tools": 128  # match OpenAI's tool limit
    },
    "github": {
        "submodules": ["github"],
        "client_classes": ["Github"]
    },
    "boto3": {
        "main_module": True,  # scan main module for factory methods
        "discover_functions": True,  # find client(), resource(), Session(), etc.
        "max_tools": 128
    },
    "azure": {  # generic azure (will try to find methods)
        "main_module": True,
        "discover_functions": True,
        "max_tools": 128
    },
    "azure.mgmt.resource": {
        "submodules": ["azure.mgmt.resource"],
        "client_classes": ["ResourceManagementClient"],
        "discover_operation_groups": True,  # Discover operation groups like resource_groups
        "max_tools": 128
    },
    "azure.mgmt.compute": {
        "submodules": ["azure.mgmt.compute"],
        "client_classes": ["ComputeManagementClient"],
        "discover_operation_groups": True,  # Discover operation groups like virtual_machines
        "max_tools": 128
    },
    "stripe": {
        "main_module": True,  # scan resource classes
        "discover_classes": True,  # find Customer, Charge, PaymentIntent, etc.
        "resource_classes": ["Customer", "Charge", "PaymentIntent", "Subscription", 
                           "Invoice", "Product", "Price", "PaymentMethod"],
        "max_tools": 128  # limit to OpenAI's max
    },
    "requests": {
        "main_module": True,
        "discover_functions": True
    }
}


def discover_methods(module, module_name, allow_dangerous=False):
    """find all callable methods in a module."""
    methods = []
    
    # check if this is a complex SDK
    sdk_config = SDK_CONFIGS.get(module_name, {})
    max_tools = sdk_config.get("max_tools", None)
    
    # try to load better submodules for complex SDKs
    modules_to_scan = [module]
    for submodule_name in sdk_config.get("submodules", []):
        try:
            submodule = importlib.import_module(submodule_name)
            modules_to_scan.append(submodule)
        except:
            pass
    
    for mod in modules_to_scan:
        # find module-level functions (both regular and builtin)
        if sdk_config.get("discover_functions", True):
            for name, obj in inspect.getmembers(mod, lambda x: inspect.isfunction(x) or inspect.isbuiltin(x)):
                if not name.startswith("_"):
                    sig = _get_signature(obj)
                    if sig:
                        method_info = _create_method_info(
                            f"{module_name}.{name}", 
                            obj, 
                            sig,
                            allow_dangerous
                        )
                        if method_info:
                            methods.append(method_info)
                            # check max tools limit
                            if max_tools and len(methods) >= max_tools:
                                return methods
        
        # find class methods - but handle complex SDKs specially
        target_classes = sdk_config.get("client_classes", None)
        resource_classes = sdk_config.get("resource_classes", None)
        
        for class_name, cls in inspect.getmembers(mod, inspect.isclass):
            # skip private classes
            if class_name.startswith("_"):
                continue
            
            # if we have a whitelist, only process those classes
            if target_classes and class_name not in target_classes:
                continue
            
            # if we have resource classes (like Stripe), only process those
            if resource_classes and class_name not in resource_classes:
                continue
            
            # Handle client classes (need instantiation for instance methods)
            if target_classes and class_name in target_classes:
                try:
                    instance = _try_instantiate_client(cls, class_name, module_name)
                    if instance:
                        # Check if we should discover operation groups (Azure pattern)
                        if sdk_config.get("discover_operation_groups", False):
                            # Discover Azure operation groups (resource_groups, virtual_machines, etc.)
                            new_methods = _discover_azure_operation_groups(instance, f"{module_name}.{class_name}", allow_dangerous, max_tools - len(methods) if max_tools else None)
                            methods.extend(new_methods)
                        else:
                            # Regular instance method discovery
                            new_methods = _discover_instance_methods(instance, f"{module_name}.{class_name}", allow_dangerous, max_tools - len(methods) if max_tools else None)
                            methods.extend(new_methods)
                        
                        if max_tools and len(methods) >= max_tools:
                            return methods
                        continue
                except:
                    pass
            
            # Handle resource classes (Stripe - use class methods, not instance)
            if resource_classes and class_name in resource_classes:
                # For Stripe resources, discover class methods (list, create, retrieve, etc.)
                for method_name in dir(cls):
                    if method_name.startswith("_"):
                        continue
                    try:
                        method = getattr(cls, method_name)
                        if callable(method) and (inspect.ismethod(method) or inspect.isfunction(method)):
                            sig = _get_signature(method)
                            if sig:
                                method_info = _create_method_info(
                                    f"{module_name}.{class_name}.{method_name}",
                                    method,
                                    sig,
                                    allow_dangerous
                                )
                                if method_info:
                                    methods.append(method_info)
                                    if max_tools and len(methods) >= max_tools:
                                        return methods
                    except:
                        pass
                continue
            
            # fallback: discover class methods normally
            for method_name, method in inspect.getmembers(cls, lambda x: inspect.isfunction(x) or inspect.isbuiltin(x) or inspect.ismethod(x)):
                if not method_name.startswith("_"):
                    sig = _get_signature(method)
                    if sig:
                        method_info = _create_method_info(
                            f"{module_name}.{class_name}.{method_name}",
                            method,
                            sig,
                            allow_dangerous
                        )
                        if method_info:
                            methods.append(method_info)
                            if max_tools and len(methods) >= max_tools:
                                return methods
    
    return methods


def _try_instantiate_client(cls, class_name, module_name):
    """try to instantiate a client class with actual credentials."""
    import os
    
    try:
        # GitHub - use token from environment
        if module_name == "github" and class_name == "Github":
            token = os.getenv("GITHUB_TOKEN")
            if token:
                return cls(token)
            # Fallback: try without token (some methods work)
            try:
                return cls()
            except:
                return None
        
        # Azure - use credentials from environment
        if "azure" in module_name and "ManagementClient" in class_name:
            try:
                from azure.identity import DefaultAzureCredential
                subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
                tenant_id = os.getenv("AZURE_TENANT_ID")
                
                if subscription_id:
                    # Set tenant ID if provided
                    if tenant_id:
                        os.environ["AZURE_TENANT_ID"] = tenant_id
                    
                    credential = DefaultAzureCredential()
                    return cls(credential, subscription_id)
            except Exception as e:
                # If Azure auth fails, skip instantiation
                return None
        
        # Kubernetes - load kubeconfig if available
        if module_name == "kubernetes":
            try:
                from kubernetes import config
                # Try to load kubeconfig (will use default ~/.kube/config)
                config.load_kube_config()
            except:
                # If no kubeconfig, skip (might be in-cluster)
                pass
            
            # Instantiate the client
            return cls()
        
        # Try without args for other SDKs
        return cls()
    except Exception:
        return None


def _discover_instance_methods(instance, prefix, allow_dangerous, max_methods=None):
    """discover methods from an instance."""
    methods = []
    
    for method_name in dir(instance):
        if method_name.startswith("_"):
            continue
        
        try:
            method = getattr(instance, method_name)
            if callable(method):
                sig = _get_signature(method)
                if sig:
                    method_info = _create_method_info(
                        f"{prefix}.{method_name}",
                        method,
                        sig,
                        allow_dangerous
                    )
                    if method_info:
                        methods.append(method_info)
                        if max_methods and len(methods) >= max_methods:
                            return methods
        except:
            continue
    
    return methods


def _discover_azure_operation_groups(client_instance, prefix, allow_dangerous, max_methods=None):
    """discover Azure operation groups (resource_groups, virtual_machines, etc.) and their methods."""
    methods = []
    
    # Priority operation groups (discover these first!)
    priority_groups = ['virtual_machines', 'resource_groups', 'deployments', 'disks', 'virtual_machine_scale_sets']
    
    # First pass: discover priority operation groups
    for attr_name in priority_groups:
        if not hasattr(client_instance, attr_name):
            continue
        
        try:
            operation_group = getattr(client_instance, attr_name)
            
            # Check if this looks like an operation group (has list, get, create, etc.)
            if hasattr(operation_group, 'list') or hasattr(operation_group, 'get') or hasattr(operation_group, 'create_or_update') or hasattr(operation_group, 'list_all'):
                # This is an operation group! Discover its methods
                for method_name in dir(operation_group):
                    if method_name.startswith("_"):
                        continue
                    
                    try:
                        method = getattr(operation_group, method_name)
                        if callable(method):
                            sig = _get_signature(method)
                            if sig:
                                # Name format: azure.mgmt.resource.ResourceManagementClient.resource_groups.list
                                method_info = _create_method_info(
                                    f"{prefix}.{attr_name}.{method_name}",
                                    method,
                                    sig,
                                    allow_dangerous
                                )
                                if method_info:
                                    methods.append(method_info)
                                    if max_methods and len(methods) >= max_methods:
                                        return methods
                    except:
                        continue
        except:
            continue
    
    # Second pass: discover remaining operation groups
    for attr_name in dir(client_instance):
        if attr_name.startswith("_") or attr_name in priority_groups:
            continue
        
        try:
            operation_group = getattr(client_instance, attr_name)
            
            # Check if this looks like an operation group (has list, get, create, etc.)
            if hasattr(operation_group, 'list') or hasattr(operation_group, 'get') or hasattr(operation_group, 'create_or_update') or hasattr(operation_group, 'list_all'):
                # This is an operation group! Discover its methods
                for method_name in dir(operation_group):
                    if method_name.startswith("_"):
                        continue
                    
                    try:
                        method = getattr(operation_group, method_name)
                        if callable(method):
                            sig = _get_signature(method)
                            if sig:
                                # Name format: azure.mgmt.resource.ResourceManagementClient.resource_groups.list
                                method_info = _create_method_info(
                                    f"{prefix}.{attr_name}.{method_name}",
                                    method,
                                    sig,
                                    allow_dangerous
                                )
                                if method_info:
                                    methods.append(method_info)
                                    if max_methods and len(methods) >= max_methods:
                                        return methods
                    except:
                        continue
        except:
            continue
    
    return methods


def _get_signature(obj):
    """safely get signature."""
    try:
        return inspect.signature(obj)
    except:
        return None


def _create_method_info(name, obj, sig, allow_dangerous):
    """create method metadata."""
    dangerous = is_dangerous(name)
    
    # filter out dangerous methods unless explicitly allowed
    if dangerous and not allow_dangerous:
        return None
    
    return {
        "name": name,
        "callable": obj,
        "signature": sig,
        "docstring": inspect.getdoc(obj),
        "is_dangerous": dangerous
    }
