"""关注股票服务层 - tracked_stock 表的 CRUD 操作"""

from stockshark.utils.database import get_mysql_connection
from stockshark.utils.logger import get_logger

logger = get_logger(__name__)


class TrackedStockService:
    """关注股票服务"""

    def list_all(self, group_name=None):
        """
        查询所有关注股票

        Args:
            group_name: 可选，按分组名称过滤

        Returns:
            list: 关注股票列表
        """
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            if group_name:
                cursor.execute(
                    "SELECT * FROM tracked_stock WHERE group_name = %s "
                    "ORDER BY sort_order ASC, created_at ASC",
                    (group_name,),
                )
            else:
                cursor.execute(
                    "SELECT * FROM tracked_stock ORDER BY sort_order ASC, created_at ASC"
                )
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"查询关注股票列表失败: {e}")
            raise
        finally:
            conn.close()

    def get_by_id(self, stock_id):
        """
        根据 ID 查询单条关注股票

        Args:
            stock_id: 关注股票 ID

        Returns:
            dict or None
        """
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tracked_stock WHERE id = %s", (stock_id,))
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"查询关注股票失败: {e}")
            raise
        finally:
            conn.close()

    def _auto_fill_stock_name(self, stock_code, stock_name=None):
        """
        自动填充股票名称：优先使用传入名称，其次从 stock_basic_info 表查找，最后用代码

        Args:
            stock_code: 股票代码
            stock_name: 传入的名称（可能为空）

        Returns:
            str: 最终的股票名称
        """
        if stock_name:
            return stock_name
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM stock_basic_info WHERE symbol = %s", (stock_code,)
            )
            row = cursor.fetchone()
            if row and row["name"]:
                return row["name"]
        except Exception as e:
            logger.warning(f"自动填充股票名称失败: {e}")
        finally:
            if conn:
                conn.close()
        return stock_code

    def _is_duplicate(self, stock_code):
        """检查股票代码是否已关注"""
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM tracked_stock WHERE stock_code = %s", (stock_code,)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"检查重复关注股票失败: {e}")
            raise
        finally:
            conn.close()

    def add(self, stock_code, stock_name=None, group_name=None, sort_order=0, notes=None):
        """
        添加关注股票

        Args:
            stock_code: 股票代码（必填）
            stock_name: 股票名称（可选，自动填充）
            group_name: 分组名称（可选）
            sort_order: 排序权重（默认 0）
            notes: 备注（可选）

        Returns:
            dict: 新建的关注股票记录

        Raises:
            ValueError: 股票代码已关注
        """
        if self._is_duplicate(stock_code):
            raise ValueError("该股票已在关注列表中")

        resolved_name = self._auto_fill_stock_name(stock_code, stock_name)

        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tracked_stock (stock_code, stock_name, group_name, sort_order, notes) "
                "VALUES (%s, %s, %s, %s, %s)",
                (stock_code, resolved_name, group_name, sort_order, notes),
            )
            conn.commit()
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM tracked_stock WHERE id = %s", (new_id,))
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"添加关注股票失败: {e}")
            raise
        finally:
            conn.close()

    def update(self, stock_id, **kwargs):
        """
        更新关注股票信息（stock_code 不可修改）

        Args:
            stock_id: 关注股票 ID
            **kwargs: 可更新字段 stock_name, group_name, sort_order, notes

        Returns:
            dict: 更新后的记录

        Raises:
            ValueError: 关注股票不存在
        """
        existing = self.get_by_id(stock_id)
        if not existing:
            raise ValueError("关注股票不存在")

        allowed_fields = {"stock_name", "group_name", "sort_order", "notes"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return existing

        set_clause = ", ".join(f"{k} = %s" for k in updates)
        values = list(updates.values()) + [stock_id]

        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE tracked_stock SET {set_clause} WHERE id = %s", values
            )
            conn.commit()
            cursor.execute("SELECT * FROM tracked_stock WHERE id = %s", (stock_id,))
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"更新关注股票失败: {e}")
            raise
        finally:
            conn.close()

    def delete(self, stock_id):
        """
        删除关注股票

        Args:
            stock_id: 关注股票 ID

        Returns:
            bool: 是否删除成功（False 表示不存在）

        Raises:
            ValueError: 关注股票不存在
        """
        existing = self.get_by_id(stock_id)
        if not existing:
            raise ValueError("关注股票不存在")

        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tracked_stock WHERE id = %s", (stock_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"删除关注股票失败: {e}")
            raise
        finally:
            conn.close()

    def batch_add(self, stocks):
        """
        批量添加关注股票

        Args:
            stocks: list of dict，每个 dict 包含 stock_code 等字段

        Returns:
            dict: {"added": <count>, "skipped": <count>}
        """
        added = 0
        skipped = 0
        for item in stocks:
            stock_code = item.get("stock_code")
            if not stock_code:
                skipped += 1
                continue
            try:
                self.add(
                    stock_code=stock_code,
                    stock_name=item.get("stock_name"),
                    group_name=item.get("group_name"),
                    sort_order=item.get("sort_order", 0),
                    notes=item.get("notes"),
                )
                added += 1
            except ValueError:
                # 已关注的代码，跳过
                skipped += 1
        return {"added": added, "skipped": skipped}

    def get_groups(self):
        """
        获取所有不重复的分组名称（排除 NULL）

        Returns:
            list: 分组名称列表
        """
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT group_name FROM tracked_stock "
                "WHERE group_name IS NOT NULL ORDER BY group_name"
            )
            return [row["group_name"] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取分组列表失败: {e}")
            raise
        finally:
            conn.close()
