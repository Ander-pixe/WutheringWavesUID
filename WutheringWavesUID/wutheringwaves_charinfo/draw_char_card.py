import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

from gsuid_core.models import Event
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import get_event_avatar, crop_center_img
from ..utils.api.model import RoleDetailData, AccountBaseInfo, WeaponData
from ..utils.char_info_utils import get_all_role_detail_info
from ..utils.error_reply import WAVES_CODE_102
from ..utils.fonts.waves_fonts import waves_font_30, waves_font_25, waves_font_50, waves_font_40, waves_font_20, \
    waves_font_24
from ..utils.image import get_waves_bg, add_footer, GOLD, get_role_pile, get_weapon_type, get_attribute, \
    get_square_weapon, get_attribute_prop
from ..utils.name_convert import alias_to_char_name, char_name_to_char_id
from ..utils.resource.download_file import get_skill_img, get_chain_img, get_phantom_img
from ..utils.waves_api import waves_api
from ..utils.weapon_detail import get_weapon_detail, WavesWeaponResult, get_breach
from ..wutheringwaves_config import PREFIX

TEXT_PATH = Path(__file__).parent / 'texture2d'
SPECIAL_GOLD = (234, 183, 4)


async def draw_char_detail_img(ev: Event, uid: str, char: str):
    ck = await waves_api.get_ck(uid)
    if not ck:
        return WAVES_CODE_102
    # 账户数据
    succ, account_info = await waves_api.get_base_info(uid, ck)
    if not succ:
        return account_info
    account_info = AccountBaseInfo(**account_info)

    char_id = char_name_to_char_id(char)
    if not char_id:
        return f'[鸣潮] 角色名{char}无法找到, 可能暂未适配, 请先检查输入是否正确！'

    char_name = alias_to_char_name(char)
    all_role_detail: dict[str, RoleDetailData] = await get_all_role_detail_info(uid)

    if all_role_detail is None or char_name not in all_role_detail:
        return f'[鸣潮] 未找到该角色信息, 请先使用[{PREFIX}刷新面板]进行刷新!'

    role_detail: RoleDetailData = all_role_detail[char_name]

    img = get_waves_bg(1200, 2650, 'bg3')

    # 头像部分
    avatar = await draw_pic_with_ring(ev)
    avatar_ring = Image.open(TEXT_PATH / 'avatar_ring.png')

    img.paste(avatar, (45, 20), avatar)
    avatar_ring = avatar_ring.resize((180, 180))
    img.paste(avatar_ring, (55, 30), avatar_ring)

    base_info_bg = Image.open(TEXT_PATH / 'base_info_bg.png')
    base_info_draw = ImageDraw.Draw(base_info_bg)
    base_info_draw.text((275, 120), f'{account_info.name[:7]}', 'white', waves_font_30, 'lm')
    base_info_draw.text((226, 173), f'特征码:  {account_info.id}', GOLD, waves_font_25, 'lm')
    img.paste(base_info_bg, (35, -30), base_info_bg)

    # 左侧pile部分
    role_pile = await get_role_pile(role_detail.role.roleId)
    char_mask = Image.open(TEXT_PATH / 'char_mask.png')
    char_fg = Image.open(TEXT_PATH / 'char_fg.png')

    role_attribute = await get_attribute(role_detail.role.attributeName)
    role_attribute = role_attribute.resize((50, 50)).convert('RGBA')
    char_fg.paste(role_attribute, (434, 112), role_attribute)
    weapon_type = await get_weapon_type(role_detail.role.weaponTypeName)
    weapon_type = weapon_type.resize((40, 40)).convert('RGBA')
    char_fg.paste(weapon_type, (439, 182), weapon_type)

    char_fg_image = ImageDraw.Draw(char_fg)
    roleName = role_detail.role.roleName
    if "漂泊者" in roleName:
        roleName = "漂泊者"

    draw_text_with_shadow(char_fg_image,
                          f'{roleName}',
                          296, 867,
                          waves_font_50, anchor='rm')
    draw_text_with_shadow(char_fg_image,
                          f'Lv.{role_detail.role.level}',
                          300, 875,
                          waves_font_30, anchor='lm')

    role_pile_image = Image.new('RGBA', (560, 1000))
    role_pile_image.paste(role_pile, ((560 - role_pile.size[0]) // 2, (1000 - role_pile.size[1]) // 2), role_pile)
    img.paste(role_pile_image, (25, 170), char_mask)
    img.paste(char_fg, (25, 170), char_fg)

    # 右侧属性-技能
    right_image_temp = Image.new('RGBA', (600, 1000))
    banner1 = Image.open(TEXT_PATH / 'banner1.png')
    right_image_temp.alpha_composite(banner1, dest=(0, 0))
    for i, _skill in enumerate(role_detail.skillList):
        skill_bg = Image.open(TEXT_PATH / 'skill_bg.png')

        skill_img = await get_skill_img(role_detail.role.roleId, _skill.skill.name, _skill.skill.iconUrl)
        skill_img = skill_img.resize((70, 70))
        skill_bg.paste(skill_img, (57, 65), skill_img)

        skill_bg_draw = ImageDraw.Draw(skill_bg)
        skill_bg_draw.text((150, 83), f'{_skill.skill.type}', 'white', waves_font_25, 'lm')
        skill_bg_draw.text((150, 113), f'Lv.{_skill.level}', 'white', waves_font_25, 'lm')

        skill_bg_temp = Image.new('RGBA', skill_bg.size)
        skill_bg_temp = Image.alpha_composite(skill_bg_temp, skill_bg)

        _x = 10 + (i % 2) * 280
        _y = 40 + (i // 2) * 150
        right_image_temp.alpha_composite(skill_bg_temp, dest=(_x, _y))

    # 武器banner
    banner2 = Image.open(TEXT_PATH / 'banner2.png')
    right_image_temp.alpha_composite(banner2, dest=(0, 500))

    # 右侧属性-武器
    weapon_bg = Image.open(TEXT_PATH / 'weapon_bg.png')
    weapon_bg_temp = Image.new('RGBA', weapon_bg.size)
    weapon_bg_temp.alpha_composite(weapon_bg, dest=(0, 0))

    weaponData: WeaponData = role_detail.weaponData

    weapon_icon = await get_square_weapon(weaponData.weapon.weaponId)
    weapon_icon = crop_center_img(weapon_icon, 110, 110)
    weapon_icon_bg = get_weapon_icon_bg(weaponData.weapon.weaponStarLevel)
    weapon_icon_bg.paste(weapon_icon, (10, 20), weapon_icon)

    weapon_bg_temp_draw = ImageDraw.Draw(weapon_bg_temp)
    weapon_bg_temp_draw.text((200, 30), f'{weaponData.weapon.weaponName}', SPECIAL_GOLD, waves_font_40, 'lm')
    weapon_bg_temp_draw.text((203, 75), f'Lv.{weaponData.level}/90', 'white', waves_font_30, 'lm')

    _x = 220 + 43 * len(weaponData.weapon.weaponName)
    _y = 37
    weapon_bg_temp_draw.rounded_rectangle([_x - 15, _y - 15, _x + 50, _y + 15], radius=7,
                                          fill=(128, 138, 135, int(0.8 * 255)))
    weapon_bg_temp_draw.text((_x, _y), f'精{weaponData.resonLevel}', 'white',
                             waves_font_24, 'lm')

    weapon_breach = get_breach(weaponData.breach, weaponData.level)
    for i in range(0, weapon_breach):
        promote_icon = Image.open(TEXT_PATH / 'promote_icon.png')
        weapon_bg_temp.alpha_composite(promote_icon, dest=(200 + 40 * i, 100))

    weapon_bg_temp.alpha_composite(weapon_icon_bg, dest=(45, 0))

    weapon_detail: WavesWeaponResult = get_weapon_detail(
        weaponData.weapon.weaponId,
        weaponData.level,
        weaponData.breach,
        weaponData.resonLevel)
    stats_main = await get_attribute_prop(weapon_detail.stats[0]['name'])
    stats_main = stats_main.resize((40, 40))
    weapon_bg_temp.alpha_composite(stats_main, (65, 187))
    weapon_bg_temp_draw.text((130, 207), f'{weapon_detail.stats[0]["name"]}', 'white', waves_font_30, 'lm')
    weapon_bg_temp_draw.text((500, 207), f'{weapon_detail.stats[0]["value"]}', 'white', waves_font_30, 'rm')
    stats_sub = await get_attribute_prop(weapon_detail.stats[1]['name'])
    stats_sub = stats_sub.resize((40, 40))
    weapon_bg_temp.alpha_composite(stats_sub, (65, 237))
    weapon_bg_temp_draw.text((130, 257), f'{weapon_detail.stats[1]["name"]}', 'white', waves_font_30, 'lm')
    weapon_bg_temp_draw.text((500, 257), f'{weapon_detail.stats[1]["value"]}', 'white', waves_font_30, 'rm')

    right_image_temp.alpha_composite(weapon_bg_temp, dest=(0, 600))
    img.paste(right_image_temp, (570, 220), right_image_temp)
    # 命座部分
    mz_temp = Image.new('RGBA', (1200, 300))

    for i, _mz in enumerate(role_detail.chainList):
        mz_bg = Image.open(TEXT_PATH / 'mz_bg.png')
        mz_bg_temp = Image.new('RGBA', mz_bg.size)
        mz_bg_temp_draw = ImageDraw.Draw(mz_bg_temp)
        chain = await get_chain_img(role_detail.role.roleId, _mz.order, _mz.iconUrl)
        chain = chain.resize((100, 100))
        mz_bg.paste(chain, (95, 75), chain)
        mz_bg_temp.alpha_composite(mz_bg, dest=(0, 0))

        name = re.sub(r'[",，]+', '', _mz.name)
        mz_bg_temp_draw.text((147, 230), f'{name}', 'white', waves_font_20, 'mm')

        if not _mz.unlocked:
            mz_bg_temp = ImageEnhance.Brightness(mz_bg_temp).enhance(0.5)
        mz_temp.alpha_composite(mz_bg_temp, dest=(i * 190, 0))

    img.paste(mz_temp, (0, 1100), mz_temp)

    # 声骸
    phantom_temp = Image.new('RGBA', (1200, 1200))
    banner3 = Image.open(TEXT_PATH / 'banner3.png')
    phantom_temp.alpha_composite(banner3, dest=(0, 0))

    if role_detail.phantomData and role_detail.phantomData.equipPhantomList:
        totalCost = role_detail.phantomData.cost
        equipPhantomList = role_detail.phantomData.equipPhantomList
        for i, _phantom in enumerate(equipPhantomList):
            sh_temp = Image.new('RGBA', (350, 550))
            sh_temp_draw = ImageDraw.Draw(sh_temp)
            sh_title = Image.open(TEXT_PATH / 'sh_title1.png')
            sh_bg = Image.open(TEXT_PATH / 'sh_bg.png')
            sh_temp.alpha_composite(sh_title, dest=(0, 0))
            sh_temp.alpha_composite(sh_bg, dest=(0, 0))
            if _phantom and _phantom.phantomProp:
                phantom_icon = await get_phantom_img(_phantom.phantomProp.phantomId, _phantom.phantomProp.iconUrl)
                phantom_icon = phantom_icon.resize((100, 100))
                sh_temp.alpha_composite(phantom_icon, dest=(20, 20))
                phantomName = _phantom.phantomProp.name.replace("·", " ").replace("（", " ").replace("）", "")
                sh_temp_draw.text((150, 40), f'{phantomName}', SPECIAL_GOLD, waves_font_30, 'lm')
                sh_temp_draw.text((150, 70), f'Lv.{_phantom.level}', 'white', waves_font_24, 'lm')
                for index in range(0, _phantom.cost):
                    promote_icon = Image.open(TEXT_PATH / 'promote_icon.png')
                    promote_icon = promote_icon.resize((30, 30))
                    sh_temp.alpha_composite(promote_icon, dest=(145 + 30 * index, 90))

                props = []
                if _phantom.mainProps:
                    props.extend(_phantom.mainProps)
                if _phantom.subProps:
                    props.extend(_phantom.subProps)

                for index, _prop in enumerate(props):
                    oset = 55
                    prop_img = await get_attribute_prop(_prop.attributeName)
                    prop_img = prop_img.resize((40, 40))
                    sh_temp.alpha_composite(prop_img, (15, 167 + index * oset))
                    sh_temp_draw = ImageDraw.Draw(sh_temp)
                    sh_temp_draw.text((60, 187 + index * oset), f'{_prop.attributeName[:6]}', 'white', waves_font_24,
                                      'lm')
                    sh_temp_draw.text((343, 187 + index * oset), f'{_prop.attributeValue}', 'white', waves_font_24,
                                      'rm')

            phantom_temp.alpha_composite(sh_temp, dest=(40 + (i % 3) * 380, 120 + (i // 3) * 600))

    img.paste(phantom_temp, (0, 1350), phantom_temp)
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


def draw_text_with_shadow(
    image: ImageDraw,
    text: str,
    _x: int, _y: int,
    font: ImageFont,
    fill_color: str = "white",
    shadow_color: str = "black",
    offset: tuple[int, int] = (2, 2),
    anchor='rm'
):
    """描边"""
    for i in range(-offset[0], offset[0] + 1):
        for j in range(-offset[1], offset[1] + 1):
            image.text((_x + i, _y + j), text, font=font, fill=shadow_color, anchor=anchor)

    image.text((_x, _y), text, font=font, fill=fill_color, anchor=anchor)


def get_weapon_icon_bg(star: int = 3) -> Image.Image:
    if star < 3:
        star = 3
    bg_path = TEXT_PATH / f'weapon_icon_bg_{star}.png'
    bg_img = Image.open(bg_path)
    return bg_img
