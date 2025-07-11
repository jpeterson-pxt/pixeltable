import threading
import urllib.parse
from typing import Any, Optional


class S3ClientContainer:
    """Contains a group of clients for a service
    New clients are created lazily when needed
    Client access is thread-safe
    Clients can be used for any purpose, but for performance reasons
    they are separated into two groups, one for read and one for write.
    """

    class ProtectedClientPool:
        """An array of clients which can be used to access the S3 resource (thread-safe)"""

        client: list[Optional[Any]]
        client_lock: threading.Lock  # Proctects creation of the read client
        round_robin: int  # Used to select a slot in the pool
        client_config: Optional[dict[str, Any]]  # Used when factorying a new client

        def __init__(self, max_clients: int = 1, client_config: Optional[dict[str, Any]] = None) -> None:
            self.client = [None for _ in range(max_clients)]
            self.client_lock = threading.Lock()
            self.round_robin = 0
            self.client_config = client_config

        def get_client(self) -> Any:
            """Get a client, creating one if needed"""
            # This may be unprotected increment of a state variable across threads
            # So the result is unpredictable, though it will be an integer
            # So rather than round-robin, this may be considered to be a random selection
            # Either way works.
            # This non-issue would be different if we choose to require and use 'atomics'
            self.round_robin += 1
            index = self.round_robin % len(self.client)
            if self.client[index] is not None:
                return self.client[index]

            with self.client_lock:
                if self.client[index] is not None:
                    return self.client[index]
                if self.client_config is not None:
                    client = S3ClientContainer.get_client_raw(**self.client_config)
                else:
                    client = S3ClientContainer.get_client_raw()

                # Do not set the visible client until it is completely created
                self.client[index] = client
            return self.client[index]

    client_read: ProtectedClientPool
    client_write: ProtectedClientPool
    client_config: dict[str, Any]

    def __init__(self, max_read_clients: int = 1, max_write_clients: int = 2, max_pool_connections: int = 5) -> None:
        self.client_config = {
            'max_pool_connections': max_pool_connections,
            'connect_timeout': 15,
            'read_timeout': 30,
            'retries': {'max_attempts': 3, 'mode': 'adaptive'},
        }
        self.client_read = self.ProtectedClientPool(max_read_clients, self.client_config)
        self.client_write = self.ProtectedClientPool(max_write_clients, self.client_config)

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
        if for_write:
            return self.client_write.get_client(**self.client_config)
        else:
            return self.client_read.get_client(**self.client_config)

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
