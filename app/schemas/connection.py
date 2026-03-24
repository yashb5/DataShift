from datetime import datetime
from pydantic import BaseModel, Field


class ConnectionRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=50)
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., gt=0, le=65535)
    database_name: str = Field(..., min_length=1, max_length=255, alias="databaseName")
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)

    class Config:
        populate_by_name = True


class ConnectionResponse(BaseModel):
    id: int
    name: str
    type: str
    host: str
    port: int
    database_name: str = Field(..., alias="databaseName")
    username: str
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    connection_time_ms: int | None = Field(None, alias="connectionTimeMs")

    class Config:
        populate_by_name = True


class ColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool
    size: int | None = None

    class Config:
        from_attributes = True


class TableSchema(BaseModel):
    table_name: str = Field(..., alias="tableName")
    columns: list[ColumnInfo]

    class Config:
        from_attributes = True
        populate_by_name = True
