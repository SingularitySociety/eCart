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

# ブレーキセンサーの設定
sensor_brake = analogio.AnalogIn(board.A1)

# 前回の読み取り値を初期化
t_before_read = int(sensor_throttle.value)

# 急な操作をキャンセルするための差分閾値、緩やかに加速するための時間差、加速単位、制限値を設定
diff_term = 0.1
diff_unit = 1000
diff_limit = 10000
b_low_limit = 40000
t_low_limit = 20000
b_high_limit = 50000
t_high_limit = 50000

# 無限ループでスロットルセンサーの値を読み取り、PWMのデューティー比に反映する
while True:
    t_reading = int(sensor_throttle.value)
    b_reading = int(sensor_brake.value)

    # スロットルセンサーの値が上限値を超えた場合はスロットル値を0にする
    if t_reading > t_high_limit:
        t_reading = 0
        b_reading = 65535

    # ブレーキセンサーの値が上限値を超えた場合は上限値に制限する
    if b_reading > b_high_limit:
        b_reading = 65535

    # 前回の値との差分が閾値を超えた場合は規定の加速単位で穏やかに加速する
    if t_reading > t_before_read:
        # 加速
        if t_reading - t_before_read > diff_limit:
            t_reading = int(t_before_read + diff_unit)
        # スロットルセンサーの値をPWMのデューティー比に反映する
        t_pwm_l.duty_cycle = t_reading
        t_pwm_r.duty_cycle = t_reading
    else:
        # 減速
        # スロットルセンサーの値をPWMのデューティー比に反映する
        t_pwm_l.duty_cycle = t_reading
        t_pwm_r.duty_cycle = t_reading

    #  加速に合わせ、ブレーキセンサー値がスロットルセンサー値を下回る場合はデューティー比を0(ブレーキなし)にする
    if b_reading < t_reading:
        b_reading = 0
    else:
        pass
    
    # ブレーキセンサーの値をPWMのデューティー比に反映する
    b_pwm_l.duty_cycle = b_reading
    b_pwm_r.duty_cycle = b_reading

    # 値の確認のために、前回の値、現在の値、制限フラグを出力する
    print(str(t_before_read) + " " + str(t_reading) + " " + str(b_reading))

    # 前回の値を更新して、一定時間待つ
    t_before_read = t_reading
    time.sleep(diff_term)
