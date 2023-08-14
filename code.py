import os               # ファイル操作など、OSレベルの機能を提供するために使用
import socketpool       # TCP/IP接続用のソケット管理用
import wifi             # WiFi接続を管理用
import digitalio        # デジタルピンの入出力を制御用
from board import *     # マイクロコントローラーのボード定義から全てのピンをインポート
import microcontroller  # マイクロコントローラーに関する情報（CPU温度等）を取得
from adafruit_httpserver import Server, Request, Response, FileResponse # HTTPサーバー用ライブラリ

led = digitalio.DigitalInOut(LED)           # 本体LEDをGPIO端子に割り当て
led.direction = digitalio.Direction.OUTPUT  # LED端子を出力に設定

# グローバル変数
state = "OFF!"  # 本体LED状態格納用

# Wi-FiアクセスポイントのSSIDとパスワードを取得（setting.tomlから取得する場合）
ssid = os.getenv("CIRCUITPY_WIFI_SSID")         # Wi-Fi接続先SSID
password = os.getenv("CIRCUITPY_WIFI_PASSWORD") # Wi-Fi接続先パスワード
port_num = 80                                   # ポート番号（標準は80）

# Wi-Fi接続を実行
wifi.radio.connect(ssid, password)  # 指定したSSIDとパスワードで接続
print("Connected to", ssid)         # 接続先SSID表示

# ソケットプールを作成してHTTPサーバーを起動するための準備
pool = socketpool.SocketPool(wifi.radio)      # Wi-Fi接続上でソケットを管理するためのオブジェクトを作成
server = Server(pool, "/static", debug=True)  # サーバー起動時にPicoWのルートディレクトリからデータを提供できるようにする

# ルート（IPアドレス:ポート）アクセス時に実行される関数（トップページ表示、ポート80は省略可）
@server.route("/")
def base(request: Request):       # HTTPリクエストを処理する関数を定義
    return FileResponse(request, filename='index.html', root_path='/')  # レスポンスとして「index.html」ファイルを返す

# 本体LED点灯（IPアドレス:ポート/lighton）アクセス時に実行される関数（ポート80なら省略可）
@server.route("/lighton")
def light_on(request: Request):
    led.value = True              # 本体LEDを点灯
    return Response(request, "LED_ON!", content_type="text/plane")  # レスポンスとして「テキスト（文字列）」を返す

# 本体LED消灯（IPアドレス:ポート/lightoff）アクセス時に実行される関数（ポート80なら省略可）
@server.route("/lightoff")
def light_on(request: Request):
    led.value = False             # 本体LEDを消灯
    return Response(request, "LED_OFF!", content_type="text/plane")

# 本体温度取得（IPアドレス:ポート/get_data）アクセス時に実行される関数（ポート80なら省略可）
@server.route("/get_data")
def get_data(request: Request):
    temp = microcontroller.cpu.temperature  # 本体温度センサの温度取得
    temp = "{:.1f}".format(temp)            # 温度の値を小数点1桁に成形
    return Response(request, temp, content_type="text/plane")

# HTTPサーバーを開始して待ち受けるIPアドレスを表示する
print(f"Listening on http://{wifi.radio.ipv4_address}:{port_num}")  # f文字列を使って「IPアドレス」と「ポート番号」を埋め込んで表示
server.serve_forever(str(wifi.radio.ipv4_address), port=port_num)   # HTTPサーバーを指定された「IPアドレス」と「ポート」で開始