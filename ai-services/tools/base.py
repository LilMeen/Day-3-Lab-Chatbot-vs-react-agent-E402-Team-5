from __future__ import annotations

import json

# Tool registry — filled by each tool module on import
TOOL_REGISTRY: dict[str, dict] = {}


def register_tool(name: str, description: str, parameters: dict, function):
    TOOL_REGISTRY[name] = {
        "function": function,
        "description": description,
        "parameters": parameters,
    }


def get_tool_descriptions() -> str:
    lines = []
    for name, info in TOOL_REGISTRY.items():
        lines.append(f"- **{name}**: {info['description']}")
        lines.append(f"  Parameters: {json.dumps(info['parameters'], ensure_ascii=False)}")
    return "\n".join(lines)


def execute_tool(name: str, parameters: dict) -> str:
    if name not in TOOL_REGISTRY:
        return f"Error: Tool '{name}' not found. Available: {', '.join(TOOL_REGISTRY.keys())}"
    try:
        result = TOOL_REGISTRY[name]["function"](**parameters)
        return json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, (dict, list)) else str(result)
    except Exception as e:
        return f"Error executing {name}: {str(e)}"
