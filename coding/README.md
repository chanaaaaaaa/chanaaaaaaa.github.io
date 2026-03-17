# 程式競賽題解

LibOfManyCodes 題解網站，主頁依**題目類型**與**難度**分組排序。

## 建置

```bash
cd coding
python analyze_complexity.py   # 分析複雜度、類型、難度
python build.py --code-dir "C:\path\to\CodeLib\code" --output "." --seed 42
```

## 分類說明

- **類型**：圖論、DP、貪心、排序、搜尋、數學、字串、資料結構、模擬、其他
- **難度**：1 入門、2 簡單、3 中等、4 困難、5 進階

主頁依類型分區，同類型內依難度由易到難排序。

## 補充或覆寫 meta

編輯 `meta.json` 可手動設定題解、複雜度、類型、難度：

```json
{
  "a132 uva10931": {
    "solution": "將十進位轉二進位，同時計算 1 的個數（parity）。",
    "complexity": "O(log n)",
    "type": "數學",
    "difficulty": 2
  }
}
```

重新執行 `build.py` 即可更新頁面。
