#!/usr/bin/env python3
"""Entry point script for DataShift."""

import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.server_port,
        reload=settings.debug,
    )
