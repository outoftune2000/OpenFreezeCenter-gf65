#! /usr/bin/python3

import os
import gi
import tempfile
import json
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

EC_IO_FILE = '/sys/kernel/debug/ec/ec0/io'
NOISE_TEXTURE_PATH = os.path.join(tempfile.gettempdir(), "ofc_fbm_noise.png")
NOISE_PROFILE_PATH = os.path.join(os.path.realpath(os.path.dirname(__file__)), "noise_profile.json")
WEBCAM_CONTROL_ADDRESS = 46
WEBCAM_ON_VALUE = 75
WEBCAM_OFF_VALUE = 73
KEYBOARD_BACKLIGHT_ADDRESS = 243
KEYBOARD_BACKLIGHT_MIN_VALUE = 128
KEYBOARD_BACKLIGHT_MAX_VALUE = 131
DEFAULT_NOISE_SETTINGS = {
    "image_width": 220,
    "image_height": 220,
    "frequency": 0.035,
    "num_layers": 5,
    "seed": 1337,
    "blend_mode": "mixed",
    "blur_radius": 2,
    "grain_amount": 0.35,
    "gamma": 1.35,
    "tone_base": 26,
    "tone_range": 0,
    "alpha_base": 0,
    "alpha_range": 36,
}

# Universal EC Byte writing

def write(BYTE, VALUE):
    with open(EC_IO_FILE,'w+b') as file:
        file.seek(BYTE)
        file.write(bytes((VALUE,)))

# Universal EC Byte reading

def read(BYTE, SIZE, FORMAT):
    with open(EC_IO_FILE,'r+b') as file:
        file.seek(BYTE)
        if SIZE == 1 and FORMAT == 0:
            VALUE = int(file.read(1).hex(),16)
        elif SIZE == 1 and FORMAT == 1:
            VALUE = file.read(1).hex()
        elif SIZE == 2 and FORMAT == 0:
            VALUE = int(file.read(2).hex(),16)
        elif SIZE == 2 and FORMAT == 1:
            VALUE = file.read(2).hex()
    return VALUE

def fan_profile(PROFILE, ONOFF, ADDRESS = 0, SPEED = 0):
    # Setting up fan profiles
    if PROFILE != 4:
        write(ONOFF[0][0], ONOFF[0][1])      # Cooler Booster fan curve off
        write(ONOFF[1][0], ONOFF[1][1])      # Auto/Adv/Basic/ fan curve on
        for CPU_GPU_ROWS in range (0, 2):
            for FAN_SPEEDS in range (0, 7):
                write(ADDRESS[CPU_GPU_ROWS][FAN_SPEEDS], SPEED[CPU_GPU_ROWS][FAN_SPEEDS])
    else:
        write(ONOFF[0], ONOFF[1])      # Cooler Booster fan curve on/off

#   PROFILE                      = 1 or 2 or 3 or 4
#	AUTO_SPEED                   = [[CPU1, CPU2, CPU3, CPU4, CPU5, CPU6, CPU7], [GPU1, GPU2, GPU3, GPU4, GPU5, GPU6, GPU7]]
#	ADV_SPEED                    = [[CPU1, CPU2, CPU3, CPU4, CPU5, CPU6, CPU7], [GPU1, GPU2, GPU3, GPU4, GPU5, GPU6, GPU7]]
#   BASIC_OFFSET                 = Value between -30 to +30
#	CPU                          = 1 if CPU is 11th gen and above || 0 if CPU is 10th gen or below
#	AUTO_ADV_VALUES              = [FAN PROFILE ADDRESS, AUTO VALUE, ADVANCED VALUE]
#	COOLER_BOOSTER_OFF_ON_VALUES = [COOLER BOOSTER ADDRESS, COOLER BOOSTER OFF VALUE, COOLER BOOSTER ON VALUE]
#	CPU_GPU_FAN_SPEED_ADDRESS    = [[CPU1, CPU2, CPU3, CPU4, CPU5, CPU6, CPU7], [GPU1, GPU2, GPU3, GPU4, GPU5, GPU6, GPU7]]
#	CPU_GPU_TEMP_ADDRESS         = [CPU CURRENT TEMP ADDRESS, GPU CURRENT TEMP ADDRESS]
#	CPU_GPU_RPM_ADDRESS          = [CPU FAN RPM ADDRESS, GPU FAN RPM ADDRESS]
#   BATTERY_THRESHOLD_VALUE      = 50 to 100

MIN_MAX = [100, 0, 100, 0]
BASIC_SPEED = [[0, 0, 0, 0, 0, 0, 0],[0, 0, 0, 0, 0, 0, 0]]

