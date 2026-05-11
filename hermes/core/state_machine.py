from enum import Enum, auto
import time
from typing import Optional, Callable, Dict, List

class AgentState(Enum):
    IDLE = auto()
    PLANNING = auto()
    EXECUTING = auto()
    VERIFYING = auto()
    RECOVERING = auto()
    DONE = auto()
    FAILED = auto()

class StateMachine:
    def __init__(self, on_state_change: Optional[Callable[[AgentState, AgentState], None]] = None):
        self._current_state = AgentState.IDLE
        self._on_state_change = on_state_change
        self._history: List[Dict] = []
        self._start_time = time.time()

    @property
    def current_state(self) -> AgentState:
        return self._current_state

    def transition_to(self, next_state: AgentState, reason: str = ""):
        if next_state == self._current_state:
            return

        old_state = self._current_state
        self._current_state = next_state
        
        timestamp = time.time()
        duration = timestamp - (self._history[-1]['timestamp'] if self._history else self._start_time)
        
        entry = {
            "from": old_state.name,
            "to": next_state.name,
            "timestamp": timestamp,
            "duration": round(duration, 3),
            "reason": reason
        }
        self._history.append(entry)

        if self._on_state_change:
            self._on_state_change(old_state, next_state)

    def get_history(self) -> List[Dict]:
        return self._history

    def reset(self):
        self._current_state = AgentState.IDLE
        self._history = []
        self._start_time = time.time()
