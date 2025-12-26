import pytest
from typing import Optional
from sqlmodel import SQLModel, create_engine, Field, Session

from app.services.base import BaseService


class DummyModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    value: Optional[int] = None


class DummyService(BaseService[DummyModel]):
    _metaclass = DummyModel


@pytest.fixture
def engine():
    engine = create_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def service():
    return DummyService()


@pytest.mark.asyncio
async def test_base_service_create_and_read(session, service):
    dummy = DummyModel(name="alpha", value=10)
    created = await service.create(session, dummy.model_dump())

    assert created.id is not None
    fetched = service.read(session, created.id)
    assert fetched is not None
    assert fetched.name == "alpha"


def test_read_returns_none(session, service):
    assert service.read(session, 999) is None


def test_build_filter_eq_is_null(session, service):
    items = [
        DummyModel(name="pepito", value=None),
        DummyModel(name="don jose", value=5),
    ]
    session.add_all(items)
    session.commit()

    results = service.search(session, {"name__eq": "pepito", "value__is_null": True})
    assert len(results) == 1
    assert results[0].name == "pepito"


def test_build_filter_in_operator(session, service):
    session.add_all(
        [
            DummyModel(name="pepito", value=1),
            DummyModel(name="doña laura", value=2),
            DummyModel(name="don jose", value=3),
        ]
    )
    session.commit()

    results = service.search(session, {"name__in": ["pepito", "don jose"]})
    assert {row.name for row in results} == {"pepito", "don jose"}


def test_build_filter_is_null_false(session, service):
    session.add_all(
        [
            DummyModel(name="pepito", value=1),
            DummyModel(name="don jose", value=None),
        ]
    )
    session.commit()

    results = service.search(session, {"value__is_null": False})
    assert [row.name for row in results] == ["pepito"]


def test_build_filter_invalid_attribute_raises(service):
    with pytest.raises(ValueError):
        service._build_filter({"unknown__eq": "value"})


def test_build_filter_invalid_operator_raises(service):
    with pytest.raises(ValueError):
        service._build_filter({"name__contains": "a"})


def test_build_order_valid(service):
    column = service._build_order("name__desc")
    assert column is not None


def test_build_order_invalid_attribute_raises(service):
    with pytest.raises(ValueError):
        service._build_order("unknown__asc")


def test_build_order_invalid_direction_raises(service):
    with pytest.raises(ValueError):
        service._build_order("name__sideways")


def test_search_with_sort_limit_offset(session, service):
    session.add_all(
        [
            DummyModel(name="a", value=3),
            DummyModel(name="b", value=2),
            DummyModel(name="c", value=1),
        ]
    )
    session.commit()

    results = service.search(session, {}, sortby="value__asc", limit=2, offset=1)
    assert [row.name for row in results] == ["b", "a"]


@pytest.mark.asyncio
async def test_base_service_update_missing_returns_none(session, service):
    result = await service.update(session, 999, {"name": "missing"})
    assert result is None


@pytest.mark.asyncio
async def test_base_service_delete_missing_returns_none(session, service):
    result = await service.delete(session, 999)
    assert result is None


def test_build_filter_skips_none_values(session, service):
    session.add(DummyModel(name="alpha", value=None))
    session.commit()

    results = service.search(session, {"name__eq": "alpha", "value__eq": None})
    assert len(results) == 1


def test_refresh_returns_none(session, service):
    obj = DummyModel(name="alpha", value=1)
    session.add(obj)
    session.commit()
    session.refresh(obj)

    result = service.refresh(session, obj)
    assert result is None
