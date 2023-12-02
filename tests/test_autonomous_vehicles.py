import abc
import enum
import functools
import typing
import pydantic
import pydantic.generics as py_generic


class BaseModel(py_generic.GenericModel, pydantic.BaseModel):
    ...


class Event(BaseModel):
    ...


C = typing.TypeVar("C")  # , bound=Command, covariant=True)
S = typing.TypeVar("S")  # , bound=Aggregate)  # , bound=State, covariant=True)
E = typing.TypeVar("E")  # , bound=Event, covariant=True)


class Command(BaseModel):
    ...


class State(BaseModel):
    ...


class Aggregate(BaseModel, py_generic.Generic[E], abc.ABC):
    @abc.abstractmethod
    def apply(self, event: E) -> "Aggregate":
        ...


class VehicleEvent(Event):
    ...


class VehicleRemoved(VehicleEvent):
    owner_id: str
    vin: str


class VehicleAdded(VehicleEvent):
    owner_id: str
    vin: str


class MakeVehicleAvailableForRides(Command):
    owner_id: str
    vin: str


class VehicleMadeAvailable(Event):
    owner_id: str
    vin: str


class Vehicle(BaseModel):
    class Status(enum.StrEnum):
        NOT_AVAILABLE = enum.auto()
        AVAILABLE = enum.auto()

    owner_id: str
    vin: str
    status: Status = Status.NOT_AVAILABLE


VehicleEvents = VehicleAdded | VehicleRemoved | VehicleMadeAvailable


class MyVehicles(Aggregate):
    owner_id: str
    vehicles: list[Vehicle] = []

    @classmethod
    def initial_state(cls):
        return cls.construct()

    def apply(self, event: VehicleEvents) -> "MyVehicles":
        match event:
            case VehicleAdded():
                self.owner_id = event.owner_id
                self.vehicles.append(Vehicle(vin=event.vin, owner_id=event.owner_id))
            case VehicleMadeAvailable():
                vehicle: Vehicle = next(
                    filter(lambda v: v.vin == event.vin, self.vehicles)
                )
                vehicle.status = Vehicle.Status.AVAILABLE
            case VehicleRemoved():
                return self
            case _:
                typing.assert_never(event)

        return self


class AddVehicle(Command):
    owner_id: str
    vin: str


class RideRequested(Event):
    rider_id: str


class RideScheduled(Event):
    rider_id: str
    vin: str


class RequestRide(Command):
    rider_id: str


class ScheduleRide(Command):
    rider_id: str
    vin: str


VehicleCommands = AddVehicle
VehicleAggregates = MyVehicles

RideCommands = RequestRide | ScheduleRide
RideAggregates = typing.Any


class VehiclesHandler:
    def handle(
        self, command: VehicleCommands, aggregate: VehicleAggregates
    ) -> list[Event]:
        match command:
            case AddVehicle():
                return [VehicleAdded(owner_id=command.owner_id, vin=command.vin)]
            case MakeVehicleAvailableForRides():
                return [
                    VehicleMadeAvailable(owner_id=command.owner_id, vin=command.vin)
                ]
            case _:
                typing.assert_never(command)


class RidesHandler:
    def handle(self, command: RideCommands, aggregate: RideAggregates) -> list[Event]:
        match command:
            case RequestRide():
                return [RideRequested(rider_id=command.rider_id)]
            case ScheduleRide():
                return [RideScheduled(rider_id=command.rider_id, vin=vin)]
            case _:
                typing.assert_never(command)


def aggregate(state: S, events: typing.Iterable[E]) -> S:
    return functools.reduce(lambda s, e: s.apply(e), events, state)


def handle(command, state, handler) -> list[Event]:
    return handler.handle(command, state)


owner_id = "ME"
rider_id = "YOU"
vin = "VIN"
initial_vehicle_state = MyVehicles.initial_state()


def test_add_vehicle_given_inital_state():
    command = AddVehicle(owner_id=owner_id, vin=vin)
    command_handler = VehiclesHandler()

    assert handle(command, initial_vehicle_state, command_handler) == [
        VehicleAdded(vin=vin, owner_id=owner_id)
    ]


def test_making_a_vehicle_available_for_rides():
    command = MakeVehicleAvailableForRides(owner_id=owner_id, vin=vin)

    command_handler = VehiclesHandler()

    assert handle(command, initial_vehicle_state, command_handler) == [
        VehicleMadeAvailable(vin=vin, owner_id=owner_id)
    ]


def test_requesting_a_ride():
    command = RequestRide(rider_id=rider_id)

    command_handler = RidesHandler()

    assert handle(command, initial_vehicle_state, command_handler) == [
        RideRequested(rider_id=rider_id)
    ]


def test_scheduling_a_ride():
    command = ScheduleRide(rider_id=rider_id, vin=vin)

    command_handler = RidesHandler()

    assert handle(command, initial_vehicle_state, command_handler) == [
        RideScheduled(rider_id=rider_id, vin=vin)
    ]

    # events = []
    # expected_view = initial_vehicle_state

    # events = [VehicleAdded(vin=vin, owner_id=owner_id)]
    # expected_view = MyVehicles(
    #     owner_id=owner_id, vehicles=[Vehicle(vin=vin, owner_id=owner_id)]
    # )

    # assert aggregate(MyVehicles.initial_state(), events) == expected_view
