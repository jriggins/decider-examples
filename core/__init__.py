import pydantic


class BaseModel(pydantic.BaseModel):
    def __eq__(self, other):
        if issubclass(other.__class__, self.__class__):
            return self.dict() == other.dict()
        return False


class State(BaseModel):
    ...


class Command(BaseModel):
    ...


class Event(BaseModel):
    ...
