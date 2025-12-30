# Custom WhiteNoise storage with explicit MIME types
from whitenoise.storage import CompressedStaticFilesStorage
import mimetypes

class MonlamWhiteNoiseStorage(CompressedStaticFilesStorage):
    """
    Custom WhiteNoise storage that ensures .js files are served with correct MIME type
    """
    
    def __init__(self, *args, **kwargs):
        # Register JavaScript MIME type before initialization
        mimetypes.add_type('application/javascript', '.js', True)
        super().__init__(*args, **kwargs)
    
    def post_process(self, *args, **kwargs):
        # Ensure MIME types are registered
        mimetypes.add_type('application/javascript', '.js', True)
        return super().post_process(*args, **kwargs)

