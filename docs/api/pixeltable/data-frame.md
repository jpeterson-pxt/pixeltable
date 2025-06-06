# DataFrame

`DataFrame` represents a query against a specific table. Unlike computation container frameworks like pandas or Dask,
Pixeltable dataframes do not hold data or allow you to update data
(use [insert][pixeltable.Table.insert]/[update][pixeltable.Table.update]/[delete][pixeltable.Table.delete]
for that purpose).
Another difference to pandas is that query execution needs to be initiated explicitly in order to return results.

## Overview

| Query Construction                          |                                                       |
|---------------------------------------------|-------------------------------------------------------|
| [`select`][pixeltable.DataFrame.select]     | Select output expressions                             |
| [`join`][pixeltable.DataFrame.join]         | Join to another table                                 |
| [`where`][pixeltable.DataFrame.where]       | Filter table rows                                     |
| [`group_by`][pixeltable.DataFrame.group_by] | Group table rows in order to apply aggregate functions |
| [`order_by`][pixeltable.DataFrame.order_by] | Order output rows                                     |
| [`limit`][pixeltable.DataFrame.limit]       | Limit the number of output rows                       |
| [`distinct`][pixeltable.DataFrame.distinct] | Remove duplicate rows                                 |
| [`sample`][pixeltable.DataFrame.sample]     | Select shuffled sample of rows                        |

| Query Execution                           |                                     |
|-------------------------------------------|-------------------------------------|
| [`collect`][pixeltable.DataFrame.collect] | Return all output rows              |
| [`show`][pixeltable.DataFrame.show]       | Return a number of output rows      |
| [`head`][pixeltable.DataFrame.head]       | Return the oldest rows              |
| [`tail`][pixeltable.DataFrame.tail]       | Return the most recently added rows |

| Data Export                                                     |                                                                                                                                      |
|-----------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| [`to_pytorch_dataset`][pixeltable.DataFrame.to_pytorch_dataset] | Return the query result as a pytorch [`IterableDataset`](https://pytorch.org/docs/stable/data.html#torch.utils.data.IterableDataset) |
| [`to_coco_dataset`][pixeltable.DataFrame.to_coco_dataset]       | Return the query result as a COCO dataset                                                                                            |

## ::: pixeltable.DataFrame

    options:
      members:
      - collect
      - group_by
      - head
      - limit
      - order_by
      - select
      - join
      - show
      - tail
      - to_pytorch_dataset
      - to_coco_dataset
      - where
      - distinct
      - sample
