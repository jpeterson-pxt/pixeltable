from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import sqlalchemy as sql

import pixeltable.type_system as ts

from .data_row import DataRow
from .expr import _GLOBAL_SCOPE, Expr, ExprScope
from .row_builder import RowBuilder
from .sql_element_cache import SqlElementCache

if TYPE_CHECKING:
    from .object_ref import ObjectRef


class JsonMapper(Expr):
    """
    JsonMapper transforms the list output of a JsonPath by applying a target expr to every element of the list.
    The target expr would typically contain relative JsonPaths, which are bound to an ObjectRef, which in turn
    is populated by JsonMapper.eval(). The JsonMapper effectively creates a new scope for its target expr.
    """

    target_expr_scope: ExprScope
    parent_mapper: Optional[JsonMapper]
    target_expr_eval_ctx: Optional[RowBuilder.EvalCtx]

    def __init__(self, src_expr: Expr, target_expr: Expr):
        # TODO: type spec should be list[target_expr.col_type]
        super().__init__(ts.JsonType())

        # we're creating a new scope, but we don't know yet whether this is nested within another JsonMapper;
        # this gets resolved in bind_rel_paths(); for now we assume we're in the global scope
        self.target_expr_scope = ExprScope(_GLOBAL_SCOPE)

        from .object_ref import ObjectRef

        self.components = [src_expr, target_expr]
        self.parent_mapper = None
        self.target_expr_eval_ctx = None

        # Intentionally create the id now, before adding the scope anchor; this ensures that JsonMappers will
        # be recognized as equal so long as they have the same src_expr and target_expr.
        # TODO: Might this cause problems after certain substitutions?
        self.id = self._create_id()

        scope_anchor = ObjectRef(self.target_expr_scope, self)
        self.components.append(scope_anchor)

    def _bind_rel_paths(self, mapper: Optional[JsonMapper] = None) -> None:
        self._src_expr._bind_rel_paths(mapper)
        self._target_expr._bind_rel_paths(self)
        self.parent_mapper = mapper
        parent_scope = _GLOBAL_SCOPE if mapper is None else mapper.target_expr_scope
        self.target_expr_scope.parent = parent_scope

    def scope(self) -> ExprScope:
        # need to ignore target_expr
        return self._src_expr.scope()

    def dependencies(self) -> list[Expr]:
        result = [self._src_expr]
        result.extend(self._target_dependencies(self._target_expr))
        return result

    def _target_dependencies(self, e: Expr) -> list[Expr]:
        """
        Return all subexprs of e of which the scope isn't contained in target_expr_scope.
        Those need to be evaluated before us.
        """
        expr_scope = e.scope()
        if not expr_scope.is_contained_in(self.target_expr_scope):
            return [e]
        result: list[Expr] = []
        for c in e.components:
            result.extend(self._target_dependencies(c))
        return result

    def equals(self, other: Expr) -> bool:
        """
        We override equals() because we need to avoid comparing our scope anchor.
        """
        if type(self) is not type(other):
            return False
        return self._src_expr.equals(other._src_expr) and self._target_expr.equals(other._target_expr)

    def __repr__(self) -> str:
        return f'map({self._src_expr}, lambda R: {self._target_expr})'

    @property
    def _src_expr(self) -> Expr:
        return self.components[0]

    @property
    def _target_expr(self) -> Expr:
        return self.components[1]

    @property
    def scope_anchor(self) -> 'ObjectRef':
        from .object_ref import ObjectRef

        result = self.components[2]
        assert isinstance(result, ObjectRef)
        return result

    def _equals(self, _: JsonMapper) -> bool:
        return True

    def sql_expr(self, _: SqlElementCache) -> Optional[sql.ColumnElement]:
        return None

    def eval(self, data_row: DataRow, row_builder: RowBuilder) -> None:
        # this will be called, but the value has already been materialized elsewhere
        src = data_row[self._src_expr.slot_idx]
        if not isinstance(src, list):
            # invalid/non-list src path
            data_row[self.slot_idx] = None
            return

        result = [None] * len(src)
        if self.target_expr_eval_ctx is None:
            self.target_expr_eval_ctx = row_builder.create_eval_ctx([self._target_expr])
        for i, val in enumerate(src):
            data_row[self.scope_anchor.slot_idx] = val
            # stored target_expr
            row_builder.eval(data_row, self.target_expr_eval_ctx, force_eval=self._target_expr.scope())
            result[i] = data_row[self._target_expr.slot_idx]
        data_row[self.slot_idx] = result

    def _as_dict(self) -> dict:
        """
        We need to avoid serializing component[2], which is an ObjectRef.
        """
        return {'components': [c.as_dict() for c in self.components[0:2]]}

    @classmethod
    def _from_dict(cls, d: dict, components: list[Expr]) -> JsonMapper:
        assert len(components) == 2
        return cls(components[0], components[1])
