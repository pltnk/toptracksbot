import os
import uuid

import asyncpg
import pytest


@pytest.fixture
def required_env_vars():
    return ["TTBOT_TOKEN", "TTBOT_LASTFM_API_KEY", "TTBOT_YOUTUBE_API_KEY"]


@pytest.fixture
def track_nums():
    return [0, 1, 3]


@pytest.fixture
def yt_ids_num():
    return 3


@pytest.fixture
def keyphrase():
    return "Nirvana"


@pytest.fixture
def bad_keyphrase():
    return "".join(str(uuid.uuid4()) for _ in range(10))


@pytest.fixture
def playlist():
    return [
        "Nirvana - Smells Like Teen Spirit",
        "Nirvana - Come As You Are",
        "Nirvana - Lithium",
    ]


@pytest.fixture
def expected_yt_ids():
    return ["hTWKbfoikeg", "vabnZ9-ex7o", "pkcJEvMcnEg"]


@pytest.fixture
def name_corrections():
    return {
        "norvana": "Nirvana",
        "slipnot": "Slipknot",
        "sustem of a down": "System of a Down",
        "author and punisher": "Author & Punisher",
    }


@pytest.fixture
def database_uri():
    return os.environ["TTBOT_DATABASE_URI"]


@pytest.fixture
def init_sql_path():
    return "./db/init.sql"


@pytest.fixture
async def db_conn(database_uri, init_sql_path):
    conn = await asyncpg.connect(dsn=database_uri)
    with open(init_sql_path, "r") as f:
        query = f.read()
    await conn.execute(query)
    yield conn
    await conn.close()


@pytest.fixture
def get_artist_cases():
    return {
        "Norvana": "nirvana",
        "Slipnot": "slipknot",
        "Sustem Of A Down": "system of a down",
        "Random Text That Is No Way A Band Name": "random text that is no way a band name",
        "Author and Punisher": "author & punisher",
    }
