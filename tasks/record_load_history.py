import asyncio
import logging
from datetime import datetime
import psutil
from database.database import session
from database.models import LoadHistory
from config.settings import BOT_NAME, RECORD_INTERVAL

logger = logging.getLogger(BOT_NAME)


async def record_load_history():
    while True:
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

            session.add(load_entry)
            session.commit()
            logger.debug(
                f"Записана история загрузки: CPU {cpu_load}%, RAM {memory_load}%, Средняя {average_load}%"
            )

        except Exception as e:
            logger.debug(f"Ошибка при записи истории загрузки: {str(e)}")

        await asyncio.sleep(RECORD_INTERVAL)
