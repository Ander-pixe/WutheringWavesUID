from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV
from .deal import add_cookie, delete_cookie, get_cookie
from ..utils.database.models import WavesBind
from ..utils.message import send_diff_msg
from ..utils.waves_prefix import PREFIX

waves_bind_uid = SV('鸣潮绑定特征码', priority=10)
waves_add_ck = SV('鸣潮添加token', priority=5)
waves_del_ck = SV('鸣潮删除token', priority=5)
waves_get_ck = SV('waves获取ck', area='DIRECT')


@waves_add_ck.on_prefix((
    f'{PREFIX}添加CK', f'{PREFIX}添加ck',
    f'{PREFIX}添加Token', f'{PREFIX}添加token', f'{PREFIX}添加TOKEN'
),
    block=True)
async def send_waves_add_ck_msg(bot: Bot, ev: Event):
    ck = ev.text.strip()
    at_sender = True if ev.group_id else False
    await bot.send(await add_cookie(ev, ck), at_sender)


@waves_del_ck.on_command((
    f'{PREFIX}删除ck', f'{PREFIX}删除CK',
    f'{PREFIX}删除Token', f'{PREFIX}删除token', f'{PREFIX}删除TOKEN'
),
    block=True)
async def send_waves_del_ck_msg(bot: Bot, ev: Event):
    at_sender = True if ev.group_id else False
    uid = ev.text.strip()
    if not uid or len(uid) != 9:
        return await bot.send(f'[鸣潮] 该命令末尾需要跟正确的特征码! \n例如【{PREFIX}删除token123456】\n', at_sender)
    await bot.send(await delete_cookie(ev, uid), at_sender)


@waves_get_ck.on_fullmatch((
    f'{PREFIX}获取ck', f'{PREFIX}获取CK',
    f'{PREFIX}获取Token', f'{PREFIX}获取token', f'{PREFIX}获取TOKEN'
),
    block=True)
async def send_waves_del_ck_msg(bot: Bot, ev: Event):
    await bot.send(await get_cookie(bot, ev))


@waves_bind_uid.on_command(
    (
        f'{PREFIX}绑定',
        f'{PREFIX}切换',
        f'{PREFIX}删除全部特征码',
        f'{PREFIX}删除全部UID',
        f'{PREFIX}删除',
        f'{PREFIX}查看',
    ),
    block=True,
)
async def send_waves_bind_uid_msg(bot: Bot, ev: Event):
    uid = ev.text.strip().replace('uid', '').replace('UID', '')
    qid = ev.user_id

    at_sender = True if ev.group_id else False

    if '绑定' in ev.command:
        if not uid:
            return await bot.send(f'该命令需要带上正确的uid!\n{PREFIX}绑定uid\n', at_sender)
        code = await WavesBind.insert_waves_uid(qid, ev.bot_id, uid, ev.group_id, lenth_limit=9)
        if code == 0 or code == -2:
            retcode = await WavesBind.switch_uid_by_game(qid, ev.bot_id, uid)
        return await send_diff_msg(
            bot,
            code,
            {
                0: f'[鸣潮] 特征码[{uid}]绑定成功！\n\n当前仅支持查询部分信息，完整功能请使用【{PREFIX}登录】\n使用【{PREFIX}查看】查看已绑定的特征码\n使用【{PREFIX}刷新面板】更新角色面板\n更新角色面板后可以使用【{PREFIX}暗主排行】查询暗主排行\n',
                -1: f'[鸣潮] 特征码[{uid}]的位数不正确！\n',
                -2: f'[鸣潮] 特征码[{uid}]已经绑定过了！\n',
                -3: '[鸣潮] 你输入了错误的格式!\n',
            },
            at_sender=at_sender
        )
    elif '切换' in ev.command:
        retcode = await WavesBind.switch_uid_by_game(qid, ev.bot_id, uid)
        if retcode == 0:
            uid_list = await WavesBind.get_uid_list_by_game(qid, ev.bot_id)
            return await bot.send(f'[鸣潮] 切换特征码[{uid_list[0]}]成功！\n', at_sender)
        else:
            return await bot.send(f'[鸣潮] 尚未绑定该特征码[{uid}]\n', at_sender)
    elif '查看' in ev.command:
        uid_list = await WavesBind.get_uid_list_by_game(qid, ev.bot_id)
        if uid_list:
            uids = '\n'.join(uid_list)
            return await bot.send(f'[鸣潮] 绑定的特征码列表为：\n{uids}\n', at_sender)
        else:
            return await bot.send(f'[鸣潮] 尚未绑定任何特征码\n', at_sender)
    elif '删除全部' in ev.command:
        retcode = await WavesBind.update_data(
            user_id=qid,
            bot_id=ev.bot_id,
            **{WavesBind.get_gameid_name(None): None},
        )
        if retcode == 0:
            return await bot.send(f'[鸣潮] 删除全部特征码成功！\n', at_sender)
        else:
            return await bot.send(f'[鸣潮] 尚未绑定任何特征码\n', at_sender)
    else:
        if not uid:
            return await bot.send(f'[鸣潮] 该命令末尾需要跟正确的特征码!\n例如【{PREFIX}删除123456】\n', at_sender)
        data = await WavesBind.delete_uid(qid, ev.bot_id, uid)
        return await send_diff_msg(
            bot,
            data,
            {
                0: f'[鸣潮] 删除特征码[{uid}]成功！\n',
                -1: f'[鸣潮] 该特征码[{uid}]不在已绑定列表中！\n',
            },
            at_sender=at_sender
        )
