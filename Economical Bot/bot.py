import asyncio
from contextlib import suppress


from aiogram import Router, Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.enums.parse_mode import ParseMode

from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticDatabase as MDB
from pymongo.errors import DuplicateKeyError 

from keyboards.builders import inline_builder

from middlewares.throttling import ThrottlingMiddleware
from middlewares.subscription_checker import CheckSubscription

from config_reader import config

router = Router()


@router.message(CommandStart())
async def start(message: Message, db: MDB) -> None: 
    with suppress(DuplicateKeyError):
        await db.users.insert_one(
            dict(
                _id = message.from_user.id,
                balance = 100,
                bank = {
                    "currency":[0,0,0],
                    "loans":{
                        "total_amount": 0,
                        "repaid":{"amount":0, "when": []},
                        "when": {"start": "", "end": ""}
                    },
                    "deposit": {"total_emounds": 0, "when": ""}
                },
                actives = {"total_amount":0, "items": []},
                passives = {"total_amount":0, "items": []},
                bussinesses = {"total_amount":0, "items": []}

            )
        )
    await message.answer(
        "Let's get down business",
        reply_markup=inline_builder(
            ["👲 Профиль","🏢 Рынки", "🏦 Банк", "🏭 Бизнес"],
            ["profile","markets","bank","business"]
        )
        )


async def main() -> None:
    bot = Bot(config.BOT_TOKEN.get_secret_value(), parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    cluster = AsyncIOMotorClient(host="localhost", port=27017)
    db = cluster.ecodb


    dp.message.middleware(ThrottlingMiddleware())
    #dp.message.middleware(CheckSubscription())

    dp.include_routers(
        router
    )

    await bot.delete_webhook(True)
    await dp.start_polling(bot, db=db)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Error')