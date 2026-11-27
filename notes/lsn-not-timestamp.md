# Why the payments MERGE trusts the LSN, not the timestamp

*From [payments-data-platform](https://github.com/HarshitGadge/payments-data-platform).*

The pipeline streams every change to the payments table from Postgres, through Debezium and Kafka, into an Iceberg lakehouse. Kafka can deliver an old change again after a newer one has already landed, for example after a consumer restart. If the lakehouse applies that old change, a refunded payment can flip back to paid.

The Silver table's MERGE only applies an event when `cdc_lsn > target.cdc_lsn`. The LSN is Postgres's own position in its write-ahead log, so it orders changes exactly the way the database made them. A stale event that arrives late simply doesn't match, and it's ignored.

I didn't use the change timestamp, because two changes can land in the same millisecond. A timestamp guard would have to break that tie somehow, and any tie-break can pick the wrong row.

Gold follows the same idea. It's recomputed rather than appended, because a refund today changes last week's revenue.

The repo has 102 tests, including one named after each way CDC corrupts payment data.
