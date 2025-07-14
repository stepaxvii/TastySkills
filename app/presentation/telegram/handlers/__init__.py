from aiogram import Router
from .registration import registration_router
from .manager import manager_router
from .password import password_router
from .common import common_router
from .misc import misc_router

router = Router()
router.include_router(registration_router)
router.include_router(manager_router)
router.include_router(password_router)
router.include_router(common_router)
router.include_router(misc_router) 