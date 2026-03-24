import time
import asyncio
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.connection import Connection
from app.schemas.connection import (
    ConnectionRequest,
    ConnectionResponse,
    ConnectionTestResponse,
    TableSchema,
    ColumnInfo,
)
from app.services.encryption_service import encryption_service


class ConnectionService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, request: ConnectionRequest) -> ConnectionResponse:
        existing = await self.db.execute(
            select(Connection).where(Connection.name == request.name)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Connection with name '{request.name}' already exists")
        
        connection = Connection(
            name=request.name,
            type=request.type,
            host=request.host,
            port=request.port,
            database_name=request.database_name,
            username=request.username,
            password=encryption_service.encrypt(request.password),
        )
        
        self.db.add(connection)
        await self.db.commit()
        await self.db.refresh(connection)
        
        return self._to_response(connection)
    
    async def get_all(self) -> list[ConnectionResponse]:
        result = await self.db.execute(select(Connection))
        connections = result.scalars().all()
        return [self._to_response(c) for c in connections]
    
    async def get_by_id(self, connection_id: int) -> ConnectionResponse:
        connection = await self._get_connection(connection_id)
        return self._to_response(connection)
    
    async def delete(self, connection_id: int) -> None:
        connection = await self._get_connection(connection_id)
        await self.db.delete(connection)
        await self.db.commit()
    
    async def test_connection(self, connection_id: int) -> ConnectionTestResponse:
        connection = await self._get_connection(connection_id)
        decrypted_password = encryption_service.decrypt(connection.password)
        
        start_time = time.time()
        try:
            conn = await self._create_db_connection(
                connection.type,
                connection.host,
                connection.port,
                connection.database_name,
                connection.username,
                decrypted_password,
            )
            if conn:
                await self._close_db_connection(conn, connection.type)
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            return ConnectionTestResponse(
                success=True,
                message="Connection successful",
                connection_time_ms=elapsed_ms,
            )
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return ConnectionTestResponse(
                success=False,
                message=str(e),
                connection_time_ms=elapsed_ms,
            )
    
    async def get_schemas(self, connection_id: int) -> list[TableSchema]:
        connection = await self._get_connection(connection_id)
        decrypted_password = encryption_service.decrypt(connection.password)
        
        try:
            schemas = await self._fetch_schemas(
                connection.type,
                connection.host,
                connection.port,
                connection.database_name,
                connection.username,
                decrypted_password,
            )
            return schemas
        except Exception as e:
            raise ValueError(f"Failed to fetch schemas: {e}")
    
    async def _get_connection(self, connection_id: int) -> Connection:
        result = await self.db.execute(
            select(Connection).where(Connection.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        if not connection:
            raise ValueError(f"Connection with id {connection_id} not found")
        return connection
    
    async def get_connection_entity(self, connection_id: int) -> Connection:
        return await self._get_connection(connection_id)
    
    def _to_response(self, connection: Connection) -> ConnectionResponse:
        return ConnectionResponse(
            id=connection.id,
            name=connection.name,
            type=connection.type,
            host=connection.host,
            port=connection.port,
            database_name=connection.database_name,
            username=connection.username,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
        )
    
    def build_jdbc_url(self, conn: Connection) -> str:
        db_type = conn.type.lower()
        if db_type == "h2":
            if "mem:" in conn.database_name:
                return f"jdbc:h2:mem:{conn.database_name.replace('mem:', '')}"
            elif "tcp:" in conn.database_name or conn.host:
                return f"jdbc:h2:tcp://{conn.host}:{conn.port}/{conn.database_name}"
            else:
                return f"jdbc:h2:file:{conn.database_name}"
        elif db_type in ("mysql", "mariadb"):
            return f"jdbc:mysql://{conn.host}:{conn.port}/{conn.database_name}"
        elif db_type == "postgresql":
            return f"jdbc:postgresql://{conn.host}:{conn.port}/{conn.database_name}"
        else:
            return f"jdbc:{db_type}://{conn.host}:{conn.port}/{conn.database_name}"
    
    def build_python_url(self, conn: Connection, decrypted_password: str) -> str:
        db_type = conn.type.lower()
        if db_type == "sqlite":
            return f"sqlite:///{conn.database_name}"
        elif db_type in ("mysql", "mariadb"):
            return f"mysql+pymysql://{conn.username}:{decrypted_password}@{conn.host}:{conn.port}/{conn.database_name}"
        elif db_type == "postgresql":
            return f"postgresql+psycopg2://{conn.username}:{decrypted_password}@{conn.host}:{conn.port}/{conn.database_name}"
        elif db_type == "h2":
            return f"h2://{conn.host}:{conn.port}/{conn.database_name}"
        else:
            return f"{db_type}://{conn.username}:{decrypted_password}@{conn.host}:{conn.port}/{conn.database_name}"
    
    async def _create_db_connection(
        self,
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
    ):
        db_type = db_type.lower()
        
        if db_type == "sqlite":
            import aiosqlite
            return await aiosqlite.connect(database)
        elif db_type in ("mysql", "mariadb"):
            import aiomysql
            return await aiomysql.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                db=database,
            )
        elif db_type == "postgresql":
            import asyncpg
            return await asyncpg.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                database=database,
            )
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    async def _close_db_connection(self, conn, db_type: str):
        db_type = db_type.lower()
        if db_type == "sqlite":
            await conn.close()
        elif db_type in ("mysql", "mariadb"):
            conn.close()
        elif db_type == "postgresql":
            await conn.close()
    
    async def _fetch_schemas(
        self,
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
    ) -> list[TableSchema]:
        db_type = db_type.lower()
        schemas = []
        
        if db_type == "sqlite":
            import aiosqlite
            async with aiosqlite.connect(database) as conn:
                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = await cursor.fetchall()
                for (table_name,) in tables:
                    cursor = await conn.execute(f"PRAGMA table_info({table_name})")
                    columns_info = await cursor.fetchall()
                    columns = [
                        ColumnInfo(
                            name=col[1],
                            type=col[2],
                            nullable=not col[3],
                            size=None,
                        )
                        for col in columns_info
                    ]
                    schemas.append(TableSchema(table_name=table_name, columns=columns))
        
        elif db_type in ("mysql", "mariadb"):
            import aiomysql
            conn = await aiomysql.connect(
                host=host, port=port, user=username, password=password, db=database
            )
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute("SHOW TABLES")
                    tables = await cursor.fetchall()
                    for (table_name,) in tables:
                        await cursor.execute(f"DESCRIBE {table_name}")
                        columns_info = await cursor.fetchall()
                        columns = [
                            ColumnInfo(
                                name=col[0],
                                type=col[1],
                                nullable=col[2] == "YES",
                                size=None,
                            )
                            for col in columns_info
                        ]
                        schemas.append(TableSchema(table_name=table_name, columns=columns))
            finally:
                conn.close()
        
        elif db_type == "postgresql":
            import asyncpg
            conn = await asyncpg.connect(
                host=host, port=port, user=username, password=password, database=database
            )
            try:
                tables = await conn.fetch(
                    """
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    """
                )
                for table in tables:
                    table_name = table["table_name"]
                    columns_info = await conn.fetch(
                        """
                        SELECT column_name, data_type, is_nullable, character_maximum_length
                        FROM information_schema.columns
                        WHERE table_name = $1
                        ORDER BY ordinal_position
                        """,
                        table_name,
                    )
                    columns = [
                        ColumnInfo(
                            name=col["column_name"],
                            type=col["data_type"],
                            nullable=col["is_nullable"] == "YES",
                            size=col["character_maximum_length"],
                        )
                        for col in columns_info
                    ]
                    schemas.append(TableSchema(table_name=table_name, columns=columns))
            finally:
                await conn.close()
        
        return schemas
