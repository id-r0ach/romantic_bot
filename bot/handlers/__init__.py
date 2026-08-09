from aiogram import Router

from . import start
from . import navigation
from . import profile
from . import settings
from . import couple
from . import letter
from . import memory

# Создаем главный роутер, который включает в себя все остальные
router = Router()

router.include_router(start.router)
router.include_router(navigation.router)
router.include_router(profile.router)
router.include_router(settings.router)
router.include_router(couple.router)
router.include_router(letter.router)
router.include_router(memory.router)