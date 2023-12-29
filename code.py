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

# 急な操作をキャンセルするための差分閾値、緩やかに加速するための時間差、加速単位、制限値を設定
diff_term = 0.1
t_diff_unit = 1000
b_diff_unit = 5000
diff_limit = 10000
b_low_limit = 40000
t_low_limit = 20000
b_high_limit = 50000
t_high_limit = 50000
straight_range = 10000
a_center = 32767
high_max = 65535

# 前回の読み取り値を初期化
t_before_read = int(sensor_throttle.value)
b_before_read = high_max
a_before_read = a_center

# 無限ループでスロットルセンサーの値を読み取り、PWMのデューティー比に反映する
while True:
    t_reading = int(sensor_throttle.value)
    a_reading = int(sensor_angle.value)
    if a_reading > a_center:
        l_subtract = 0
        r_subtract = a_reading - a_center - straight_range
    else:
        l_subtract = a_center - a_reading - straight_range
        r_subtract = 0
    
    # スロットルセンサーの値が上限値を超えた場合はスロットル値を0, ブレーキ値を最大値にする
    if t_reading > t_high_limit:
        t_reading = t_low_limit
        b_reading = high_max
    else:
        # スロットルセンサーの値が下限値を下回った場合はスロットル値を0, ブレーキ値を最大値にする
        if t_reading < t_low_limit:
            t_reading = t_low_limit
            b_reading = high_max
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
                if b_reading == high_max:
                    pass
                else:
                    b_reading = int(b_before_read + b_diff_unit)

    # スロットルセンサーの値をPWMのデューティー比に反映する
    if t_reading - l_subtract < 0:
        t_reading_l = 0
    else:
        t_reading_l = t_reading - l_subtract
    
    if t_reading - r_subtract < 0:
        t_reading_r = 0
    else:
        t_reading_r = t_reading - r_subtract
    t_pwm_l.duty_cycle = t_reading_l
    t_pwm_r.duty_cycle = t_reading_r
    # ブレーキ値をPWMのデューティー比に反映する
    b_pwm_l.duty_cycle = b_reading
    b_pwm_r.duty_cycle = b_reading

    # 値の確認のために、前回の値、現在の値、制限フラグを出力する
    print(str(t_before_read) + " " + str(t_reading_l) + " " + str(t_reading_r) + " " + str(b_before_read) + " " + str(b_reading))

    # 前回の値を更新して、一定時間待つ
    t_before_read = t_reading
    b_before_read = b_reading
    time.sleep(diff_term)
