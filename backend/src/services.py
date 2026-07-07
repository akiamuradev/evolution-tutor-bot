"""Runtime services shared by bot routers."""
from types import SimpleNamespace

from aiogram import Dispatcher

from .database import Database


dp = Dispatcher()
db = Database()


class ServiceProxy:
    def __init__(self, name: str):
        self.name = name

    def get(self):
        return getattr(services, self.name)

    def __bool__(self):
        return self.get() is not None

    def __getattr__(self, attr):
        service = self.get()
        if service is None:
            raise RuntimeError(f"Service {self.name} is not initialized")
        return getattr(service, attr)


services = SimpleNamespace(bot=None, db_pool=None, task_search=None, trend_analyzer=None)
task_search = ServiceProxy("task_search")
trend_analyzer = ServiceProxy("trend_analyzer")
