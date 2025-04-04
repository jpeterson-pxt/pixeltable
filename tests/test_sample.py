from pathlib import Path
from typing import Any

import pytest

import pixeltable as pxt
from pixeltable import catalog, exceptions as excs, exprs

# from .utils import (
#    ReloadTester,
# )


class TestSampling:
    def test_sample_errors(self, test_tbl: catalog.Table) -> None:
        t = test_tbl

        # ------- Test that sample is not preceded by anything unexpected
        with pytest.raises(excs.Error, match='cannot be used with'):
            _ = t.select().sample(n=10).sample(n=10)
        with pytest.raises(excs.Error, match='cannot be used with'):
            _ = t.select().group_by(t.c1).sample(n=10)
        with pytest.raises(excs.Error, match='cannot be used with'):
            _ = t.select().order_by(t.c1).sample(n=10)
        with pytest.raises(excs.Error, match='cannot be used with'):
            _ = t.select().limit(5).sample(n=10)
        with pytest.raises(excs.Error, match='cannot be used with'):
            _ = t.select().join(t, on=t.c1).sample(n=10)

        # ------- Test that sample is not followed by anything unexpected
        with pytest.raises(excs.Error, match='cannot be used with'):
            _ = t.select().sample(n=10).show()
        with pytest.raises(excs.Error, match='cannot be used with'):
            _ = t.select().sample(n=10).head()
        with pytest.raises(excs.Error, match='cannot be used with'):
            _ = t.select().sample(n=10).tail()
        with pytest.raises(excs.Error, match='cannot be used after'):
            _ = t.select().sample(n=10).where(t.c1 > 10)
        with pytest.raises(excs.Error, match='cannot be used with'):
            _ = t.select().sample(n=10).group_by(t.c1)
        with pytest.raises(excs.Error, match='cannot be used with'):
            _ = t.select().sample(n=10).order_by(t.c1)
        with pytest.raises(excs.Error, match='cannot be used with'):
            _ = t.select().sample(n=10).group_by(t.c1)
        with pytest.raises(excs.Error, match='cannot be used with'):
            _ = t.select().sample(n=10).limit(5)
        with pytest.raises(excs.Error, match='cannot be used with'):
            _ = t.select().sample(n=10).join(t, on=t.c1)

        # ------- Test sample parameter correctness
        with pytest.raises(excs.Error, match='At least one of '):
            _ = t.select().sample()
        # with pytest.raises(excs.Error, match='Exactly one'):
        #     _ = t.select().sample(fraction=0.10, n=10)
        with pytest.raises(excs.Error, match='must be of type int'):
            _ = t.select().sample(n=0.01)  # type: ignore[arg-type]
        with pytest.raises(excs.Error, match='must be of type float'):
            _ = t.select().sample(fraction=24)
        with pytest.raises(excs.Error, match='fraction parameter must be between'):
            _ = t.select().sample(fraction=-0.5)
        with pytest.raises(excs.Error, match='fraction parameter must be between'):
            _ = t.select().sample(fraction=12.9)
        with pytest.raises(excs.Error, match='must be of type int'):
            _ = t.select().sample(n=10, seed=-123.456)  # type: ignore[arg-type]

        # test stratify_by list
        with pytest.raises(excs.Error, match='must be composed of expressions'):
            _ = t.select().sample(n=10, stratify_by=47)  # type: ignore[arg-type]
        with pytest.raises(excs.Error, match='Invalid expression'):
            _ = t.select().sample(n=10, stratify_by=[None])
        with pytest.raises(excs.Error, match='Invalid expression'):
            _ = t.select().sample(n=10, stratify_by=[123])
        with pytest.raises(excs.Error, match='Invalid type'):
            _ = t.select().sample(n=10, stratify_by=[t.c6])

        # String, Int, and Bool types
        _ = t.select().sample(n=10, stratify_by=[t.c1, t.c2, t.c4])

    def test_sample_smoke(self, test_tbl: catalog.Table) -> None:
        t = test_tbl
        df = t.select(t.c1.hashed(), t.c2.hashed())
        print(df.head(5))

        assert False

    def funky(self) -> None:
        fract = 0.123

        threshold_hex = exprs.HashOp.fraction_to_md5_hex(fract)
        print(threshold_hex)

        import hashlib
        import random

        for count in (10, 100, 1000, 10000, 100000, 1000000, 10000000):
            k = 1
            for i in range(count):
                b = hashlib.md5(str(random.randint(0, 1000000000)).encode()).hexdigest() < threshold_hex
                if b:
                    #                print(i, b)
                    k += 1
            print(fract, count, k, k / count)

    def test_sample_basic(self, test_tbl: catalog.Table) -> None:
        schema = {
            'id': pxt.IntType(nullable=True),
            'cat1': pxt.IntType(nullable=True),
            'cat2': pxt.IntType(nullable=True),
        }
        if 1:
            self.funky()
        rows = [{'id': i, 'cat1': i % 6, 'cat2': (i // 6) % 6} for i in range(360)]
        t = pxt.create_table('s_t', source=rows, schema_overrides=schema)

        df = t.select().sample(fraction=0.123, seed=42)
        print(df)
        print(df.collect())

        df = t.select().sample(n=50, seed=42)
        print(df)
        print(df.collect())

        df = t.select().sample(n=12, stratify_by=[t.cat1, t.cat2])
        print(df)

        assert False
