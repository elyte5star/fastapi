from pydantic import BaseModel, ConfigDict, Field


class BaseResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        use_enum_values=True,
        str_strip_whitespace=True,
        extra="allow",
        serialize_by_alias=True,
    )
    req_id: str = Field(default="", serialization_alias="requestId")
    start_time: float = Field(default=0.0, serialization_alias="startTime")
    stop_time: float = Field(default=0.0, serialization_alias="stopTime")
    process_time: str = Field(default="0.0", serialization_alias="processTime")
    success: bool = False
    message: str = ""


class GetInfoResponse(BaseResponse):
    info: dict = {}


class GetUUIDStrResponse(BaseResponse):
    id: str = ""
