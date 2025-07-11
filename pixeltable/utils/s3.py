import threading
import urllib.parse
from typing import Any, Optional


class S3ClientContainer:
    """Contains a boto client whose initialization / creation is protected by a threading lock"""

    boto_client: Optional[Any]
    boto_client_lock: threading.Lock  # Proctects creation of the client
    boto_config: dict[str, Any]

    def __init__(self, max_pool_connections: int = 5):
        self.boto_client = None
        self.boto_client_lock = threading.Lock()
        self.boto_config = {
            'max_pool_connections': max_pool_connections,
            'connect_timeout': 15,
            'read_timeout': 30,
            'retries': {'max_attempts': 3, 'mode': 'adaptive'},
        }

    @classmethod
    def get_client_raw(cls, **kwargs: Any) -> Any:
        """Get a raw client without any locking"""
        import boto3
        import botocore

        try:
            boto3.Session().get_credentials().get_frozen_credentials()
            config = botocore.config.Config(**kwargs)
            return boto3.client('s3', config=config)  # credentials are available
        except AttributeError:
            # No credentials available, use unsigned mode
            config_args = kwargs.copy()
            config_args['signature_version'] = botocore.UNSIGNED
            config = botocore.config.Config(**config_args)
            return boto3.client('s3', config=config)

    def get_client(self, for_write: bool) -> Any:
        """Get a client, creating one if needed"""
        if self.boto_client is not None:
            return self.boto_client

        with self.boto_client_lock:
            if self.boto_client is not None:
                return self.boto_client
            client = self.get_client_raw(**self.boto_config)
            # Do not set the visible client until it is completely created
            self.boto_client = client
        return self.boto_client

    def list_uris(self, source_uri: str, n_max: int = 10) -> list[str]:
        """Return a list of URIs found within the specified S3 bucket/path"""
        # I think the n_max parameter should be passed into the list_objects_v2 call
        parsed = urllib.parse.urlparse(source_uri)
        assert parsed.scheme == 's3'
        bucket_name = parsed.netloc
        prefix = parsed.path.lstrip('/')
        s3_client = self.get_client_raw()
        uris: list[str] = []
        # Use paginator to handle more than 1000 objects
        paginator = s3_client.get_paginator('list_objects_v2')

        for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
            if 'Contents' not in page:
                continue
            for obj in page['Contents']:
                if len(uris) >= n_max:
                    return uris
                uris.append(f's3://{bucket_name}/{obj["Key"]}')
        return uris
