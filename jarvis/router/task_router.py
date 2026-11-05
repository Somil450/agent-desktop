"""
JARVIS Autonomous Task Router.
Classifies natural language instructions into specialized agent modes:
- GENERAL_ASSISTANT: Philosophy, essays, explanations, science, math, research, conversation.
- CODE_AGENT: Programming (Python, C++, JS/React, Rust, Android), debugging, project generation.
- VISUAL_AGENT: Screen perception, GUI grounding, unlabeled icons, canvas regions, coordinate clicks.
- DESKTOP_AGENT: OS actions, WhatsApp, Gmail, browser navigation, file management, system volume/lock.
- RESEARCH_AGENT: Deep technical analysis, literature synthesis, technology comparisons.
- MULTI_AGENT: Complex tasks spanning multiple domains (e.g. research + code + desktop report).
"""

import re
from enum import Enum
from dataclasses import dataclass, field

class TaskMode(Enum):
    GENERAL_ASSISTANT = "GENERAL_ASSISTANT"
    CODE_AGENT = "CODE_AGENT"
    VISUAL_AGENT = "VISUAL_AGENT"
    DESKTOP_AGENT = "DESKTOP_AGENT"
    RESEARCH_AGENT = "RESEARCH_AGENT"
    MULTI_AGENT = "MULTI_AGENT"

@dataclass
class RouteDecision:
    mode: TaskMode
    confidence: float
    reason: str
    target_domains: list[str] = field(default_factory=list)
    multi_step: bool = False
    parameters: dict = field(default_factory=dict)

class TaskRouter:
    def __init__(self):
        # Patterns indicative of general conversation, essays, philosophy & concepts
        self._general_patterns = [
            r'\b(?:write|compose|generate)\s+(?:a|an)\s+(?:\d+[- ]word\s+)?(?:essay|story|article|poem|script|paragraph)\b',
            r'\bexplain\s+(?:quantum\s+computing|relativity|philosophy|calculus|consciousness|agi|the\s+meaning|how\s+does)\b',
            r'\b(?:philosophical|ethical|existential|metaphysical)\s+(?:consequences|implications|questions|debate)\b',
            r'\b(?:what\s+is|define|tell\s+me\s+about|describe)\s+(?:the\s+theory|the\s+concept|love|life|universe|quantum)\b',
            r'\b(?:discuss|debate|analyze\s+the\s+philosophy|give\s+your\s+opinion)\b',
            r'\b(?:explain\s+to\s+me\s+as\s+if\s+i\s+am\s+a\s+beginner|eli5)\b',
            r'\b(?:solve\s+this\s+math|calculate|derivative|integral|eigenvector)\b'
        ]

        # Patterns indicative of coding, project creation & software engineering
        self._code_patterns = [
            r'\b(?:write|create|generate|implement|build)\s+(?:a|an)?\s*(?:complete\s+)?(?:python|c\+\+|rust|java|kotlin|react|html|css|javascript|typescript|android)\s+(?:app|application|code|script|project|program|component|module|function|class|pipeline)\b',
            r'\b(?:detecting\s+objects\s+using\s+yolo|yolo\s+detector|machine\s+learning\s+pipeline|neural\s+network|jetpack\s+compose)\b',
            r'\b(?:debug|fix\s+the\s+error|analyze\s+compiler\s+error|refactor|optimize\s+this\s+code)\b',
            r'\b(?:inspect\s+my\s+current\s+project|identify\s+errors\s+and\s+fix|run\s+tests|write\s+unit\s+tests)\b',
            r'\b(?:create\s+project\s+structure|generate\s+readme|build\s+an\s+api|create\s+rest\s+endpoint)\b'
        ]

        # Patterns indicative of visual perception & unlabeled GUI controls
        self._visual_patterns = [
            r'\b(?:click\s+(?:the\s+)?|find\s+(?:the\s+)?|locate\s+(?:the\s+)?|press\s+(?:the\s+)?)\s*(?:small|large|tiny)?\s*(?:settings|gear|hamburger|close|minimize|search)?\s*icon\s+(?:in|at)\s+(?:the\s+)?(?:upper|lower|top|bottom|left|right)\b',
            r'\bclick\s+(?:the\s+)?(?:(?:red|blue|green|yellow|circular|square|round|small|large)\s*)+\s*button\b',
            r'\b(?:open|click)\s+the\s+(?:first|second|third|fourth|last|\d+(?:st|nd|rd|th)?)\s+icon\s+(?:from|in)\b',
            r'\b(?:canvas|draw|sketch|drag\s+from|on\s+the\s+screen|coordinate|pixel|screenshot\s+analysis)\b',
            r'\b(?:locate\s+visually|read\s+text\s+on\s+screen\s+using\s+ocr|visual\s+inspection)\b'
        ]

        # Patterns indicative of multi-agent tasks
        self._multi_patterns = [
            r'\b(?:research\s+.+?[,\s]+(?:and\s+)?write\s+(?:code|python|implementations)|write\s+code\s+[,\s]+(?:and\s+)?create\s+(?:a\s+)?report)\b',
            r'\b(?:inspect\s+.+?\s+(?:and\s+)?send\s+.*?(?:to|on)\s+(?:whatsapp|email))\b'
        ]

    def route(self, instruction: str, context: dict = None) -> RouteDecision:
        clean = instruction.lower().strip()

        # 1. Multi-Agent Cooperative Tasks
        for pat in self._multi_patterns:
            if re.search(pat, clean):
                return RouteDecision(
                    mode=TaskMode.MULTI_AGENT,
                    confidence=0.95,
                    reason="Composite instruction requiring research, code generation, and desktop operations.",
                    target_domains=["research", "coding", "desktop"],
                    multi_step=True
                )

        # 2. General Conversation & Knowledge
        for pat in self._general_patterns:
            if re.search(pat, clean):
                return RouteDecision(
                    mode=TaskMode.GENERAL_ASSISTANT,
                    confidence=0.95,
                    reason="Instruction requests essay, explanation, philosophy, creative writing, or conceptual knowledge."
                )

        # 3. Code Generation & Software Engineering
        for pat in self._code_patterns:
            if re.search(pat, clean):
                return RouteDecision(
                    mode=TaskMode.CODE_AGENT,
                    confidence=0.95,
                    reason="Instruction requests programming, debugging, project creation, or code inspection."
                )

        # 4. Visual Computer-Use & GUI Grounding
        for pat in self._visual_patterns:
            if re.search(pat, clean):
                return RouteDecision(
                    mode=TaskMode.VISUAL_AGENT,
                    confidence=0.92,
                    reason="Instruction requests clicking unlabeled icons, visual objects, colors, or canvas interaction."
                )

        # 5. Question/Explanation fallback for "what is", "how does", "why is" if not desktop automation
        if any(clean.startswith(w) for w in ["what is ", "what are ", "why is ", "how does ", "explain ", "tell me about ", "who was "]):
            if not any(w in clean for w in ["open", "launch", "chrome", "whatsapp", "file", "download"]):
                return RouteDecision(
                    mode=TaskMode.GENERAL_ASSISTANT,
                    confidence=0.88,
                    reason="Informational or conceptual question routed to General Assistant."
                )

        # 6. Default to Desktop Agent (app launch, close, whatsapp, browser, files, system control)
        return RouteDecision(
            mode=TaskMode.DESKTOP_AGENT,
            confidence=0.90,
            reason="Standard desktop automation, application control, communication, or system command."
        )