def create_dialog(TITLE, TEXT, YES, NO, x, y, RESPONSE_TYPE):
	dialog = Gtk.Dialog(title = TITLE)
	dialog.set_default_size(x, y)
	if RESPONSE_TYPE == 1:
		dialog.add_button("Yes", Gtk.ResponseType.YES)
		dialog.add_button("No", Gtk.ResponseType.NO)
	elif RESPONSE_TYPE == 2:
		dialog.add_button("Yes", Gtk.ResponseType.OK)
		dialog.add_button("No", Gtk.ResponseType.CANCEL)
	else:
		dialog.add_button("Yes", Gtk.ResponseType.OK)
	label = Gtk.Label(TEXT)
	dialog.vbox.add(label)
	label.show()

	response = dialog.run()
	if RESPONSE_TYPE == 1:
		if response == Gtk.ResponseType.YES: LINE = YES
		elif response == Gtk.ResponseType.NO: LINE = NO
	elif RESPONSE_TYPE == 2:
		if response == Gtk.ResponseType.OK: os.system("shutdown -r +1")
		elif response == Gtk.ResponseType.CANCEL: create_dialog("Warning", "The Application will not be able to perform EC Read/Write for changing Fan profiles and Monitoring!", "", "", 200, 150, 3)

	dialog.show_all()
	dialog.destroy()
	return LINE

################################################################
# Setting the config.py file where all the data will be stored #
################################################################

PATH_TO_CONFIG = str(os.path.realpath(os.path.dirname(__file__))) + "/config.py"
try:
	open(PATH_TO_CONFIG, "r")
except FileNotFoundError:
	CONFIG = []
	CHOICE = "\nIf you want universal auto fan profile which is as below then [SELECT YES]\n\tAUTO SPEEDS = [[0, 40, 48, 56, 64, 72, 80], [0, 48, 56, 64, 72, 79, 86]]\n\nIf you want to fetch vendor specified auto fan profile which will require you to \n\t1 :- Close this(Before closing read all the steps)\n\t2 :- boot into windows\n\t3 :- set the fan profile to auto\n\t4 :- boot back to linux and then [SELECT NO]"
	LINE_YES = "PROFILE = 1\nAUTO_SPEED = [[0, 40, 48, 56, 64, 72, 80], [0, 48, 56, 64, 72, 79, 86]]"
	LINE_NO = "PROFILE = 1\nAUTO_SPEED = [["+str(read(0x72, 1, 0))+", "+str(read(0x73, 1, 0))+", "+str(read(0x74, 1, 0))+", "+str(read(0x75, 1, 0))+", "+str(read(0x76, 1, 0))+", "+str(read(0x77, 1, 0))+", "+str(read(0x78, 1, 0))+"], ["+str(read(0x8a, 1, 0))+", "+str(read(0x8b, 1, 0))+", "+str(read(0x8c, 1, 0))+", "+str(read(0x8d, 1, 0))+", "+str(read(0x8e, 1, 0))+", "+str(read(0x8f, 1, 0))+", "+str(read(0x90, 1, 0))+"]]"
	CONFIG.append(create_dialog("Auto Profile Selection", CHOICE, LINE_YES, LINE_NO, 300, 150, 1))

	CHOICE = "\nIs your CPU intel 10th Gen and above\n"
	LINE_YES = "\nADV_SPEED =  [[0, 40, 48, 56, 64, 72, 80], [0, 48, 56, 64, 72, 79, 86]] # Edit this list for ADVANCED FAN SPEEDS first the CPU speeds the GPU speeds\nBASIC_OFFSET = 0 # Edit this for a offset of fan speeds from AUTO SPEEDS from -30 to 30\nCPU = 1\nAUTO_ADV_VALUES = [0xd4, 13, 141]\nCOOLER_BOOSTER_OFF_ON_VALUES = [0x98, 2, 130]\nCPU_GPU_FAN_SPEED_ADDRESS = [[0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78], [0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f, 0x90]]\nCPU_GPU_TEMP_ADDRESS = [0x68, 0x80]\nCPU_GPU_RPM_ADDRESS = [0xc8, 0xca]\nBATTERY_THRESHOLD_VALUE = 100 # Edit this value from between 50 to 100 for the percentage your battery will charge upto"
	LINE_NO =  "\nADV_SPEED =  [[0, 40, 48, 56, 64, 72, 80], [0, 48, 56, 64, 72, 79, 86]] # Edit this list for ADVANCED FAN SPEEDS first the CPU speeds the GPU speeds\nBASIC_OFFSET = 0 # Edit this for a offset of fan speeds from AUTO SPEEDS from -30 to 30\nCPU = 0\nAUTO_ADV_VALUES = [0xf4, 12, 140]\nCOOLER_BOOSTER_OFF_ON_VALUES = [0x98, 0, 128]\nCPU_GPU_FAN_SPEED_ADDRESS = [[0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78], [0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f, 0x90]]\nCPU_GPU_TEMP_ADDRESS = [0x68, 0x80]\nCPU_GPU_RPM_ADDRESS = [0xc8, 0xca]\nBATTERY_THRESHOLD_VALUE = 100 # Edit this value from between 50 to 100 for the percentage your battery will charge upto"
	CONFIG.append(create_dialog("CPU Gen Selection", CHOICE, LINE_YES, LINE_NO, 300, 50, 1))

	CONFIG_FILE = open(PATH_TO_CONFIG, "w")
	CONFIG_FILE.writelines(CONFIG)
	CONFIG_FILE.close()
finally:
	import config

##########################
# Writing config.py file #
##########################

