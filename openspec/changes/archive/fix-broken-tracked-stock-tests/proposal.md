# Proposal: Fix 2 Broken Tests in test_tracked_stock_service

## Summary
修复 `tests/unit/test_tracked_stock_service.py` 中 2 个失败的测试用例。

## Motivation
全量回归测试发现 2 个测试失败：
- `test_add_success` — mock `fetchone` 返回值导致 `_is_duplicate` 检查误判，抛出 ValueError("该股票已在关注列表中")
- `test_batch_add_mixed` — 同样的 mock 问题导致 `assert result["added"] == 2` 失败（实际为 0）

根本原因：mock 设置中 `fetchone_result` 只有一个值，但 `add()` 方法会多次调用 `fetchone`（先检查重复，再查询结果）。第一次调用应该返回 None（不重复），第二次返回新行。

## Expected Behavior
- `test_add_success` 应该 PASS：mock 需要让 `_is_duplicate` 检查返回 None（不重复），然后 INSERT 成功，最后 SELECT 返回新行
- `test_batch_add_mixed` 应该 PASS：mock 需要支持多次 `fetchone` 调用，对重复检查返回 None，对最终查询返回行

## Constraints
- 只修改 `tests/unit/test_tracked_stock_service.py` 中的 mock 设置
- 不要修改 `stockshark/services/tracked_stock_service.py` 源码
- 保持其他 15 个通过的测试不受影响
