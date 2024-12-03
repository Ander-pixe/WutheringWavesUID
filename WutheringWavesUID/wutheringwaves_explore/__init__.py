from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.sv import SV
from .draw_explore_card import draw_explore_img
from ..utils.database.models import WavesBind
from ..utils.error_reply import WAVES_CODE_103
from ..utils.hint import error_reply
from ..utils.waves_prefix import PREFIX

waves_get_explore = SV('waves获取探索度')


@waves_get_explore.on_fullmatch(
    (
        f'{PREFIX}ts',
        f'{PREFIX}探索',
        f'{PREFIX}探索度',
    )
)
async def send_card_info(bot: Bot, ev: Event):
    user_id = ev.at if ev.at else ev.user_id

    uid = await WavesBind.get_uid_by_game(user_id, ev.bot_id)
    if not uid:
        return await bot.send(error_reply(WAVES_CODE_103))

    msg = await draw_explore_img(ev, uid, user_id)
    return await bot.send(msg)
