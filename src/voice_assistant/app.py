from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from typing import Iterator
from voice_assistant.brain import Brain, Message, PlainText, ToolCall, ContentChunk, ToolCallReady
from voice_assistant.tools.schema import ToolSpec, ToolResult

log = logging.getLogger(__name__)


@dataclass
class Orchestrator:
    brain: Brain
    tools: list[ToolSpec]
    history: list[Message] = field(default_factory=list)

    def _tool_by_name(self, name: str) -> ToolSpec | None:
        for t in self.tools:
            if t.name == name:
                return t
        return None

    def handle(self, user_text: str) -> str:
        log.info("user: %s", user_text)
        response = self.brain.respond(
            user_text=user_text, history=self.history, tools=self.tools
        )
        self.history.append(Message(role="user", content=user_text))

        if isinstance(response, PlainText):
            self.history.append(
                Message(role="assistant", content=response.content)
            )
            log.info("assistant: %s", response.content)
            return response.content

        # tool call
        tc: ToolCall = response
        log.info("tool_call: %s args=%s", tc.name, tc.arguments)
        spec = self._tool_by_name(tc.name)
        if spec is None:
            result = ToolResult(
                ok=False, summary=f"unknown tool {tc.name}",
                error="tool not registered",
            )
        else:
            try:
                result = spec.func(**tc.arguments)
            except TypeError as e:
                result = ToolResult(
                    ok=False, summary="bad arguments", error=str(e),
                )

        log.info("tool_result: %s", result.summary)

        # Record assistant tool-call + tool result, then ask brain to summarise.
        self.history.append(
            Message(
                role="assistant",
                content="",
                tool_calls=[{
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    },
                }],
            )
        )
        self.history.append(
            Message(
                role="tool",
                content=json.dumps(result.model_dump(), default=str),
                tool_call_id=tc.id,
                name=tc.name,
            )
        )

        followup = self.brain.respond(
            user_text=(
                "Tool result above. Reply to the user in one short sentence."
            ),
            history=self.history,
            tools=[],
        )
        if not isinstance(followup, PlainText):
            log.warning(
                "followup brain call returned a tool call (%s) despite tools=[]; "
                "falling back to tool summary",
                getattr(followup, "name", "?"),
            )
        text = followup.content if isinstance(followup, PlainText) else result.summary
        self.history.append(Message(role="assistant", content=text))
        log.info("assistant: %s", text)
        return text

    def handle_stream(self, text: str) -> Iterator[dict]:
        """Yield orchestrator events as the brain streams.

        Events: dict with "type" in:
          - "assistant_delta": {"text": str}
          - "tool_invoked":    {"name": str, "args": dict}
          - "tool_result":     {"text": str}
          - "done":            {}
        """
        tool_schemas = [t.to_openai_format() for t in self.tools]
        messages: list[dict] = [{"role": "user", "content": text}]
        for _ in range(5):  # bounded tool-call iterations
            text_buf = ""
            tool_call: ToolCallReady | None = None
            for item in self.brain.complete_stream(messages, tool_schemas):
                if isinstance(item, ContentChunk):
                    text_buf += item.text
                    yield {"type": "assistant_delta", "text": item.text}
                elif isinstance(item, ToolCallReady):
                    tool_call = item

            if tool_call is None:
                yield {"type": "done"}
                return

            yield {"type": "tool_invoked", "name": tool_call.name, "args": tool_call.args}
            spec = self._tool_by_name(tool_call.name)
            try:
                if spec is None:
                    raise ValueError(f"unknown tool {tool_call.name}")
                result = spec.func(**tool_call.args)
                result_text = json.dumps(result.model_dump(), default=str)
            except Exception as exc:
                result_text = f"Tool error: {exc}"
            yield {"type": "tool_result", "text": result_text}
            # Continue loop: feed result back to brain
            messages = messages + [
                {"role": "assistant", "content": text_buf or None,
                 "tool_calls": [{"id": tool_call.id, "type": "function",
                                 "function": {"name": tool_call.name,
                                              "arguments": json.dumps(tool_call.args)}}]},
                {"role": "tool", "tool_call_id": tool_call.id, "content": result_text},
            ]
        yield {"type": "done"}
