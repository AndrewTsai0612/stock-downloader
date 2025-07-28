# app.py (已修正 CSS 版面)

from flask import Flask, request, send_file, Response
import yfinance as yf
import pandas as pd
import io, datetime, textwrap

app = Flask(__name__)

# ---------- 首頁：顯示輸入介面 ---------- #
@app.route('/')
def index():
    # 直接回傳一段 HTML；使用者填表單後 POST /download
    return Response(textwrap.dedent("""
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head><meta charset="UTF-8">
      <title>台股歷史資料下載</title>
      <style>
        body{font-family:sans-serif;padding:20px;max-width:480px;margin:auto;}
        
        /* --- 以下為修正後的 CSS --- */

        /* 針對文字和日期輸入框，讓它們變寬 */
        input[type="text"], input[type="date"] {
            width: 95%;
            padding: 6px;
            margin: .4em 0;
        }
        
        /* 保持 Checkbox 的 Label 正常，不要變寬 */
        fieldset label {
            display: inline-block; /* 讓它們可以並排 */
            margin-right: 15px; /* 增加右邊距，讓選項分開一點 */
            width: auto; /* 取消寬度設定 */
        }
        
        /* 美化按鈕，讓它變寬且變色 */
        button {
            width: 100%; /* 按鈕寬度100% */
            padding: 10px;
            margin-top: 1em;
            font-size: 16px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }

        button:hover {
            background-color: #0056b3; /* 按鈕滑鼠移過時變色 */
        }

        fieldset{
            margin-top:.6em;
            border: 1px solid #ccc;
            border-radius: 5px;
        }

        h2 {
            text-align: center;
            color: #333;
        }

      </style>
    </head>
    <body>
    <h2>Yahoo Finance 台股資料下載</h2>
    <form method="post" action="/download">
      <!-- 將股票代號的 input type 明確設為 "text" -->
      股票代號：<br><input type="text" name="symbol" placeholder="例如：2330" required><br>
      開始日期：<br><input type="date" name="start" required><br>
      結束日期：<br><input type="date" name="end" required><br>

      <fieldset>
        <legend>下載欄位（可複選）</legend>
        <label><input type="checkbox" name="fields" value="Open"  checked> Open</label>
        <label><input type="checkbox" name="fields" value="High"  checked> High</label>
        <label><input type="checkbox" name="fields" value="Low"   checked> Low</label>
        <label><input type="checkbox" name="fields" value="Close" checked> Close</label>
      </fieldset>

      <button type="submit">下載 CSV</button>
    </form>
    </body></html>
    """), mimetype='text/html')

# ---------- 下載路由 ---------- #
@app.route('/download', methods=['POST'])
def download():
    # 1. 讀取使用者輸入
    code_raw = request.form.get('symbol', '').strip()
    if not code_raw:
        return '股票代號不得為空', 400
    code   = code_raw + '.TW'
    start  = request.form['start']
    end    = request.form['end']
    fields = request.form.getlist('fields') or ['Open','High','Low','Close']
    
    # 2. 向 Yahoo Finance 下載資料
    try:
        df = yf.download(code, start=start, end=end, interval='1d')
    except Exception as e:
        return f'下載失敗：{e}', 500

    if df.empty:
        return '找不到任何資料，請確認代號或日期區間', 404
        
    # 3. 只留使用者選擇欄位，並四捨五入到 2 位
    df = df[fields].round(2)
    
    # 4. 轉成 CSV → BytesIO
    buf = io.StringIO()
    df.to_csv(buf, float_format='%.2f')
    buf.seek(0)
    csv_bytes = io.BytesIO(buf.getvalue().encode('utf-8'))
    
    # 5. 回傳檔案
    fname = f"{code_raw}_{start}_{end}.csv"
    return send_file(csv_bytes,
                     as_attachment=True,
                     download_name=fname,
                     mimetype='text/csv')

# ---------- 主程式 ---------- #
# if __name__ == '__main__':
#     app.run(debug=True)
