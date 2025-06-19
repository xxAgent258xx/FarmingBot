import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import aiosqlite
import datetime
from tokens import FARMING_BOT_TOKEN

"""Коэффициенты"""
koffs = [1, 2, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
"""Количество использований, необходимое для применения коэффициента"""
koffs_kol = [0, 10, 100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000]
DB_NAME = 'm_db.db'
TOKEN = FARMING_BOT_TOKEN


"""Сравнение дат в формате ДД.ММ.ГГГГ ЧЧ:ММ:СС"""
def check_min_datetime(date1: str, date2: str):
    """"""
    """Сравнение по году"""
    if int(date1[6:11]) > int(date2[6:11]):
        return date2
    elif int(date1[6:11]) < int(date2[6:11]):
        return date1
    else:
        """Сравнение по месяцу"""
        if int(date1[3:5]) > int(date2[3:5]):
            return date2
        elif int(date1[3:5]) < int(date2[3:5]):
            return date1
        else:
            """Сравнение по дню"""
            if int(date1[0:2]) > int(date2[0:2]):
                return date2
            elif int(date1[0:2]) < int(date2[0:2]):
                return date1
            else:
                """Сравнение по часам"""
                if int(date1[11:13]) > int(date2[11:13]):
                    return date2
                elif int(date1[11:13]) < int(date2[11:13]):
                    return date1
                else:
                    """Сравнение по минутам"""
                    if int(date1[14:16]) > int(date2[14:16]):
                        return date2
                    elif int(date1[14:16]) < int(date2[14:16]):
                        return date1
                    else:
                        """Сравнение по секундам"""
                        if int(date1[17:19]) > int(date2[17:19]):
                            return date2
                        elif int(date1[17:19]) < int(date2[17:19]):
                            return date1
                        else:
                            return 0


"""Создание экземпляра бота"""
bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# 01.01.2025 00:00:00


@dp.message(Command(commands=['get']))
async def get_m(message: Message):
    lvl_up = False
    maybe = False
    new = True
    """Подключение БД"""
    async with aiosqlite.connect(DB_NAME) as db:
        """Проверка на запись в БД"""
        async with db.execute(f'SELECT kol FROM stat WHERE user_id={message.from_user.id}') as cursor:
            async for row in cursor:
                new = False
        if new:
            await db.execute(f'INSERT INTO stat(user_id, kol, koff, gets_kol) VALUES ({message.from_user.id}, 0, 0, 1)')
            await db.commit()
            kol, last, koff_index, gets_kol = 0, None, 0, 1
        else:
            """Получение значений из БД"""
            async with db.execute(
                    f'SELECT kol, last, gets_kol, koff FROM stat WHERE user_id={message.from_user.id}') as cursor:
                async for row in cursor:
                    kol = row[0]
                    last = row[1]
                    gets_kol = row[2] + 1
                    koff_index = row[3]

        dtime = datetime.datetime.now().strftime("%d.%m.%Y %X")
        h2 = (datetime.datetime(day=int(last[2][0:2]), month=int(last[2][3:5]), year=int(last[2][6:10]),
                                hour=int(last[2][11:13]), minute=int(last[2][14:16]),
                                second=int(last[2][17:19])) + datetime.timedelta(hours=2)).strftime("%d.%m.%Y %X")
        get_kol = koffs[koff_index]

        """Проверка на интервал времени"""
        if last is None:
            maybe = True
        elif check_min_datetime(dtime, h2) != dtime:
            maybe = True

        if maybe:
            """Проверка на переход на новый уровень"""
            if koff_index + 1 < len(koffs_kol):
                if gets_kol == koffs_kol[koff_index + 1]:
                    koff_index += 1
                    lvl_up = True

            """Обновление БД"""
            await db.execute(
                f'UPDATE stat SET kol={kol + get_kol}, last="{dtime}", koff={koff_index}, gets_kol={gets_kol} WHERE user_id={message.from_user.id}')
            await db.commit()

            """Отправка ответа"""
            await message.reply(
                f'{message.from_user.full_name}, вы получили {get_kol}🍊\n'
                f'Возвращайтесь через 2 часа. Всего: {kol + get_kol}🍊\n'
                f'{"Новый уровень! " if lvl_up else ""}Ваш уровень: {koff_index + 1} (x{get_kol}). До следующего уровня:{koffs_kol[koff_index + 1] - gets_kol}')
        else:
            await message.reply('Рано получать мандарины❌')


@dp.message()
async def hello(message: Message):
    await message.reply('Напиши /get')


if __name__ == '__main__':
    dp.run_polling(bot)
