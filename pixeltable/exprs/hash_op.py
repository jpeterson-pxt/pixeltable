from __future__ import annotations

from typing import Optional

import sqlalchemy as sql

from pixeltable import type_system as ts

from .expr import DataRow, Expr
from .literal import Literal
from .row_builder import RowBuilder
from .sql_element_cache import SqlElementCache


class HashOp(Expr):
    """
    An `Expr` that computes a hash of the underlying expression with a seed.
    """

    def __init__(self, source: Expr, alg: Expr, seed: Expr):
        super().__init__(ts.StringType(nullable=True))
        self.components: list[Expr] = [source, alg, seed]
        assert isinstance(self._op2, Literal)
        self.id: Optional[int] = self._create_id()

    @classmethod
    def fraction_to_md5_hex(cls, fraction: float) -> str:
        """Convert a float value between 0 and 1 to an MD5 hash string suitable for string comparison"""
        max_md5_value = (2**32) - 1
        fract_int = max_md5_value * int(1_000_000_000 * fraction) // 1_000_000_000
        # Convert to hexadecimal string with proper padding
        return format(fract_int, '08x') + 'ffffffffffffffffffffffff'

    def _equals(self, other: HashOp) -> bool:
        # `TypeCast` has no properties beyond those captured by `Expr`.
        return True

    @property
    def _op1(self) -> Expr:
        return self.components[0]

    @property
    def _op2(self) -> Expr:
        return self.components[1]

    @property
    def _op3(self) -> Expr:
        return self.components[2]

    def sql_expr(self, sql_elements: SqlElementCache) -> Optional[sql.ColumnElement]:
        """
        sql_expr() is unimplemented for now, in order to sidestep potentially thorny
        questions about consistency of doing type conversions in both Python and Postgres.
        """
        return sql.func.md5(str(self._op3.val) + '___' + self._op1.sql_expr(sql_elements))

    def eval(self, data_row: DataRow, row_builder: RowBuilder) -> None:
        import hashlib

        src = self._op3.val + '___' + data_row[self._op1.slot_idx]
        data_row[self.slot_idx] = Literal(hashlib.md5(src))

    def as_literal(self) -> Optional[Literal]:
        return None

    def _as_dict(self) -> dict:
        return {**super()._as_dict()}

    @classmethod
    def _from_dict(cls, d: dict, components: list[Expr]) -> HashOp:
        assert len(components) == 3
        return cls(components[0], components[1], components[2])

    def __repr__(self) -> str:
        return f'({self._op1}).hashed({self._op2}, {self._op3})'


class Md5Op(Expr):
    """
    An `Expr` that computes an md5 of the given expression.
    """

    def __init__(self, source: Expr):
        super().__init__(ts.StringType(nullable=True))
        self.components: list[Expr] = [source]
        self.id: Optional[int] = self._create_id()

    @classmethod
    def fraction_to_md5_hex(cls, fraction: float) -> str:
        """Convert a float value between 0 and 1 to an MD5 hash string suitable for string comparison"""
        max_md5_value = (2**32) - 1
        fract_int = max_md5_value * int(1_000_000_000 * fraction) // 1_000_000_000
        # Convert to hexadecimal string with proper padding
        return format(fract_int, '08x') + 'ffffffffffffffffffffffff'

    def _equals(self, other: Md5Op) -> bool:
        # `TypeCast` has no properties beyond those captured by `Expr`.
        return True

    @property
    def _op1(self) -> Expr:
        return self.components[0]

    def sql_expr(self, sql_elements: SqlElementCache) -> Optional[sql.ColumnElement]:
        """
        sql_expr() is unimplemented for now, in order to sidestep potentially thorny
        questions about consistency of doing type conversions in both Python and Postgres.
        """
        return sql.func.md5(self._op1.sql_expr(sql_elements))

    def eval(self, data_row: DataRow, row_builder: RowBuilder) -> None:
        import hashlib

        src = data_row[self._op1.slot_idx]
        data_row[self.slot_idx] = Literal(hashlib.md5(src))

    def as_literal(self) -> Optional[Literal]:
        return None

    def _as_dict(self) -> dict:
        return {**super()._as_dict()}

    @classmethod
    def _from_dict(cls, d: dict, components: list[Expr]) -> Md5Op:
        assert len(components) == 1
        return cls(components[0])

    def __repr__(self) -> str:
        return f'({self._op1}).md5()'
