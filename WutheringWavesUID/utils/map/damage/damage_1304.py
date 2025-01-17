# 今夕
from .buff import weilinai_buff, zhezhi_buff
from .damage import echo_damage, weapon_damage, phase_damage
from ...api.model import RoleDetailData
from ...ascension.char import get_char_detail, WavesCharResult
from ...damage.damage import DamageAttribute
from ...damage.utils import skill_damage_calc, skill_damage, cast_skill, \
    liberation_damage, cast_liberation


def calc_damage_1(attr: DamageAttribute, role: RoleDetailData, isGroup: bool = False) -> (str, str):
    """
    惊龙破空·炳星
    """
    damage_func = cast_skill
    attr.set_char_damage(skill_damage)

    role_name = role.role.roleName
    role_id = role.role.roleId
    role_level = role.role.level
    role_breach = role.role.breach
    char_result: WavesCharResult = get_char_detail(role_id, role_level, role_breach)

    # 惊龙破空·炳星 技能倍率
    skillLevel = role.get_skill_level("共鸣回路")
    # 技能倍率
    skill_multi = skill_damage_calc(char_result.skillTrees, "7", "9", skillLevel)
    title = "惊龙破空·炳星"
    msg = f"技能倍率{skill_multi}"
    attr.add_skill_multi(skill_multi, title, msg)

    #
    skill_multi = skill_damage_calc(char_result.skillTrees, "7", "10", skillLevel)
    dmg = f"{skill_multi}*50"
    title = "【韶光】增加倍率"
    msg = f"技能倍率{dmg}"
    attr.add_skill_multi(dmg, title, msg)

    # 设置角色等级
    attr.set_character_level(role_level)

    damage_func = [cast_skill]
    phase_damage(attr, role, damage_func, isGroup)

    attr.set_phantom_dmg_bonus()

    chain_num = role.get_chain_num()

    if chain_num >= 1:
        # 1命
        title = f"{role_name}-一命"
        msg = f"施放共鸣技能时，共鸣技能造成的伤害提升20%*4"
        attr.add_dmg_bonus(0.2 * 4, title, msg)

    if chain_num >= 3 and isGroup:
        # 3命
        title = f"{role_name}-三命"
        msg = f"施放变奏技能后，获得一层谪仙效果，攻击提升25%*2"
        attr.add_atk_percent(0.25 * 2, title, msg)

    if chain_num >= 4:
        # 4命
        title = f"{role_name}-四命"
        msg = f"施放共鸣技能时，角色全属性伤害加成提升20%"
        attr.add_dmg_bonus(0.2, title, msg)

    if chain_num >= 6:
        # 6命
        title = f"{role_name}-六命"
        msg = "共鸣技能伤害倍率提升45%，消耗韶光时倍率额外提升45%。"
        attr.add_skill_ratio(0.45)
        attr.add_effect(title, msg)

    # 声骸技能
    echo_damage(attr, isGroup)

    # 武器谐振
    weapon_damage(attr, role.weaponData, damage_func, isGroup)

    # 暴击伤害
    crit_damage = f"{attr.calculate_crit_damage():,.0f}"
    # 期望伤害
    expected_damage = f"{attr.calculate_expected_damage():,.0f}"
    return crit_damage, expected_damage


def calc_damage_2(attr: DamageAttribute, role: RoleDetailData, isGroup: bool = False) -> (str, str):
    """
    移岁诛邪
    """
    attr.set_char_damage(liberation_damage)

    role_name = role.role.roleName
    role_id = role.role.roleId
    role_level = role.role.level
    role_breach = role.role.breach
    char_result: WavesCharResult = get_char_detail(role_id, role_level, role_breach)

    # 移岁诛邪 技能倍率
    skillLevel = role.get_skill_level("共鸣解放")
    # 技能倍率
    skill_multi = skill_damage_calc(char_result.skillTrees, "3", "1", skillLevel)
    title = "移岁诛邪"
    msg = f"技能倍率{skill_multi}"
    attr.add_skill_multi(skill_multi, title, msg)

    # 设置角色等级
    attr.set_character_level(role_level)

    damage_func = [cast_liberation]
    phase_damage(attr, role, damage_func, isGroup)

    attr.set_phantom_dmg_bonus()

    chain_num = role.get_chain_num()

    if chain_num >= 3 and isGroup:
        # 3命
        title = f"{role_name}-三命"
        msg = f"施放变奏技能后，获得一层谪仙效果，攻击提升25%*2"
        attr.add_atk_percent(0.25 * 2, title, msg)

    if chain_num >= 4:
        # 4命
        title = f"{role_name}-四命"
        msg = f"施放共鸣解放时，角色全属性伤害加成提升20%"
        attr.add_dmg_bonus(0.2, title, msg)

    if chain_num >= 5:
        # 4命
        title = f"{role_name}-五命"
        msg = f"共鸣解放移岁诛邪伤害倍率提升120%。"
        attr.add_skill_ratio(1.2, title, msg)

    # 声骸技能
    echo_damage(attr, isGroup)

    # 武器谐振
    weapon_damage(attr, role.weaponData, damage_func, isGroup)

    # 暴击伤害
    crit_damage = f"{attr.calculate_crit_damage():,.0f}"
    # 期望伤害
    expected_damage = f"{attr.calculate_expected_damage():,.0f}"
    return crit_damage, expected_damage


def calc_damage_3(attr: DamageAttribute, role: RoleDetailData, isGroup: bool = True) -> (str, str):
    """
    0维/0折枝/惊龙破空·炳星
    """
    attr.set_char_damage(skill_damage)

    # 维里奈buff
    weilinai_buff(attr, 0, 1, isGroup)

    # 折枝buff
    zhezhi_buff(attr, 0, 1, isGroup)

    return calc_damage_1(attr, role, isGroup)


damage_detail = [
    {
        "title": "惊龙破空·炳星",
        "func": lambda attr, role: calc_damage_1(attr, role)
    },
    {
        "title": "移岁诛邪",
        "func": lambda attr, role: calc_damage_2(attr, role),
    },
    {
        "title": "0维/0折枝/惊龙破空·炳星",
        "func": lambda attr, role: calc_damage_3(attr, role),
    }
]

rank = damage_detail[0]
