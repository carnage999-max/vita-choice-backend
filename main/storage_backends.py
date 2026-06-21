from django.core.files.storage import FileSystemStorage

class MediaStorage(FileSystemStorage):
    """
    Compatibility shim for historical migrations that reference MediaStorage.
    Runtime uploads use Django's default FileSystemStorage via MEDIA_ROOT/MEDIA_URL.
    """

    file_overwrite = False
