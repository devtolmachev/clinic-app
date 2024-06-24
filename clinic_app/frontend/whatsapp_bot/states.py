from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Self, Tuple, Type

from whatsapp_chatbot_python import BaseStates


class StateWhatsapp:
    def __init__(self) -> None:
        self._state_name = None
        self._group: Type[WhatsappFSMGroup] = None

    @property
    def state(self) -> Optional[str]:
        return f"{self._group.__name__}:{self._state_name}"
    
    @property
    def group(self) -> Optional["Type[WhatsappFSMGroup]"]:
        return self._group
    
    @property
    def state_name(self) -> Optional[str]:
        return self._state_name

    def __set_name__(self, owner: "Type[WhatsappFSMGroup]", name: str) -> None:
        """Set name of state by name define in variable of state."""
        if self._state_name is None:
            self._state_name = name
        if not issubclass(owner, WhatsappFSMGroup):
            msg = "States Group Class must be a subclass of WhatsappFSMGroup"
            raise TypeError(msg)
        self._group = owner


class MetaFSM(type):
    def __new__(
        mcs, name: str, bases: Tuple, namespace: dict, **kwargs
    ) -> Self:
        cls = super().__new__(mcs, name, bases, namespace)

        states = []

        for name, arg in namespace.items():
            if isinstance(arg, StateWhatsapp):
                states.append(arg)

        cls.__states__ = tuple(states)
        cls.__state_names__ = tuple(state.state for state in states)

        return cls

    @property
    def __all_states_names__(cls) -> Tuple[str]:
        return tuple(state.state for state in cls.__states__ if state.state)

    def __contains__(cls, item: Any) -> bool:
        if isinstance(item, str):
            return item in cls.__all_states_names__
        if isinstance(item, StateWhatsapp):
            return item in cls.__states__
        return False

    def __str__(cls) -> str:
        return f"<StatesGroup '{cls.__name__}'>"


class WhatsappFSMGroup(metaclass=MetaFSM):
    def __str__(self) -> str:
        return f"StatesGroup {type(self).__name__}"


@dataclass
class MemoryStorageRecord:
    data: Dict[str, Any] = field(default_factory=dict)
    state: Optional[str] = None


class WhatsappFSMContext:
    def __init__(self) -> None:
        self.storage = defaultdict(MemoryStorageRecord)

    def set_state(self, state: StateWhatsapp, user_id: int):
        self.storage[user_id].state = state

    def get_state(self, user_id: int) -> Optional[StateWhatsapp]:
        return self.storage[user_id].state

    def update_data(self, user_id: int, **kwargs):
        data = self.storage[user_id].data
        if data is None:
            data = kwargs

        data.update(kwargs)

    def set_data(self, user_id: int, **kwargs):
        self.storage[user_id].data = kwargs
    
    def get_data(self, user_id: int):
        return self.storage[user_id].data

    def clear(self, user_id: int):
        self.set_state(None, user_id)
        self.set_data(user_id)

    def get_users_id(self):
        return list(self.storage.keys())


class MainFSM(WhatsappFSMGroup):
    notify_tommorow = StateWhatsapp()
    review = StateWhatsapp()
    rescheduling = StateWhatsapp()
    get_review = StateWhatsapp()


_state = WhatsappFSMContext()


def get_fsm() -> WhatsappFSMContext:
    """Get whatsapp bot FSMContext."""
    return _state


class WhStates(BaseStates):
    notify_tommorow = "notify_tommorow"
    review = "review"
    rescheduling = "rescheduling"
    get_review = "get_review"
