"""TrackedStockService 单元测试 — mock DB 连接"""

import pytest
from unittest.mock import patch, MagicMock

from stockshark.services.tracked_stock_service import TrackedStockService


@pytest.fixture
def svc():
    return TrackedStockService()


def _mock_conn(fetchall_result=None, fetchone_result=None, lastrowid=1):
    """构建一个 mock 连接对象"""
    cursor = MagicMock()
    cursor.fetchall.return_value = fetchall_result or []
    cursor.fetchone.return_value = fetchone_result
    cursor.lastrowid = lastrowid
    conn = MagicMock()
    conn.cursor.return_value = cursor
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    return conn, cursor


# ── list_all ────────────────────────────────────────────────


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_list_all(mock_get_conn, svc):
    rows = [
        {"id": 1, "stock_code": "000001", "stock_name": "平安银行", "group_name": "银行",
         "sort_order": 0, "notes": None},
        {"id": 2, "stock_code": "603009", "stock_name": "北特科技", "group_name": "科技",
         "sort_order": 1, "notes": "关注中"},
    ]
    conn, cursor = _mock_conn(fetchall_result=rows)
    mock_get_conn.return_value = conn

    result = svc.list_all()
    assert len(result) == 2
    cursor.execute.assert_called_once()
    assert "ORDER BY sort_order" in cursor.execute.call_args[0][0]


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_list_all_by_group(mock_get_conn, svc):
    rows = [{"id": 1, "stock_code": "000001", "group_name": "科技"}]
    conn, cursor = _mock_conn(fetchall_result=rows)
    mock_get_conn.return_value = conn

    result = svc.list_all(group_name="科技")
    assert len(result) == 1
    assert cursor.execute.call_args[0][1] == ("科技",)


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_list_all_empty(mock_get_conn, svc):
    conn, _ = _mock_conn(fetchall_result=[])
    mock_get_conn.return_value = conn

    result = svc.list_all()
    assert result == []


# ── get_by_id ───────────────────────────────────────────────


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_get_by_id_found(mock_get_conn, svc):
    row = {"id": 5, "stock_code": "000001", "stock_name": "平安银行"}
    conn, _ = _mock_conn(fetchone_result=row)
    mock_get_conn.return_value = conn

    result = svc.get_by_id(5)
    assert result["id"] == 5


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_get_by_id_not_found(mock_get_conn, svc):
    conn, _ = _mock_conn(fetchone_result=None)
    mock_get_conn.return_value = conn

    result = svc.get_by_id(999)
    assert result is None


# ── add ─────────────────────────────────────────────────────


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_add_success(mock_get_conn, svc):
    new_row = {"id": 1, "stock_code": "603009", "stock_name": "北特科技",
               "group_name": "科技", "sort_order": 1, "notes": "关注中"}
    conn, cursor = _mock_conn(fetchone_result=new_row, lastrowid=1)
    mock_get_conn.return_value = conn

    result = svc.add("603009", "北特科技", "科技", 1, "关注中")
    assert result["stock_code"] == "603009"


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_add_duplicate_raises(mock_get_conn, svc):
    conn, _ = _mock_conn(fetchone_result={"id": 1})
    mock_get_conn.return_value = conn

    with pytest.raises(ValueError, match="该股票已在关注列表中"):
        svc.add("000001")


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_add_auto_fill_name(mock_get_conn, svc):
    """stock_name 省略时从 stock_basic_info 自动填充"""
    call_count = 0
    fetchone_results = [
        None,   # _is_duplicate check: not found
        {"name": "平安银行"},  # _auto_fill_stock_name: found
        {"id": 1, "stock_code": "000001", "stock_name": "平安银行"},  # final SELECT
    ]

    def make_conn():
        nonlocal call_count
        result = fetchone_results[call_count] if call_count < len(fetchone_results) else None
        call_count += 1
        conn, cursor = _mock_conn(fetchone_result=result, lastrowid=1)
        return conn

    mock_get_conn.side_effect = lambda: make_conn()

    result = svc.add("000001")
    assert result["stock_name"] == "平安银行"


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_add_auto_fill_name_fallback(mock_get_conn, svc):
    """stock_basic_info 中找不到时用 stock_code 作为名称"""
    call_count = 0
    fetchone_results = [
        None,   # _is_duplicate: not found
        None,   # _auto_fill_stock_name: not found in stock_basic_info
        {"id": 1, "stock_code": "999999", "stock_name": "999999"},  # final SELECT
    ]

    def make_conn():
        nonlocal call_count
        result = fetchone_results[call_count] if call_count < len(fetchone_results) else None
        call_count += 1
        conn, cursor = _mock_conn(fetchone_result=result, lastrowid=1)
        return conn

    mock_get_conn.side_effect = lambda: make_conn()

    result = svc.add("999999")
    assert result["stock_name"] == "999999"


