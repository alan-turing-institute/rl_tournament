import os

config = {
    "storage_account_name": os.environ["AZ_STORAGE_ACCOUNT_NAME"],
    "storage_account_key": os.environ["AZ_STORAGE_ACCOUNT_KEY"],
    "config_container_name": os.environ["AZ_CONFIG_CONTAINER"],
    "logfile_container_name": os.environ["AZ_LOGFILE_CONTAINER"],
    "video_container_name": os.environ["AZ_VIDEO_CONTAINER"],
}
