from __future__ import annotations


def validate_page_args(page: int, per_page: int) -> None:
    if page < 0:
        raise ValueError("page must be greater than or equal to 0")
    if per_page <= 0:
        raise ValueError("per_page must be greater than 0")


def validate_optional_page_args(page: int | None, per_page: int | None) -> None:
    if page is not None and page < 0:
        raise ValueError("page must be greater than or equal to 0")
    if per_page is not None and per_page <= 0:
        raise ValueError("per_page must be greater than 0")
