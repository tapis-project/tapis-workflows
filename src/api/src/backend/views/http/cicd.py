from typing import Union

from typing_extensions import Annotated
from pydantic import Field

from backend.views.http.requests import (
    Pipeline,
    DockerhubContext,
    GithubContext,
    DockerhubDestination,
    LocalDestination
)


class CIPipeline(Pipeline):
    cache: bool = False
    builder: str
    context: Annotated[
        Union[
            DockerhubContext,
            GithubContext
        ],
        Field(discriminator="type")
    ]
    destination: Annotated[
        Union[
            DockerhubDestination,
            LocalDestination
        ],
        Field(discriminator="type")
    ] = None