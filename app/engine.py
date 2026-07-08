"""Multi-bot runtime: loads every active bot_config and runs all of them
concurrently from one process (build step 3).

Each business's bot is its own independent python-telegram-bot
Application, with its own business_id/owner_chat_id bound into
app.bot_data at build time (see app/channels/telegram_bot.py). That is
what gives tenant isolation here: a message arriving on Business A's
bot can only ever resolve Business A's bot_data, knowledge, history,
and owner — there is no shared state between Applications. One bot
failing to start (bad token) or erroring at runtime is caught and
logged with its business_id; it never takes down the others.
"""
import asyncio
import logging

from sqlalchemy.orm import Session
from telegram.ext import Application

from app.channels.telegram_bot import build_application
from app.core.security import decrypt_secret
from app.core.time import utcnow
from app.db.session import SessionLocal
from app.models import BotConfig, Business

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 30


def _load_active_bot_configs(db: Session) -> list[dict]:
    """Not tenant-scoped by design: this is the bootstrap lookup that discovers
    which businesses have a bot to run, the same exception as the single-bot
    loader had in step 2.
    """
    rows = (
        db.query(BotConfig, Business)
        .join(Business, Business.id == BotConfig.business_id)
        .filter(BotConfig.is_active.is_(True))
        .all()
    )
    return [
        {
            "bot_config_id": bot_config.id,
            "business_id": business.id,
            "business_name": business.name,
            "token_encrypted": bot_config.telegram_bot_token_encrypted,
            "owner_chat_id": bot_config.owner_chat_id,
        }
        for bot_config, business in rows
    ]


class BotEngine:
    def __init__(self) -> None:
        self.running: dict[int, Application] = {}  # business_id -> Application

    async def _start_one(self, config: dict) -> None:
        business_id = config["business_id"]
        business_name = config["business_name"]
        try:
            token = decrypt_secret(config["token_encrypted"])
            app = build_application(token, business_id, config["owner_chat_id"])
            await app.initialize()
            await app.start()
            await app.updater.start_polling()
            self.running[business_id] = app

            db = SessionLocal()
            try:
                bot_config = db.get(BotConfig, config["bot_config_id"])
                bot_config.last_started_at = utcnow()
                db.commit()
            finally:
                db.close()

            logger.info("business_id=%s (%s): bot started", business_id, business_name)
        except Exception:
            logger.exception(
                "business_id=%s (%s): failed to start bot; other bots are unaffected",
                business_id,
                business_name,
            )

    async def start_all(self) -> None:
        db = SessionLocal()
        try:
            configs = _load_active_bot_configs(db)
        finally:
            db.close()

        if not configs:
            logger.warning("No active bot_configs found in the database.")
            return

        for config in configs:
            await self._start_one(config)

        logger.info("%d/%d bot(s) running.", len(self.running), len(configs))

    async def poll_for_new_bots(self) -> None:
        """Simple polling loop: picks up bot_configs added/activated while running
        (e.g. a new business finishing onboarding), without needing a restart.
        """
        while True:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            db = SessionLocal()
            try:
                configs = _load_active_bot_configs(db)
            finally:
                db.close()

            for config in configs:
                if config["business_id"] not in self.running:
                    logger.info(
                        "business_id=%s (%s): new active bot_config detected, starting",
                        config["business_id"],
                        config["business_name"],
                    )
                    await self._start_one(config)

    async def stop_all(self) -> None:
        for business_id, app in list(self.running.items()):
            try:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
                logger.info("business_id=%s: bot stopped", business_id)
            except Exception:
                logger.exception("business_id=%s: error while stopping bot", business_id)

    async def run_forever(self) -> None:
        await self.start_all()
        try:
            await self.poll_for_new_bots()
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop_all()
