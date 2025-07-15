from flask import Flask
from flask_socketio import SocketIO
import asyncio
from typing import AsyncGenerator, Optional, TypeVar, Union, cast
from autogen_core import CancellationToken
from autogen_core.models import RequestUsage
from autogen_agentchat.base import Response, TaskResult
from autogen_agentchat.messages import AgentEvent, ChatMessage, MultiModalMessage, UserInputRequestedEvent
import time

T = TypeVar("T", bound=TaskResult | Response)

def aprint(output: str, end: str = "\n"):
    return asyncio.to_thread(print, output, end=end)


class SocketIOConsole:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        
    async def emit_message(self, sender: str, content: str) -> None:
        """Emit message to socket client with sender info"""
        self.socketio.emit('message', {
            'sender': sender,
            'content': content
        })


    async def __call__(
        self,
        stream: AsyncGenerator[AgentEvent | ChatMessage | T, None],
        *,
        output_stats: bool = False,
    ) -> T:
        """
        Consumes the message stream and emits messages via Socket.IO.
        """
        start_time = time.time()
        total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
        last_processed: Optional[T] = None

        async for message in stream:
            if isinstance(message, TaskResult):
                duration = time.time() - start_time
                if output_stats:
                    output = (
                        f"{'-' * 10} Summary {'-' * 10}\n"
                        f"Number of messages: {len(message.messages)}\n"
                        f"Finish reason: {message.stop_reason}\n"
                        f"Total prompt tokens: {total_usage.prompt_tokens}\n"
                        f"Total completion tokens: {total_usage.completion_tokens}\n"
                        f"Duration: {duration:.2f} seconds\n"
                    )
                    await aprint(output, end="")
                    await self.emit_message("System", summary)
                    # await self.emit_message(output)
                last_processed = message

            elif isinstance(message, Response):
                duration = time.time() - start_time
                
                # Emit response message
                output = f"{'-' * 10} {message.chat_message.source} {'-' * 10}\n{self._message_to_str(message.chat_message)}\n"
                if message.chat_message.models_usage and output_stats:
                    output += f"[Prompt tokens: {message.chat_message.models_usage.prompt_tokens}, Completion tokens: {message.chat_message.models_usage.completion_tokens}]\n"
                    total_usage.completion_tokens += message.chat_message.models_usage.completion_tokens
                    total_usage.prompt_tokens += message.chat_message.models_usage.prompt_tokens
                # await self.emit_message(output)
                await aprint(output, end="")
                await self.emit_message(message.chat_message.source, output)
                # Emit summary if stats are enabled
                if output_stats:
                    num_inner_messages = len(message.inner_messages) if message.inner_messages is not None else 0
                    summary = (
                        f"{'-' * 10} Summary {'-' * 10}\n"
                        f"Number of inner messages: {num_inner_messages}\n"
                        f"Total prompt tokens: {total_usage.prompt_tokens}\n"
                        f"Total completion tokens: {total_usage.completion_tokens}\n"
                        f"Duration: {duration:.2f} seconds\n"
                    )
                    await aprint(output, end="")
                    await self.emit_message(message.chat_message.source, summary)
                    # await self.emit_message(summary)
                last_processed = message

            elif isinstance(message, UserInputRequestedEvent):
                # Handle user input requests if needed
                pass
            else:
                # Handle regular messages
                message = cast(AgentEvent | ChatMessage, message)
                output = f"{'-' * 10} {message.source} {'->' * 10}\n{self._message_to_str(message)}\n"
                if message.models_usage and output_stats:
                    output += f"[Prompt tokens: {message.models_usage.prompt_tokens}, Completion tokens: {message.models_usage.completion_tokens}]\n"
                    total_usage.completion_tokens += message.models_usage.completion_tokens
                    total_usage.prompt_tokens += message.models_usage.prompt_tokens
                await aprint(output, end="")
                # await self.emit_message("msg":{"sender":message.source, "content ":output})
                await self.emit_message(message.source, output)
        if last_processed is None:
            raise ValueError("No TaskResult or Response was processed.")

        return last_processed

    def _message_to_str(self, message: AgentEvent | ChatMessage) -> str:
        """Convert message to string format"""
        if isinstance(message, MultiModalMessage):
            result = []
            for c in message.content:
                if isinstance(c, str):
                    result.append(c)
                else:
                    result.append("<image>")
            return "\n".join(result)
        else:
            return f"{message.content}"