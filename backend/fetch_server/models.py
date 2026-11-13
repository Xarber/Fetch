# SPDX-License-Identifier: AGPL-3.0-only
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')

class Inspect(Strict):
    url: str = Field(min_length=1,max_length=8192)

class Selection(Strict):
    preset: Literal['best','compatible','small','audio','original','custom'] = 'compatible'
    format_id: str | None = Field(default=None,pattern=r'^[\w.-]{1,80}$')
    audio_id: str | None = Field(default=None,pattern=r'^[\w.-]{1,80}$')
    audio_format: Literal['original','m4a','mp3','opus','flac','wav'] = 'original'
    bitrate: Literal[128,192,256,320] = 192
    subtitles: bool = False
    embed_metadata: bool = True

class CreateJob(Strict):
    inspection_id: str
    selection: Selection = Field(default_factory=Selection)
    request_key: str = Field(min_length=8,max_length=128)
    authorized: bool
    priority: int = Field(default=0,ge=-100,le=100)

class Batch(Strict):
    jobs: list[CreateJob] = Field(min_length=1,max_length=50)

class Login(Strict):
    username: str = Field(max_length=100)
    password: str = Field(max_length=1024)
    device_name: str = Field(default='Fetch',max_length=100)

class Pair(Strict):
    challenge: str = Field(max_length=200)
    device_name: str = Field(max_length=100)

class Priority(Strict):
    priority: int = Field(ge=-100,le=100)

class Settings(Strict):
    concurrency: int = Field(ge=1,le=4)
    retention_hours: int = Field(ge=1,le=8760)

class Preset(Strict):
    name: str = Field(min_length=1,max_length=80)
    selection: Selection

class PairStart(Strict):
    server_url: str | None = Field(default=None,max_length=2048)
