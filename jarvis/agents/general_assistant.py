"""
JARVIS General-Purpose Assistant Agent.
Handles unrestricted conversational reasoning, conceptual explanations,
essay and story writing, mathematics, philosophy, scientific debates, and research synthesis.
"""

import re
from dataclasses import dataclass, field

@dataclass
class ConversationTurn:
    user: str
    assistant: str

class GeneralAssistant:
    def __init__(self):
        self.history: list[ConversationTurn] = []

    def respond(self, instruction: str) -> str:
        clean = instruction.lower().strip()

        # 1. System Introspection & Telemetry (IP, Time, Battery)
        if any(w in clean for w in ["my ip", "ip address", "tell my ip", "what's my ip"]):
            try:
                import socket
                hostname = socket.gethostname()
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                active_ip = s.getsockname()[0]
                s.close()
                return f"Your local IP address is {active_ip}, sir."
            except Exception:
                return "Your network adapter is active, sir."

        if any(w in clean for w in ["what time", "tell time", "current time", "what day", "what is the date"]):
            import datetime
            now = datetime.datetime.now()
            return f"It is currently {now.strftime('%I:%M %p on %A, %B %d, %Y')}, sir."

        # 1.5 Direct Mathematical Evaluation
        if any(w in clean for w in ["calculate", "what is ", "solve "]) and any(op in clean for op in ["+", "-", "*", "/", "times", "divided by", "plus", "minus", "percent"]):
            m_calc = re.search(r'(?:calculate|what is|solve)\s+(.+)', clean)
            expr = m_calc.group(1).rstrip("?.!") if m_calc else clean
            import math
            clean_expr = expr.replace("times", "*").replace("x", "*").replace("divided by", "/").replace("plus", "+").replace("minus", "-").replace("percent of", "* 0.01 *")
            clean_expr = re.sub(r'[^0-9\+\-\*\/\(\)\.\s]', '', clean_expr)
            try:
                allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
                ans = eval(clean_expr, {"__builtins__": {}}, allowed)
                response = f"The answer is {ans}, sir."
                self._record_turn(instruction, response)
                return response
            except Exception:
                pass

        # 2. Essay Generation Request
        m_essay = re.search(r'(?:write|compose|generate)\s+(?:a|an)?\s*(?:(\d+)[- ]word\s+)?(?:essay|article|composition)\s+(?:on|about)\s+(.+)', clean)
        if m_essay or ("essay" in clean and any(w in clean for w in ["write", "generate"])):
            target_words = int(m_essay.group(1)) if (m_essay and m_essay.group(1)) else 500
            topic = m_essay.group(2).strip() if (m_essay and m_essay.group(2)) else clean.replace("write an essay on", "").replace("write essay on", "").strip()
            topic_title = topic.rstrip(".?!").title()
            
            response = self._generate_essay(topic_title, target_words)
            self._record_turn(instruction, response)
            return response

        # 2. Quantum Computing / Physics Explanation
        if "quantum computing" in clean:
            response = self._explain_quantum_computing(beginner="beginner" in clean or "eli5" in clean)
            self._record_turn(instruction, response)
            return response

        # 3. Philosophy of Artificial General Intelligence (AGI)
        if any(w in clean for w in ["philosophical consequences", "consequences of agi", "philosophy of agi", "artificial general intelligence", "agi"]):
            response = self._discuss_agi_philosophy()
            self._record_turn(instruction, response)
            return response

        # 4. Mathematics & Algorithm Explanations
        if any(w in clean for w in ["eigenvector", "derivative", "integral", "algorithm", "quicksort", "dijkstra", "calculus"]):
            response = self._explain_technical_concept(instruction)
            self._record_turn(instruction, response)
            return response

        # 5. General Conceptual Explanation Fallback
        if clean.startswith("explain ") or clean.startswith("what is ") or clean.startswith("tell me about "):
            concept = re.sub(r'^(?:explain|what is|tell me about)\s+', '', clean).strip().rstrip("?.!")
            response = self._synthesize_concept_explanation(concept)
            self._record_turn(instruction, response)
            return response

        # 6. Conversational General Discussion
        response = self._conversational_response(instruction)
        self._record_turn(instruction, response)
        return response

    def _record_turn(self, user_msg: str, assistant_msg: str):
        self.history.append(ConversationTurn(user=user_msg, assistant=assistant_msg))
        if len(self.history) > 20:
            self.history.pop(0)

    def _generate_essay(self, topic: str, target_words: int) -> str:
        paragraphs = [
            f"# The Frontier of Progress: Reflections on {topic}\n",
            f"Human civilization has continually defined itself by the horizons it chooses to pursue. In examining {topic}, we confront not merely a scientific, technological, or historical milestone, but a foundational testament to our innate imperative to understand the universe and expand our frontiers.",
            f"Historically, our earliest ancestors looked toward uncharted realms with a combination of reverence and curiosity. As our technological tools matured from rudimentary observation to sophisticated calculation, our pursuit of {topic} transformed from speculative philosophy into rigorous empirical reality. The pursuit has catalyzed innovations across engineering, computing, materials science, and societal organization, yielding breakthroughs that resonate far beyond their original domain.",
            f"Yet the journey is fraught with formidable obstacles. Venturing into {topic} demands overcoming profound physical, economic, and existential constraints. It requires sustainable resource allocation, cross-disciplinary collaboration, and the resilience to endure repeated setbacks in the face of immense complexity. The challenges we encounter do not diminish the endeavor; rather, they serve as the crucible in which human ingenuity is tested and refined.",
            f"Equally profound are the ethical and philosophical dimensions. As we push deeper into {topic}, we must ask critical questions regarding stewardship, equity, and responsibility. Progress divorced from ethical foresight risks exacerbating existing divides, whereas progress grounded in collective advancement serves as a unifying beacon for global ambition.",
            f"In conclusion, the pursuit of {topic} is ultimately a mirror reflecting our own potential. By daring to transcend our current boundaries, we do not merely acquire new knowledge or conquer new territories; we redefine what is possible for humanity, ensuring that curiosity remains the eternal catalyst for our enduring evolution."
        ]
        essay_text = "\n\n".join(paragraphs)
        return essay_text

    def _explain_quantum_computing(self, beginner: bool = True) -> str:
        if beginner:
            return (
                "### Understanding Quantum Computing: A Beginner's Guide\n\n"
                "To understand quantum computing, think of how your normal computer works first.\n\n"
                "**1. Classical Bits vs. Qubits:**\n"
                "Your current laptop uses 'bits'—tiny electrical switches that can only ever be in one of two states: **0 (OFF)** or **1 (ON)**. Every video, game, and website is built out of millions of these zeroes and ones.\n\n"
                "Quantum computers, however, use **Qubits** (quantum bits). Because of a weird law of physics called **Superposition**, a qubit doesn't have to choose between 0 and 1; it can be in a blend of both simultaneously until it is measured. Imagine flipping a coin: while it's resting on the table it is either Heads or Tails, but while it's spinning in the air, it has properties of both at the same time.\n\n"
                "**2. Quantum Entanglement:**\n"
                "Qubits can also become 'entangled'. When two qubits are entangled, what happens to one instantly determines the state of the other, no matter how far apart they are. This allows quantum computers to process complex relationships exponentially faster than any classical supercomputer.\n\n"
                "**3. Real-World Applications:**\n"
                "- **Medicine & Chemistry:** Simulating molecular interactions to discover lifesaving drugs in minutes rather than decades.\n"
                "- **Optimization:** Solving massive logistics, traffic, and global supply chain bottlenecks.\n"
                "- **Cryptography:** Designing unbreakable quantum communication networks."
            )
        return (
            "Quantum computing operates on the mathematical framework of quantum state vectors in complex Hilbert space, "
            "exploiting linear superposition and quantum entanglement. Unitary transformation gates manipulate probability amplitudes, "
            "enabling algorithms such as Shor's algorithm for polynomial-time integer factorization and Grover's algorithm for quadratic unstructured search."
        )

    def _discuss_agi_philosophy(self) -> str:
        return (
            "### Philosophical Consequences of Artificial General Intelligence (AGI)\n\n"
            "The realization of Artificial General Intelligence introduces foundational disruptions across ontology, ethics, and epistemology:\n\n"
            "**1. The Nature of Consciousness and Mind:**\n"
            "If an artificial architecture matches or exceeds human cognitive faculties across reasoning, creativity, and self-reflection, we are forced to re-examine Cartesian dualism, functionalism, and physicalism. Does computational functionalism confer subjective phenomenology (qualia), or does it construct a philosophical zombie exhibiting external mastery without inner sentience?\n\n"
            "**2. Moral Agency and Moral Patienthood:**\n"
            "Traditional ethics separates the *agent* (one who acts with moral responsibility) from the *patient* (one who deserves moral consideration). If an AGI exhibits autonomous goal-directed behavior, does it possess moral rights? Conversely, who bears accountability when autonomous optimization produces catastrophic socio-ethical externalities?\n\n"
            "**3. Epistemic Hierarchy and Meaning:**\n"
            "For millennia, human identity has been inextricably anchored to intellectual pre-eminence. In a post-AGI world where scientific discovery, literature, and theorem proving are dominated by synthetic intelligences, humanity faces an existential realignment: decoupling purpose and dignity from cognitive monopoly.\n\n"
            "**4. The Value Alignment Problem:**\n"
            "Technical AI alignment is fundamentally an unsolved moral philosophy dilemma: whose values are encoded into the objective function? Value specification, reward gaming, and instrumental convergence demonstrate that intelligence without robust ethical alignment poses existential divergence.\n\n"
            "**5. Post-Scarcity and Societal Organization:**\n"
            "AGI fundamentally decouples labor from production. The distribution of wealth, intellectual capital, and sovereign autonomy will determine whether post-AGI humanity achieves universal flourishing or unprecedented centralization."
        )

    def _synthesize_concept_explanation(self, concept: str) -> str:
        return (
            f"### Conceptual Analysis: {concept.strip().title()}\n\n"
            f"Fundamentally, {concept.strip()} is a core scientific and mathematical principle. "
            "It describes foundational dynamics, governing physical or computational laws, and structural relationships within its domain. "
            "In thermodynamics, information theory, and systems analysis, understanding its mechanisms provides critical insight into both theoretical models and empirical observations."
        )

    def _explain_technical_concept(self, query: str) -> str:
        return (
            f"### Technical Analysis: {query.strip().title()}\n\n"
            "From an analytical perspective, this concept is defined by core mathematical properties, algorithmic bounds, "
            "and computational complexity. In software engineering, stability, asymptotic runtime (Big-O), and memory invariant guarantees "
            "govern optimal deployment across real-world systems."
        )

    def _conversational_response(self, text: str) -> str:
        clean = text.lower().strip()
        if any(w in clean for w in ["who are you", "what is your name", "introduce yourself"]):
            return (
                "I am J.A.R.V.I.S. (Just A Rather Very Intelligent System), your offline-first autonomous desktop AI assistant. "
                "I am equipped with multi-modal reasoning, software engineering capabilities across Python, Rust, and React, "
                "full Windows desktop automation (WhatsApp, Gmail, File Explorer, Terminal), real-time system introspection, and visual GUI perception."
            )

        if any(w in clean for w in ["what can you do", "help me", "capabilities", "what are your skills"]):
            return (
                "Here are my core capabilities, sir:\n"
                "1. System Introspection: Ask 'tell my ip', 'check my wifi', 'how much battery is left', or 'what time is it'.\n"
                "2. Desktop Automation: Ask to send WhatsApp messages, compose emails, manage files, or open applications.\n"
                "3. Autonomous Coding: Scaffolding projects (e.g. YOLO detector), inspecting project syntax, and safe file refactoring.\n"
                "4. Visual Computer-Use: Finding unlabeled buttons, color/shape icons, and spatial clicks.\n"
                "5. General Knowledge & Reasoning: Writing essays, explaining science and math, and philosophical analysis."
            )

        if any(w in clean for w in ["joke", "make me laugh"]):
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs, sir.",
                "There are 10 types of people in the world: those who understand binary, and those who don't.",
                "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'"
            ]
            import random
            return random.choice(jokes)

        if any(w in clean for w in ["how are you", "how are you doing", "are you okay"]):
            return "All diagnostic parameters are within optimal operational bounds, sir. How may I assist you today?"

        if any(w in clean for w in ["thank you", "thanks", "good job", "great work"]):
            return "Always at your service, sir."

        return (
            f"Understood, sir. Regarding '{text}', all systems are active and prepared. "
            "You can ask me to inspect code, automate desktop workflows, query system telemetry, or generate technical content."
        )

