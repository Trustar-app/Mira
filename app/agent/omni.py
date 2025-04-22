from typing import List, Optional

from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.logger import logger
from app.prompt.omni import NEXT_STEP_PROMPT
from app.prompt.omni import SYSTEM_PROMPT
from app.tool import Bash, StrReplaceEditor, Terminate, ToolCollection
from app.schema import ROLE_TYPE, AgentState, Memory, Message
from app.sandbox.client import SANDBOX_CLIENT

class QwenOmniAgent(ToolCallAgent):
    """QwenOmniAgent implementation."""

    name: str = "Qwen-Omni"
    description: str = "A fully modal large model Agent"

    system_prompt: str = SYSTEM_PROMPT
    next_step_prompt: str = NEXT_STEP_PROMPT

    available_tools: ToolCollection = ToolCollection(
         Terminate()
    )
    special_tool_names: List[str] = Field(default_factory=lambda: [Terminate().name])

    max_steps: int = 8

    def update_omni_memory(
        self,
        role: ROLE_TYPE,  # type: ignore
        content: str,
        base64_image: Optional[str] = None,
        base64_video: Optional[str] = None,
        base64_audio: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Add a message to the agent's memory.

        Args:
            role: The role of the message sender (user, system, assistant, tool).
            content: The message content.
            base64_image: Optional base64 encoded image.
            **kwargs: Additional arguments (e.g., tool_call_id for tool messages).

        Raises:
            ValueError: If the role is unsupported.
        """
        message_map = {
            "user": Message.user_message,
            "system": Message.system_message,
            "assistant": Message.assistant_message,
            "tool": lambda content, **kw: Message.tool_message(content, **kw),
        }

        if role not in message_map:
            raise ValueError(f"Unsupported message role: {role}")

        # Create message with appropriate parameters based on role
        extra_kwargs = kwargs
        kwargs = {}

        if base64_image:
            kwargs["base64_image"] = base64_image
        if base64_video:
            kwargs["base64_video"] = base64_video
        if base64_audio:
            kwargs["base64_audio"] = base64_audio

        if role == "tool":
            kwargs.update(extra_kwargs)  # 原来的 kwargs

        self.memory.add_message(message_map[role](content, **kwargs))


    async def run(
              self,
              text_request: Optional[str] = None,
              image_request: Optional[str] = None,
              video_request: Optional[str] = None,
              audio_request: Optional[str] = None
    ) -> str:
        """Execute the agent's main loop asynchronously.

        Args:
            request: Optional initial user request to process.

        Returns:
            A string summarizing the execution results.

        Raises:
            RuntimeError: If the agent is not in IDLE state at start.
        """
        if self.state != AgentState.IDLE:
            raise RuntimeError(f"Cannot run agent from state: {self.state}")

        if text_request or image_request or video_request or audio_request:
            self.update_omni_memory(
                role="user",
                content=text_request,
                base64_image=image_request,
                base64_video=video_request,
                base64_audio=audio_request,
            )

        results: List[str] = []
        async with self.state_context(AgentState.RUNNING):
            while (
                    self.current_step < self.max_steps and self.state != AgentState.FINISHED
            ):
                self.current_step += 1
                logger.info(f"Executing step {self.current_step}/{self.max_steps}")
                step_result = await self.step()

                # Check for stuck state
                if self.is_stuck():
                    self.handle_stuck_state()

                results.append(f"Step {self.current_step}: {step_result}")

            if self.current_step >= self.max_steps:
                self.current_step = 0
                self.state = AgentState.IDLE
                results.append(f"Terminated: Reached max steps ({self.max_steps})")
        await SANDBOX_CLIENT.cleanup()
        return_results = "\n".join(results) if results else "No steps executed"

        # TODO 这里需要支持LLM再次总结并给出最终的答复和音频
        # TODO 1. 使用更强大的LLM（例如deepseek）总结前面的所有东西，这里可以增加情感，语气等效果
        # TODO 2. 然后使用TTS模型转换成文本+音频输出
        # TODO 或者这里的实现更正为 MLLM 再来一遍
        result_dict = {}
        result_dict["text"] = return_results

        logger.info(f"result_dict[\"text\"]:\n{return_results}")

        return result_dict


