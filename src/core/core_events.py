import dataclasses


# raised ImportError
# from messages import SystemMessage


@dataclasses.dataclass
class ErrorMessage:
    err_type: str
    err_msg: str


@dataclasses.dataclass
class InfoMessage:
    msg_type: str
    payload: str
