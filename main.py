from machine import Pin, PWM
import machine
import utime

# PWMの設定
pwm_l = PWM(Pin(0))
pwm_r = PWM(Pin(1))
pwm_l.freq(10000)
pwm_r.freq(10000)

# スロットルセンサーの設定
sensor_throttle = machine.ADC(0)

# 前回の読み取り値を初期化
before_read = sensor_throttle.read_u16()

# 急な操作をキャンセルするための差分閾値、緩やかに加速するための時間差、制限値を設定
diff_term = 0.1
diff_limit = 10000
low_limit = 18000
high_limit = 65535

# 制限フラグの初期化
limit_over = False

# 無限ループでスロットルセンサーの値を読み取り、PWMのデューティー比に反映する
while True:
    reading = sensor_throttle.read_u16()

    # スロットルセンサーの値が上限値を超えた場合は上限値に制限する
    if reading > high_limit:
        reading = high_limit

    # 制限フラグがONの場合は前回の値に戻す
    if limit_over:
        if reading < low_limit:
            limit_over = False
            print("limit off")
        reading = before_read
    else:
        # 前回の値との差分が閾値を超えた場合は制限フラグをONにする
        if reading > before_read:
            if reading - before_read > diff_limit:
                limit_over = True
                print("limit over")
            else:
                # スロットルセンサーの値をPWMのデューティー比に反映する
                pwm_l.duty_u16(int(reading))
                pwm_r.duty_u16(int(reading))
        else:
            # スロットルセンサーの値をPWMのデューティー比に反映する
            pwm_l.duty_u16(int(reading))
            pwm_r.duty_u16(int(reading))

    # 値の確認のために、前回の値、現在の値、制限フラグを出力する
    print(str(before_read) + " " + str(reading) + " " + str(limit_over))

    # 前回の値を更新して、一定時間待つ
    before_read = reading
    utime.sleep(diff_term)
