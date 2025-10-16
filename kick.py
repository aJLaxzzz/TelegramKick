#!/usr/bin/env python3
"""
Универсальный пакетный скрипт для удаления участников из Telegram каналов
- Полностью настраиваемый (канал, количество, таймер)
- Одна авторизация для всех операций
"""

import asyncio
import time
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsRecent
from telethon.errors import FloodWaitError, UserNotParticipantError, ChatAdminRequiredError
import config

class SimpleBatchKicker:
    def __init__(self):
        self.api_id = config.API_ID
        self.api_hash = config.API_HASH
        self.phone = config.PHONE_NUMBER
        self.channel_username = None
        self.total_to_remove = 0
        self.per_cycle_limit = 200  # Максимум за один проход
        
    async def get_channel_info(self, client):
        """Получить информацию о канале"""
        try:
            entity = await client.get_entity(self.channel_username)
            return entity
        except Exception as e:
            print(f"❌ Ошибка при получении канала: {e}")
            return None
    
    async def get_recent_participants(self, client, entity, limit):
        """Получить последних участников"""
        participants = []
        offset = 0
        batch_size = 200
        
        print(f"📋 Получаем последних {limit} участников...")
        
        while len(participants) < limit:
            try:
                result = await client(GetParticipantsRequest(
                    channel=entity,
                    filter=ChannelParticipantsRecent(),
                    offset=offset,
                    limit=min(batch_size, limit - len(participants)),
                    hash=0
                ))
                
                if not result.users:
                    break
                    
                participants.extend(result.users)
                offset += len(result.users)
                print(f"📊 Получено участников: {len(participants)}/{limit}")
                
                if len(result.users) < batch_size:
                    break
                    
            except Exception as e:
                print(f"❌ Ошибка при получении участников: {e}")
                break
        
        print(f"✅ Получено участников: {len(participants)}")
        return participants
    
    async def kick_participants(self, client, entity, participants, cycle_num):
        """Удаление участников"""
        print(f"🗑️ Удаление участников (цикл {cycle_num})...")
        
        kicked_count = 0
        errors = 0
        skipped = 0
        
        for i, user in enumerate(participants, 1):
            try:
                # Пропускаем себя
                if user.id == (await client.get_me()).id:
                    print(f"⏭️ [{i}/{len(participants)}] Пропускаем себя")
                    skipped += 1
                    continue
                
                # Удаляем участника
                await client.kick_participant(entity, user)
                kicked_count += 1
                print(f"✅ [{i}/{len(participants)}] Удален: {user.first_name or 'Unknown'}")
                
                # Задержка для избежания флуд-лимитов
                await asyncio.sleep(0.5)
                
            except FloodWaitError as e:
                print(f"\n⏳ Флуд-лимит обнаружен, ждем {e.seconds} секунд...")
                await self.flood_wait_countdown(e.seconds)
                
                try:
                    await client.kick_participant(entity, user)
                    kicked_count += 1
                    print(f"✅ [{i}/{len(participants)}] Удален: {user.first_name or 'Unknown'}")
                except Exception as retry_e:
                    print(f"❌ [{i}/{len(participants)}] Ошибка при повторной попытке: {retry_e}")
                    errors += 1
                    
            except UserNotParticipantError:
                print(f"ℹ️ [{i}/{len(participants)}] Пользователь уже не участник: {user.first_name or 'Unknown'}")
                skipped += 1
                
            except ChatAdminRequiredError:
                print(f"❌ [{i}/{len(participants)}] Нет прав администратора для удаления: {user.first_name or 'Unknown'}")
                errors += 1
                
            except Exception as e:
                print(f"❌ [{i}/{len(participants)}] Ошибка при удалении {user.first_name or 'Unknown'}: {e}")
                errors += 1
        
        return kicked_count, errors, skipped
    
    async def flood_wait_countdown(self, seconds):
        """Динамический обратный отсчет для флуд-лимита"""
        while seconds > 0:
            hours_left = seconds // 3600
            minutes_left = (seconds % 3600) // 60
            seconds_left = seconds % 60
            
            if hours_left > 0:
                print(f"\r⏳ Флуд-лимит, ждем {hours_left:02d}:{minutes_left:02d}:{seconds_left:02d}", end="", flush=True)
            else:
                print(f"\r⏳ Флуд-лимит, ждем {minutes_left:02d}:{seconds_left:02d}", end="", flush=True)
            
            await asyncio.sleep(1)
            seconds -= 1
        
        print(f"\r✅ Флуд-лимит завершен, продолжаем...")
    
    async def run_cycle(self, client, entity, cycle_num, total_cycles, limit_per_cycle):
        """Выполнить один цикл удаления"""
        print(f"\n🔄 ЦИКЛ {cycle_num}/{total_cycles}")
        print("=" * 30)
        
        # Получаем участников
        participants = await self.get_recent_participants(client, entity, limit_per_cycle)
        
        if not participants:
            print("ℹ️ Участники не найдены")
            return False
        
        # Удаляем участников
        kicked_count, errors, skipped = await self.kick_participants(client, entity, participants, cycle_num)
        
        print(f"\n📊 Результат цикла {cycle_num}:")
        print(f"✅ Успешно удалено: {kicked_count}")
        print(f"❌ Ошибок: {errors}")
        print(f"⏭️ Пропущено: {skipped}")
        
        return True
    
    def get_user_input(self):
        """Получить все параметры от пользователя"""
        print("🚀 НАСТРОЙКА ПАКЕТНОГО УДАЛЕНИЯ УЧАСТНИКОВ")
        print("=" * 60)
        
        # Название канала
        channel = input("📺 Введите username канала (например: @mychannel): ").strip()
        if not channel.startswith('@'):
            channel = '@' + channel
        self.channel_username = channel
        
        # Количество участников для удаления
        while True:
            try:
                total = input("📊 Введите общее количество участников для удаления: ").strip()
                self.total_to_remove = int(total)
                if self.total_to_remove <= 0:
                    print("❌ Количество должно быть больше 0")
                    continue
                break
            except ValueError:
                print("❌ Введите корректное число")
        
        # Расчет циклов
        total_cycles = (self.total_to_remove + self.per_cycle_limit - 1) // self.per_cycle_limit
        print(f"📋 Будет выполнено {total_cycles} циклов (максимум {self.per_cycle_limit} участников за цикл)")
        
        
        # Показываем сводку
        print(f"\n📋 СВОДКА НАСТРОЕК:")
        print(f"📺 Канал: {self.channel_username}")
        print(f"📊 Всего к удалению: {self.total_to_remove} участников")
        print(f"🔄 Циклов: {total_cycles}")
        print(f"⏱️ Ожидаемое время: ~{total_cycles * 2} минут")
        
        confirm = input("\nНачать авторизацию? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("❌ Операция отменена")
            return False
        
        return total_cycles
    
    async def run(self):
        """Основной метод запуска"""
        # Получаем параметры от пользователя
        total_cycles = self.get_user_input()
        if not total_cycles:
            return
        
        # Создаем клиент
        client = TelegramClient('session', self.api_id, self.api_hash)
        
        try:
            # Подключаемся (здесь потребуется код и пароль)
            print("\n🔐 АВТОРИЗАЦИЯ")
            print("=" * 30)
            print("📱 Введите код подтверждения и пароль:")
            await client.start(phone=self.phone)
            print("✅ Успешно подключились к Telegram")
            
            # Получаем информацию о канале
            entity = await self.get_channel_info(client)
            if not entity:
                return False
            
            print(f"📺 Канал: {entity.title}")
            
            # Выполняем циклы
            successful_cycles = 0
            total_removed = 0
            
            for cycle in range(1, total_cycles + 1):
                try:
                    # Рассчитываем сколько участников удалять в этом цикле
                    remaining = self.total_to_remove - total_removed
                    limit_this_cycle = min(self.per_cycle_limit, remaining)
                    
                    success = await self.run_cycle(client, entity, cycle, total_cycles, limit_this_cycle)
                    if success:
                        successful_cycles += 1
                        total_removed += limit_this_cycle
                    
                    # Пауза между циклами (кроме последнего)
                    if cycle < total_cycles:
                        print(f"⏳ Пауза 30 секунд перед следующим циклом...")
                        await asyncio.sleep(30)
                        
                except Exception as e:
                    print(f"❌ Ошибка в цикле {cycle}: {e}")
            
            # Итоговый отчет
            print(f"\n📊 ИТОГОВЫЙ ОТЧЕТ:")
            print(f"✅ Успешных циклов: {successful_cycles}/{total_cycles}")
            print(f"📊 Примерно удалено участников: ~{total_removed}")
            
            if successful_cycles == total_cycles:
                print("🎉 Все циклы выполнены успешно!")
            elif successful_cycles > 0:
                print(f"⚠️ Выполнено {successful_cycles} из {total_cycles} циклов")
            else:
                print("❌ Ни один цикл не выполнен успешно")
            
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            
        finally:
            await client.disconnect()
            print("🔌 Соединение закрыто")

def main():
    kicker = SimpleBatchKicker()
    
    try:
        asyncio.run(kicker.run())
    except KeyboardInterrupt:
        print("\n❌ Операция прервана пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Операция прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
