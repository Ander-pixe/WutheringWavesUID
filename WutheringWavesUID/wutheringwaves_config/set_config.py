from gsuid_core.logger import logger
from gsuid_core.models import Event
from ..utils.database.models import WavesUser, WavesPush

PUSH_MAP = {
    '体力': 'resin',
}
SIGN_MAP = {
    "自动签到": "sign",
    "推送": "push",
}


async def set_push_value(bot_id: str, func: str, uid: str, value: int):
    if func in PUSH_MAP:
        status = PUSH_MAP[func]
    else:
        return '该配置项不存在!'
    logger.info('[设置推送阈值]func: {}, value: {}'.format(status, value))
    if (
        await WavesPush.update_data_by_uid(
            uid=uid, bot_id=bot_id, **{f'{status}_value': value}
        )
        == 0
    ):
        return f'设置成功!\n当前{func}推送阈值:{value}'
    else:
        return '设置失败!\n请检查参数是否正确!'


async def set_config_func(ev: Event, uid: str = "0"):
    config_name = ev.text
    if '开启' in ev.command:
        option = ev.group_id if ev.group_id else 'on'
    else:
        option = 'off'

    logger.info(f"uid: {uid}, option: {option}, config_name: {config_name}")
    if config_name in SIGN_MAP:
        # 执行设置
        await WavesUser.update_data_by_uid(
            uid=uid,
            bot_id=ev.bot_id,
            **{f"{SIGN_MAP[config_name]}_switch": option, },
        )
    elif config_name.replace('推送', '') in PUSH_MAP:
        await WavesPush.update_data_by_uid(
            uid=uid,
            bot_id=ev.bot_id,
            **{f'{PUSH_MAP[config_name.replace("推送", "")]}_push': option, },
        )
    else:
        return "该配置项不存在!"

    if option == "on":
        succeed_msg = "开启至私聊消息!"
    elif option == "off":
        succeed_msg = "关闭!"
    else:
        succeed_msg = f"开启至群{option}"
    return f"{config_name}已{succeed_msg}"