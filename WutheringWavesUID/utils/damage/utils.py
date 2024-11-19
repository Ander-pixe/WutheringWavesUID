from typing import Dict

SONATA_FREEZING = "凝夜白霜"
SONATA_MOLTEN = "熔山裂谷"
SONATA_VOID = "彻空冥雷"
SONATA_SIERRA = "啸谷长风"
SONATA_CELESTIAL = "浮星祛暗"
SONATA_SINKING = "沉日劫明"
SONATA_REJUVENATING = "隐世回光"
SONATA_MOONLIT = "轻云出月"
SONATA_LINGERING = "不绝余音"

CHAR_ATTR_FREEZING = "冷凝"
CHAR_ATTR_CELESTIAL = "衍射"
CHAR_ATTR_VOID = "导电"
CHAR_ATTR_MOLTEN = "热熔"
CHAR_ATTR_SIERRA = "气动"
CHAR_ATTR_SINKING = "湮灭"


def check_if_ph_5(ph_name: str, ph_num: int, check_name: str):
    return ph_name == check_name and ph_num == 5


def skill_damage(skillTree: Dict, skillTreeId: str, skillParamId: str, skillLevel: int) -> str:
    """
    获取技能伤害
    :param skillTree: 技能树
    :param skillTreeId: 技能树id
    :param skillParamId: 技能参数id
    :param skillLevel: 技能等级
    :return: 技能伤害
    """
    return skillTree[skillTreeId]["skill"]["level"][skillParamId]["param"][0][skillLevel]