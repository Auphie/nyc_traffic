from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    from build.database import connect_duckdb
except ImportError:  # pragma: no cover - supports direct script execution
    from database import connect_duckdb


LOCAL_DATA_DIR = "data"


class SourceDiscoveryError(RuntimeError):
    """Raised when source discovery cannot complete."""


@dataclass(frozen=True)
class SourceDefinition:
    table_name: str
    source_name: str
    source_category: str
    object_prefix: str
    file_extension: str
    load_mode: str
    timestamp_column: str | None


@dataclass(frozen=True)
class SourceObject:
    table_name: str
    source_name: str
    source_category: str
    object_key: str
    source_month: date | None
    load_mode: str
    timestamp_column: str | None
    source_last_modified_at: datetime | None
    source_etag: str | None
    size_bytes: int | None


@dataclass(frozen=True)
class SourceMetadataRecord:
    table_name: str
    source_name: str
    object_key: str
    source_month: date | None
    source_etag: str | None
    source_last_modified_at: datetime | None
    load_status: str | None


@dataclass(frozen=True)
class SourcePlanEntry:
    table_name: str
    source_name: str
    object_key: str
    source_month: date | None
    load_mode: str
    timestamp_column: str | None
    disposition: str
    reason: str
    source_last_modified_at: datetime | None
    source_etag: str | None


SOURCE_DEFINITIONS = (
    SourceDefinition(
        table_name="fhv_trips",
        source_name="fhv_tripdata",
        source_category="trip_records",
        object_prefix="fhv_tripdata_",
        file_extension=".parquet",
        load_mode="incremental",
        timestamp_column="pickup_datetime",
    ),
    SourceDefinition(
        table_name="fhvhv_trips",
        source_name="fhvhv_tripdata",
        source_category="trip_records",
        object_prefix="fhvhv_tripdata_",
        file_extension=".parquet",
        load_mode="incremental",
        timestamp_column="pickup_datetime",
    ),
    SourceDefinition(
        table_name="green_trips",
        source_name="green_tripdata",
        source_category="trip_records",
        object_prefix="green_tripdata_",
        file_extension=".parquet",
        load_mode="incremental",
        timestamp_column="lpep_pickup_datetime",
    ),
    SourceDefinition(
        table_name="yellow_trips",
        source_name="yellow_tripdata",
        source_category="trip_records",
        object_prefix="yellow_tripdata_",
        file_extension=".parquet",
        load_mode="incremental",
        timestamp_column="tpep_pickup_datetime",
    ),
    SourceDefinition(
        table_name="taxi_zone_shape",
        source_name="taxi_zone_shape",
        source_category="reference_data",
        object_prefix="taxi_zone",
        file_extension=".parquet",
        load_mode="replace_on_change",
        timestamp_column=None,
    ),
)

SOURCE_DEFINITIONS_BY_TABLE = {
    definition.table_name: definition for definition in SOURCE_DEFINITIONS
}


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None

    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _parse_month(value: str) -> date:
    return datetime.strptime(value, "%Y-%m").date()


