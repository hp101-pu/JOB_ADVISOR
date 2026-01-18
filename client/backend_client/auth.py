from contextvars import ContextVar

_current_jwt: ContextVar[str | None] = ContextVar("current_jwt", default=None)

def set_current_jwt(jwt: str):
    _current_jwt.set(jwt)

def get_current_jwt() -> str:
    jwt = _current_jwt.get()
    if not jwt:
        raise RuntimeError("JWT not set in context")
    return jwt