# ── update ──────────────────────────────────────────────────


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_update_success(mock_get_conn, svc):
    existing = {"id": 5, "stock_code": "000001", "stock_name": "平安银行",
                "group_name": "银行", "sort_order": 0, "notes": None}
    updated = {**existing, "group_name": "金融", "notes": "重点关注"}

    call_count = 0

    def make_conn():
        nonlocal call_count
        if call_count == 0:
            result = existing
        elif call_count == 1:
            result = updated
        else:
            result = updated
        call_count += 1
        conn, cursor = _mock_conn(fetchone_result=result)
        return conn

    mock_get_conn.side_effect = lambda: make_conn()

    result = svc.update(5, group_name="金融", notes="重点关注")
    assert result["group_name"] == "金融"
    assert result["notes"] == "重点关注"


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_update_not_found(mock_get_conn, svc):
    conn, _ = _mock_conn(fetchone_result=None)
    mock_get_conn.return_value = conn

    with pytest.raises(ValueError, match="关注股票不存在"):
        svc.update(999, notes="test")


# ── delete ──────────────────────────────────────────────────


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_delete_success(mock_get_conn, svc):
    existing = {"id": 3, "stock_code": "000001"}
    call_count = 0

    def make_conn():
        nonlocal call_count
        result = existing if call_count == 0 else None
        call_count += 1
        conn, cursor = _mock_conn(fetchone_result=result)
        return conn

    mock_get_conn.side_effect = lambda: make_conn()

    assert svc.delete(3) is True


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_delete_not_found(mock_get_conn, svc):
    conn, _ = _mock_conn(fetchone_result=None)
    mock_get_conn.return_value = conn

    with pytest.raises(ValueError, match="关注股票不存在"):
        svc.delete(999)


# ── batch_add ───────────────────────────────────────────────


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_batch_add_mixed(mock_get_conn, svc):
    """测试批量添加：有新增有跳过"""
    added_count = 0
    skipped_via_duplicate = False

    def make_conn():
        nonlocal added_count, skipped_via_duplicate
        # Each call to add() will open a new connection
        # For the duplicate check (first add for 000001):
        if not skipped_via_duplicate:
            skipped_via_duplicate = True
            conn, _ = _mock_conn(fetchone_result={"id": 1})  # duplicate
            return conn
        added_count += 1
        new_row = {"id": added_count + 1, "stock_code": "new", "stock_name": "new"}
        conn, _ = _mock_conn(fetchone_result=new_row, lastrowid=added_count + 1)
        return conn

    mock_get_conn.side_effect = lambda: make_conn()

    stocks = [
        {"stock_code": "000001"},  # already tracked → skip
        {"stock_code": "000002"},  # new → add
        {"stock_code": "603009"},  # new → add
    ]
    result = svc.batch_add(stocks)
    assert result["added"] == 2
    assert result["skipped"] == 1


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_batch_add_empty_stocks(mock_get_conn, svc):
    result = svc.batch_add([])
    assert result["added"] == 0
    assert result["skipped"] == 0


# ── get_groups ──────────────────────────────────────────────


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_get_groups(mock_get_conn, svc):
    rows = [{"group_name": "科技"}, {"group_name": "银行"}]
    conn, _ = _mock_conn(fetchall_result=rows)
    mock_get_conn.return_value = conn

    result = svc.get_groups()
    assert result == ["科技", "银行"]


@patch("stockshark.services.tracked_stock_service.get_mysql_connection")
def test_get_groups_empty(mock_get_conn, svc):
    conn, _ = _mock_conn(fetchall_result=[])
    mock_get_conn.return_value = conn

    result = svc.get_groups()
    assert result == []