def _normalize_etag(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip('"')


def _match_monthly_object(
    definition: SourceDefinition,
    object_key: str,
) -> SourceObject | None:
    filename = Path(object_key).name
    expected_prefix = definition.object_prefix
    expected_suffix = definition.file_extension

    if not filename.startswith(expected_prefix) or not filename.endswith(expected_suffix):
        return None

    source_month_text = filename.removeprefix(expected_prefix).removesuffix(expected_suffix)
    try:
        source_month = _parse_month(source_month_text)
    except ValueError:
        return None

    return SourceObject(
        table_name=definition.table_name,
        source_name=definition.source_name,
        source_category=definition.source_category,
        object_key=object_key,
        source_month=source_month,
        load_mode=definition.load_mode,
        timestamp_column=definition.timestamp_column,
        source_last_modified_at=None,
        source_etag=None,
        size_bytes=None,
    )


def _match_taxi_zone_object(
    definition: SourceDefinition,
    object_key: str,
) -> SourceObject | None:
    filename = Path(object_key).name.lower()
    accepted_names = {
        "taxi_zone_shape.parquet",
        "taxi_zones.parquet",
        "taxi_zone_shapefile.parquet",
    }
    if filename not in accepted_names:
        return None

    return SourceObject(
        table_name=definition.table_name,
        source_name=definition.source_name,
        source_category=definition.source_category,
        object_key=object_key,
        source_month=None,
        load_mode=definition.load_mode,
        timestamp_column=definition.timestamp_column,
        source_last_modified_at=None,
        source_etag=None,
        size_bytes=None,
    )


def parse_source_object(
    definition: SourceDefinition,
    object_key: str,
    *,
    source_last_modified_at: datetime | None = None,
    source_etag: str | None = None,
    size_bytes: int | None = None,
) -> SourceObject | None:
    if definition.load_mode == "incremental":
        parsed_object = _match_monthly_object(definition, object_key)
    else:
        parsed_object = _match_taxi_zone_object(definition, object_key)

    if parsed_object is None:
        return None

    return SourceObject(
        table_name=parsed_object.table_name,
        source_name=parsed_object.source_name,
        source_category=parsed_object.source_category,
        object_key=parsed_object.object_key,
        source_month=parsed_object.source_month,
        load_mode=parsed_object.load_mode,
        timestamp_column=parsed_object.timestamp_column,
        source_last_modified_at=source_last_modified_at,
        source_etag=_normalize_etag(source_etag),
        size_bytes=size_bytes,
    )


def parse_source_objects(listed_objects: list[dict[str, Any]]) -> list[SourceObject]:
    parsed_objects: list[SourceObject] = []
    for listed_object in listed_objects:
        object_key = listed_object["Key"]
        for definition in SOURCE_DEFINITIONS:
            parsed_object = parse_source_object(
                definition,
                object_key,
                source_last_modified_at=_parse_datetime(listed_object.get("LastModified")),
                source_etag=listed_object.get("ETag"),
                size_bytes=listed_object.get("Size"),
            )
            if parsed_object is not None:
                parsed_objects.append(parsed_object)
                break

    return sorted(
        parsed_objects,
        key=lambda item: (item.table_name, item.source_month or date.min, item.object_key),
    )


def list_source_objects_from_local_data_dir(
    data_dir: str | Path = LOCAL_DATA_DIR,
) -> list[dict[str, Any]]:
    source_dir = Path(data_dir)
    if not source_dir.exists():
        raise SourceDiscoveryError(
            f"Local data directory '{source_dir}' does not exist. "
            "Create it with build/download_from_tlc.py or pass --listing-file."
        )

    if not source_dir.is_dir():
        raise SourceDiscoveryError(f"'{source_dir}' is not a directory.")

    listed_objects: list[dict[str, Any]] = []
    for path in sorted(source_dir.iterdir()):
        if not path.is_file():
            continue

        stat_result = path.stat()
        listed_objects.append(
            {
                "Key": str(path),
                "LastModified": datetime.fromtimestamp(
                    stat_result.st_mtime,
                    tz=datetime.now().astimezone().tzinfo,
                ).isoformat(),
                "ETag": None,
                "Size": stat_result.st_size,
            }
        )

    return listed_objects


def load_source_metadata_records(
    path_override: str | Path | None = None,
) -> dict[tuple[str, str], SourceMetadataRecord]:
    query = """
        select
            table_name,
            source_name,
            object_key,
            source_month,
            source_etag,
            source_last_modified_at,
            load_status
        from ops.source_metadata
        where object_key is not null
    """

    with connect_duckdb(path_override) as connection:
        existing_tables = {
            row[0]
            for row in connection.execute(
                """
                select table_name
                from information_schema.tables
                where table_schema = 'ops'
                """
            ).fetchall()
        }
        if "source_metadata" not in existing_tables:
            return {}

        rows = connection.execute(query).fetchall()

    metadata_records: dict[tuple[str, str], SourceMetadataRecord] = {}
    for row in rows:
        metadata_record = SourceMetadataRecord(
            table_name=row[0],
            source_name=row[1],
            object_key=row[2],
            source_month=row[3],
            source_etag=_normalize_etag(row[4]),
            source_last_modified_at=row[5],
            load_status=row[6],
        )
        metadata_records[(metadata_record.table_name, metadata_record.object_key)] = (
            metadata_record
        )

    return metadata_records


def plan_source_object(
    source_object: SourceObject,
    metadata_record: SourceMetadataRecord | None,
) -> SourcePlanEntry:
    if metadata_record is None:
        return SourcePlanEntry(
            table_name=source_object.table_name,
            source_name=source_object.source_name,
            object_key=source_object.object_key,
            source_month=source_object.source_month,
            load_mode=source_object.load_mode,
            timestamp_column=source_object.timestamp_column,
            disposition="new",
            reason="No matching source_metadata record exists for this object key.",
            source_last_modified_at=source_object.source_last_modified_at,
            source_etag=source_object.source_etag,
        )

    if metadata_record.load_status not in {None, "completed"}:
        return SourcePlanEntry(
            table_name=source_object.table_name,
            source_name=source_object.source_name,
            object_key=source_object.object_key,
            source_month=source_object.source_month,
            load_mode=source_object.load_mode,
            timestamp_column=source_object.timestamp_column,
            disposition="reload",
            reason=f"Previous load status was '{metadata_record.load_status}'.",
            source_last_modified_at=source_object.source_last_modified_at,
            source_etag=source_object.source_etag,
        )

    if (
        source_object.source_etag
        and metadata_record.source_etag
        and source_object.source_etag != metadata_record.source_etag
    ):
        return SourcePlanEntry(
            table_name=source_object.table_name,
            source_name=source_object.source_name,
            object_key=source_object.object_key,
            source_month=source_object.source_month,
            load_mode=source_object.load_mode,
            timestamp_column=source_object.timestamp_column,
            disposition="reload",
            reason="Source ETag changed since the last recorded load.",
            source_last_modified_at=source_object.source_last_modified_at,
            source_etag=source_object.source_etag,
        )

    if (
        source_object.source_last_modified_at
        and metadata_record.source_last_modified_at
        and source_object.source_last_modified_at != metadata_record.source_last_modified_at
    ):
        return SourcePlanEntry(
            table_name=source_object.table_name,
            source_name=source_object.source_name,
            object_key=source_object.object_key,
            source_month=source_object.source_month,
            load_mode=source_object.load_mode,
            timestamp_column=source_object.timestamp_column,
            disposition="reload",
            reason="Source last-modified timestamp changed since the last recorded load.",
            source_last_modified_at=source_object.source_last_modified_at,
            source_etag=source_object.source_etag,
        )

    return SourcePlanEntry(
        table_name=source_object.table_name,
        source_name=source_object.source_name,
        object_key=source_object.object_key,
        source_month=source_object.source_month,
        load_mode=source_object.load_mode,
        timestamp_column=source_object.timestamp_column,
        disposition="unchanged",
        reason="Source metadata matches the previously recorded object state.",
        source_last_modified_at=source_object.source_last_modified_at,
        source_etag=source_object.source_etag,
    )


def plan_source_discovery(
    source_objects: list[SourceObject],
    metadata_records: dict[tuple[str, str], SourceMetadataRecord],
    *,
    table_names: set[str] | None = None,
) -> list[SourcePlanEntry]:
    plan_entries: list[SourcePlanEntry] = []
    for source_object in source_objects:
        if table_names and source_object.table_name not in table_names:
            continue

        metadata_record = metadata_records.get(
            (source_object.table_name, source_object.object_key)
        )
        plan_entries.append(plan_source_object(source_object, metadata_record))

    return plan_entries


def summarize_plan(plan_entries: list[SourcePlanEntry]) -> dict[str, int]:
    summary = {"new": 0, "unchanged": 0, "reload": 0}
    for entry in plan_entries:
        summary[entry.disposition] += 1
    return summary


def _render_text_plan(plan_entries: list[SourcePlanEntry]) -> str:
    summary = summarize_plan(plan_entries)
    lines = [
        "Source discovery plan",
        "",
        f"- new: {summary['new']}",
        f"- unchanged: {summary['unchanged']}",
        f"- reload: {summary['reload']}",
        "",
    ]

    for entry in plan_entries:
        source_month = entry.source_month.isoformat() if entry.source_month else "n/a"
        lines.append(
            f"[{entry.disposition}] {entry.table_name} | {source_month} | {entry.object_key}"
        )
        lines.append(f"  load_mode={entry.load_mode}")
        lines.append(f"  timestamp_column={entry.timestamp_column or 'n/a'}")
        lines.append(f"  reason={entry.reason}")

    return "\n".join(lines)


def _render_json_plan(plan_entries: list[SourcePlanEntry]) -> str:
    payload = {
        "summary": summarize_plan(plan_entries),
        "entries": [asdict(entry) for entry in plan_entries],
    }
    return json.dumps(payload, default=str, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover TLC source files and plan incremental ingestion actions."
    )
    parser.add_argument(
        "--table",
        action="append",
        choices=sorted(SOURCE_DEFINITIONS_BY_TABLE.keys()),
        help="Limit discovery to one or more logical tables.",
    )
    parser.add_argument(
        "--duckdb-path",
        help="Optional override for the DuckDB database path.",
    )
    parser.add_argument(
        "--data-dir",
        default=LOCAL_DATA_DIR,
        help="Read source files from a local landing directory. Default: ./data",
    )
    parser.add_argument(
        "--output",
        choices=("text", "json"),
        default="text",
        help="Choose text or JSON output.",
    )
    args = parser.parse_args()

    try:
        listed_objects = list_source_objects_from_local_data_dir(args.data_dir)

        source_objects = parse_source_objects(listed_objects)
        metadata_records = load_source_metadata_records(args.duckdb_path)
        table_names = set(args.table) if args.table else None
        plan_entries = plan_source_discovery(
            source_objects,
            metadata_records,
            table_names=table_names,
        )

        if args.output == "json":
            print(_render_json_plan(plan_entries))
        else:
            print(_render_text_plan(plan_entries))
    except SourceDiscoveryError as exc:
        print(f"source discovery error: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
