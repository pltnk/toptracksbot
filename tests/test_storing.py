import pytest

from bot import storing


pytestmark = pytest.mark.asyncio


async def test_get_artist():
    cases = {
        "Norvana": "nirvana",
        "Slipnot": "slipknot",
        "Sustem Of A Down": "system of a down",
        "Random Text That Is No Way A Band Name": "random text that is no way a band name",
    }
    for key in cases:
        res = await storing.get_artist(key)
        assert res == cases[key]
