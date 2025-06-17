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

# 01.01.2025 00:00:00


@dp.message(Command(commands=['get']))
async def get_m(message: Message):
    lvl_up = False
    """Подключение БД"""
    connector = await aiosqlite.connect(DB_NAME)
    cursor = await connector.cursor()

    """Проверка на запись в БД"""
    if await cursor.execute(f'SELECT kol FROM stat WHERE user_id={message.from_user.id}').fetchone() is None:
        await cursor.execute(f'INSERT INTO stat(user_id, kol, koff, gets_kol) VALUES ({message.from_user.id}, 0, 0, 0)')

    """Получение значений из БД"""
    m_kol = await cursor.execute(f'SELECT kol FROM stat WHERE user_id={message.from_user.id}').fetchone()[0]
    last = await cursor.execute(f'SELECT last FROM stat WHERE user_id={message.from_user.id}').fetchone()[0]
    dtime = datetime.datetime.now().strftime("%d.%m.%Y %X")
    gets_kol = await cursor.execute(f'SELECT gets_kol FROM stat WHERE user_id={message.from_user.id}').fetchone()[0] + 1
    koff_index = await cursor.execute(f'SELECT koff FROM stat WHERE user_id={message.from_user.id}').fetchone()[0]
    get_kol = koffs[koff_index]

    """Проверка на переход на новый уровень"""
    if gets_kol == koffs_kol[koff_index + 1]:
        koff_index += 1
        lvl_up = True

    """Проверка на интервал времени"""
    if (
            last is None
            or
            check_min_datetime(dtime, (
                    datetime.datetime(day=int(last[0:2]), month=int(last[3:5]), year=int(last[6:10]),
                                      hour=int(last[11:13]), minute=int(last[14:16]),
                                      second=int(last[17:19])) + datetime.timedelta(hours=2)
            ).strftime("%d.%m.%Y %X")) != dtime
       ):
        maybe = True
    else:
        maybe = False

    if maybe:
        """Обновление БД"""
        await cursor.execute(
            f'UPDATE stat SET kol={m_kol + get_kol}, last="{dtime}", koff={koff_index}, gets_kol={gets_kol} WHERE user_id={message.from_user.id}')

        """Отправка ответа"""
        await message.reply(
            f'{message.from_user.full_name}, вы получили {get_kol}🍊\n'
            f'Возвращайтесь через 2 часа. Всего: {m_kol + get_kol}🍊\n'
            f'{"Новый уровень! " if lvl_up else ""}Ваш уровень: {koff_index + 1} (x{get_kol}). До следующего уровня:{koffs_kol[koff_index + 1] - gets_kol}')
    else:
        await message.reply('Рано получать мандарины❌')
    await connector.commit()
    await cursor.close()
    await connector.close()


@dp.message()
async def hello(message: Message):
    await message.reply('Напиши /get')


if __name__ == '__main__':
    dp.run_polling(bot)
