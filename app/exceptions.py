class ImageAlreadyExistsError(Exception):
    def __init__(self, external_photo_id: str):
        self.external_photo_id = external_photo_id