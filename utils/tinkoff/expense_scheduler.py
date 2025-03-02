# utils/tinkoff/expense_scheduler.py

# Стандартные модули Python
import time
import asyncio

# Сторонние модули
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Собственные модули
from utils.tinkoff.fixed_time_import_expenses import load_expenses


# Часовой пояс Москвы
moscow_tz = pytz.timezone("Europe/Moscow")


class ExpenseScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduled_times = {}  # Храним текущее запланированное время
        self.scheduler.start()


    def start_schedules(self, schedule_data):
        """
        Инициализация расписаний на основе полученных данных.
        :param schedule_data: Список словарей с export_type и export_time.
        """
        for export_type, export_time in schedule_data.items():
            if export_type in self.scheduled_times and self.scheduled_times[export_type] == export_time:
                continue  # Уже запланировано с этим временем
            elif export_type in self.scheduled_times:
                self.update_schedule(export_type, export_time)
            else:
                self.set_schedule(export_type, export_time)
    

    def set_schedule(self, export_type: str, export_time: time):
        """
        Добавление расписания.
        :param export_type: Тип экспорта ('expenses' или 'full').
        :param export_time: Время запуска (datetime.time).
        """
        # Запускаем новую задачу
        self.scheduler.add_job(
            lambda: self.async_to_sync(load_expenses, export_type), 
            CronTrigger(hour=export_time.hour, minute=export_time.minute, timezone=moscow_tz),
            id=export_type) 

        self.scheduled_times[export_type] = export_time  # Сохраняем новое время


    def update_schedule(self, export_type: str, export_time: time):
        """
        Обновление расписания на новое время.
        :param export_type: Тип экспорта ('expenses' или 'full').
        :param export_time: Время запуска (datetime.time).
        """
        # Удаляем старую задачу, если она была
        self.scheduler.remove_job(job_id=export_type, jobstore=None)

        # Запускаем новую задачу
        self.set_schedule(export_type, export_time)


    def stop(self):
        """Остановка всех задач и шедулера."""
        self.scheduler.shutdown()

    
    # Обёртка для вызова асинхронной функции в синхронном контексте
    def async_to_sync(self, async_func, export_type):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Если нет текущего цикла событий, создаём новый
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(async_func(export_type))