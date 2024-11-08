import math
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from gsuid_core.models import Event
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import crop_center_img
from gsuid_core.utils.image.utils import sget
from ..utils import hint
from ..utils.api.model import AccountBaseInfo, ExploreList, AreaInfo, ExploreItem, ExploreArea
from ..utils.error_reply import WAVES_CODE_102
from ..utils.fonts.waves_fonts import waves_font_30, waves_font_25, waves_font_26, waves_font_42, waves_font_36, \
    waves_font_24
from ..utils.image import get_event_avatar, get_waves_bg, GOLD, add_footer, GREY, YELLOW, change_color, WAVES_FREEZING, \
    WAVES_MOLTEN, WAVES_SIERRA, WAVES_SINKING, WAVES_VOID, WAVES_MOONLIT, WAVES_LINGERING
from ..utils.waves_api import waves_api

TEXT_PATH = Path(__file__).parent / 'texture2d'

tag_yes = Image.open(TEXT_PATH / 'tag_yes.png')
tag_yes_draw = ImageDraw.Draw(tag_yes)
tag_yes_draw.text((85, 30), '已完成', 'white', waves_font_36, 'mm')
tag_no = Image.open(TEXT_PATH / 'tag_no.png')
tag_no_draw = ImageDraw.Draw(tag_no)
tag_no_draw.text((85, 30), '未完成', 'white', waves_font_36, 'mm')

country_color_map = {
    "黑海岸": (28, 55, 118),
    "瑝珑": (140, 113, 58),
}

progress_color = [
    (10, WAVES_MOONLIT),
    (20, WAVES_LINGERING),
    (35, WAVES_FREEZING),
    (50, WAVES_SIERRA),
    (70, WAVES_SINKING),
    (80, WAVES_VOID),
    (90, YELLOW),
    (100, WAVES_MOLTEN)
]


def get_progress_color(progress):
    float_progress = float(progress)
    result = WAVES_MOONLIT
    for _p, color in progress_color:
        if float_progress >= _p:
            result = color
    return result


