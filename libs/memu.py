#  cmd commands
#  https://www.memuplay.com/blog/2016/04/01/how-to-manipulate-memu-thru-command-line/

import logging
import os, sys
from datetime import datetime
from time import sleep
import random
random.seed

import shutil

from libs.common import run_command, first, CommandStdErrException, find_template_img, flatten, \
    generate_imei, generate_imsi, generate_phone_num, generate_mac, find_template_all_img
import libs.common as common

# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    ABSOLUTE_PATH = lambda x: os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(sys.executable)), x[3:]))
elif __file__:
    ABSOLUTE_PATH = lambda x: os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), x))

logger = logging.getLogger(__name__)

#
# logger.debug('__file__')
# logger.debug(__file__)
# logger.debug('sys.executable')
# raise Exception(sys.executable)
# logger.debug)
# exit(0)




class TemplateNotFoundException(Exception):
    pass


class MemuDevice(object):
    def __init__(self, code, id, memu: 'MemuController'):
        self.code = code
        self.id = id
        self.memu = memu
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
            self.__info = self.memu._get_vm_info(self.id)
        return self.__info

    @property
    def _screenshots_local_dir(self):
        if not self.__screenshots_dir:
            # Name: 'picture', Host path: 'C:\Users\Art\Pictures\MEmu Photo' (machine mapping), writable
            for line in self._vm_info.splitlines():
                if line.startswith("Name: 'picture'"):
                    path = line.split('path:')[1]
                    path = path.split("'")[1]
                    self.__screenshots_dir = path
                    logger.debug(f'Нашли директорию скриншотов {path}')
                    break
            else:
                raise Exception('Нет пути к скриншотам')
        return self.__screenshots_dir

    @property
    def _adb_address(self):
        if not self.__addr_adb:
            # Name: 'picture', Host path: 'C:\Users\Art\Pictures\MEmu Photo' (machine mapping), writable
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

    pictures_memu_path = '/mnt/shell/emulated/0/Pictures/'

    def adb(self, parameters, timeout=30):
        try:
            self._adb_address
        except:
            self._adb_address = None
        output = run_command(f'{self.memu.adb_exe} -s {self._adb_address} {parameters}',
                             cwd=f'{self.memu.memu_dir}/MEmu', timeout=timeout)
        return output

    def make_screenshot(self, attempt=1, file_name=''):
        if file_name:
            img_name = file_name
        else:
            img_name = 'wam_' + self.name + '_' + datetime.now().strftime("%Y%m%d-%H%M%S") + '.png'
        img_memu_path = os.path.join(self.pictures_memu_path, img_name).replace('\\', '/')
        output = self.adb(f'shell screencap  {img_memu_path}')
        img_local_path = os.path.join(self._screenshots_local_dir, img_name)
        if not os.path.exists(img_local_path):
            if attempt > 5:
                raise Exception(f'Скриншот не сделан {img_local_path}')
            return self.make_screenshot(attempt+1)
        logger.debug('Сделан скриншот ' + img_local_path)
        return img_local_path

    def clean_screenshots_dir(self):
        logger.debug('Удаляем скриншоты из директории')
        for file in os.listdir(self._screenshots_local_dir):
            if file.lower().endswith('png') and file.find('wam_' + self.name + '_') > -1:
                file_path = os.path.join(self._screenshots_local_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.debug(str(e))

    def start(self):
        logger.debug(f'Запускаем {self.name}')
        run_command(f'{self.memu.memu_console_exe} {self.code}', cwd=f'{self.memu.memu_dir}/MEmu')
        sleep(5)

    def wait_loaded(self, attempt=1):
        logger.debug('Ожидаем загрузки Android')
        for ii in range(60):
            try:
                screenshot_path = self.make_screenshot()
                if os.path.isfile(screenshot_path):
                    sleep(5)
                    return True
                if self.is_android_loaded():
                    return True
            except:
                pass
            sleep(1)
        if attempt < 3:
            self.start()
            return self.wait_loaded(attempt + 1)
        return False

    def stop(self):
        logger.debug(f'Останавливаем {self.name}')
        run_command(f'{self.memu.memu_console_exe} ShutdownVM {self.code}', cwd=f'{self.memu.memu_dir}/MEmu')
        sleep(5)

    def set_root(self, is_root):
        run_command(f'{self.memu.memu_manager_exe} guestproperty set {self.code} enable_su %d' % is_root,
                    cwd=f'{self.memu.memu_dir}/MEmu')
        self.stop()
        self.start()

    def input_pin_device(self):
        self.tap_on('login/input_login_device')
        sleep(0.5)
        self.tap_on('login/input_login_device', one_attempt=True)
        sleep(0.5)
        self.tap_on('login/input_login_device', one_attempt=True)
        sleep(0.5)
        self.tap_on('login/input_login_device', one_attempt=True)
        sleep(0.5)
        # self.wait_for('login/device_pin_enter')
        self.tap_on('login/device_pin_enter')
        sleep(0.5)


    def instal_cert(self):
        self.send_back()
        sleep(1.5)
        self.send_back()
        sleep(1.5)
        self.send_back()
        sleep(1.5)
        self.tap_on('login/cert_settings')
        sleep(1.5)
        self.send_pgdn()
        sleep(1.5)
        self.send_pgdn()
        self.tap_on('login/cert_lock.png', one_attempt=True)
        sleep(1.5)
        self.send_pgdn()
        sleep(1.5)
        self.send_pgdn()
        sleep(1.5)
        self.send_pgdn()
        sleep(1.5)
        self.tap_on('login/cert_install_from_sd', one_attempt=True)
        sleep(1.5)
        self.tap_on('login/cert_sd', one_attempt=True)
        sleep(1.5)
        self.adb("shell input swipe 100 300 100 100 300")  # send_pgdn не работает на этом экране
        sleep(1.2)
        self.tap_on('login/cert_donload_folder', one_attempt=True)
        sleep(1.5)
        self.tap_on('login/cert_system_folder', one_attempt=True)
        sleep(1.5)
        self.tap_on('login/cert_ca_pem_file', one_attempt=True)
        sleep(2)
        self.send_text('swex')
        sleep(1.5)
        self.wait_for('login/cert_ok')
        self.tap_on('login/cert_ok')
        # sleep(3.5)
        # self.send_back()
        sleep(1.5)

    def get_vm_properties(self):
        values = {}
        out = run_command(f'{self.memu.memu_manager_exe} guestproperty enumerate {self.id}',
                          cwd=f'{self.memu.memu_dir}/MEmu')
        for line in out.splitlines():
            name, value = line.split('value:')
            name = name.split(':')[1]
            name = name.strip('\r\n\t :,')
            value = value.split(',')[0]
            value = value.strip('\r\n\t ')
            values[name] = value
        return values

    def is_android_loaded(self, attempt=1):
        try:
            out = self.adb('''shell "getprop sys.boot_completed | tr -d '\r'"''')
            # состояние готовности сим карты при первой загрузке более верный
            # признак загруженности вмки, чем boot_completed
            out2 = self.adb('''shell "getprop gsm.sim.state | tr -d '\r'"''')
        except CommandStdErrException as e:
            if 'error: device not found' in str(e):
                return False
            if 'MEmuManage.exe: error: The object is not ready' in str(e):
                return False
            if 'error: device offline' in str(e):
                return False
            if attempt < 5:
                self.stop()
                self.start()
                return self.is_android_loaded(attempt + 1)
            raise
        # if out.strip() == 'running':
        if out.strip() == '1':
            return True
        if out2.strip() == 'READY':
            return True
        return False

    # delta_coor - разница в координатах, при которых нахождение принимать за одно единственное
    def get_all_images(self, *templates, threshold=0.65, debug=True, delta_coor=10, prepared_scr_shot='', method_search=1,
                       crop=False, cropx1=-20, cropy1=-20, cropx2=20, cropy2=20, mask=None):
        if type(templates[0]) == tuple:
            templates = templates[0]
        logger.debug(f'Ищем изображения {templates}')

        search_for_files = []
        for template in templates:
            file = template
            if not file.lower().endswith('.png'):
                file = file + '.png'
            if not '/' in file and not '\\' in file:
                file = ABSOLUTE_PATH('..\\images\\' + file)
            search_for_files.append((file, template))

        if prepared_scr_shot:
            screenshot_path = prepared_scr_shot
        else:
            screenshot_path = self.make_screenshot()

        for file, template in search_for_files:
            r = find_template_all_img(screenshot_path, file, threshold, debug=debug,
                delta_coor=delta_coor, method_search=method_search,
                crop=crop, cropx1=cropx1, cropy1=cropy1, cropx2=cropx2, cropy2=cropy2, mask=mask)
            if r:
                logger.debug(f'{template} найден')
                return r
        return []

    # блокируем твинк от работы на других эмуляторах, если он уже не заблокирован
    def block_acc(self, acc):
        memu_names = ['MEmu']
        for ii in range(1, 20):
            memu_names.append('MEmu%d' % ii)
        try:
            os.remove('twins/old_block_' + self.name + '.txt')
        except Exception as e:
            logger.debug(str(e))
        try:
            os.rename('twins/block_' + self.name + '.txt', 'twins/old_block_' + self.name + '.txt')
        except Exception as e:
            logger.debug(str(e))
        for name in memu_names:
            if name == self.name:
                continue
            fn = 'twins/block_' + name + '.txt'
            cur_block_info = common.get_json_from_file(fn)
            if 'nick' in cur_block_info and cur_block_info['nick'] == acc['nick']:
                return False
            fn = 'twins/old_block_' + name + '.txt'
            cur_block_info = common.get_json_from_file(fn)
            if 'nick' in cur_block_info and cur_block_info['nick'] == acc['nick']:
                return False
        fn = ABSOLUTE_PATH('..\\twins\\block_' + self.name + '.txt')
        logger.debug('block_acc dir: fn')
        common.save_json_to_file(acc, fn)
        return True

    # return_quality - третьим параметром возвращать качество найденной картинки
    # templates_exclude - если найденная картинка совпадает по координатам с картинкой в
    #       исключениях, причем та, которая в исключениях найдена с более хорошим качеством
    #       чем искомая, то считаем этот поиск недействительным
    # best_templ - искать все шаблоны и выдавать наилучшее совпадение
    def wait_for(self, *templates, trys=None, threshold=0.65, one_attempt=False, attempts=120,
                 false_is_except=False, return_quality=False, templates_exclude=None,
                 prepared_scr_shot='', best_templ=False, b_color=0, g_color=0,
                 prefer_x=-1, prefer_y=-1, radius=0,
                 grain=0, grain_x2=0, grain_y1=0, grain_y2=0,
                 crop=False, cropx1=-20, cropy1=-20, cropx2=20, cropy2=20, method_search=1, break_first_find=False):
        if type(templates[0]) == tuple:
            templates = templates[0]
        logger.debug(f'Ищем изображения {templates}')

        if templates_exclude:
            return_quality = True
        search_for_files = []
        try:
            for template in templates:
                file = template
                if not file.lower().endswith('.png'):
                    file = file + '.png'
                if not 'war_magic/' in file:
                    file = ABSOLUTE_PATH('..\\images\\' + file)
                search_for_files.append((file, template))
        except Exception as e:
            logger.debug(str(e))

        if best_templ:
            best_res = (0, 0, 0)
        for ii in range(attempts):
            if prepared_scr_shot:
                screenshot_path = prepared_scr_shot
            else:
                screenshot_path = self.make_screenshot()
            for file, template in search_for_files:
                if templates_exclude:
                    crop = True
                r = find_template_img(screenshot_path, file, threshold, debug=True,
                  return_quality=True, b_color=b_color, g_color=g_color,
                  grain=grain, grain_x2=grain_x2, grain_y1=grain_y1, grain_y2=grain_y2,
                  method_search=method_search, crop=crop, cropx1=cropx1, cropy1=cropy1,
                  cropx2=cropx2, cropy2=cropy2, break_first_find=break_first_find, prefer_x=prefer_x, prefer_y=prefer_y, radius=radius)
                if (type(r) is tuple and r[1]):
                    if best_templ:
                        if best_res[2] < r[2]:
                            best_res = template, r[0], r[2]
                        continue
                    if templates_exclude:
                        tmpls = templates_exclude
                        if not type(templates_exclude) is str:
                            tmpls = tuple(templates_exclude)
                        r_excl = self.wait_for(tmpls, trys=trys,
                            grain=grain, grain_x2=grain_x2, grain_y1=grain_y1, grain_y2=grain_y2,
                            break_first_find=break_first_find, threshold=threshold,
                            prefer_x = prefer_x, prefer_y = prefer_y, radius = radius,
                            one_attempt=True, return_quality=True, method_search=method_search,
                            prepared_scr_shot=screenshot_path[0:-4] + '_crop_%s.png' % template, best_templ=True, b_color=b_color, g_color=g_color)
                        if r_excl[0] and r_excl[2] > r[2]:
                            continue
                    logger.debug(f'{template} найден')
                    if return_quality:
                        return template, r[0], r[2]
                    return template, r
            if best_templ and best_res[2] > 0:
                if not templates_exclude:
                    logger.debug('Наилучший картинка-якорь %s, качество %.6f' % (best_res[0], best_res[2]))
                    return best_res
                logger.debug('Ищем картинки исключения')
                tmpls = templates_exclude
                if not type(templates_exclude) is str:
                    tmpls = tuple(templates_exclude)
                r_excl = self.wait_for(tmpls, trys=trys, threshold=threshold,
                                       one_attempt=True, return_quality=True,
                                       prefer_x=prefer_x, prefer_y=prefer_y, radius=radius,
                                       grain=grain, grain_x2=grain_x2, grain_y1=grain_y1, grain_y2=grain_y2,
                                       break_first_find=break_first_find,
                                       prepared_scr_shot=screenshot_path[0:-4] + '_crop_%s.png' % best_res[0],
                                       best_templ=True, b_color=b_color, g_color=g_color, method_search=method_search)
                if r_excl[0] and r_excl[2] > best_res[2]:
                    logger.debug('В исключениях более сильная картинка чем в искомых')
                else:
                    logger.debug('Наилучший картинка-якорь %s, качество %.6f' % (best_res[0], best_res[2]))
                    return best_res
            if one_attempt:
                if return_quality:
                    return False, False, None
                return False, False
            if trys:
                trys -= 1
                if not trys:
                    raise TemplateNotFoundException()
            sleep(1)
        if false_is_except:
            raise Exception('error searching template' + str(templates))
        else:
            if return_quality:
                return False, False, None
            return False, False

    # grain - ограничение области нахождения, чтобы не по всему экрану, а в пределах, не меньших чем grain пикселей до краев экрана
    def tap_on(self, template, one_attempt=False, threshold=0.65, false_is_except=False, dx=0, dy=0,
               attempts=120, return_rect=True, template_exclude=None, b_color=0, grain=0, prepared_scr_shot=''):
        if template_exclude:
            _, rect, quality = self.wait_for(template, one_attempt=one_attempt, threshold=threshold,
                attempts=attempts, return_quality=True, b_color=b_color, templates_exclude=template_exclude,
                                             prepared_scr_shot=prepared_scr_shot)
            if not rect:
                return False
        else:
            _, rect = self.wait_for(template, one_attempt=one_attempt, threshold=threshold, attempts=attempts,
                                    b_color=b_color, grain=grain, prepared_scr_shot=prepared_scr_shot)
        if rect:
            self.tap(rect, dx, dy)
            if return_rect:
                return True, rect
            return True
        if false_is_except:
            raise Exception('Error tap_on, template = ' + template)
        return False

    def is_image(self, template, threshold=0.65, template_exclude=None, prepared_scr_shot=''):
        ret = self.wait_for(template, one_attempt=True, threshold=threshold,
                            templates_exclude=template_exclude, prepared_scr_shot=prepared_scr_shot)
        if ret[1]:
            return True
        return False

    def scroll_down_to(self, template, threshold=0.65):
        for ii in range(10):
            try:
                self.wait_for(template, trys=1, threshold=threshold)
                return
            except TemplateNotFoundException:
                pass
            self.send_pgdn()
        raise Exception('scroll_down_to: not found template ' + template)

    def long_tap(self, point, pause, dx=0, dy=0):
        point = flatten(point)
        if len(point) == 4:
            # Это прямоугольная область, кликаем в центр
            dest = (round((point[0] + point[2]) / 2) + random.randint(-2, 2) + dx,
                    round((point[1] + point[3]) / 2) + random.randint(-2, 2) + dy)
        else:
            dest = (point[0] + dx, point[1] + dy)
        self.adb('shell input swipe %d %d %d %d %d' % (dest[0], dest[1], dest[0], dest[1], pause))

    def tap(self, point, dx=0, dy=0):
        point = flatten(point)
        if len(point) == 4:
            # Это прямоугольная область, кликаем в центр
            dest = (round((point[0] + point[2]) / 2) + random.randint(-2, 2) + dx,
                    round((point[1] + point[3]) / 2) + random.randint(-2, 2) + dy)
        else:
            dest = (point[0] + dx, point[1] + dy)
        logger.debug(f'Кликаем в {dest} ({point})')
        self.adb('shell input tap %d %d' % (dest[0], dest[1]))

    def swipe_down(self):
        self.adb('shell input swipe 600 600 600 100 1000')

    def send_text(self, text):
        self.adb('shell input text %s' % (text))

    def _send_event(self, event, num_ev=1):
        logger.debug('press key ' + str(event))
        postf = ''
        if num_ev > 1:
            for ii in range(1, num_ev):
                postf += ' ' + event
        self.adb('shell input keyevent %s%s' % (event, postf))

    def send_back(self):
        self._send_event('KEYCODE_BACK')

    def volume_down(self):
        self._send_event('KEY_VOLUME_DOWN')
        self._send_event('KEY_VOLUME_DOWN')
        self._send_event('KEY_VOLUME_DOWN')
        self._send_event('KEY_VOLUME_DOWN')
        self._send_event('KEY_VOLUME_DOWN')
        self._send_event('KEY_VOLUME_DOWN')
        self._send_event('KEY_VOLUME_DOWN')
        self._send_event('KEY_VOLUME_DOWN')

    def send_pgdn(self):
        self._send_event('KEYCODE_PAGE_DOWN')

    def send_pgup(self):
        self._send_event('KEYCODE_PAGE_UP')

    def send_del(self, num_ev=1):
        self._send_event('KEYCODE_DEL', num_ev=num_ev)

    def swipe(self, x, y, x0=400, y0=200, speed=170, sleep_sec=0.2):
        self.adb('shell input swipe %d %d %d %d %d' % (x0, y0, x0 + x, y0+y, speed))
        sleep(sleep_sec)

    def set_proxy(self, host, port):
        logger.debug(f'Устанавливаем в MEmu прокси {host} {port}')
        self.adb(f'shell settings put global http_proxy {host}:{port}')

    def _set_vm_property(self, key, value):
        out = run_command(f'{self.memu.memu_manager_exe} guestproperty set {self.id} {key} {value}',
                          cwd=f'{self.memu.memu_dir}/MEmuHyperv')
        a = 1

    def set_random_id(self):
        # Меняем imei, imsi телефон, mac
        imei = generate_imei('86213')
        imsi = generate_imsi()
        phone = generate_phone_num()
        mac = generate_mac()
        self._set_vm_property('imei', imei)
        self._set_vm_property('imsi', imsi)
        self._set_vm_property('linenum', phone)
        self._set_vm_property('hmac', mac)

    def recreate1(self, delete_old=True):
        try:
            if delete_old:
                logger.debug(f'Пересоздаем {self.name}')
                self.stop()
                for ii in range(10):
                    # удаление проходит всегда с ошибкой (видимо это нормально)
                    try:
                        run_command(f'{self.memu.memu_manager_exe} unregistervm "{self.code}" --delete',
                                      cwd=f'{self.memu.memu_dir}/MEmuHyperv')
                    except Exception as e:
                        if str(e).find('...100%') == -1:
                            if ii > 8:
                                break
                            sleep(1)
                        else:
                            break
                run_command(f'{self.memu.memu_console_exe} create', cwd=f'{self.memu.memu_dir}/MEmu')
            while not os.path.isfile(self.memu.memu_dir + '/MEmu/MemuHyperv VMs/' + self.code + '/' + self.code + '.memu'):
                sleep(5)
            sleep(5)
            run_command(f'{self.memu.memu_manager_exe} guestproperty set {self.code} enable_su 1', cwd=f'{self.memu.memu_dir}/MEmu')
            sleep(1)
            run_command(f'{self.memu.memu_manager_exe} guestproperty set {self.code} is_customed_resolution 1', cwd=f'{self.memu.memu_dir}/MEmu')
            sleep(1)
            run_command(f'{self.memu.memu_manager_exe} guestproperty set {self.code} resolution_width 850', cwd=f'{self.memu.memu_dir}/MEmu')
            sleep(1)
            run_command(f'{self.memu.memu_manager_exe} guestproperty set {self.code} resolution_height 500', cwd=f'{self.memu.memu_dir}/MEmu')
            sleep(1)
            run_command(f'{self.memu.memu_manager_exe} guestproperty set {self.code} vbox_dpi 133', cwd=f'{self.memu.memu_dir}/MEmu')
            sleep(1)
            sleep(1)
            run_command(f'{self.memu.memu_manager_exe} guestproperty set {self.code} lang en', cwd=f'{self.memu.memu_dir}/MEmu')

            mac = generate_mac()
            run_command(f'{self.memu.memu_manager_exe} guestproperty set {self.code} hmac "%s"' % mac, cwd=f'{self.memu.memu_dir}/MEmu')
            # out = self.adb('''shell "getprop"''')

            self.start()
            sleep(12)
        except Exception as e:
            logger.debug(str(e))

    def recreate2(self, path):
        logger.debug(f'Продолжаем пересоздавать {self.name}')
        self.wait_loaded()
        sleep(50)  # first boot
        try:
            shutil.copyfile(r'c:\Users\denis\Downloads\MEmu Download\wam\com.stgl.global-1.apk',
                        path + 'com.stgl.global-1.apk')
        except:
            pass
        try:    # from /data/app/*.apk
            fn_apk = path + "com.stgl.global-1.apk"
            self.adb('install -r ' + fn_apk, 180)
            sleep(10)
        except Exception as e:
            logger.debug(str(e))
            sleep(5)
            res = self.adb('shell pm list packages')
            if res.find('com.stgl.global') == -1:
                raise Exception('error wam installation')
        try:
            fn_apk = path + "com.google.android.gms-1.apk"
            self.adb('install -r ' + fn_apk, 120)
            sleep(15)
        except Exception as e:
            logger.debug(str(e))
            pass
        sleep(2)



class MemuController(object):
    __memu_manager_exe = 'MEmuHyperv/MEmuManage.exe'
    __memu_console_exe = 'MEmu/MEmuConsole.exe'
    __adb_exe = 'MEmu/adb.exe'

    def _find_memu_dir(self):
        for drive in range(ord('A'), ord('N')):
            drive = chr(drive)
            search_path = f'{drive}:/Microvirt'
            memu_dir = first(common.find_file(search_path, self.__memu_manager_exe))
            if memu_dir:
                logger.debug(f'Нашли memu в {search_path}')
                return search_path
        for drive in range(ord('A'), ord('N')):
            drive = chr(drive)
            search_path = f'{drive}:/Program Files/Microvirt'
            memu_dir = first(common.find_file(search_path, self.__memu_manager_exe))
            if memu_dir:
                logger.debug(f'Нашли memu в {search_path}')
                return search_path
        raise Exception('No memu dir')

    def __init__(self):
        # Ищем adb.exe MEmuManager.exe
        self.memu_dir = self._find_memu_dir()
        self.memu_manager_exe = os.path.join(self.memu_dir, self.__memu_manager_exe)
        self.memu_console_exe = os.path.join(self.memu_dir, self.__memu_console_exe)
        self.adb_exe = os.path.join(self.memu_dir, self.__adb_exe)

    def _get_vm_info(self, id):
        return run_command(f'{self.memu_manager_exe} showvminfo {id}', cwd=f'{self.memu_dir}/MEmuHyperv')

    def get_device(self, name, empty=False) -> MemuDevice:
        for device in self.get_devices():
            if device.name == name:
                return device
        return None

    def get_devices(self):
        # for line in traceback.format_stack():
        #     print(line.strip())
        vms_output = run_command(f'{self.memu_manager_exe} list vms', cwd=f'{self.memu_dir}/MEmuHyperv')
        devices = []
        for line in vms_output.splitlines():
            if '{' in line:
                name, id = line.split('{')
                name = name.strip('\r\n\t "')
                id = id.split('}')[0]
                devices.append(MemuDevice(name, id, self))
                logger.debug(f'Нашли memu устройство {name} {id}')
        return devices

    def create_device(self):
        # for line in traceback.format_stack():
        #     print(line.strip())
        vms_output = run_command(f'{self.memu_console_exe} create', cwd=f'{self.memu_dir}/MEmu')
        sleep(20)
        return True

    # res = imlib.find_image(img_fn, "template1", 0.8)
    # if res:
    #     self.click(res[0] + 4 + random.randint(0, 4),
    #                res[1] + 4 + random.randint(0, 4))
