import os
import json

from azure.storage.blob import (
    BlockBlobService,
)
from azure.common import AzureMissingResourceHttpError

from battleground.azure_config import config


def check_container_exists(container_name, bbs=None):
    """
    See if a container already exists for this account name.
    """
    if not bbs:
        bbs = BlockBlobService(
            account_name=config["storage_account_name"],
            account_key=config["storage_account_key"],
        )
    return bbs.exists(container_name)


def create_container(container_name, bbs=None):
    """
    Create a storage container with the specified name.
    """
    if not bbs:
        bbs = BlockBlobService(
            account_name=config["storage_account_name"],
            account_key=config["storage_account_key"],
        )
    exists = check_container_exists(container_name, bbs)
    if not exists:
        bbs.create_container(container_name)


def check_blob_exists(blob_name, container_name, bbs=None):
    """
    See if a blob already exists for this account name.
    """
    if not bbs:
        bbs = BlockBlobService(
            account_name=config["storage_account_name"],
            account_key=config["storage_account_key"],
        )
    blob_names = bbs.list_blob_names(container_name)
    return blob_name in blob_names


def retrieve_blob(blob_name, container_name, destination="/tmp/", bbs=None):
    """
    use the BlockBlobService to retrieve file from Azure,
    and place in destination folder.
    """
    if not bbs:
        bbs = BlockBlobService(
            account_name=config["storage_account_name"],
            account_key=config["storage_account_key"],
        )
    local_filename = blob_name.split("/")[-1]
    try:
        bbs.get_blob_to_path(
            container_name,
            blob_name,
            os.path.join(destination, local_filename),
        )
        return True, "retrieved script OK"
    except (AzureMissingResourceHttpError):
        return False, "failed to retrieve {} from {}".format(
            blob_name, container_name
        )
    return os.path.join(destination, local_filename)


def list_directory(path, container_name, bbs=None):
    if not bbs:
        bbs = BlockBlobService(
            account_name=config["storage_account_name"],
            account_key=config["storage_account_key"],
        )
        pass
    prefix = remove_container_name_from_blob_path(path, container_name)
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    blob_names = bbs.list_blob_names(
        container_name, prefix=prefix, delimiter="/"
    )
    blob_names = [bn[:-1] if bn.endswith("/") else bn for bn in blob_names]
    return [os.path.basename(bn) for bn in blob_names]


def split_filepath(path):
    allparts = []
    if path.endswith("/") or path.endswith("\\"):
        path = path[:-1]
    while True:
        parts = os.path.split(path)
        if parts[0] == path:  # for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path:  # for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def remove_container_name_from_blob_path(blob_path, container_name):
    """
    Get the bit of the filepath after the container name.
    """
    # container name will often be part of filepath - we want
    # the blob name to be the bit after that
    if container_name not in blob_path:
        return blob_path
    blob_name_parts = []
    filepath_parts = split_filepath(blob_path)
    container_name_found = False
    for path_part in filepath_parts:
        if container_name_found:
            blob_name_parts.append(path_part)
        if path_part == container_name:
            container_name_found = True
    if len(blob_name_parts) == 0:
        return ""
    return "/".join(blob_name_parts)


def delete_blob(blob_name, container_name, bbs=None):
    if not bbs:
        bbs = BlockBlobService(
            account_name=config["storage_account_name"],
            account_key=config["storage_account_key"],
        )
    blob_exists = check_blob_exists(blob_name, container_name, bbs)
    if not blob_exists:
        return
    bbs.delete_blob(container_name, blob_name)


def write_file_to_blob(file_path, blob_name, container_name, bbs=None):
    if not bbs:
        bbs = BlockBlobService(
            account_name=config["storage_account_name"],
            account_key=config["storage_account_key"],
        )
    bbs.create_blob_from_path(container_name, blob_name, file_path)


def write_files_to_blob(
    path, container_name, blob_path=None, file_endings=[], bbs=None
):
    """
    Upload a whole directory structure to blob storage.
    If we are given 'blob_path' we use that - if not we preserve
    the given file path structure.
    In both cases we take care to remove the container name from
    the start of the blob path
    """

    if not bbs:
        bbs = BlockBlobService(
            account_name=config["storage_account_name"],
            account_key=config["storage_account_key"],
        )
    filepaths_to_upload = []
    for root, dirs, files in os.walk(path):
        for filename in files:
            filepath = os.path.join(root, filename)
            if file_endings:
                for ending in file_endings:
                    if filename.endswith(ending):
                        filepaths_to_upload.append(filepath)
            else:
                filepaths_to_upload.append(filepath)
    for filepath in filepaths_to_upload:
        if blob_path:
            blob_fullpath = os.path.join(
                blob_path, os.path.split(filepath)[-1]
            )
        else:
            blob_fullpath = filepath
        blob_name = remove_container_name_from_blob_path(
            blob_fullpath, container_name
        )

        write_file_to_blob(filepath, blob_name, container_name, bbs)


def read_json(blob_name, container_name, bbs=None):
    if not bbs:
        bbs = BlockBlobService(
            account_name=config["storage_account_name"],
            account_key=config["storage_account_key"],
        )
    blob_name = remove_container_name_from_blob_path(blob_name, container_name)
    data_blob = bbs.get_blob_to_text(container_name, blob_name)
    data = json.loads(data_blob.content)
    return data
