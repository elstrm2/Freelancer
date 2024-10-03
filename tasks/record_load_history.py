import asyncio
from datetime import datetime
import psutil
from sqlalchemy.ext.asyncio import AsyncSession
from core.parser.main import get_interval_setting
from database.database import get_session
from database.models import LoadHistory
from config.settings import BOT_NAME
import logging

logger = logging.getLogger(BOT_NAME)


async def record_load_history() -> None:
    while True:
        record_interval = int(
            await get_interval_setting("record_load_history_interval") or 3600
        )
        try:
            cpu_load = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_load = memory_info.percent
            average_load = (cpu_load + memory_load) / 2

            load_entry = LoadHistory(
                timestamp=datetime.now(),
                cpu_load=int(cpu_load),
                memory_load=int(memory_load),
                average_load=int(average_load),
            )

            async with get_session() as session:
                session: AsyncSession
                try:
                    session.add(load_entry)
                    await session.commit()
                    logger.debug(
                        f"Записана история загрузки: CPU {cpu_load}%, RAM {memory_load}%, Средняя {average_load}%"
                    )
                except Exception as e:
                    await session.rollback()
                    logger.debug(f"Ошибка при записи истории загрузки: {str(e)}")

        except Exception as e:
            logger.error(f"Ошибка при сборе данных о загрузке: {str(e)}")

        await asyncio.sleep(record_interval)