def config_writer():
    CONFIG = ""
    CONFIG_FILE = open(PATH_TO_CONFIG, "r")
    CONFIG = CONFIG_FILE.read()
    CONFIG_FILE.close()

    CONFIG = ("PROFILE = " + str(config.PROFILE))
    CONFIG = CONFIG + ("\nAUTO_SPEED = " + str(config.AUTO_SPEED))
    CONFIG = CONFIG + ("\nADV_SPEED = " + str(config.ADV_SPEED))
    CONFIG = CONFIG + ("\nBASIC_OFFSET = " + str(config.BASIC_OFFSET))
    CONFIG = CONFIG + ("\nCPU = " + str(config.CPU))
    CONFIG = CONFIG + ("\nAUTO_ADV_VALUES = " + str(config.AUTO_ADV_VALUES))
    CONFIG = CONFIG + ("\nCOOLER_BOOSTER_OFF_ON_VALUES = " + str(config.COOLER_BOOSTER_OFF_ON_VALUES))
    CONFIG = CONFIG + ("\nCPU_GPU_FAN_SPEED_ADDRESS = " + str(config.CPU_GPU_FAN_SPEED_ADDRESS))
    CONFIG = CONFIG + ("\nCPU_GPU_TEMP_ADDRESS = " + str(config.CPU_GPU_TEMP_ADDRESS))
    CONFIG = CONFIG + ("\nCPU_GPU_RPM_ADDRESS = " + str(config.CPU_GPU_RPM_ADDRESS))
    CONFIG = CONFIG + ("\nBATTERY_THRESHOLD_VALUE = " + str(config.BATTERY_THRESHOLD_VALUE))

    CONFIG_FILE = open(PATH_TO_CONFIG, "w")
    CONFIG_FILE.writelines(CONFIG)
    CONFIG_FILE.close()

#########################################
# chekcing fan speeds are within limits #
#########################################

def speed_checker(SPEEDS, OFFSET):
	for ROW in range(0, 2):
		for COLUMN in range(0, 7):
			SPEEDS[ROW][COLUMN] = 0 if (SPEEDS[ROW][COLUMN] + OFFSET < 0) else 150 if (SPEEDS[ROW][COLUMN] + OFFSET > 150) else SPEEDS[ROW][COLUMN] + OFFSET
	return SPEEDS

#############################################
# Below functions are part of GUI designing #
#############################################

def profile_selection(combobox):
    profile = combobox.get_active_text()
    if profile is None:
        return

    if profile == "Auto":
        config.PROFILE = 1
        config_writer()
        fan_profile(
            1,
            [
                [config.AUTO_ADV_VALUES[0], config.AUTO_ADV_VALUES[1]],
                [config.COOLER_BOOSTER_OFF_ON_VALUES[0], config.COOLER_BOOSTER_OFF_ON_VALUES[1]],
            ],
            config.CPU_GPU_FAN_SPEED_ADDRESS,
            speed_checker(config.AUTO_SPEED, 0),
        )
    elif profile == "Basic":
        config.PROFILE = 2
        config_writer()
        fan_profile(
            2,
            [
                [config.AUTO_ADV_VALUES[0], config.AUTO_ADV_VALUES[2]],
                [config.COOLER_BOOSTER_OFF_ON_VALUES[0], config.COOLER_BOOSTER_OFF_ON_VALUES[1]],
            ],
            config.CPU_GPU_FAN_SPEED_ADDRESS,
            speed_checker(
                BASIC_SPEED,
                30 if (config.BASIC_OFFSET > 30) else -30 if (config.BASIC_OFFSET < -30) else config.BASIC_OFFSET,
            ),
        )
    elif profile == "Advanced":
        config.PROFILE = 3
        config_writer()
        fan_profile(
            3,
            [
                [config.AUTO_ADV_VALUES[0], config.AUTO_ADV_VALUES[2]],
                [config.COOLER_BOOSTER_OFF_ON_VALUES[0], config.COOLER_BOOSTER_OFF_ON_VALUES[1]],
            ],
            config.CPU_GPU_FAN_SPEED_ADDRESS,
            speed_checker(config.ADV_SPEED, 0),
        )
    elif profile == "Cooler Booster":
        config.PROFILE = 4
        config_writer()
        fan_profile(4, [config.COOLER_BOOSTER_OFF_ON_VALUES[0], config.COOLER_BOOSTER_OFF_ON_VALUES[2]])

def bct_selection(combobox):
    value = combobox.get_active_text()
    if value is None:
        return
    config.BATTERY_THRESHOLD_VALUE = int(value)
    write(0xe4, config.BATTERY_THRESHOLD_VALUE + 128)
    config_writer()

def read_webcam_state():
    try:
        webcam_value = read(WEBCAM_CONTROL_ADDRESS, 1, 0)
    except (OSError, ValueError):
        return False
    return webcam_value == WEBCAM_ON_VALUE

def write_webcam_state(enabled):
    write(WEBCAM_CONTROL_ADDRESS, WEBCAM_ON_VALUE if enabled else WEBCAM_OFF_VALUE)

def clamp_keyboard_backlight_value(value):
    try:
        numeric_value = int(value)
    except (TypeError, ValueError):
        numeric_value = KEYBOARD_BACKLIGHT_MIN_VALUE
    return max(KEYBOARD_BACKLIGHT_MIN_VALUE, min(KEYBOARD_BACKLIGHT_MAX_VALUE, numeric_value))

