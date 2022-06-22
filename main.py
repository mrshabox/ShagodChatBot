#
# Copyright (C) 2021-2022 by TeamYukki@Github, < https://github.com/YukkiChatBot >.
#
# This file is part of < https://github.com/TeamYukki/YukkiChatBot > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TeamYukki/YukkiChatBot/blob/master/LICENSE >
#
# All rights reserved.
#

import asyncio
from sys import version as pyver

import pyrogram
from pyrogram import __version__ as pyrover
from pyrogram import filters, idle
from pyrogram.errors import FloodWait
from pyrogram.types import Message

import config
import mongo
from mongo import db

loop = asyncio.get_event_loop()
SUDO_USERS = config.SUDO_USER

app = pyrogram.Client(
    ":YukkiBot:",
    config.API_ID,
    config.API_HASH,
    bot_token=config.BOT_TOKEN,
)

save = {}
grouplist = 1


async def init():
    await app.start()

    @app.on_message(filters.command(["start", "help"]))
    async def start_command(_, message: Message):
        if await mongo.is_banned_user(message.from_user.id):
            return
        await mongo.add_served_user(message.from_user.id)
        await message.reply_text(config.PRIVATE_START_MESSAGE)

    @app.on_message(
        filters.command("mode") & filters.user(SUDO_USERS)
    )
    async def mode_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var không được xác định.  Hãy xác định nó trước"
            )
        usage = "**Sử dụng:**\n\n/mode [group | private]\n\n**group**: Tất cả các tin nhắn đến sẽ được chuyển tiếp đến nhóm Nhật ký.\n\n**private**: Tất cả các tin nhắn đến sẽ được chuyển tiếp đến Tin nhắn riêng tư của quản trị viên."
        if len(message.command) != 2:
            return await message.reply_text(usage)
        state = message.text.split(None, 1)[1].strip()
        state = state.lower()
        if state == "group":
            await mongo.group_on()
            await message.reply_text(
                "Chế độ nhóm được bật. Tất cả các tin nhắn đến sẽ được chuyển tiếp đến LOG Group"
            )
        elif state == "private":
            await mongo.group_off()
            await message.reply_text(
                "Đã bật Chế độ Riêng tư. Tất cả các tin nhắn đến sẽ được chuyển tiếp đến Tin nhắn riêng của quản trị viên!"
            )
        else:
            await message.reply_text(usage)

    @app.on_message(
        filters.command("block") & filters.user(SUDO_USERS)
    )
    async def block_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var không được xác định.  Hãy xác định nó trước"
            )
        if message.reply_to_message:
            if not message.reply_to_message.forward_sender_name:
                return await message.reply_text(
                    "Vui lòng chỉ trả lời các tin nhắn được chuyển tiếp."
                )
            replied_id = message.reply_to_message_id
            try:
                replied_user_id = save[replied_id]
            except Exception as e:
                print(e)
                return await message.reply_text(
                    "Không tìm nạp được người dùng. Bạn có thể đã khởi động lại bot hoặc một số lỗi đã xảy ra.  Vui lòng kiểm tra nhật ký"
                )
            if await mongo.is_banned_user(replied_user_id):
                return await message.reply_text("Đã bị chặn")
            else:
                await mongo.add_banned_user(replied_user_id)
                await message.reply_text("Cấm người dùng khởi động Bot")
                try:
                    await app.send_message(
                        replied_user_id,
                        "Bạn hiện bị quản trị viên cấm sử dụng Bot.",
                    )
                except:
                    pass
        else:
            return await message.reply_text(
                "Trả lời tin nhắn được chuyển tiếp của người dùng để chặn anh ta sử dụng bot"
            )

    @app.on_message(
        filters.command("unblock") & filters.user(SUDO_USERS)
    )
    async def unblock_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var không được xác định. Hãy xác định nó trước"
            )
        if message.reply_to_message:
            if not message.reply_to_message.forward_sender_name:
                return await message.reply_text(
                    "Vui lòng chỉ trả lời các tin nhắn được chuyển tiếp."
                )
            replied_id = message.reply_to_message_id
            try:
                replied_user_id = save[replied_id]
            except Exception as e:
                print(e)
                return await message.reply_text(
                    "Không tìm nạp được người dùng.  Bạn có thể đã khởi động lại bot hoặc một số lỗi đã xảy ra. Vui lòng kiểm tra nhật ký"
                )
            if not await mongo.is_banned_user(replied_user_id):
                return await message.reply_text("Đã được mở khóa")
            else:
                await mongo.remove_banned_user(replied_user_id)
                await message.reply_text(
                    "Người dùng được mở khóa!"
                )
                try:
                    await app.send_message(
                        replied_user_id,
                        "Bạn hiện đã được bỏ cấm bởi quản trị viên.",
                    )
                except:
                    pass
        else:
            return await message.reply_text(
                "Trả lời tin nhắn được chuyển tiếp của người dùng để bỏ chặn anh ta khỏi bot"
            )

    @app.on_message(
        filters.command("stats") & filters.user(SUDO_USERS)
    )
    async def stats_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var không được xác định. Hãy xác định nó trước"
            )
        served_users = len(await mongo.get_served_users())
        blocked = await mongo.get_banned_count()
        text = f""" **Số liệu thống kê ChatBot:**
        
**Phiên bản Python:** {pyver.split()[0]}
**Phiên bản Pyrogram:** {pyrover}

**Người dùng được phục vụ:** {served_users} 
**Người dùng bị chặn:** {blocked}"""
        await message.reply_text(text)

    @app.on_message(
        filters.command("broadcast") & filters.user(SUDO_USERS)
    )
    async def broadcast_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var không được xác định. Hãy xác định nó trước"
            )
        if message.reply_to_message:
            x = message.reply_to_message.message_id
            y = message.chat.id
        else:
            if len(message.command) < 2:
                return await message.reply_text(
                    "**Sử dụng**:\n/broadcast [MESSAGE] hoặc [Reply to a Message]"
                )
            query = message.text.split(None, 1)[1]

        susr = 0
        served_users = []
        susers = await mongo.get_served_users()
        for user in susers:
            served_users.append(int(user["user_id"]))
        for i in served_users:
            try:
                await app.forward_messages(
                    i, y, x
                ) if message.reply_to_message else await app.send_message(
                    i, text=query
                )
                susr += 1
            except FloodWait as e:
                flood_time = int(e.x)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time)
            except Exception:
                pass
        try:
            await message.reply_text(
                f"**Truyền tin nhắn tới {susr} người dùng.**"
            )
        except:
            pass

    @app.on_message(filters.private & ~filters.edited)
    async def incoming_private(_, message):
        user_id = message.from_user.id
        if await mongo.is_banned_user(user_id):
            return
        if user_id in SUDO_USERS:
            if message.reply_to_message:
                if (
                    message.text == "/unblock"
                    or message.text == "/block"
                    or message.text == "/broadcast"
                ):
                    return
                if not message.reply_to_message.forward_sender_name:
                    return await message.reply_text(
                        "Vui lòng chỉ trả lời các tin nhắn được chuyển tiếp."
                    )
                replied_id = message.reply_to_message_id
                try:
                    replied_user_id = save[replied_id]
                except Exception as e:
                    print(e)
                    return await message.reply_text(
                        "Không tìm nạp được người dùng.  Bạn có thể đã khởi động lại bot hoặc một số lỗi đã xảy ra. Vui lòng kiểm tra nhật ký"
                    )
                try:
                    return await app.copy_message(
                        replied_user_id,
                        message.chat.id,
                        message.message_id,
                    )
                except Exception as e:
                    print(e)
                    return await message.reply_text(
                        "Không tìm nạp được người dùng.  Bạn có thể đã khởi động lại bot hoặc một số lỗi đã xảy ra. Vui lòng kiểm tra nhật ký"
                    )
        else:
            if await mongo.is_group():
                try:
                    forwarded = await app.forward_messages(
                        config.LOG_GROUP_ID,
                        message.chat.id,
                        message.message_id,
                    )
                    save[forwarded.message_id] = user_id
                except:
                    pass
            else:
                for user in SUDO_USERS:
                    try:
                        forwarded = await app.forward_messages(
                            user, message.chat.id, message.message_id
                        )
                        save[forwarded.message_id] = user_id
                    except:
                        pass

    @app.on_message(
        filters.group & ~filters.edited & filters.user(SUDO_USERS),
        group=grouplist,
    )
    async def incoming_groups(_, message):
        if message.reply_to_message:
            if (
                message.text == "/unblock"
                or message.text == "/block"
                or message.text == "/broadcast"
            ):
                return
            replied_id = message.reply_to_message_id
            if not message.reply_to_message.forward_sender_name:
                return await message.reply_text(
                    "Vui lòng chỉ trả lời các tin nhắn được chuyển tiếp."
                )
            try:
                replied_user_id = save[replied_id]
            except Exception as e:
                print(e)
                return await message.reply_text(
                    "Không tìm nạp được người dùng.  Bạn có thể đã khởi động lại bot hoặc một số lỗi đã xảy ra. Vui lòng kiểm tra nhật ký"
                )
            try:
                return await app.copy_message(
                    replied_user_id,
                    message.chat.id,
                    message.message_id,
                )
            except Exception as e:
                print(e)
                return await message.reply_text(
                    "Không gửi được tin nhắn, người dùng có thể đã chặn bot hoặc đã xảy ra sự cố. Vui lòng kiểm tra nhật ký"
                )

    print("[LOG] - Shagod Chat Bot Started")
    await idle()


if __name__ == "__main__":
    loop.run_until_complete(init())
