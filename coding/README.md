# 程式競賽題解

LibOfManyCodes 題解網站，主頁依**題目類型**與**難度**分組排序。

## 背景圖片

將 `back-g.jpg` 放在 `coding/` 資料夾內，即可作為網頁背景，並套用霧面毛玻璃效果。

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

編輯 `meta.json` 可手動設定**題目大意**、**題解**、複雜度、類型、難度：

```json
{
  "a132 uva10931": {
    "summary": "給定十進位整數，輸出其二進位表示與 1 的個數（parity）。",
    "solution": "將十進位轉二進位，同時計算 1 的個數（parity）。",
    "complexity": "O(log n)",
    "type": "數學",
    "difficulty": 2
  }
}
```

- **summary**：題目大意（若未填則顯示「請自行查閱題目描述」）
- **solution**：題解（若未填則顯示「請自行補充」或從程式碼註解擷取）

重新執行 `build.py` 即可更新頁面。

## MathJax 數學式

題目大意與題解支援 LaTeX 數學式，使用 MathJax 渲染：

| 用途 | 語法 | 範例 |
|------|------|------|
| 行內數學 | `\( ... \)` | `給定 \(n\)，求 \(\sum_{i=1}^n i\)` |
| 區塊數學 | `\[ ... \]` | `\[ \frac{n(n+1)}{2} \]` |

在 `meta.json` 中需將反斜線寫成 `\\`，例如：

```json
"solution": "時間複雜度為 \\(O(n \\log n)\\)，使用 \\(\\sum_{i=1}^n i = \\frac{n(n+1)}{2}\\)。"
```
