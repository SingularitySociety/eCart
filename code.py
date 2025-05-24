import board
import pwmio
import digitalio
import analogio
import time

# LEDの設定
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# LEDの点灯
led.value = True

# スロットルのPWMの設定
t_pwm_l = pwmio.PWMOut(board.GP0, frequency=10000)
t_pwm_r = pwmio.PWMOut(board.GP1, frequency=10000)

# ブレーキのPWMの設定
b_pwm_l = pwmio.PWMOut(board.GP2, frequency=10000)
b_pwm_r = pwmio.PWMOut(board.GP3, frequency=10000)

# スロットルセンサーの設定
sensor_throttle = analogio.AnalogIn(board.A0)

# 左右センサーの設定
sensor_angle = analogio.AnalogIn(board.A1)

# パラメータの設定
# これらはデバイスの動作を制御するための値です
diff_term = 0.01        # 急な操作をキャンセルするための差分単位
t_diff_unit = 1         # スロットルの急な操作をキャンセルするための差分単位
b_diff_unit = 1000         # ブレーキの急な操作をキャンセルするための差分単位
diff_limit = 10000      # 急な操作をキャンセルするための差分の上限値
b_low_limit = 40000     # ブレーキの急な操作をキャンセルするための下限値
t_low_limit = 20000     # スロットルの急な操作をキャンセルするための下限値
b_high_limit = 50000    # ブレーキの急な操作をキャンセルするための上限値
t_high_limit = 50000    # スロットルの急な操作をキャンセルするための上限値
straight_range = 10000  # 直進時の急な操作をキャンセルするための制限値
a_center = 32767        # ステアリング角度の中央値
a_trim = 0              # ステアリング角度の調整値
high_max = 65535        # アナログ入力の最大値

a_trim = -9500

# 前回の読み取り値を初期化
t_before_read = int(sensor_throttle.value)
b_before_read = high_max
a_before_read = a_center
b_reading = high_max

# 無限ループでスロットルセンサーの値を読み取り、PWMのデューティー比に反映する
while True:
    # ...（ループ内の処理）
    # ループ内では、スロットルセンサーとステアリング角度センサーの値を読み取り、
    # それらをPWM出力に反映させています。また、異常値や急な操作に対応するための
    # ロジックも含まれています。

    # センサーから現在の値を読み取る
    t_reading = int(sensor_throttle.value)
    a_reading = int(sensor_angle.value) + a_trim

    # ステアリング角度が中央値より大きい場合、右に移動するため左側の減算はせずに、右側の減算値を計算する
    if a_reading > a_center:
        # 左側の減算値は0
        l_subtract = 0
        # 右側の減算値は読み込み値から中央値と直進制限値を引いた値
        r_subtract = a_reading - a_center
    # ステアリング角度が中央値より小さい場合、左に移動するため右側の減算はせずに、左側の減算値を計算する
    else:
        # 左側の減算値は中央値から読み込み値と直進制限値を引いた値
        l_subtract = a_center - a_reading
        # 右側の減算値は0
        r_subtract = 0
    
    o_reading = t_reading
    # スロットルセンサーの値が上限値を超えた場合はスロットル値を0, ブレーキ値を最大値にする
    if t_reading > t_high_limit:
        b_reading = high_max
        t_reading = t_low_limit
        if int(b_before_read + b_diff_unit) > high_max:
            b_reading = high_max
        else:
            b_reading = int(b_before_read + b_diff_unit)
        # print("t_reading > t_high_limit:" + str(b_reading) + "  b_before_read:" + str(b_before_read) + " b_diff_unit" + str(b_diff_unit))
    else:
        # スロットルセンサーの値が下限値を下回った場合はスロットル値を0, ブレーキ値を最大値にする
        if t_reading < t_low_limit:
            t_reading = t_low_limit
            if int(b_before_read + b_diff_unit) > high_max:
                b_reading = high_max
            else:
                b_reading = int(b_before_read + b_diff_unit)
            # print("t_reading > t_high_limit:" + str(b_reading) + "  b_before_read:" + str(b_before_read) + " b_diff_unit" + str(b_diff_unit))
        else:
            b_reading = 0

    # 前回の値との差分が閾値を超えた場合は規定の加速単位で穏やかに加速する
    if t_reading > t_before_read:
        # 加速
        if t_reading - t_before_read > diff_limit:
            t_reading = int(t_before_read + t_diff_unit)
    else:
        # 前回の値との差分が閾値を超えた場合は規定の減速単位で穏やかに減速する
        if b_reading > b_before_read:
            # 減速
            if b_reading - b_before_read > diff_limit:
                # 緊急ブレーキ
                if b_reading == b_high_limit:
                    pass
                else:
                    b_reading = int(b_before_read + b_diff_unit)

    # 左右のPWM値を設定する。
    # 左側
    t_value_l = t_reading - l_subtract
    if t_value_l <= 0:
        t_value_l = 0
        b_value_l = high_max
    if l_subtract >= 0:
        b_value_l = b_reading

    # 右側
    t_value_r = t_reading - r_subtract
    if t_value_r <= 0:
        t_value_r = 0
        b_value_r = high_max
    if r_subtract >= 0:
        b_value_r = b_reading
    
    # PWM出力の更新
    # スロットル値をPWMのデューティー比に反映する
    t_pwm_l.duty_cycle = t_value_l
    t_pwm_r.duty_cycle = t_value_r
    # ブレーキ値をPWMのデューティー比に反映する
    b_pwm_l.duty_cycle = b_value_l
    b_pwm_r.duty_cycle = b_value_r

    # 値の確認のために、前回の値、現在の値、制限フラグを出力する
    print(str(a_reading) + " " + str(o_reading) + " " + str(t_value_l) + " " + str(t_value_r) + " " + str(b_value_l) + " " + str(b_value_r))

    # 前回のスロットル値とブレーキ値を更新し、次のループでの比較のために保存する。
    t_before_read = t_reading
    b_before_read = b_reading
    # プログラムの実行を一時的に中断し一定の時間間隔を設ける。
    # 制御信号が適切なレートで更新されるようにセンサーからのデータの読み取りやPWM信号の更新を待つ。
    time.sleep(diff_term)


