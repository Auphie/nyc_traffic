from __future__ import annotations

import shutil
import ssl
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import certifi

try:
    from build.source_discovery import SOURCE_DEFINITIONS_BY_TABLE
except ImportError:  # pragma: no cover - supports direct script execution
    from source_discovery import SOURCE_DEFINITIONS_BY_TABLE


TLC_TRIPDATA_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
DEFAULT_DATA_DIR = "data"


class DownloadFromTlcError(RuntimeError):
    """Raised when a TLC download request cannot be completed."""


@dataclass(frozen=True)
class DownloadTarget:
    table_name: str
    source_name: str
    source_month: date
    url: str
    destination_path: Path


def parse_month(value: str) -> date:
    return datetime.strptime(value, "%Y-%m").date()


def iter_months(start_month: date, end_month: date) -> list[date]:
    if start_month > end_month:
        raise DownloadFromTlcError("start month must be earlier than or equal to end month.")

    months: list[date] = []
    current_month = start_month
    while current_month <= end_month:
        months.append(current_month)
        year = current_month.year + (current_month.month // 12)
        month = (current_month.month % 12) + 1
        current_month = date(year, month, 1)

    return months


def incremental_trip_tables() -> list[str]:
    return [
        table_name
        for table_name, definition in SOURCE_DEFINITIONS_BY_TABLE.items()
        if definition.load_mode == "incremental"
    ]


def current_system_month() -> date:
    today = date.today()
    return date(today.year, today.month, 1)


def build_trip_download_target(
    table_name: str,
    source_month: date,
    data_dir: str | Path = DEFAULT_DATA_DIR,
) -> DownloadTarget:
    definition = SOURCE_DEFINITIONS_BY_TABLE[table_name]
    if definition.load_mode != "incremental":
        raise DownloadFromTlcError(
            f"Table '{table_name}' is not a monthly parquet trip dataset."
        )

    month_text = source_month.strftime("%Y-%m")
    filename = f"{definition.source_name}_{month_text}.parquet"
    destination_path = Path(data_dir) / filename
    url = f"{TLC_TRIPDATA_BASE_URL}/{filename}"

    return DownloadTarget(
        table_name=table_name,
        source_name=definition.source_name,
        source_month=source_month,
        url=url,
        destination_path=destination_path,
    )


def build_download_targets(
    table_names: list[str],
    source_months: list[date],
    data_dir: str | Path = DEFAULT_DATA_DIR,
) -> list[DownloadTarget]:
    return [
        build_trip_download_target(table_name, source_month, data_dir)
        for table_name in table_names
        for source_month in source_months
    ]


def download_target(
    target: DownloadTarget,
    *,
    overwrite: bool = False,
) -> Path:
    target.destination_path.parent.mkdir(parents=True, exist_ok=True)
    if target.destination_path.exists() and not overwrite:
        return target.destination_path

    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(target.url, context=ssl_context) as response:
            with target.destination_path.open("wb") as output_file:
                shutil.copyfileobj(response, output_file)
    except HTTPError as exc:
        raise DownloadFromTlcError(
            f"Download failed for {target.url} with HTTP {exc.code}."
        ) from exc
    except URLError as exc:
        raise DownloadFromTlcError(
            f"Download failed for {target.url}: {exc.reason}"
        ) from exc

    return target.destination_path


def download_targets(
    targets: list[DownloadTarget],
    *,
    overwrite: bool = False,
) -> list[Path]:
    return [download_target(target, overwrite=overwrite) for target in targets]
