# 程式競賽題解

LibOfManyCodes 題解網站，每題包含：題目大意、題解、時間複雜度、程式碼。

## 建置

```bash
cd coding
python build.py --code-dir "C:\Users\吳瑞宸\Downloads\git\CodeLib\code" --output "." --seed 42
```

## 補充題解與時間複雜度

編輯 `meta.json`，以題目 ID 為 key 加入內容：

```json
{
  "a132 uva10931": {
    "solution": "將十進位轉二進位，同時計算 1 的個數（parity）。",
    "complexity": "O(log n)"
  },
  "uva924": {
    "solution": "BFS 遍歷圖，記錄每層節點數，找出最大層。",
    "complexity": "O(V + E)"
  }
}
```

重新執行 `build.py` 即可更新頁面。
