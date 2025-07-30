from datetime import datetime, timedelta

import pytest

import pixeltable as pxt
from pixeltable import exceptions as excs


class TestDestination:
    def pr_us(self, us: pxt.UpdateStatus, op: str = '') -> None:
        """Print contents of UpdateStatus"""
        print(f'=========================== pr_us =========================== op: {op}')
        print(f'num_rows: {us.num_rows}')
        print(f'num_computed_values: {us.num_computed_values}')
        print(f'num_excs: {us.num_excs}')
        print(f'updated_cols: {us.updated_cols}')
        print(f'cols_with_excs: {us.cols_with_excs}')
        print(us.row_count_stats)
        print(us.cascade_row_count_stats)
        print('============================================================')

    def test_dest_foo(self, reset_db: None) -> None:
        t = pxt.create_table('test_foo', schema={'img': pxt.Image})
        t.insert([{'img': 'tests/data/imagenette2-160/ILSVRC2012_val_00000557.JPEG'}])
        t.add_computed_column(img_rot=t.img.rotate(90))
        t.add_computed_column(img_url=t.img_rot.fileurl)
        #        t.add_computed_column(img_filepath = t.img_rot.filepath)
        print(t.collect())
        t.insert([{'img': 'tests/data/imagenette2-160/ILSVRC2012_val_00000557.JPEG'}])
        #        t.insert([{'img': 'tests/data/imagenette2-160/ILSVRC2012_val_00000557.JPEG'}])
        print(t.collect())

        # Just a placeholder test to ensure the test suite runs
        assert True, 'This test is a placeholder and should be replaced with actual tests.'

    def test_dest_foo2(self, reset_db: None) -> None:
        t = pxt.create_table('test_foo', schema={'img': pxt.Image})
        t.insert([{'img': 'tests/data/imagenette2-160/ILSVRC2012_val_00000557.JPEG'}])
        t.add_computed_column(img_rot=t.img.rotate(90))
        t.add_computed_column(img_rot_copy=t.img_rot)
        #        t.add_computed_column(img_filepath = t.img_rot.filepath)
        print(t.select(t.img.fileurl, t.img_rot.fileurl, t.img_rot_copy.fileurl).collect())
        t.insert([{'img': 'tests/data/imagenette2-160/ILSVRC2012_val_00000557.JPEG'}])
        #        t.insert([{'img': 'tests/data/imagenette2-160/ILSVRC2012_val_00000557.JPEG'}])
        print(t.collect())

        # Just a placeholder test to ensure the test suite runs
        assert False, 'This test is a placeholder and should be replaced with actual tests.'