def read_keyboard_backlight_value():
    try:
        backlight_value = read(KEYBOARD_BACKLIGHT_ADDRESS, 1, 0)
    except (OSError, ValueError):
        return KEYBOARD_BACKLIGHT_MIN_VALUE
    return clamp_keyboard_backlight_value(backlight_value)

def write_keyboard_backlight_value(value):
    write(KEYBOARD_BACKLIGHT_ADDRESS, clamp_keyboard_backlight_value(value))

def clamp_noise_settings(raw_settings):
    settings = dict(DEFAULT_NOISE_SETTINGS)
    if isinstance(raw_settings, dict):
        settings.update(raw_settings)

    def as_int(name):
        try:
            return int(settings[name])
        except (TypeError, ValueError):
            return int(DEFAULT_NOISE_SETTINGS[name])

    def as_float(name):
        try:
            return float(settings[name])
        except (TypeError, ValueError):
            return float(DEFAULT_NOISE_SETTINGS[name])

    settings["image_width"] = max(64, min(1024, as_int("image_width")))
    settings["image_height"] = max(64, min(1024, as_int("image_height")))
    settings["frequency"] = max(0.001, min(1.0, as_float("frequency")))
    settings["num_layers"] = max(1, min(8, as_int("num_layers")))
    settings["seed"] = max(0, min(2147483647, as_int("seed")))
    blend_mode = str(settings.get("blend_mode", DEFAULT_NOISE_SETTINGS["blend_mode"])).strip().lower()
    settings["blend_mode"] = blend_mode if blend_mode in ("mixed", "burn", "add") else DEFAULT_NOISE_SETTINGS["blend_mode"]
    settings["blur_radius"] = max(0, min(8, as_int("blur_radius")))
    settings["grain_amount"] = max(0.0, min(1.0, as_float("grain_amount")))
    settings["gamma"] = max(0.1, min(3.0, as_float("gamma")))
    settings["tone_base"] = max(0, min(255, as_int("tone_base")))
    settings["tone_range"] = max(0, min(255, as_int("tone_range")))
    settings["alpha_base"] = max(0, min(255, as_int("alpha_base")))
    settings["alpha_range"] = max(0, min(255, as_int("alpha_range")))
    return settings

