from machine import Pin, PWM
import machine
import utime

# for pico
#led = machine.Pin(25, machine.Pin.OUT)
#led.value(1)
# for pico w
led = machine.Pin("LED", machine.Pin.OUT)
led.on()

# スロットルのPWMの設定
t_pwm_l = PWM(Pin(0))
t_pwm_r = PWM(Pin(1))
t_pwm_l.freq(10000)
t_pwm_r.freq(10000)

# ブレーキのPWMの設定
b_pwm_l = PWM(Pin(2))
b_pwm_r = PWM(Pin(3))
b_pwm_l.freq(10000)
b_pwm_r.freq(10000)

# スロットルセンサーの設定
sensor_throttle = machine.ADC(0)

# ブレーキセンサーの設定
sensor_brake = machine.ADC(1)

# 前回の読み取り値を初期化
t_before_read = sensor_throttle.read_u16()

# 急な操作をキャンセルするための差分閾値、緩やかに加速するための時間差、加速単位、制限値を設定
diff_term = 0.1
diff_unit = 1000
diff_limit = 10000
b_low_limit = 40000
t_low_limit = 20000
high_limit = 65535

# 制限フラグの初期化
limit_over = False

# 無限ループでスロットルセンサーの値を読み取り、PWMのデューティー比に反映する
while True:

    t_reading = sensor_throttle.read_u16()
    b_reading = sensor_brake.read_u16()

    # スロットルセンサーの値が上限値を超えた場合は上限値に制限する
    if t_reading > high_limit:
        t_reading = high_limit

    # ブレーキセンサーの値が上限値を超えた場合は上限値に制限する
    if b_reading > high_limit:
        b_reading = high_limit

    # 制限フラグがONの場合は前回の値に戻す
    if limit_over:
        # スロットルが下限値より小さい場合に制限フラグをOFFにする
        if t_reading < t_low_limit:
            limit_over = False
            print("limit off")
        t_reading = t_before_read
    else:
        # 前回の値との差分が閾値を超えた場合は制限フラグをONにする
        if t_reading > t_before_read:
            if t_reading - t_before_read > diff_limit:
                limit_over = True
                t_reading = t_low_limit
                print("limit over")
            else:
                # 穏やかに加速するため、加速単位以上の加速を抑える
                if t_reading > t_before_read + diff_unit:
                    t_reading = t_before_read + diff_unit
                # スロットルセンサーの値をPWMのデューティー比に反映する
                t_pwm_l.duty_u16(int(t_reading))
                t_pwm_r.duty_u16(int(t_reading))
        else:
            # スロットルセンサーの値をPWMのデューティー比に反映する
            t_pwm_l.duty_u16(int(t_reading))
            t_pwm_r.duty_u16(int(t_reading))

    #  加速に合わせ、ブレーキセンサーが下限値を下回る場合はデューティー比を0(ブレーキなし)にする
    if b_reading < b_low_limit:
        b_reading = 0
    
    # ブレーキセンサーの値をPWMのデューティー比に反映する
    b_pwm_l.duty_u16(int(b_reading))
    b_pwm_r.duty_u16(int(b_reading))

    # 値の確認のために、前回の値、現在の値、制限フラグを出力する
    print(str(t_before_read) + " " + str(t_reading) + " " + str(b_reading) + " " + str(limit_over))

    # 前回の値を更新して、一定時間待つ
    t_before_read = t_reading
    utime.sleep(diff_term)
