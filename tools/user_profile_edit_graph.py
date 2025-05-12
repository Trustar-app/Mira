def parse_edit_intent(user_input: str) -> Optional[str]:
    """
    解析用户输入，提取要编辑的字段名。
    :param user_input: 用户输入
    :return: 字段名（如"age"、"gender"等），未识别返回 None
    """

def validate_edit_value(field: str, value: Any) -> bool:
    """
    校验用户输入的新值是否合法。
    :param field: 字段名
    :param value: 新值
    :return: 合法返回 True，否则 False
    """