def load_noise_settings():
    try:
        with open(NOISE_PROFILE_PATH, "r", encoding="utf-8") as profile_file:
            loaded = json.load(profile_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
        loaded = {}
    return clamp_noise_settings(loaded)

def generate_fractal_noise_texture(
    texture_path,
    image_width=220,
    image_height=220,
    frequency=0.035,
    num_layers=5,
    seed=1337,
    blend_mode="mixed",
    blur_radius=2,
    grain_amount=0.35,
    gamma=1.35,
    tone_base=26,
    tone_range=0,
    alpha_base=0,
    alpha_range=36,
):
    # Runtime fallback: if cairo is unavailable, skip texture generation.
    try:
        import cairo
    except Exception:
        return None

    def hash_noise(x, y, local_seed):
        n = (x * 374761393 + y * 668265263 + local_seed * 69069) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        n = n ^ (n >> 16)
        return n / 4294967295.0

    def lerp(a, b, t):
        return a + (b - a) * t

    def smooth(t):
        return t * t * (3.0 - 2.0 * t)

    def value_noise(x, y, local_seed):
        x0 = int(x)
        y0 = int(y)
        x1 = x0 + 1
        y1 = y0 + 1

        tx = x - x0
        ty = y - y0
        sx = smooth(tx)
        sy = smooth(ty)

        n00 = hash_noise(x0, y0, local_seed)
        n10 = hash_noise(x1, y0, local_seed)
        n01 = hash_noise(x0, y1, local_seed)
        n11 = hash_noise(x1, y1, local_seed)

        ix0 = lerp(n00, n10, sx)
        ix1 = lerp(n01, n11, sx)
        return (lerp(ix0, ix1, sy) * 2.0) - 1.0

    def box_blur(src, width, height, radius):
        if radius <= 0:
            return src[:]

        window = (radius * 2) + 1
        temp = [0.0] * (width * height)
        out = [0.0] * (width * height)

        for y in range(height):
            row = y * width
            window_sum = 0.0
            for k in range(-radius, radius + 1):
                cx = 0 if k < 0 else (width - 1 if k >= width else k)
                window_sum += src[row + cx]

            for x in range(width):
                temp[row + x] = window_sum / window
                left = x - radius
                right = x + radius + 1
                left_c = 0 if left < 0 else (width - 1 if left >= width else left)
                right_c = 0 if right < 0 else (width - 1 if right >= width else right)
                window_sum += src[row + right_c] - src[row + left_c]

        for x in range(width):
            window_sum = 0.0
            for k in range(-radius, radius + 1):
                cy = 0 if k < 0 else (height - 1 if k >= height else k)
                window_sum += temp[(cy * width) + x]

            for y in range(height):
                out[(y * width) + x] = window_sum / window
                top = y - radius
                bottom = y + radius + 1
                top_c = 0 if top < 0 else (height - 1 if top >= height else top)
                bottom_c = 0 if bottom < 0 else (height - 1 if bottom >= height else bottom)
                window_sum += temp[(bottom_c * width) + x] - temp[(top_c * width) + x]

        return out

    values = [0.0] * (image_width * image_height)
    min_noise_val = float("inf")
    max_noise_val = float("-inf")

    for j in range(image_height):
        for i in range(image_width):
            p_noise_x = i * frequency
            p_noise_y = j * frequency
            amplitude = 1.0
            value = 0.0
            amp_sum = 0.0

            # Fractal sum: multiple octaves with halved amplitude and doubled frequency.
            for layer in range(num_layers):
                value += value_noise(p_noise_x, p_noise_y, seed + (layer * 97)) * amplitude
                amp_sum += amplitude
                p_noise_x *= 2.0
                p_noise_y *= 2.0
                amplitude *= 0.5

            index = j * image_width + i
            values[index] = value / amp_sum
            if values[index] > max_noise_val:
                max_noise_val = values[index]
            if values[index] < min_noise_val:
                min_noise_val = values[index]

    normalized_map = [0.0] * (image_width * image_height)
    noise_range = max_noise_val - min_noise_val
    if noise_range < 1e-9:
        noise_range = 1.0
    for idx, value in enumerate(values):
        normalized_map[idx] = (value - min_noise_val) / noise_range

    blurred_map = box_blur(normalized_map, image_width, image_height, blur_radius)
    data = bytearray(image_width * image_height * 4)

    mode = str(blend_mode).strip().lower()
    if mode not in ("mixed", "burn", "add"):
        mode = "mixed"

    for idx, value in enumerate(normalized_map):
        blurred = blurred_map[idx]
        blended = blurred + ((value - blurred) * grain_amount)
        blended = max(0.0, min(1.0, blended))
        centered = (blended - 0.5) * 2.0
        strength = abs(centered) ** gamma

        if mode == "burn":
            noise_metric = ((1.0 - blended) ** gamma)
        elif mode == "add":
            noise_metric = blended ** gamma
        else:
            noise_metric = strength

        # Noise controls opacity only; color stays constant to avoid milky wash.
        grain_metric = max(0.0, min(1.0, (noise_metric - 0.32) / 0.68))
        tone = int(max(0, min(64, tone_base + tone_range)))
        alpha = int(max(0, min(255, alpha_base + (grain_metric * alpha_range))))

        offset = idx * 4
        data[offset] = tone
        data[offset + 1] = tone
        data[offset + 2] = tone
        data[offset + 3] = alpha

    try:
        surface = cairo.ImageSurface.create_for_data(data, cairo.FORMAT_ARGB32, image_width, image_height, image_width * 4)
        surface.mark_dirty()
        surface.write_to_png(texture_path)
        return texture_path
    except Exception:
        return None

def apply_class(widget, class_name):
    widget.get_style_context().add_class(class_name)

def make_label(text, class_name="", xalign=0.0):
    label = Gtk.Label(label=text)
    label.set_xalign(xalign)
    label.set_halign(Gtk.Align.FILL)
    if class_name:
        apply_class(label, class_name)
    return label

def set_metric_value(label, value):
    label.set_text(value)

def update_label():
    CPU_TEMP = read(config.CPU_GPU_TEMP_ADDRESS[0], 1, 0)
    GPU_TEMP = read(config.CPU_GPU_TEMP_ADDRESS[1], 1, 0)
    try:
        CPU_FAN_RPM = 478000 // read(config.CPU_GPU_RPM_ADDRESS[0], 2, 0)
    except ZeroDivisionError:
        CPU_FAN_RPM = 0
    try:
        GPU_FAN_RPM = 478000 // read(config.CPU_GPU_RPM_ADDRESS[1], 2, 0)
    except ZeroDivisionError:
        GPU_FAN_RPM = 0

    set_metric_value(parent_window.CPU_CURR_TEMP, str(CPU_TEMP) + " C")
    if MIN_MAX[0] > CPU_TEMP:
        MIN_MAX[0] = CPU_TEMP
    if MIN_MAX[1] < CPU_TEMP:
        MIN_MAX[1] = CPU_TEMP
    set_metric_value(parent_window.CPU_MIN_TEMP, str(MIN_MAX[0]) + " C")
    set_metric_value(parent_window.CPU_MAX_TEMP, str(MIN_MAX[1]) + " C")

    set_metric_value(parent_window.GPU_CURR_TEMP, str(GPU_TEMP) + " C")
    if MIN_MAX[2] > GPU_TEMP:
        MIN_MAX[2] = GPU_TEMP
    if MIN_MAX[3] < GPU_TEMP:
        MIN_MAX[3] = GPU_TEMP
    set_metric_value(parent_window.GPU_MIN_TEMP, str(MIN_MAX[2]) + " C")
    set_metric_value(parent_window.GPU_MAX_TEMP, str(MIN_MAX[3]) + " C")

    set_metric_value(parent_window.CPU_FAN_RPM, str(CPU_FAN_RPM) + " RPM")
    set_metric_value(parent_window.GPU_FAN_RPM, str(GPU_FAN_RPM) + " RPM")
    return True

class ParentWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Open Freeze Center (OFC)")
        self.set_default_size(780, 470)
        self.set_name("root-window")
        self.set_border_width(18)

        settings = Gtk.Settings.get_default()
        if settings is not None:
            settings.set_property("gtk-application-prefer-dark-theme", True)

        self._apply_css()

        screen = self.get_screen()
        visual = screen.get_rgba_visual() if screen is not None else None
        if visual is not None and screen.is_composited():
            self.set_visual(visual)

        self.main_shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        apply_class(self.main_shell, "app-shell")
        self.add(self.main_shell)
        self._reveal_sequence = []
        self._syncing_webcam_switch = False
        self._syncing_backlight_slider = False

        self._build_header()
        self._build_profile_panel()
        self._build_metrics_panel()
        self._build_battery_panel()
        self._build_webcam_panel()
        self._build_keyboard_backlight_panel()
        self._start_intro_animation()

        self.set_glass_mode(False)
        GLib.timeout_add(500, update_label)

    def _apply_css(self):
        noise_settings = load_noise_settings()
        noise_texture = generate_fractal_noise_texture(NOISE_TEXTURE_PATH, **noise_settings)
        noise_layer = "none"
        if noise_texture:
            noise_layer = 'url("' + noise_texture + '")'
        noise_size = str(noise_settings["image_width"]) + "px " + str(noise_settings["image_height"]) + "px"

        css_data = """
            #root-window {
                background-image: none;
                background-color: rgba(0, 0, 0, 0.44);
            }

            #root-window.glass-enabled {
                background-image: none;
                background-color: rgba(26, 52, 94, 0.16);
            }

            .app-shell {
                background-image:
                    __NOISE_LAYER__,
                    linear-gradient(160deg, rgba(255, 255, 255, 0.018), rgba(255, 255, 255, 0.00)),
                    linear-gradient(180deg, rgba(0, 0, 0, 0.24), rgba(0, 0, 0, 0.08));
                background-size:
                    __NOISE_SIZE__,
                    auto,
                    auto;
                background-repeat:
                    repeat,
                    no-repeat,
                    no-repeat;
                background-color: rgba(1, 4, 9, 0.82);
                border-radius: 24px;
                border: 1px solid rgba(92, 122, 172, 0.48);
                box-shadow:
                    0 34px 78px rgba(0, 0, 0, 0.84),
                    inset 0 0 0 1px rgba(180, 207, 246, 0.06),
                    inset 0 -22px 30px rgba(0, 0, 0, 0.36);
                padding: 22px;
            }

            .app-shell.glass {
                background-image: linear-gradient(145deg, rgba(165, 204, 255, 0.22), rgba(104, 158, 240, 0.08));
                background-color: rgba(34, 68, 112, 0.28);
                border: 1px solid rgba(184, 218, 255, 0.34);
                box-shadow: 0 20px 48px rgba(8, 20, 36, 0.36), inset 0 0 0 1px rgba(225, 238, 255, 0.11);
            }

            .heading {
                color: #ecf5ff;
                font-size: 24px;
                font-weight: 700;
            }

            .subheading {
                color: rgba(204, 217, 235, 0.9);
                font-size: 12px;
                font-weight: 500;
            }

            .toggle-label {
                color: #dce6fa;
                font-size: 12px;
                font-weight: 600;
            }

            .mode-symbol {
                color: #dce8ff;
                font-size: 18px;
                font-weight: 700;
                margin-right: 2px;
            }

            .toggle-pill {
                background-color: rgba(255, 255, 255, 0.09);
                border: 1px solid rgba(132, 161, 214, 0.34);
                border-radius: 999px;
                padding: 4px 10px;
            }

            .app-shell.glass .toggle-pill {
                background-color: rgba(139, 190, 255, 0.14);
                border: 1px solid rgba(206, 228, 255, 0.30);
            }

            .panel {
                background-image:
                    __NOISE_LAYER__,
                    linear-gradient(160deg, rgba(255, 255, 255, 0.015), rgba(255, 255, 255, 0.00));
                background-size:
                    __NOISE_SIZE__,
                    auto;
                background-repeat:
                    repeat,
                    no-repeat;
                background-color: rgba(6, 10, 16, 0.58);
                border-radius: 16px;
                border: 1px solid rgba(101, 128, 178, 0.26);
                padding: 14px;
                transition: 180ms ease;
            }

            .panel:hover {
                background-color: rgba(10, 16, 24, 0.66);
                border: 1px solid rgba(156, 186, 236, 0.28);
            }

            .app-shell.glass .panel {
                background-color: rgba(124, 182, 255, 0.11);
                border: 1px solid rgba(212, 231, 255, 0.24);
            }

            .panel-title {
                color: #f0f6ff;
                font-size: 14px;
                font-weight: 700;
            }

            .table-header {
                color: rgba(171, 188, 214, 0.95);
                font-size: 12px;
                font-weight: 600;
                margin-bottom: 8px;
            }

            .table-key {
                color: #d6e4ff;
                font-size: 13px;
                font-weight: 700;
            }

            .metric-value {
                color: #f9fcff;
                font-size: 13px;
                font-weight: 600;
                letter-spacing: 0.2px;
            }

            combobox,
            combobox button {
                color: #f0f7ff;
                background-image: none;
                background-color: rgba(10, 20, 35, 0.64);
                border-radius: 10px;
                border: 1px solid rgba(135, 166, 217, 0.38);
                padding: 6px 10px;
            }

            .app-shell.glass combobox,
            .app-shell.glass combobox button {
                background-color: rgba(82, 130, 200, 0.26);
                border: 1px solid rgba(205, 225, 255, 0.28);
            }

            switch {
                min-height: 24px;
                min-width: 52px;
                padding: 2px;
                border-radius: 999px;
                border: 1px solid rgba(120, 145, 188, 0.45);
                background-color: rgba(16, 28, 44, 0.95);
                transition: 140ms ease;
            }

            switch:checked {
                border: 1px solid rgba(146, 219, 255, 0.75);
                background-image: linear-gradient(120deg, #2e9fff 0%, #36d1ff 100%);
            }

            switch slider {
                min-width: 20px;
                min-height: 20px;
                border-radius: 999px;
                background-color: #dce8ff;
                border: 1px solid rgba(132, 153, 196, 0.70);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.55);
                transition: 120ms ease;
            }

            switch:checked slider {
                background-color: #f4fcff;
                border: 1px solid rgba(170, 239, 255, 0.95);
            }
        """
        css_data = css_data.replace("__NOISE_LAYER__", noise_layer)
        css_data = css_data.replace("__NOISE_SIZE__", noise_size)
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css_data.encode())
        screen = Gdk.Screen.get_default()
        if screen is not None:
            Gtk.StyleContext.add_provider_for_screen(
                screen,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    def _build_header(self):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        header.set_hexpand(True)

        title_group = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_group.pack_start(make_label("Open Freeze Center", "heading"), False, False, 0)
        title_group.pack_start(make_label("Hardware controls with live thermal telemetry", "subheading"), False, False, 0)

        glass_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        apply_class(glass_controls, "toggle-pill")
        glass_controls.set_halign(Gtk.Align.END)
        self.mode_symbol = make_label("☾", "mode-symbol", 0.5)
        glass_controls.pack_start(self.mode_symbol, False, False, 0)

        self.glass_switch = Gtk.Switch()
        self.glass_switch.connect("notify::active", self._toggle_glass_mode)
        glass_controls.pack_start(self.glass_switch, False, False, 0)

        header.pack_start(title_group, True, True, 0)
        header.pack_end(glass_controls, False, False, 0)

        self.main_shell.pack_start(header, False, False, 0)

    def _build_profile_panel(self):
        panel = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        apply_class(panel, "panel")

        panel.pack_start(make_label("Fan Profile", "panel-title"), False, False, 0)

        self.profile_selector = Gtk.ComboBoxText()
        for profile in ["Auto", "Basic", "Advanced", "Cooler Booster"]:
            self.profile_selector.append_text(profile)
        self.profile_selector.set_active(max(0, min(3, config.PROFILE - 1)))
        self.profile_selector.connect("changed", profile_selection)
        panel.pack_end(self.profile_selector, False, False, 0)

        self._pack_with_revealer(panel, 80, Gtk.RevealerTransitionType.SLIDE_DOWN)

    def _build_metrics_panel(self):
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        apply_class(panel, "panel")
        panel.pack_start(make_label("Live Metrics", "panel-title"), False, False, 0)

        metrics_grid = Gtk.Grid()
        metrics_grid.set_column_spacing(18)
        metrics_grid.set_row_spacing(10)
        metrics_grid.set_hexpand(True)
        metrics_grid.attach(make_label("COMPONENT", "table-header"), 0, 0, 1, 1)
        metrics_grid.attach(make_label("CURRENT", "table-header"), 1, 0, 1, 1)
        metrics_grid.attach(make_label("MIN", "table-header"), 2, 0, 1, 1)
        metrics_grid.attach(make_label("MAX", "table-header"), 3, 0, 1, 1)
        metrics_grid.attach(make_label("FAN RPM", "table-header"), 4, 0, 1, 1)

        metrics_grid.attach(make_label("CPU", "table-key"), 0, 1, 1, 1)
        self.CPU_CURR_TEMP = make_label("--", "metric-value")
        self.CPU_MIN_TEMP = make_label("--", "metric-value")
        self.CPU_MAX_TEMP = make_label("--", "metric-value")
        self.CPU_FAN_RPM = make_label("--", "metric-value")
        metrics_grid.attach(self.CPU_CURR_TEMP, 1, 1, 1, 1)
        metrics_grid.attach(self.CPU_MIN_TEMP, 2, 1, 1, 1)
        metrics_grid.attach(self.CPU_MAX_TEMP, 3, 1, 1, 1)
        metrics_grid.attach(self.CPU_FAN_RPM, 4, 1, 1, 1)

        metrics_grid.attach(make_label("GPU", "table-key"), 0, 2, 1, 1)
        self.GPU_CURR_TEMP = make_label("--", "metric-value")
        self.GPU_MIN_TEMP = make_label("--", "metric-value")
        self.GPU_MAX_TEMP = make_label("--", "metric-value")
        self.GPU_FAN_RPM = make_label("--", "metric-value")
        metrics_grid.attach(self.GPU_CURR_TEMP, 1, 2, 1, 1)
        metrics_grid.attach(self.GPU_MIN_TEMP, 2, 2, 1, 1)
        metrics_grid.attach(self.GPU_MAX_TEMP, 3, 2, 1, 1)
        metrics_grid.attach(self.GPU_FAN_RPM, 4, 2, 1, 1)

        panel.pack_start(metrics_grid, False, False, 0)
        self._pack_with_revealer(panel, 150, Gtk.RevealerTransitionType.CROSSFADE, expand=True, fill=True)

    def _build_battery_panel(self):
        panel = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        apply_class(panel, "panel")
        panel.pack_start(make_label("Battery Charge Threshold", "panel-title"), False, False, 0)

        self.bct_selector = Gtk.ComboBoxText()
        for value in range(50, 101, 5):
            self.bct_selector.append_text(str(value))
        selected_index = max(0, min(10, (config.BATTERY_THRESHOLD_VALUE - 50) // 5))
        self.bct_selector.set_active(selected_index)
        self.bct_selector.connect("changed", bct_selection)
        panel.pack_end(self.bct_selector, False, False, 0)

        self._pack_with_revealer(panel, 230, Gtk.RevealerTransitionType.SLIDE_UP)

    def _build_webcam_panel(self):
        panel = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        apply_class(panel, "panel")
        panel.pack_start(make_label("Webcam", "panel-title"), False, False, 0)

        self.webcam_switch = Gtk.Switch()
        self.webcam_switch.connect("notify::active", self._on_webcam_switch_changed)
        self._set_webcam_switch_state(read_webcam_state())
        panel.pack_end(self.webcam_switch, False, False, 0)

        self._pack_with_revealer(panel, 290, Gtk.RevealerTransitionType.SLIDE_UP)

    def _build_keyboard_backlight_panel(self):
        panel = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        apply_class(panel, "panel")
        panel.pack_start(make_label("Keyboard Backlight", "panel-title"), False, False, 0)

        slider_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        slider_box.set_hexpand(True)
        panel.pack_end(slider_box, True, True, 0)

        self.backlight_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            KEYBOARD_BACKLIGHT_MIN_VALUE,
            KEYBOARD_BACKLIGHT_MAX_VALUE,
            1,
        )
        self.backlight_scale.set_digits(0)
        self.backlight_scale.set_draw_value(False)
        self.backlight_scale.set_hexpand(True)
        self.backlight_scale.add_mark(128, Gtk.PositionType.BOTTOM, "Off")
        self.backlight_scale.add_mark(129, Gtk.PositionType.BOTTOM, "Low")
        self.backlight_scale.add_mark(130, Gtk.PositionType.BOTTOM, "Med")
        self.backlight_scale.add_mark(131, Gtk.PositionType.BOTTOM, "Max")
        self.backlight_scale.connect("value-changed", self._on_backlight_slider_changed)
        slider_box.pack_start(self.backlight_scale, True, True, 0)

        self._set_backlight_slider_value(read_keyboard_backlight_value())
        self._pack_with_revealer(panel, 350, Gtk.RevealerTransitionType.SLIDE_UP)

    def _set_webcam_switch_state(self, enabled):
        self._syncing_webcam_switch = True
        try:
            self.webcam_switch.set_active(enabled)
        finally:
            self._syncing_webcam_switch = False

    def _set_backlight_slider_value(self, value):
        self._syncing_backlight_slider = True
        try:
            clamped_value = clamp_keyboard_backlight_value(value)
            self.backlight_scale.set_value(clamped_value)
        finally:
            self._syncing_backlight_slider = False

    def _on_webcam_switch_changed(self, switch, _):
        if self._syncing_webcam_switch:
            return
        try:
            write_webcam_state(switch.get_active())
        except OSError:
            self._set_webcam_switch_state(read_webcam_state())

    def _on_backlight_slider_changed(self, scale):
        if self._syncing_backlight_slider:
            return
        requested_value = int(round(scale.get_value()))
        try:
            write_keyboard_backlight_value(requested_value)
            self._set_backlight_slider_value(requested_value)
        except OSError:
            self._set_backlight_slider_value(read_keyboard_backlight_value())

    def _pack_with_revealer(self, widget, delay_ms, transition_type, expand=False, fill=False):
        revealer = Gtk.Revealer()
        revealer.set_transition_type(transition_type)
        revealer.set_transition_duration(320)
        revealer.set_reveal_child(False)
        revealer.add(widget)
        self.main_shell.pack_start(revealer, expand, fill, 0)
        self._reveal_sequence.append((delay_ms, revealer))

    def _start_intro_animation(self):
        for delay_ms, revealer in self._reveal_sequence:
            GLib.timeout_add(delay_ms, self._reveal_widget, revealer)

    def _reveal_widget(self, revealer):
        revealer.set_reveal_child(True)
        return False

    def _toggle_glass_mode(self, switch, _):
        self.set_glass_mode(switch.get_active())

    def set_glass_mode(self, enabled):
        window_context = self.get_style_context()
        shell_context = self.main_shell.get_style_context()
        if enabled:
            window_context.add_class("glass-enabled")
            shell_context.add_class("glass")
            self.mode_symbol.set_text("☀")
            self.glass_switch.set_tooltip_text("Light / Glass mode")
        else:
            window_context.remove_class("glass-enabled")
            shell_context.remove_class("glass")
            self.mode_symbol.set_text("☾")
            self.glass_switch.set_tooltip_text("Dark mode")

parent_window = ParentWindow()
parent_window.connect("destroy", Gtk.main_quit)
parent_window.show_all()
Gtk.main()
