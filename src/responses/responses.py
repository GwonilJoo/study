from __future__ import annotations
from typing import Dict, Any
from src.requests.room_list import RoomListInvalidRequest


class ResponseTypes:
    PARAMETERS_ERROR = "ParametersError"
    RESOURCE_ERROR = "ResourceError"
    SYSTEM_ERROR = "SystemError"
    SUCCESS = "Success"


class ResponseFailure:
    def __init__(self, type: ResponseTypes, message: str | Exception) -> None:
        self.type = type
        self.message = self._format_message(message)


    def _format_message(self, msg: str | Exception) -> str:
        if isinstance(msg, Exception):
            return f"{msg.__class__.__name__}: {str(msg)}"
        return msg


    @property
    def value(self) -> Dict[str, Any]:
        return {"type": self.type, "message": self.message}
    

    def __bool__(self) -> bool:
        return False
    

    @classmethod
    def from_invalid_request(cls, invalid_request: RoomListInvalidRequest) -> ResponseFailure:
        message = "\n".join([f"{err['parameter']}: {err['message']}" for err in invalid_request.errors])
        return cls(ResponseTypes.PARAMETERS_ERROR, message)


class ResponseSuccess:
    def __init__(self, value: Any = None) -> None:
        self.type = ResponseTypes.SUCCESS
        self.value = value
    
    def __bool__(self) -> bool:
        return True