async def draw_explore_img(ev: Event, uid: str):
    ck = await waves_api.get_ck(uid)
    if not ck:
        return hint.error_reply(WAVES_CODE_102)
    # 账户数据
    succ, account_info = await waves_api.get_base_info(uid, ck)
    if not succ:
        return account_info
    account_info = AccountBaseInfo(**account_info)

    succ, explore_data = await waves_api.get_explore_data(uid, ck)
    if not succ:
        return explore_data
    explore_data = ExploreList(**explore_data)
    if not explore_data.open:
        return hint.error_reply(msg='探索数据未开启')

    # 计算总高度
    h = 0
    for mi, _explore in enumerate(explore_data.exploreList):
        h += 250
        h += math.ceil(len(_explore.areaInfoList) / 3) * 570

    img = get_waves_bg(2000, h, 'bg3')

    # 头像部分
    avatar = await draw_pic_with_ring(ev)
    avatar_ring = Image.open(TEXT_PATH / 'avatar_ring.png')
    img.paste(avatar, (85, 70), avatar)
    avatar_ring = avatar_ring.resize((180, 180))
    img.paste(avatar_ring, (95, 80), avatar_ring)

    # 基础信息 名字 特征码
    base_info_bg = Image.open(TEXT_PATH / 'base_info_bg.png')
    base_info_draw = ImageDraw.Draw(base_info_bg)
    base_info_draw.text((275, 120), f'{account_info.name[:7]}', 'white', waves_font_30, 'lm')
    base_info_draw.text((226, 173), f'特征码:  {account_info.id}', GOLD, waves_font_25, 'lm')
    img.paste(base_info_bg, (75, 20), base_info_bg)

    # 账号基本信息，由于可能会没有，放在一起
    if account_info.is_full:
        title_bar = Image.open(TEXT_PATH / 'title_bar.png')
        title_bar_draw = ImageDraw.Draw(title_bar)
        title_bar_draw.text((660, 125), '账号等级', GREY, waves_font_26, 'mm')
        title_bar_draw.text((660, 78), f'Lv.{account_info.level}', 'white', waves_font_42, 'mm')

        title_bar_draw.text((810, 125), '世界等级', GREY, waves_font_26, 'mm')
        title_bar_draw.text((810, 78), f'Lv.{account_info.worldLevel}', 'white', waves_font_42, 'mm')
        img.paste(title_bar, (40, 70), title_bar)

    explore_title = Image.open(TEXT_PATH / 'explore_title.png')

    explore_frame = Image.open(TEXT_PATH / 'explore_frame.png')
    explore_bar = Image.open(TEXT_PATH / 'explore_bar.png')
    max_len = 357
    hi = 250
    for mi, _explore in enumerate(explore_data.exploreList):
        _explore: ExploreArea
        _explore_title = explore_title.copy()
        _explore_title = await change_color(_explore_title, country_color_map.get(_explore.country.countryName, YELLOW))
        # 大区域探索度
        content_img = Image.open(BytesIO((await sget(_explore.country.homePageIcon)).content)).convert('RGBA')
        _explore_title.alpha_composite(content_img, (150, 30))
        _explore_title_draw = ImageDraw.Draw(_explore_title)
        _explore_title_draw.text((370, 100), f'{_explore.country.countryName}', 'white', waves_font_42, 'lm')
        _explore_title_draw.text((370, 150), f'探索度: {_explore.countryProgress}%', 'white', waves_font_42, 'lm')
        tag = tag_yes if float(_explore.countryProgress) == 100 else tag_no
        _explore_title.alpha_composite(tag, (1740, 60))

        img.paste(_explore_title, (0, hi), _explore_title)

        for ni, _subArea in enumerate(_explore.areaInfoList):
            _subArea: AreaInfo
            _explore_frame = explore_frame.copy()
            _explore_frame = await change_color(
                _explore_frame,
                get_progress_color(_subArea.areaProgress),
                h=83
            )
            _explore_frame_draw = ImageDraw.Draw(_explore_frame)

            _explore_frame_draw.text((30, 50), f'{_subArea.areaName}', 'white', waves_font_36, 'lm')
            _explore_frame_draw.text((570, 50), f'{_subArea.areaProgress}%', 'white', waves_font_36, 'rm')

            for bi, _item in enumerate(_subArea.itemList):
                _item: ExploreItem
                _explore_bar = explore_bar.copy()

                _explore_frame.alpha_composite(_explore_bar, (20, 90 + 70 * bi))
                ratio = _item.progress * 0.01
                # 进度条
                _explore_frame_draw.rounded_rectangle(
                    (131, 113 + 70 * bi, int(131 + ratio * max_len), 126 + 70 * bi),
                    radius=10,
                    fill=get_progress_color(_item.progress))

                # 小地区探索度
                if len(_item.name) >= 4:
                    s = len(_item.name) // 2
                    _explore_frame_draw.text((68, 95 + 70 * bi), f'{_item.name[:s]}', 'white', waves_font_24, 'mm')
                    _explore_frame_draw.text((68, 125 + 70 * bi), f'{_item.name[s:]}', 'white', waves_font_24, 'mm')
                else:
                    _explore_frame_draw.text((68, 120 + 70 * bi), f'{_item.name}', 'white', waves_font_30, 'mm')
                _explore_frame_draw.text((580, 120 + 70 * bi), f'{_item.progress}%', 'white', waves_font_30, 'rm')

            _w = 100 + 600 * (ni % 3)
            _h = hi + 250 + 510 * int(ni / 3)
            img.alpha_composite(_explore_frame, (_w, _h))

        hi += math.ceil(len(_explore.areaInfoList) / 3) * 570

    img = add_footer(img)
    img = await convert_img(img)
    return img


async def draw_pic_with_ring(ev: Event):
    pic = await get_event_avatar(ev)

    mask_pic = Image.open(TEXT_PATH / 'avatar_mask.png')
    img = Image.new('RGBA', (180, 180))
    mask = mask_pic.resize((160, 160))
    resize_pic = crop_center_img(pic, 160, 160)
    img.paste(resize_pic, (20, 20), mask)

    return img