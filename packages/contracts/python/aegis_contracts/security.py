import secrets
from typing import Annotated

from fastapi import Header, HTTPException


def validate_token(token: str) -> str:
    if len(token) < 32 or not token.isascii() or any(c.isspace() for c in token):
        raise ValueError("A local token of at least 32 ASCII non-whitespace characters is required")
    return token


class RequireToken:
    def __init__(self, token: str) -> None:
        self._token = validate_token(token)

    def __call__(self, authorization: Annotated[str | None, Header()] = None) -> None:
        supplied = authorization.removeprefix("Bearer ") if authorization else ""
        if not authorization or not authorization.startswith("Bearer ") or not supplied.isascii():
            raise HTTPException(
                401, "Authentication required", headers={"WWW-Authenticate": "Bearer"}
            )
        if not secrets.compare_digest(supplied, self._token):
            raise HTTPException(
                401, "Authentication required", headers={"WWW-Authenticate": "Bearer"}
            )
