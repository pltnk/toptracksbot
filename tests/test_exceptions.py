import pytest

from bot.exceptions import PlaylistRetrievalError, VideoIDsRetrievalError


def test_playlist_retrieval_error():
    keyphrase = "test"
    with pytest.raises(PlaylistRetrievalError) as exc_info:
        raise PlaylistRetrievalError(keyphrase)
    assert (
        str(exc_info.value) == f"Unable to get playlist for '{keyphrase}' from Last.fm"
    )


def test_video_ids_retrieval_error():
    playlist = ["a", "b", "c"]
    with pytest.raises(VideoIDsRetrievalError) as exc_info:
        raise VideoIDsRetrievalError(playlist)
    assert str(exc_info.value) == f"Unable to get video IDs for {playlist} from YouTube"
