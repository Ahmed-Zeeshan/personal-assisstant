from voice_assistant.tools.schema import ToolResult, ToolSpec


def test_tool_result_ok():
    r = ToolResult(ok=True, summary="created folder /tmp/foo")
    assert r.ok
    assert r.error is None


def test_tool_result_error():
    r = ToolResult(ok=False, summary="failed", error="permission denied")
    assert not r.ok
    assert r.error == "permission denied"


def test_tool_spec_to_openai_schema():
    def my_tool(path: str, content: str = "") -> ToolResult:
        """Create a file."""
        return ToolResult(ok=True, summary="ok")

    spec = ToolSpec(
        name="create_file",
        description="Create a file with optional content.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path"],
        },
        func=my_tool,
    )
    schema = spec.to_openai_format()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "create_file"
    assert schema["function"]["parameters"]["required"] == ["path"]
