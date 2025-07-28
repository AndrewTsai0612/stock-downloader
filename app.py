# app.py
from flask import Flask, request, send_file, Response
import yfinance as yf
import pandas as pd
import io, textwrap

app = Flask(__name__)

# 首頁 HTML 內容
HOME_HTML = textwrap.dedent("""
<!DOCTYPE html>
<html lang="zh-Hant">
<head><meta charset="UTF-8">
  <title>台股歷史資料下載</title>
  <style>
    body{font-family:sans-serif;padding:20px;max-width:480px;margin:auto;}
    input,button,label{margin:.4em 0;width:95%;padding:8px;}
    button{width:100%;background-color:#007bff;color:white;border:none;cursor:pointer;}
    fieldset{margin-top:.6em;border:1px solid #ccc;}
    h2{text-align:center;}
    #status { margin-top: 1em; font-weight: bold; border: 1px solid transparent; padding: 10px; border-radius: 4px; display: none; }
    #status.show { display: block; }
    #status.error { color: #a94442; background-color: #f2dede; border-color: #ebccd1; }
  </style>
</head>
<body>
<h2>Yahoo Finance 台股資料下載</h2>
<form method="post" action="/download">
  股票代號：<input name="symbol" placeholder="例如: 2330" required><br>
  開始日期：<input type="date" name="start" required><br>
  結束日期：<input type="date" name="end" required><br>

  <fieldset>
    <legend>下載欄位（可複選）</legend>
    <label><input type="checkbox" name="fields" value="Open"  checked> Open</label>
    <label><input type="checkbox" name="fields" value="High"  checked> High</label>
    <label><input type="checkbox" name="fields" value="Low"   checked> Low</label>
    <label><input type="checkbox" name="fields" value="Close" checked> Close</label>
  </fieldset>

  <button type="submit">下載 CSV</button>
</form>
<div id="status"></div>
</body></html>
""")

# ---------- 首頁路由 ---------- #
@app.route('/')
def index():
    return Response(HOME_HTML, mimetype='text/html')

# ---------- 下載路由 ---------- #
@app.route('/download', methods=['POST'])
def download():
    try:
        code_raw = request.form.get('symbol', '').strip()
        if not code_raw:
            return Response(f'<script>alert("股票代號不得為空");window.history.back();</script>', mimetype='text/html'), 400
        
        code   = code_raw + '.TW'
        start  = request.form['start']
        end    = request.form['end']
        fields = request.form.getlist('fields') or ['Open','High','Low','Close']

        df = yf.download(code, start=start, end=end, interval='1d')

        if df.empty:
            return Response(f'<script>alert("找不到任何資料，請確認代號或日期區間");window.history.back();</script>', mimetype='text/html'), 404

        df = df[fields].round(2)

        buf = io.StringIO()
        df.to_csv(buf, float_format='%.2f')
        buf.seek(0)
        csv_bytes = io.BytesIO(buf.getvalue().encode('utf-8'))

        fname = f"{code_raw}_{start}_{end}.csv"
        return send_file(csv_bytes,
                         as_attachment=True,
                         download_name=fname,
                         mimetype='text/csv')

    except Exception as e:
        error_message = str(e).replace('"', "'").replace('\n', ' ')
        return Response(f'<script>alert("下載失敗：{error_message}");window.history.back();</script>', mimetype='text/html'), 500

# 注意：我們不再需要 if __name__ == '__main__': app.run() 了
# Vercel 會自動使用 Gunicorn 來運行 app