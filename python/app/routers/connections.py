from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.connection_service import ConnectionService
from app.schemas.connection import (
    ConnectionRequest,
    ConnectionResponse,
    ConnectionTestResponse,
    TableSchema,
)

router = APIRouter(prefix="/api/v1/connections", tags=["Connections"])


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    request: ConnectionRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ConnectionService(db)
    try:
        return await service.create(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[ConnectionResponse])
async def get_all_connections(db: AsyncSession = Depends(get_db)):
    service = ConnectionService(db)
    return await service.get_all()


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(connection_id: int, db: AsyncSession = Depends(get_db)):
    service = ConnectionService(db)
    try:
        return await service.get_by_id(connection_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(connection_id: int, db: AsyncSession = Depends(get_db)):
    service = ConnectionService(db)
    try:
        await service.delete(connection_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{connection_id}/test", response_model=ConnectionTestResponse)
async def test_connection(connection_id: int, db: AsyncSession = Depends(get_db)):
    service = ConnectionService(db)
    try:
        return await service.test_connection(connection_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{connection_id}/schemas", response_model=list[TableSchema])
async def get_connection_schemas(connection_id: int, db: AsyncSession = Depends(get_db)):
    service = ConnectionService(db)
    try:
        return await service.get_schemas(connection_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
