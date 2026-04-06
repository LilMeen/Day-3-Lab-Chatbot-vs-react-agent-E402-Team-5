import re
import json
import time
from typing import Optional

from agent.memory import ShortTermMemory
from agent.models import ReActStep, ToolAction, AgentResponse
from agent.prompt_templates import (
    STOP_TOKEN, HALLUCINATION_STRINGS, SYSTEM_PROMPT, REACT_PROMPT
)
from tools.base import get_tool_descriptions, execute_tool
import config

# Import all tools to register them
import tools  # noqa: F401


class ReActAgent:
    def __init__(self):
        self.memory = ShortTermMemory(max_entries=3)
        self.max_iterations = 3
        self._init_llm_client()

    # ------------------------------------------------------------------
    # LLM client init
    # ------------------------------------------------------------------

    def _init_llm_client(self):
        self.provider = config.LLM_PROVIDER.lower()

        if self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            self.model = config.OPENAI_MODEL

        elif self.provider == "gemini":
            from google import genai
            self.client = genai.Client(api_key=config.GEMINI_API_KEY)
            self.model = config.GEMINI_MODEL

        else:
            raise ValueError(
                f"Unsupported LLM provider: '{self.provider}'. Use 'openai' or 'gemini'."
            )


    # ------------------------------------------------------------------
    # LLM call — plain text with stop token
    # ------------------------------------------------------------------

    def _call_llm(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        """Call the LLM with exponential backoff retry on failure."""
        for attempt in range(max_retries):
            try:
                if self.provider == "openai":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        stop=[STOP_TOKEN],
                        temperature=0,
                    )
                    return response.choices[0].message.content or ""

                elif self.provider == "gemini":
                    full_prompt = f"{system_prompt}\n\n{user_prompt}"
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=full_prompt,
                        config={
                            "stop_sequences": [STOP_TOKEN],
                            "temperature": 0,
                        },
                    )
                    return response.text or ""

            except Exception as e:
                if attempt < max_retries - 1:
                    delay = (2 ** attempt) * 2  # 2s, 4s, 8s
                    print(f"\n[LLM Error] {e} — retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(delay)
                else:
                    print(f"\n[LLM Error] All {max_retries} attempts failed: {e}")
                    return ""
        return ""

    # ------------------------------------------------------------------
    # Hallucination removal
    # ------------------------------------------------------------------

    def _remove_hallucinations(self, response: str) -> str:
        """Truncate response at the first hallucinated line-start string."""
        if not isinstance(response, str):
            response = str(response)

        for hallucination in HALLUCINATION_STRINGS:
            # Only detect at the start of a line (after \n or at position 0)
            pattern = r"(^|\n)" + re.escape(hallucination)
            match = re.search(pattern, response)
            if match:
                # Truncate from the hallucination position
                cut = match.start() if match.group(1) == "" else match.start() + 1
                response = response[:cut]

        return response.strip()

    # ------------------------------------------------------------------
    # Plain-text response parser
    # ------------------------------------------------------------------

    def _extract_field(self, text: str, field: str, next_fields: list[str]) -> str:
        """Extract the value of a labeled field up to the next field label."""
        stops = "|".join(re.escape(f) for f in next_fields)
        pattern = rf"{re.escape(field)}:\s*(.*?)(?=(?:{stops}):|$)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _parse_action(self, action_text: str) -> Optional[ToolAction]:
        """Parse 'tool_name({"param": "value"})' into a ToolAction."""
        action_text = action_text.strip()
        if not action_text or action_text.lower() in ("none", "null", "n/a", ""):
            return None

        # Match: tool_name({"key": "value"})
        match = re.match(r"(\w+)\s*\((\{.*\})\s*\)", action_text, re.DOTALL)
        if match:
            tool_name = match.group(1)
            try:
                params = json.loads(match.group(2))
                return ToolAction(tool=tool_name, parameters=params)
            except json.JSONDecodeError:
                pass

        # Fallback: just a bare tool name
        match = re.match(r"^(\w+)$", action_text.strip())
        if match:
            return ToolAction(tool=match.group(1), parameters={})

        return None

    def _parse_react_step(self, raw_response: str) -> ReActStep:
        """Parse the 5-field plain-text LLM response."""
        # Prepend field label that the prompt already started
        text = "Reflection: " + raw_response

        reflection = self._extract_field(text, "Reflection", ["Plan", "Thought", "Action", "Output"])
        plan       = self._extract_field(text, "Plan",       ["Thought", "Action", "Output"])
        thought    = self._extract_field(text, "Thought",    ["Action", "Output"])
        action_raw = self._extract_field(text, "Action",     ["Output"])
        output_raw = self._extract_field(text, "Output",     [STOP_TOKEN, "---"])

        action = self._parse_action(action_raw)
        output = None if (not output_raw or output_raw.lower() in ("none", "null")) else output_raw

        return ReActStep(
            reflection=reflection,
            plan=plan,
            thought=thought,
            action=action,
            output=output,
        )

    # ------------------------------------------------------------------
    # Within-turn history formatter (CyBench-style)
    # ------------------------------------------------------------------

    def _format_step_as_text(self, step: ReActStep) -> str:
        """Render a ReActStep back to the 5-field plain-text format."""
        lines = [
            f"Reflection: {step.reflection}",
            f"Plan: {step.plan}",
            f"Thought: {step.thought}",
        ]
        if step.action:
            params_str = json.dumps(step.action.parameters, ensure_ascii=False)
            lines.append(f"Action: {step.action.tool}({params_str})")
        else:
            lines.append("Action: None")
        lines.append(f"Output: {step.output or 'None'}")
        return "\n".join(lines)

    def _format_within_turn_history(self, response_observation_history: list[dict]) -> str:
        """Format the within-turn CyBench-style history for the next LLM call."""
        if not response_observation_history:
            return ""
        parts = []
        for i, pair in enumerate(response_observation_history, 1):
            parts.append(f"--- Step {i} ---")
            parts.append(pair["response"])       # full 5-field text
            parts.append(f"Observation:\n{pair['observation']}")
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Main ReAct loop
    # ------------------------------------------------------------------

    def run(self, session_id: str, user_message: str) -> AgentResponse:
        """Run the ReAct loop for one user message and return a structured response."""

        # Build system prompt once (static within this call)
        system_prompt = SYSTEM_PROMPT.format(
            tool_descriptions=get_tool_descriptions(),
            stop_token=STOP_TOKEN,
        )

        # Cross-turn memory (Observation from previous conversations)
        memory_text = self.memory.format_for_prompt(session_id)

        # Within-turn CyBench-style history (response-observation pairs this turn)
        response_observation_history: list[dict] = []

        steps: list[ReActStep] = []
        tools_used: list[str] = []
        final_answer = ""
        awaiting_input = False
        followup_question = ""

        for iteration in range(self.max_iterations):

            # Build current_observation string
            if iteration == 0:
                current_observation = f"User: {user_message}"
                original_message_line = ""
            else:
                last_pair = response_observation_history[-1]
                within_turn = self._format_within_turn_history(response_observation_history)
                current_observation = (
                    f"{within_turn}\n\n"
                    f"Tool Result ({steps[-1].action.tool if steps and steps[-1].action else 'unknown'}):\n"
                    f"{last_pair['observation']}"
                )
                original_message_line = f"\nOriginal User Message: {user_message}\n"

            # Build user prompt
            user_prompt = REACT_PROMPT.format(
                memory=memory_text,
                current_observation=current_observation,
                original_message_line=original_message_line,
            )

            # Call LLM
            raw_response = self._call_llm(system_prompt, user_prompt)

            # Remove hallucinations
            cleaned_response = self._remove_hallucinations(raw_response)

            if not cleaned_response:
                # Empty after hallucination removal — retry if iterations remain
                if iteration < self.max_iterations - 1:
                    print("[Fallback] Empty response after hallucination removal, retrying...")
                    continue
                step = ReActStep(
                    reflection="Response was empty after hallucination removal.",
                    plan="Provide a safe fallback answer.",
                    thought="The LLM response was entirely hallucinated content.",
                    action=None,
                    output="Xin lỗi, tôi gặp lỗi khi xử lý. Vui lòng thử lại.",
                )
                final_answer = step.output
                steps.append(step)
                break

            # Parse step
            step = self._parse_react_step(cleaned_response)

            # Parse produced neither action nor output — retry if iterations remain
            if step.action is None and step.output is None and iteration < self.max_iterations - 1:
                print("[Fallback] Parse returned no action and no output, retrying...")
                continue

            # --- Execute tool if action is set ---
            if step.action:
                tool_result = execute_tool(step.action.tool, step.action.parameters)
                step.tool_result = tool_result
                tools_used.append(step.action.tool)
                steps.append(step)

                # Detect HITL interrupt from smart_followup (API mode)
                try:
                    result_dict = json.loads(tool_result)
                    if result_dict.get("status") == "awaiting_input":
                        awaiting_input = True
                        followup_question = result_dict.get("question", "")
                        final_answer = followup_question
                        break
                except (json.JSONDecodeError, AttributeError):
                    pass

                # Add to within-turn history (CyBench-style)
                step_text = self._format_step_as_text(step)
                response_observation_history.append({
                    "response": step_text,
                    "observation": tool_result,
                })
                # Keep last 3 within-turn pairs
                if len(response_observation_history) > 3:
                    response_observation_history = response_observation_history[-3:]
                continue

            # --- Final answer ---
            if step.output:
                final_answer = step.output
                steps.append(step)
                break

            # Safety: neither action nor output
            step.output = "Xin lỗi, tôi không thể xử lý yêu cầu này. Vui lòng thử lại."
            final_answer = step.output
            steps.append(step)
            break

        # Exhausted iterations without final answer → use last tool result
        if not final_answer and steps:
            final_answer = steps[-1].tool_result or "Xin lỗi, tôi không thể hoàn thành yêu cầu."

        # Save to cross-turn memory: user message first (cause), agent response second (result)
        final_step_text = self._format_step_as_text(steps[-1]) if steps else ""
        self.memory.add_entry(session_id, user_message, final_step_text)

        return AgentResponse(
            session_id=session_id,
            steps=steps,
            final_answer=final_answer,
            tools_used=tools_used,
            awaiting_input=awaiting_input,
            followup_question=followup_question,
        )

    def reset_memory(self, session_id: str):
        self.memory.clear(session_id)
