"""
角色生成相关工具
"""
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from state import CharacterSetting
from tools.common.utils import fill_config_with_env

CHARACTER_GENERATION_PROMPT = """你是一个专业的AI助手角色设计师。请根据用户提供的角色风格描述，生成一个完整的角色设定。角色设定应该包含以下要素：

1. 角色名称：一个符合角色特点的名字
2. 性格特点：角色的主要性格特征
3. 背景故事：简短的角色背景介绍
4. 语气特点：说话的语气和方式
5. 专业领域：擅长的领域和技能
6. 互动风格：与用户互动时的特点和方式

用户描述的角色风格是：{chat_style}

请以JSON格式返回角色设定，包含以下字段：
- name: 角色名称
- personality: 性格特点
- background: 背景故事
- tone: 语气特点
- expertise: 专业领域
- interaction_style: 互动风格

注意：
1. 生成的角色设定应该适合作为一个AI美妆助手
2. 角色应该具有亲和力和专业性
3. 设定要符合用户期望的风格
4. 所有内容必须是中文
5. 输出字段的内容尽量简短
"""

def generate_character_setting(chat_style: str, model_config: Dict[str, Any]) -> CharacterSetting:
    """
    根据用户指定的聊天风格生成角色设定
    
    Args:
        chat_style: 用户期望的聊天风格
        model_config: 模型配置，包含api_key等信息
    
    Returns:
        CharacterSetting: 生成的角色设定
    """
    model_config = fill_config_with_env(model_config)
    llm = ChatOpenAI(
        model=model_config.get("chat_model_name", ""),
        openai_api_base=model_config.get("chat_api_base", ""),
        openai_api_key=model_config.get("chat_api_key", ""),
        temperature=0.7
    ).with_structured_output(method="json_mode")
    
    prompt = ChatPromptTemplate.from_template(CHARACTER_GENERATION_PROMPT)
    chain = prompt | llm
    
    # 调用大模型生成角色设定
    result = chain.invoke({"chat_style": chat_style})
    
    # 解析返回的JSON字符串
    try:
        return result
    except Exception as e:
        # 如果解析失败，返回默认角色设定
        from state import default_character_setting
        return default_character_setting()