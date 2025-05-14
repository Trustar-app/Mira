
# 一、LangSmith 能为你带来什么？

LangSmith 是 LangChain/LangGraph 官方出品的**LLM 应用全流程观测、评测与提示工程平台**，核心能力包括：

- **Observability（可观测性）**：自动追踪每一次 LLM/Agent/工具调用，支持链路追踪、性能监控、错误分析、流式日志、可视化仪表盘等。
- **Evaluation（评测）**：支持自动化/人工评测、A/B 测试、数据集管理、评测指标自定义、评测结果可视化等。
- **Prompt Engineering（提示工程）**：支持提示版本管理、自动化提示优化、协作、在线 Playground、Prompt 变体对比等。

---

# 二、如何在你的项目中引入 LangSmith？

## 1. 安装依赖

在你的 Python 环境中安装 langsmith：

```bash
pip install -U langsmith
```

## 2. 获取 API Key 并配置环境变量

- 注册并登录 [LangSmith 平台](https://smith.langchain.com/)
- 在设置页面创建 API Key
- 在你的开发环境中设置环境变量：

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY="你的 LangSmith API Key"
# 如果用 OpenAI，还需设置 OPENAI_API_KEY
```

## 3. 代码中集成 LangSmith 追踪

### 3.1 追踪 LLM/Agent 调用

- **OpenAI/LLM 调用**：用 `wrap_openai` 包裹你的 OpenAI 客户端
- **LangChain/LangGraph**：只需设置环境变量，所有链路自动追踪

**示例：**

```python
from openai import OpenAI
from langsmith.wrappers import wrap_openai

openai_client = wrap_openai(OpenAI())
# 之后所有 openai_client 的调用都会被追踪
```

### 3.2 追踪自定义函数/流程

- 用 `@traceable` 装饰器包裹你的关键函数（如 Agent、Graph 节点、工具等）

```python
from langsmith import traceable

@traceable
def my_chain(...):
    ...
```

- 你可以在**任意节点、工具、Agent**上加 traceable，自动记录输入输出、耗时、异常等。

### 3.3 追踪 LangGraph 流程

- 只要设置了 `LANGSMITH_TRACING=true`，**LangGraph 的所有节点、子图、工具调用都会被自动追踪**，无需额外代码改动。

### 3.4 追踪多模态/自定义数据

- 你可以在 traceable 函数中**自定义 metadata、tag、日志**，方便后续检索和分析。

---

## 4. 在项目结构中的集成建议

结合你的项目结构，推荐如下集成点：

- **app.py**：全局初始化环境变量，确保所有流程都能被追踪。
- **agents/**、**tools/**、**graphs/**：对关键 Agent、工具函数、Graph 节点用 `@traceable` 装饰器。
- **tests/**：集成测试时同样会被追踪，便于回溯和分析。

**示例：**

```python
# mira/agents/supervisor.py
from langsmith import traceable

@traceable
def multimodal_chat_agent(state: MiraState) -> str:
    ...
```

```python
# mira/tools/media_utils.py
from langsmith import traceable

@traceable
def extract_best_face_frame(video_path):
    ...
```

---

## 5. 观测与分析

- 登录 [LangSmith 控制台](https://smith.langchain.com/)，即可看到所有链路追踪、输入输出、异常、token 消耗、性能等。
- 支持**自定义仪表盘、过滤、A/B 对比、trace drilldown**等高级分析。

详细见官方文档：[Observability Quick Start](https://docs.smith.langchain.com/observability)、[如何追踪 LangGraph](https://docs.smith.langchain.com/observability/how_to_guides/trace_with_langgraph/)

---

# 三、Evaluation（评测）集成建议

- **自动化评测**：用 LangSmith 的评测数据集和评测器，对你的 Agent/Graph/Prompt 进行自动化评测。
- **人工评测**：支持人工打分、反馈收集，持续优化体验。
- **A/B 测试**：对比不同 Agent/Prompt/模型的效果，数据驱动迭代。

详细见：[Evaluation Quick Start](https://docs.smith.langchain.com/evaluation)、[评测 How-to](https://docs.smith.langchain.com/evaluation/how_to_guides/)

---

# 四、Prompt Engineering（提示工程）集成建议

- **Prompt 版本管理**：所有提示词变更、实验、效果都可在 LangSmith 平台统一管理。
- **自动化优化**：结合评测结果，自动推荐更优 Prompt。
- **Playground**：在线调试、对比不同 Prompt 效果。

详细见：[Prompt Engineering 概念](https://docs.smith.langchain.com/prompt_engineering/concepts)、[Prompt 优化教程](https://docs.smith.langchain.com/prompt_engineering/tutorials/optimize_classifier)

---

# 五、最佳实践总结

1. **全局追踪**：只需设置环境变量，LangGraph/Agent/工具/LLM 全链路自动追踪。
2. **关键节点/工具/Agent 用 @traceable 装饰**，便于细粒度观测和评测。
3. **评测与提示工程**：用 LangSmith 的数据集、评测器、Prompt 管理能力，持续优化你的智能体和用户体验。
4. **测试与生产一致**：测试代码同样被追踪，便于回溯和定位问题。
5. **安全与隐私**：可配置敏感数据脱敏、trace 采样率等，详见官方 how-to。

---

# 六、参考文档

- [LangSmith 官方文档首页](https://docs.smith.langchain.com/)
- [Observability 快速入门](https://docs.smith.langchain.com/observability)
- [如何追踪 LangGraph](https://docs.smith.langchain.com/observability/how_to_guides/trace_with_langgraph/)
- [Evaluation 快速入门](https://docs.smith.langchain.com/evaluation)
- [Prompt Engineering 概念](https://docs.smith.langchain.com/prompt_engineering/concepts)
- [Prompt 优化教程](https://docs.smith.langchain.com/prompt_engineering/tutorials/optimize_classifier)
