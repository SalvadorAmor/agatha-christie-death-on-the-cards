from typing import Generic, TypeVar, Optional, List

from sqlmodel import SQLModel, Session, select, and_

T = TypeVar("T")


class BaseService(Generic[T]):
    _metaclass = SQLModel

    async def create(self, session: Session, data: dict) -> Optional[T]:
        new_object = self._metaclass(**data)
        session.add(new_object)
        session.commit()
        session.refresh(new_object)
        return new_object

    def read(self, session: Session, oid: int) -> Optional[T]:
        return session.get(self._metaclass, oid)

    async def update(self, session: Session, oid: int, data: dict) -> Optional[T]:
        updated_object = session.get(self._metaclass, oid)
        if not updated_object:
            return None
        for k, v in data.items():
            setattr(updated_object, k, v)
        session.commit()
        session.refresh(updated_object)
        return updated_object

    async def delete(self, session: Session, oid: int) -> Optional[int]:
        delete_object = session.get(self._metaclass, oid)
        if not delete_object:
            return None
        session.delete(delete_object)
        session.commit()
        return oid

    def _build_filter(self, filterby: dict):

        expressions = []
        for k, v in filterby.items():
            if v is None:
                continue
            attribute, operator = k.split('__')
            if not hasattr(self._metaclass, attribute):
                raise ValueError(f'La clase {self._metaclass} no tiene un atributo {attribute}')
            column = getattr(self._metaclass, attribute)
            if operator == 'eq':
                expressions.append(getattr(column, '__eq__')(v))
            elif operator == 'is_null':
                if v:
                    expressions.append(getattr(column, 'is_')(None))
                else:
                    expressions.append(getattr(column, 'is_not')(None))
            elif operator == 'in':
                expressions.append(getattr(column, 'in_')(v)) 
            else:
                raise ValueError(f"El filtro '{operator}' no esta implementado")
        return and_(*expressions)

    def _build_order(self, sortby:str):
        attribute,order = sortby.split('__')
        if not hasattr(self._metaclass, attribute):
            raise ValueError(f'La clase {self._metaclass} no tiene un atributo {attribute}')
        column = getattr(self._metaclass, attribute)
        if order == "asc":
            return column.asc()
        elif order == "desc":
            return column.desc()
        else:
            raise ValueError(f"El orden '{order}' no esta implementado")


    def search(self, session: Session, filterby: dict, sortby: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        query = select(self._metaclass)
        if filterby:
            query = query.where(self._build_filter(filterby))
        if sortby:
            query = query.order_by(self._build_order(sortby))
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return session.exec(query).all()


    def refresh(self, session: Session, obj: T) -> T:
        return session.refresh(obj)
