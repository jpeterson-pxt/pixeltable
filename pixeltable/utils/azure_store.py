from __future__ import annotations

import logging
import re
import urllib.parse
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Optional

from pixeltable import env, exceptions as excs
from pixeltable.utils.client_container import ClientContainer
from pixeltable.utils.media_path import MediaPath, StorageObjectAddress
from pixeltable.utils.media_store_base import MediaStoreBase

if TYPE_CHECKING:
    from azure.core.exceptions import AzureError

    from pixeltable.catalog import Column

_logger = logging.getLogger('pixeltable')


class AzureBlobStore(MediaStoreBase):
    """Class to handle Azure Blob Storage operations."""

    # URI of the Azure Blob Storage container
    # Always ends with a slash
    __base_uri: str

    # Storage account name
    __account_name: str

    # Container name extracted from the URI
    __container_name: str

    # Prefix path within the container, either empty or ending with a slash
    __prefix_name: str

    # URI scheme (wasb, wasbs, abfs, abfss, https)
    __scheme: str

    soa: StorageObjectAddress

    def __init__(self, soa: StorageObjectAddress):
        self.soa = soa
        self.__scheme = soa.scheme
        self.__account_name = soa.account
        self.__container_name = soa.container
        self.__prefix_name = soa.prefix

        # Reconstruct base URI in normalized format
        self.__base_uri = soa.prefix_free_uri + self.__prefix_name
        if 0:
            print(
                f'Initialized AzureBlobStore with base URI: {self.__base_uri},',
                f'account: {self.__account_name}, container: {self.__container_name}, prefix: {self.__prefix_name}',
            )

    def client(self) -> Any:
        """Return the Azure Blob Storage client."""
        return ClientContainer.get().get_client(self.soa)

    @property
    def account_name(self) -> str:
        """Return the storage account name."""
        return self.__account_name

    @property
    def container_name(self) -> str:
        """Return the container name from the base URI."""
        return self.__container_name

    @property
    def prefix(self) -> str:
        """Return the prefix from the base URI."""
        return self.__prefix_name

    def validate(self, error_col_name: str) -> Optional[str]:
        """
        Checks if the URI exists and is accessible.

        Returns:
            str: The base URI if the container exists and is accessible, None otherwise.
        """
        env.Env.get().require_package('azure.storage.blob')

        try:
            container_client = self.client().get_container_client(self.container_name)
            # Check if container exists by trying to get its properties
            container_client.get_container_properties()
            return self.__base_uri
        except AzureError as e:
            self.handle_azure_error(e, self.container_name, f'validate container {error_col_name}')
        return None

    def _prepare_media_uri_raw(
        self, tbl_id: uuid.UUID, col_id: int, tbl_version: int, ext: Optional[str] = None
    ) -> str:
        """
        Construct a new, unique URI for a persisted media file.
        """
        prefix, filename = MediaPath.media_prefix_file_raw(tbl_id, col_id, tbl_version, ext)
        parent = f'{self.__base_uri}{prefix}'
        return f'{parent}/{filename}'

    def _prepare_media_uri(self, col: Column, ext: Optional[str] = None) -> str:
        """
        Construct a new, unique URI for a persisted media file.
        """
        assert col.tbl is not None, 'Column must be associated with a table'
        return self._prepare_media_uri_raw(col.tbl.id, col.id, col.tbl.version, ext=ext)

    def download_media_object(self, src_path: str, dest_path: Path) -> None:
        """Copies a blob to a local file. Thread safe."""
        from azure.core.exceptions import AzureError

        try:
            blob_client = self.client().get_blob_client(container=self.container_name, blob=self.prefix + src_path)
            with open(dest_path, 'wb') as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())
        except AzureError as e:
            self.handle_azure_error(e, self.container_name, f'download file {src_path}')
            raise

    def copy_local_media_file(self, col: Column, src_path: Path) -> str:
        """Copy a local file to Azure Blob Storage, and return its new URL"""
        from azure.core.exceptions import AzureError

        new_file_uri = self._prepare_media_uri(col, ext=src_path.suffix)

        # Extract blob name from the URI
        if self.__scheme in ['wasb', 'wasbs', 'abfs', 'abfss']:
            # Remove the scheme and container/account part
            blob_name = new_file_uri.split('/', 3)[-1] if '/' in new_file_uri else ''
        else:
            # For HTTPS URIs, extract the path after container
            parsed = urllib.parse.urlparse(new_file_uri)
            path_parts = parsed.path.lstrip('/').split('/', 1)
            blob_name = path_parts[1] if len(path_parts) > 1 else ''

        try:
            blob_client = self.client().get_blob_client(container=self.container_name, blob=blob_name)
            with open(src_path, 'rb') as data:
                blob_client.upload_blob(data, overwrite=True)
            _logger.debug(f'Media Storage: copied {src_path} to {new_file_uri}')
            return new_file_uri
        except AzureError as e:
            self.handle_azure_error(e, self.container_name, f'upload file {src_path}')
            raise

    def _get_filtered_blobs(self, tbl_id: Optional[uuid.UUID], tbl_version: Optional[int] = None) -> Iterator:
        """Private method to get filtered blobs for a table, optionally filtered by version.

        Args:
            tbl_id: Table UUID to filter by
            tbl_version: Optional table version to filter by

        Returns:
            Iterator over blob objects matching the criteria
        """
        from azure.core.exceptions import AzureError

        # Use MediaPath to construct the prefix for this table
        if tbl_id is None:
            prefix = self.prefix
            assert tbl_version is None, 'tbl_version must be None if tbl_id is None'
        else:
            table_prefix = MediaPath.media_table_prefix(tbl_id)
            prefix = f'{self.prefix}{table_prefix}/'

        try:
            container_client = self.client().get_container_client(self.container_name)

            if tbl_version is None:
                # Return all blobs with the table prefix
                blob_iterator = container_client.list_blobs(name_starts_with=prefix)
            else:
                # Filter by both table_id and table_version using the MediaPath pattern
                # Pattern: tbl_id_col_id_version_uuid
                version_pattern = re.compile(
                    rf'{re.escape(table_prefix)}_\d+_{re.escape(str(tbl_version))}_[0-9a-fA-F]+.*'
                )
                # Get all blobs with the prefix and filter by version pattern
                all_blobs = container_client.list_blobs(name_starts_with=prefix)
                blob_iterator = (blob for blob in all_blobs if version_pattern.match(blob.name.split('/')[-1]))

            return blob_iterator

        except AzureError as e:
            self.handle_azure_error(e, self.container_name, f'setup iterator {self.prefix}')
            raise

    def count(self, tbl_id: Optional[uuid.UUID], tbl_version: Optional[int] = None) -> int:
        """Count the number of files belonging to tbl_id. If tbl_version is not None,
        count only those files belonging to the specified tbl_version.

        Args:
            tbl_id: Table UUID to count blobs for
            tbl_version: Optional table version to filter by

        Returns:
            Number of blobs matching the criteria
        """
        blob_iterator = self._get_filtered_blobs(tbl_id, tbl_version)
        return sum(1 for _ in blob_iterator)

    def delete(self, tbl_id: uuid.UUID, tbl_version: Optional[int] = None) -> int:
        """Delete all files belonging to tbl_id. If tbl_version is not None, delete
        only those files belonging to the specified tbl_version.

        Args:
            tbl_id: Table UUID to delete blobs for
            tbl_version: Optional table version to filter by

        Returns:
            Number of blobs deleted
        """
        assert tbl_id is not None
        from azure.core.exceptions import AzureError

        blob_iterator = self._get_filtered_blobs(tbl_id, tbl_version)
        total_deleted = 0

        try:
            container_client = self.client().get_container_client(self.container_name)

            # Azure Blob Storage supports batch deletion
            blobs_to_delete = []

            for blob in blob_iterator:
                blobs_to_delete.append(blob.name)

                # Delete in batches of 256 (Azure's batch limit)
                if len(blobs_to_delete) >= 256:
                    # Use delete_blobs for batch deletion
                    delete_results = container_client.delete_blobs(*blobs_to_delete)
                    # Check for any failures
                    for result in delete_results:
                        if not result.get('error'):
                            total_deleted += 1
                    blobs_to_delete = []

            # Delete any remaining blobs in the final batch
            if len(blobs_to_delete) > 0:
                delete_results = container_client.delete_blobs(*blobs_to_delete)
                for result in delete_results:
                    if not result.get('error'):
                        total_deleted += 1

            print(f"Deleted {total_deleted} blobs from container '{self.container_name}'.")
            return total_deleted

        except AzureError as e:
            self.handle_azure_error(e, self.container_name, f'deleting with {self.prefix}')
            raise

    def list_objects(self, return_uri: bool, n_max: int = 10) -> list[str]:
        """Return a list of objects found in the specified destination bucket.
        Each returned object includes the full set of prefixes.
        if return_uri is True, full URI's are returned; otherwise, just the object keys.
        """
        from azure.core.exceptions import AzureError

        p = self.soa.prefix_free_uri if return_uri else ''
        r: list[str] = []
        try:
            blob_iterator = self._get_filtered_blobs(tbl_id=None, tbl_version=None)
            for blob in blob_iterator:
                r.append(f'{p}{blob.name}')
                if len(r) >= n_max:
                    return r

        except AzureError as e:
            self.handle_azure_error(e, self.__container_name, f'list objects from {self.__base_uri}')
        return r

    @classmethod
    def handle_azure_error(
        cls, e: AzureError, container_name: str, operation: str = '', *, ignore_404: bool = False
    ) -> None:
        from azure.core.exceptions import ClientAuthenticationError, HttpResponseError, ResourceNotFoundError

        if ignore_404 and isinstance(e, ResourceNotFoundError):
            return

        if isinstance(e, ResourceNotFoundError):
            raise excs.Error(f'Container {container_name} or blob not found during {operation}: {str(e)!r}')
        elif isinstance(e, ClientAuthenticationError):
            raise excs.Error(f'Authentication failed for container {container_name} during {operation}: {str(e)!r}')
        elif isinstance(e, HttpResponseError):
            if e.status_code == 403:
                raise excs.Error(f'Access denied to container {container_name} during {operation}: {str(e)!r}')
            elif e.status_code == 412:
                raise excs.Error(f'Precondition failed for container {container_name} during {operation}: {str(e)!r}')
            else:
                raise excs.Error(
                    f'HTTP error during {operation} in container {container_name}: {e.status_code} - {str(e)!r}'
                )
        else:
            raise excs.Error(f'Error during {operation} in container {container_name}: {str(e)!r}')

    @classmethod
    def create_client(cls, soa: StorageObjectAddress) -> Any:
        account_url = soa.container_free_uri if soa else None
        client_config = {
            'max_single_get_size': 32 * 1024 * 1024,  # 32MB chunks
            'max_chunk_get_size': 4 * 1024 * 1024,  # 4MB chunks
            'connection_timeout': 15,
            'read_timeout': 30,
            'retry_total': 3,
            'retry_backoff_factor': 0.5,
        }
        return cls.create_az_raw(connection_string=None, account_url=account_url, **client_config)

    @classmethod
    def create_az_raw(cls, connection_string: Optional[str], account_url: Optional[str], **kwargs: Any) -> Any:
        """Get a raw client without any locking"""
        from azure.storage.blob import BlobServiceClient

        try:
            if connection_string is not None:
                # Use connection string if available
                return BlobServiceClient.from_connection_string(
                    connection_string,
                    max_single_get_size=kwargs.get('max_single_get_size', 32 * 1024 * 1024),
                    max_chunk_get_size=kwargs.get('max_chunk_get_size', 4 * 1024 * 1024),
                    connection_timeout=kwargs.get('connection_timeout', 15),
                    read_timeout=kwargs.get('read_timeout', 30),
                )
            else:
                #  account_url = f'https://{account_name}.blob.core.windows.net'
                if account_url is None:
                    raise ValueError('No Azure Storage connection string or account information provided')

                # Use empty SAS token for anonymous authentication
                credential = None
                return BlobServiceClient(
                    account_url=account_url,
                    credential=credential,
                    max_single_get_size=kwargs.get('max_single_get_size', 32 * 1024 * 1024),
                    max_chunk_get_size=kwargs.get('max_chunk_get_size', 4 * 1024 * 1024),
                    connection_timeout=kwargs.get('connection_timeout', 15),
                    read_timeout=kwargs.get('read_timeout', 30),
                )
        except Exception as e:
            raise excs.Error(f'Failed to create Azure Blob Storage client: {str(e)!r}') from e
