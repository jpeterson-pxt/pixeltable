from __future__ import annotations

from typing import Optional

import sqlalchemy as sql

from pixeltable import exprs, type_system as ts
from pixeltable.exprs.expr import DataRow, Expr
from pixeltable.exprs.literal import Literal
from pixeltable.exprs.row_builder import RowBuilder
from pixeltable.exprs.sql_element_cache import SqlElementCache


class SampleX(Expr):
    """
    An `Expr` that computes a sample of the associated table.
    """

    def __init__(
        self,
        n_expr: Optional[Expr],
        fract_expr: Optional[Expr],
        seed_expr: Optional[Expr],
        stratify_list: Optional[list[Expr]],
    ):
        super().__init__(ts.StringType(nullable=True))
        if n_expr is None:
            n_expr = exprs.Literal(None)
        if fract_expr is None:
            fract_expr = exprs.Literal(None)
        if seed_expr is None:
            seed_expr = exprs.Literal(None)
        self.components = [n_expr, fract_expr, seed_expr, *stratify_list]
        self.id: Optional[int] = self._create_id()

    def _equals(self, other: SampleX) -> bool:
        return True

    @property
    def _n_expr(self) -> Expr:
        return self.components[0]

    @property
    def _fraction_expr(self) -> Expr:
        return self.components[1]

    @property
    def _seed_expr(self) -> Expr:
        return self.components[2]

    @property
    def _stratify_list(self) -> list[Expr]:
        return self.components[3:]

    def sql_expr(self, sql_elements: SqlElementCache) -> Optional[sql.ColumnElement]:
        raise NotImplementedError

    def eval(self, data_row: DataRow, row_builder: RowBuilder) -> None:
        raise NotImplementedError

    def as_literal(self) -> Optional[Literal]:
        return None

    def _as_dict(self) -> dict:
        return {**super()._as_dict()}

    @classmethod
    def _from_dict(cls, d: dict, components: list[Expr]) -> SampleX:
        return cls(components[0], components[1], components[2], components[3:])

    def __repr__(self) -> str:
        s = ','.join(e.display_str(inline=True) for e in self._stratify_list)
        return f'sample({self._n_expr}, {self._fraction_expr}, {self._seed_expr}, [{s}])'
