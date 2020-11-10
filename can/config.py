
#two pi should owns same machine_id but unique among all
machine_id = '123get'

### main type of machine should equiped with as follows:
# connected with net
# connected with camera (human exist report)
### sub type of machine should equiped with as follows:
# receive command through UART

mqtt_server_ip = 'xxx.xxx.xxx.xxx'
mqtt_port = 1883
mqtt_pub_path = 'report/'+machine_id
mqtt_sub_path = 'command/'+machine_id


box = {
        'name': 'bottle',
        ## weight option
        'moter_pins': [6,13,19,26],
        'hand_pin': 4,
        
        'weight_clock_pin': 20,
        'weight_output_pin': 21,
        'arrange': 10000,
        'k': 1,
        'b': 0,
        
        'full_pins':[17],
        'wait_duration': [5,30],
        'no_hand_back': 3,
        'motor_runtime': [5,6],
}

# smoke detect config
enable_smoke_report = False
smoke_pins = [14, 15]
smoke_report_duration = 20

# fire detect config
enable_fire_report = True
fire_pins = [23, 24]
fire_report_duration = 25

enable_human_report = True
human_pins = [5]
human_report_duration = 30   # unit : second
camera_resolution = (640,480)
image_upload_url = 'http://xxx.xxx.xxx.xxx/human'

card_name = 'bottle'

enable_adv_play = True
adv_dir = '/media/pi/VOL/adv/'

enable_screen_interface = False
all_box_name_cn = ['瓶子', '纸']
all_box_name = ['bottle', 'paper']
qr_url = 'http://xxx.xxx.xxx.xxx/qr/'