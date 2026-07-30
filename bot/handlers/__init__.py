from aiogram import Router

from . import start
from . import profile
from . import settings

# Создаем главный роутер, который включает в себя все остальные
router = Router()

router.include_router(start.router)
router.include_router(profile.router)
router.include_router(settings.router)