from fastapi import HTTPException
import pytest

from app.db import crud


class FakeQuery:
    def __init__(self, rows, start=0, end=0):
        self.rows = rows
        self.start = start
        self.end = end

    def range(self, start, end):
        return FakeQuery(self.rows, start, end)

    def execute(self):
        return type("Result", (), {"data": self.rows[self.start:self.end + 1]})()


def test_get_all_reads_multiple_postgrest_pages(monkeypatch):
    rows = [{"id": index} for index in range(1_253)]
    monkeypatch.setattr(crud, "_exec_query_get_data", lambda query: query.execute().data)

    result = crud._exec_query_get_all(FakeQuery(rows), page_size=500)

    assert len(result) == 1_253
    assert result[0]["id"] == 0
    assert result[-1]["id"] == 1_252


def test_get_all_stops_if_result_exceeds_safety_cap(monkeypatch):
    rows = [{"id": index} for index in range(5)]
    monkeypatch.setattr(crud, "_exec_query_get_data", lambda query: query.execute().data)

    with pytest.raises(HTTPException) as error:
        crud._exec_query_get_all(FakeQuery(rows), page_size=2, max_pages=2)

    assert error.value.status_code == 503
