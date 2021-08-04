from typing import List


class PlaylistRetrievalError(Exception):
    def __init__(self, keyphrase: str):
        super().__init__(f"Unable to get playlist for '{keyphrase}' from Last.fm")


class VideoIDsRetrievalError(Exception):
    def __init__(self, playlist: List[str]):
        super().__init__(f"Unable to get video IDs for {playlist} from YouTube")
