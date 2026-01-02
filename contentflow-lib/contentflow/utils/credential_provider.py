"""
Azure credential provider utility functions.
"""

import os
from azure.identity import ChainedTokenCredential, EnvironmentCredential, ManagedIdentityCredential, AzureCliCredential
from azure.identity.aio import (ChainedTokenCredential as ChainedTokenCredentialAsync, 
                                EnvironmentCredential as EnvironmentCredentialAsync, 
                                ManagedIdentityCredential as ManagedIdentityCredentialAsync,
                                AzureCliCredential as AzureCliCredentialAsync)

_async_credential : ChainedTokenCredentialAsync = None
_synch_credential : ChainedTokenCredential = None

async def get_azure_credential_async():
    credential_chain = (
        # Start with Azure CLI for local development
        AzureCliCredentialAsync(),
        # Try EnvironmentCredential
        EnvironmentCredentialAsync(),
        # Then try ManagedIdentityCredential
        ManagedIdentityCredentialAsync(client_id=os.environ.get("AZURE_CLIENT_ID")),
    )

    global _async_credential
    if not _async_credential:
        _async_credential = ChainedTokenCredentialAsync(*credential_chain)
        
    return _async_credential

def get_azure_credential():
    credential_chain = (
        # Start with Azure CLI for local development
        AzureCliCredential(),
        # Try EnvironmentCredential
        EnvironmentCredential(),
        # Then try ManagedIdentityCredential
        ManagedIdentityCredential(client_id=os.environ.get("AZURE_CLIENT_ID")),
    )
    
    global _synch_credential
    if not _synch_credential:
        _synch_credential = ChainedTokenCredential(*credential_chain)

    return _synch_credential

def get_azure_credential_with_details():
    """
    Get the appropriate credential for authentication.
        
    :return: Credential object
    """
    try:
        credential = get_azure_credential()
        
        token_details = _get_token_details(credential)
        
        return credential, token_details
    except Exception as e:
        raise

def _get_token_details(credential):
    if credential:
        try:
            token = credential.get_token("https://management.azure.com//.default")
            if token and token.token:
                import base64
                import json
                if "." in token.token:
                    base64_meta_data = token.token.split(".")[1]
                    padding_needed = -len(base64_meta_data) % 4
                    if padding_needed:
                        base64_meta_data += "=" * padding_needed
                    json_bytes = base64.urlsafe_b64decode(base64_meta_data)
                    json_string = json_bytes.decode("utf-8")
                    json_dict = json.loads(json_string)
                    upn = json_dict.get("upn", "unavailableUpn")
                    appid = json_dict.get("appid", "<unavailable>")
                    tid = json_dict.get("tid", "<unavailable>")
                    oid = json_dict.get("oid", "<unavailable>")
                    
                    return {
                        "client_id": appid,
                        "tenant_id": tid,
                        "upn": upn,
                        "object_id": oid
                    }
        except Exception as e:
            pass
    
    return None