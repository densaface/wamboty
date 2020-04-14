import logging
import os
import random
random.seed
from datetime import datetime
from time import sleep

from libs.common import find_file, run_command, first, CommandStdErrException, \
    find_template_img, flatten, generate_imei, generate_imsi, generate_phone_num, generate_mac, find_template_all_img

ABSOLUTE_PATH = lambda x: os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), x))

logger = logging.getLogger(__name__)


class TemplateNotFoundException(Exception):
    pass

class NoxDevice(object):
    def __init__(self, code, id, nox: 'NoxController'):
        self.code = code
        self.id = id
        self.nox = nox
        self.__vm_name = None
        self.__info = None
        self.__screenshots_dir = None
        self.__addr_adb = None

    @property
    def name(self):
        if not self.__vm_name:
            name_tag = self.get_vm_properties().get('name_tag')
            if not name_tag:
                name = self.code.replace('_','')
                logger.debug(f'Нет имени для VM, берём имя из кода {self.code} (Получилось имя {name})')
                self.__vm_name = name
            else:
                self.__vm_name = name_tag
        return self.__vm_name

    @property
    def _vm_info(self):
        if not self.__info:
            self.__info = self.nox._get_vm_info(self.id)
        return self.__info

    @property
    def _screenshots_local_dir(self):
        self.__screenshots_dir = 'c:/Users/Denis/Nox_share/ImageShare'
        # if not self.__screenshots_dir:
        #     # Name: 'picture', Host path: 'C:\Users\Art\Pictures\Nox Photo' (machine mapping), writable
        #     for line in self._vm_info.splitlines():
        #         if line.startswith("Name: 'picture'"):
        #             path = line.split('path:')[1]
        #             path = path.split("'")[1]
        #             self.__screenshots_dir = path
        #             logger.debug(f'Нашли директорию скриншотов {path}')
        #             break
        #     else:
        #         raise Exception('Нет пути к скриншотам')
        return self.__screenshots_dir

    @property
    def _adb_address(self):
        if not self.__addr_adb:
            # Name: 'picture', Host path: 'C:\Users\Art\Pictures\Nox Photo' (machine mapping), writable
            for line in self._vm_info.splitlines():
                if 'name = ADB' in line:
                    port = line.split('host port')[1]
                    port = port.split(',')[0]
                    port = port.strip('\r\n\t =')
                    self.__addr_adb = f'127.0.0.1:{port}'
                    logger.debug(f'Нашли порт adb {self.__addr_adb}')
                    break
            else:
                raise Exception('Нет пути к скриншотам')
        return self.__addr_adb

    pictures_nox_path = '/sdcard/Pictures/'

    def adb(self, cmd, timeout=30): # NoxConsole.exe adb <-name:nox_name | -index:nox_index>  -command:
        output = run_command(f'{self.nox.nox_console_exe} adb -name:{self.code} -command:"{cmd}"',
            cwd=f'{self.nox.nox_dir}/bin', timeout=timeout)
        # output = run_command(f'{self.nox.adb_exe} -s {self._adb_address} {parameters}')
        return output

    def get_prop(self, parameters):
        output = run_command(f'{self.nox.nox_console_exe} getprop -name:{self.code} -value:sys.boot_completed',
                             cwd=f'{self.nox.nox_dir}/bin')
        fi = output.find(parameters)
        if fi == -1:
            return ''
        return output[fi: output.find('\r\r', fi)]

    def make_screenshot(self):
        img_name = 'wam_' + datetime.now().strftime("%Y%m%d-%H%M%S") + '.png'
        img_nox_path = os.path.join(self.pictures_nox_path, img_name).replace('\\', '/')
        output = self.adb(f'shell screencap  {img_nox_path}')
        img_local_path = os.path.join(self._screenshots_local_dir, img_name)
        if not os.path.exists(img_local_path):
            raise Exception(f'Скриншот не сделан {img_local_path}')
        return img_local_path

    def clean_screenshots_dir(self):
        logger.debug('Удаляем скриншоты из директории')
        for file in os.listdir(self._screenshots_local_dir):
            if file.lower().endswith('png'):
                file_path = os.path.join(self._screenshots_local_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.debug(str(e))

    def check_cache(self):
        logger.debug('Копируем кеш игры если он отсутствует')
        # for file in os.listdir(self._screenshots_local_dir):
        #     if file.lower().endswith('png'):
        #         file_path = os.path.join(self.pictures_nox_path, file)
        #         try:
        #             if os.path.isfile(file_path):
        #                 os.remove(file_path)
        #         except Exception as e:
        #             logger.debug(str(e))
    def start(self):
        logger.debug(f'Запускаем nox')
        run_command(f'{self.nox.nox_console_exe} launch -name:{self.code}', cwd=f'{self.nox.nox_dir}/bin')
        sleep(20)

    def restart(self):
        logger.debug(f'Запускаем nox')
        attempts = 10
        for ii in range(attempts):
            try:
                run_command(f'{self.nox.nox_console_exe} reboot -name:{self.code}', cwd=f'{self.nox.nox_dir}/bin')
                sleep(20)
                break
            except Exception as e:
                logger.debug(str(e))
                sleep(10)
        if ii == attempts - 1:
            raise Exception('error nox restart')
        sleep(10)

    def wait_loaded(self):
        for ii in range(60):
            logger.debug('Ожидаем загрузки Android')
            try:
                screenshot_path = self.make_screenshot()
                if os.path.isfile(screenshot_path):
                    sleep(5)
                    return True
                if self.is_android_loaded():
                    return True
            except Exception as e:
                logger.debug(str(e))
            sleep(2)
        return False

    def stop(self):
        # logger.debug(f'Останавливаем {self.name}')
        logger.debug(f'Останавливаем nox')
        run_command(f'{self.nox.nox_console_exe} quit -name:{self.code}', cwd=f'{self.nox.nox_dir}/bin')
        sleep(2)

    def get_vm_properties(self):
        values = {}
        out = run_command(f'{self.nox.nox_manager_exe} guestproperty enumerate {self.id}')
        for line in out.splitlines():
            name, value = line.split('value:')
            name = name.split(':')[1]
            name = name.strip('\r\n\t :,')
            value = value.split(',')[0]
            value = value.strip('\r\n\t ')
            values[name] = value
        return values

    def is_android_loaded(self):
        try:
            out = self.get_prop('sys.boot_completed')
        except CommandStdErrException as e:
            if 'error: device not found' in str(e):
                return False
            if 'NoxManage.exe: error: The object is not ready' in str(e):
                return False
            if 'error: device offline' in str(e):
                return False
            raise
        if out.find('[1]') > -1:
            return True
        return False

    def get_all_images(self, *templates, trys=None, threshold=0.65, one_attempt=False, debug=False, delta_coor=20):
        logger.debug(f'Ищем изображения {templates}')

        search_for_files = []
        for template in templates:
            file = template
            if not file.lower().endswith('.png'):
                file = file + '.png'
            if not '/' in file and not '\\' in file:
                file = ABSOLUTE_PATH('images\\' + file)
            search_for_files.append((file, template))

        for ii in range(120):
            screenshot_path = self.make_screenshot()
            for file, template in search_for_files:
                r = find_template_all_img(screenshot_path, file, threshold, debug=debug, delta_coor=delta_coor)
                if r:
                    logger.debug(f'{template} найден')
                    return r
        return []

    def wait_for(self, *templates, trys=None, threshold=0.65, one_attempt=False):
        logger.debug(f'Ищем изображения {templates}')

        search_for_files = []
        for template in templates:
            file = template
            if not file.lower().endswith('.png'):
                file = file + '.png'
            if not '/' in file and not '\\' in file:
                file = ABSOLUTE_PATH('images\\' + file)
            search_for_files.append((file, template))

        for ii in range(120):
            screenshot_path = self.make_screenshot()
            for file, template in search_for_files:
                r = find_template_img(screenshot_path, file, threshold)
                if r:
                    logger.debug(f'{template} найден')
                    return template, r
            if one_attempt:
                return False, False
            if trys:
                trys -= 1
                if not trys:
                    raise TemplateNotFoundException()
            sleep(2)
        raise Exception('error searching template' + str(templates))

    def tap_on(self, template, one_attempt=False):
        _, rect = self.wait_for(template, one_attempt=one_attempt)
        if rect:
            self.tap(rect)
            return True
        return False

    def is_image(self, template, threshold=0.65, template_exclude=None):
        _, rect = self.wait_for(template, one_attempt=True, threshold=threshold, template_exclude=template_exclude)
        if rect:
            return True
        return False

    def scroll_down_to(self, template, threshold=0.65):
        while True:
            try:
                self.wait_for(template, trys=1, threshold=threshold)
                return
            except TemplateNotFoundException:
                pass
            self.send_pgdn()

    def tap(self, point):
        point = flatten(point)
        if len(point) == 4:
            # Это прямоугольная область, кликаем в центр
            dest = (round((point[0] + point[2]) / 2), round((point[1] + point[3]) / 2))
        else:
            dest = point
        logger.debug(f'Кликаем в {dest} ({point})')
        self.adb('shell input tap %d %d' % (point[0], point[1]))

    def swipe_down(self):
        self.adb('shell input swipe 600 600 600 100 1000')

    def send_text(self, text):
        self.adb('shell input text %s' % (text))

    def _send_event(self, event):
        self.adb('shell input keyevent %s' % event)

    def send_back(self):
        self._send_event('KEYCODE_BACK')

    def send_pgdn(self):
        self._send_event('KEYCODE_PAGE_DOWN')

    def send_pgup(self):
        self._send_event('KEYCODE_PAGE_UP')

    def send_del(self):
        self._send_event('KEYCODE_DEL')

    def set_proxy(self, host, port):
        logger.debug(f'Устанавливаем в Nox прокси {host} {port}')
        #  из-за ошибок выполнения команд при полностью не загруженном эмуляторе игнорим ошибки и повторяем попытки
        attempts = 10
        for ii in range(attempts):
            try:
                self.adb(f'shell settings put global http_proxy {host}:{port}')
                break
            except Exception as e:
                logger.debug(str(e))
                pass
        if ii == attempts - 1:
            raise Exception('set_proxy error')

    def _set_vm_property(self, key, value):
        out = run_command(f'{self.nox.nox_console_exe} setprop -name:{self.code} -key:{key} -value:{value}',
            cwd=f'{self.nox.nox_dir}/bin')
        a = 1

    def set_random_id(self):
        # Меняем imei, imsi телефон, mac
        imei = generate_imei('86213')
        imsi = generate_imsi()
        did = random.randint(500000000, 600000000)
        serial = generate_imsi()
        phone = generate_phone_num()
        mac = generate_mac()
        self.adb('shell setprop persist.nox.androidid %d' % did)
        self.adb('shell setprop persist.nox.modem.imei %s' % imei)
        self.adb('shell setprop persist.nox.modem.imsi %s' % imsi)
        self.adb('shell setprop persist.nox.modem.phonumber %s' % phone)
        self.adb('shell setprop persist.nox.modem.serial %s' % serial)
        self.adb('shell setprop persist.nox.wifimac %s' % mac)
        # self._set_vm_property('imei', imei)
        # self._set_vm_property('imsi', imsi)
        # self._set_vm_property('linenum', phone)
        # self._set_vm_property('hmac', mac)


class NoxController(object):
    __nox_manager_exe = 'bin/MultiPlayerManager.exe'
    __nox_console_exe = 'bin/NoxConsole.exe'
    __adb_exe = 'bin/adb.exe'

    def _find_nox_dir(self):
        for drive in range(ord('A'), ord('N')):
            drive = chr(drive)
            search_path = f'{drive}:/Program Files/Nox'
            nox_dir = first(find_file(search_path, self.__nox_manager_exe))
            if nox_dir:
                logger.debug(f'Нашли nox в {search_path}')
                return search_path
        raise Exception('No nox dir')

    def __init__(self):
        # Ищем adb.exe NoxManager.exe
        self.nox_dir = self._find_nox_dir()
        self.nox_manager_exe = os.path.join(self.nox_dir, self.__nox_manager_exe)
        self.nox_console_exe = os.path.join(self.nox_dir, self.__nox_console_exe)
        self.adb_exe = os.path.join(self.nox_dir, self.__adb_exe)

    def _get_vm_info(self, id):
        return run_command(f'{self.nox_manager_exe} showvminfo {id}')

    def get_device(self, name) -> NoxDevice:
        return NoxDevice(name, 0, self)
        # for device in self.get_devices():
        #     # if device.name == name:
        #         return device
        # return 'NoxPlayer'

    def get_devices(self):
        # vms_output = run_command(f'{self.nox_manager_exe} list vms')
        # out = run_command(f'cmd.exe cd /D {self.nox_dir}/bin')
        vms_output = run_command(f'{self.nox_console_exe} list', cwd=f'{self.nox_dir}/bin')
        devices = []
        devices.append(NoxDevice('NoxPlayer', 0, self))
        return devices
        # for line in vms_output.splitlines():
        #     if ',' in line:
        #         name, id = line.split(',')
        #         name = name.strip('\r\n\t "')
        #         id = id.split('}')[0]
        #         devices.append(NoxDevice(name, id, self))
        #         logger.debug(f'Нашли nox устройство {name} {id}')
        # return devices

    # res = imlib.find_image(img_fn, "template1", 0.8)
    # if res:
    #     self.click(res[0] + 4 + random.randint(0, 4),
    #                res[1] + 4 + random.randint(0, 4))
