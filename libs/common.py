# -*- coding: utf-8 -*-
import itertools
import logging
import os
import random
import socket
import string
import subprocess
import threading
import time
import cv2
import json
import shutil

logger = logging.getLogger(__name__)


def checksum(string):
    digits = list(map(int, string))
    odd_sum = sum(digits[-1::-2])
    even_sum = sum([sum(divmod(2 * d, 10)) for d in digits[-2::-2]])
    return (odd_sum + even_sum) % 10


def generate(string):
    cksum = checksum(string + '0')
    return (10 - cksum) % 10


def append_luhn(string):
    return string + str(generate(string))


def generate_imei(subject_imei):
    imei_digits = []

    for i in range(0, 14):
        # find missing digits and complete with randos
        try:
            digit = subject_imei[i]
        except IndexError:
            digit = random.randint(0, 9)

        # Add digits to IMEI
        imei_digits.append(str(digit))

    # append the luhn checksum and return
    return append_luhn("".join(imei_digits))


def generate_imsi():
    # 460003024473552
    operator_code = random.choice(['01', '02', '28', '20'])
    return '250{0}{1:010}'.format(operator_code, random.randint(0, 999999999))


def generate_phone_num():
    code = random.choice(['985', '911', '977', '916', '903', '902', '926'])
    return '+7{0}{1:07}'.format(code, random.randint(0, 9999999))


def generate_sim_serial():
    pass
    # 89860036453415139329
    # 	cc_digits = _cc_digits(opts.country)
    #
    # 	# Digitize MCC/MNC (5 or 6 digits)
    # 	plmn_digits = _mcc_mnc_digits(mcc, mnc)
    #
    # 	# ICCID (19 digits, E.118), though some phase1 vendors use 20 :(
    # 	if opts.iccid is not None:
    # 		iccid = opts.iccid
    # 		if not _isnum(iccid, 19) and not _isnum(iccid, 20):
    # 			raise ValueError('ICCID must be 19 or 20 digits !');
    #
    # 	else:
    # 		if opts.num is None:
    # 			raise ValueError('Neither ICCID nor card number specified !')
    #
    # 		iccid = (
    # 			'89' +			# Common prefix (telecom)
    # 			cc_digits +		# Country Code on 2/3 digits
    # 			plmn_digits 	# MCC/MNC on 5/6 digits
    # 		)
    #
    # 		ml = 18 - len(iccid)
    #
    # 		if opts.secret is None:
    # 			# The raw number
    # 			iccid += ('%%0%dd' % ml) % opts.num
    # 		else:
    # 			# Randomized digits
    # 			iccid += _digits(opts.secret, 'ccid', ml, opts.num)
    #
    # 		# Add checksum digit
    # 		iccid += ('%1d' % calculate_luhn(iccid))


def find_file(path, name):
    try:  # Trapping a OSError:  File permissions problem I believe
        for entry in os.scandir(path):
            if entry.is_file() and entry.path.endswith(name):
                yield entry.path
            elif entry.is_dir():  # if its a directory, then repeat process as a nested function
                yield find_file(entry.path, name)
    except OSError:
        pass


class Command(object):
    def __init__(self, cmd, cwd=''):
        self.cmd = cmd
        self.cwd = cwd
        self.process = self.stdout = self.stderr = None

    def run(self, timeout):
        def target():
            startupinfo = subprocess.STARTUPINFO()
            # set the use show window flag, might make conditional on being in Windows:
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            # pass as the startupinfo keyword argument:
            cmd_debug = self.cmd.replace('\r', '/')
            # cmd_debug = cmd_debug.replace('\\', '/')
            # logger.debug(f'Start command {cmd_debug}')
            if self.cwd:
                self.process = subprocess.Popen(self.cmd,
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.PIPE,
                                                  stdin=subprocess.PIPE,
                                                  startupinfo=startupinfo, cwd=self.cwd)
            else:
                self.process = subprocess.Popen(self.cmd,
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.PIPE,
                                                  stdin=subprocess.PIPE,
                                                  startupinfo=startupinfo)
            self.stdout, self.stderr = self.process.communicate()
            return self.process

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            logger.debug('Terminating process')
            self.process.terminate()
            # thread.join()
        return self.stdout, self.stderr

class CommandStdErrException(Exception):
    pass

# проверка параметра в словаре на его отставание больше определенного количества секунд
def is_stat_more_dif_time(stat, secs, par):
    if par not in stat:
        return True
    if type(stat[par]) == int:
        if stat[par] + secs > time.time():
            return False
    return True

from PyQt5 import QtWidgets

def message_box(txt, add_info=''):
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setWindowTitle("Информация")
    msg.setText(txt)
    if add_info:
        msg.setInformativeText(add_info)
    msg.addButton('Ok', QtWidgets.QMessageBox.AcceptRole)
    msg.exec()

def load_accs(qt_combo, set_main=False):
    if not os.path.isfile('accs.txt'):
        try:
            shutil.copyfile('accs_example.txt', 'accs.txt')
        except:
            pass
    try:
        accs = get_json_from_file('accs.txt')
    except Exception as e:
        print(str(e))
        message_box('Ошибка в файле настроек аккаунтов accs.txt', str(e))
        exit(-55)
    for ii in range(len(accs)):
        qt_combo.addItem(accs[ii]['nick'])
        if set_main and 'main' in accs[ii] and accs[ii]['main']:
            qt_combo.setCurrentIndex(ii)
    return accs


def get_json_from_file(file_name, except_return_empty = False):
    if not os.path.isfile(file_name):
        return {}
    f = open(file_name, 'r')
    str_cont = f.read()
    f.close()
    try:
        ret = json.loads(str_cont)
    except:
        f = open(file_name, 'r')
        str_cont = f.read()
        f.close()
        if str_cont == '':
            return {}
        if except_return_empty:
            try:
                ret = json.loads(str_cont)
            except:
                os.remove(file_name)
                return {}
        else:
            fi = str_cont.find("#")
            while fi > -1:
                fi2 = str_cont.find("\n", fi)
                if fi2 == -1:
                    str_cont = str_cont[0:fi, fi2:]
                else:
                    str_cont = str_cont[0:fi] + str_cont[fi2:]
                fi = str_cont.find("#", fi + 1)
            ret = json.loads(str_cont)
    return ret

def save_json_to_file(json_var, filename):
    f = open(filename, 'w+')
    f.write(json.dumps(json_var))
    f.close()

def get_array_json_from_file(file_name):
    if not os.path.isfile(file_name):
        return []
    f = open(file_name, 'r')
    array_json = f.read().splitlines()
    f.close()
    for ii in range(0, len(array_json)):
        if array_json[ii] == '':
            array_json[ii] = {}
            continue
        if not array_json[ii][0] == '{':
            if not array_json[ii][0] == '[':
                array_json[ii] = array_json[ii][array_json[ii].find('{'):]
        # print "line for load '%s'" % array_json[ii]
        # import ipdb;
        # ipdb.set_trace()
        array_json[ii] = json.loads(array_json[ii])
    return array_json

def save_json_array_to_file(json_array, file_name, file_modif='w'):
    f = open(file_name, file_modif)
    for ii in range(0, len(json_array)):
        f.write(json.dumps(json_array[ii])+"\n")
    f.close()

def run_command(cmd, cwd='', timeout=10, attempt=1):
    """given shell command, returns communication tuple of stdout and stderr"""
    # instantiate a startupinfo obj:
    command = Command(cmd, cwd)
    stdout, stderr = command.run(timeout=timeout)
    # startupinfo = subprocess.STARTUPINFO()
    # # set the use show window flag, might make conditional on being in Windows:
    # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    # # pass as the startupinfo keyword argument:
    # cmd_debug = cmd.replace('\r', '/')
    # # cmd_debug = cmd_debug.replace('\\', '/')
    # logger.debug(f'Start command {cmd_debug}')
    # if cwd:
    #     stdout, stderr = subprocess.Popen(cmd,
    #                                   stdout=subprocess.PIPE,
    #                                   stderr=subprocess.PIPE,
    #                                   stdin=subprocess.PIPE,
    #                                   startupinfo=startupinfo, cwd=cwd).communicate()
    # else:
    #     stdout, stderr = subprocess.Popen(cmd,
    #                                   stdout=subprocess.PIPE,
    #                                   stderr=subprocess.PIPE,
    #                                   stdin=subprocess.PIPE,
    #                                   startupinfo=startupinfo).communicate()
    if stderr == None:
        time.sleep(5)
        logger.debug('new attempt to run command')
        stdout, stderr = command.run(timeout=timeout)
    if stderr == None:
        logger.debug('debug me')
    if stderr.decode():
        if attempt < 5 and str(stderr.decode()).find('device not found') > -1:
            time.sleep(10)
            return run_command(cmd, cwd, timeout, attempt + 1)
        raise CommandStdErrException(stderr.decode())
    ret = stdout.decode('cp866', 'ignore')
    if ret:
        logger.debug(ret)
    return ret


def first(iterable):
    try:
        v = next(iter(iterable))
        return v
    except StopIteration:
        return None

def find_template_all_img(img_path, template, threshold=0.65, debug=False, delta_coor=10, method_search=1,
            crop=False, cropx1=-20, cropy1=-20, cropx2=20, cropy2=20, mask=None):
    template_img = cv2.imread(template)
    if template_img is None:
        raise Exception(f'Нет шаблона {template}')
    h, w = template_img.shape[:-1]
    template_name = os.path.basename(template)

    image = cv2.imread(img_path)
    if image is None:
        raise Exception(f'Нет картинки {img_path}')

    template_img_mask = None
    if mask:
        template_img_mask = cv2.imread(template[:-4] + '_mask.png')

    if method_search == 2:
        res = cv2.matchTemplate(image, template_img, cv2.TM_CCORR_NORMED, mask=template_img_mask)
    elif method_search == 3:
        res = cv2.matchTemplate(image, template_img, cv2.TM_SQDIFF_NORMED, mask=template_img_mask)
    else:
        res = cv2.matchTemplate(image, template_img, cv2.TM_CCOEFF_NORMED)
    ret = []
    for jj in range(len(res)):
        for ii in range(len(res[jj])):
            if not res[jj][ii] > threshold:
                continue
            if len(ret) == 0:
                ret.append((ii, jj, res[jj][ii]))

                if crop:
                    h_image, w_image = image.shape[:-1]
                    crop_x = ii + cropx1
                    if crop_x < 0:
                        crop_x = 0
                    crop_x2 = ii + w + cropx2
                    if crop_x2 >= w_image:
                        crop_x2 = w_image - 1
                    crop_y = jj + cropy1
                    if crop_y < 0:
                        crop_y = 0
                    crop_y2 = jj + h + cropy2
                    if crop_y2 >= h_image:
                        crop_y2 = h_image - 1
                    crop_img = image[crop_y:crop_y2, crop_x:crop_x2]
                    cv2.imwrite(img_path[0:-4] + '_crop_%d_%s' % (len(ret)-1, template_name), crop_img)

            else:
                is_pt_near = False
                for zz in range(len(ret)):
                    exist_pt = ret[zz]
                    if abs(ii - exist_pt[0]) < delta_coor and abs(jj - exist_pt[1]) < delta_coor:
                        if res[jj][ii] > exist_pt[2]:
                            ret[zz] = (exist_pt[0], exist_pt[1], res[jj][ii])
                        is_pt_near = True
                        break

                if is_pt_near:
                    continue
                ret.append((ii, jj, res[jj][ii]))
                if crop:
                    h_image, w_image = image.shape[:-1]
                    crop_x = ii + cropx1
                    if crop_x < 0:
                        crop_x = 0
                    crop_x2 = ii + w + cropx2
                    if crop_x2 >= w_image:
                        crop_x2 = w_image - 1
                    crop_y = jj + cropy1
                    if crop_y < 0:
                        crop_y = 0
                    crop_y2 = jj + h + cropy2
                    if crop_y2 >= h_image:
                        crop_y2 = h_image - 1
                    crop_img = image[crop_y:crop_y2, crop_x:crop_x2]
                    cv2.imwrite(img_path[0:-4] + '_crop_%d_%s' % (len(ret)-1, template_name), crop_img)

    if debug and len(ret):
        for pt in ret:
            pt = (pt[0], pt[1])
            cv2.rectangle(image, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)
        cv2.imwrite(img_path + '_deb.png', image)
    return ret

def get_color_level(img_path, b_color=0, g_color=0):
    img = cv2.imread(img_path)
    if img is None:
        raise Exception(f'No image {img_path}')
    h, w = img.shape[:-1]
    # img_name = os.path.basename(img_path)
    if g_color:
        sum_g = 0
        for xx in range(w):
            for yy in range(h):
                sum_g += img[yy, xx, 1]
        sum_g = 100 * sum_g / h / w / 255

        if sum_g > g_color:
            logger.debug('Уровень зеленого цвета = %.5f%% ВЫШЕ порога %.5f%%' % (sum_g, g_color))
            return True
        else:
            logger.debug('Уровень зеленого цвета = %.5f%% ниже порога %.5f%%' % (sum_g, g_color))
            return False

# b_color - определяем процент синего цвета, чтобы различать цветные и ч/б картинки
# break_first_find - прерывать поиск при первом нахождении выше порога
def find_template_img(img_path, template, threshold=0.65, debug=False,
        return_quality=False, b_color=0, g_color=0,
        prefer_x=-1, prefer_y=-1, radius=0,
        grain=0, grain_x2=0, grain_y1=0, grain_y2=0,
        break_first_find=False, method_search=1,
        crop=False, cropx1=-20, cropy1=-20, cropx2=20, cropy2=20):
    template_img = cv2.imread(template)
    if template_img is None:
        raise Exception(f'No template image {template}')
    h, w = template_img.shape[:-1]

    template_name = os.path.basename(template)

    image = cv2.imread(img_path)
    if image is None:
        time.sleep(1)
        image = cv2.imread(img_path)
        if image is None:
            raise Exception(f'Нет картинки {img_path}')
    h_im, w_im = image.shape[:-1]

    if method_search == 2:
        res = cv2.matchTemplate(image, template_img, cv2.TM_CCORR_NORMED)
    else:
        res = cv2.matchTemplate(image, template_img, cv2.TM_CCOEFF_NORMED)

    best_concide = 0
    best_ii = 0
    best_jj = 0
    if grain and not grain_x2:
        grain_x2 = grain
    if grain and not grain_y1:
        grain_y1 = grain
    if grain and not grain_y2:
        grain_y2 = grain
    if prefer_x > -1:  # поиск с предпочтительным местом нахождения и ограничением по радиусу поиска
        grain = prefer_x - radius
        if grain < 0:
            grain = 0
        grain_x2 = prefer_x + radius
        if grain_x2 + w >= w_im:
            grain_x2 = w_im - w - 1

        grain_y1 = prefer_y - radius
        if grain_y1 < 0:
            grain_y1 = 0
        grain_y2 = prefer_y + radius
        if grain_y2 + h >= h_im:
            grain_y2 = h_im - h - 1

        for jj in range(grain_y1, grain_y2):
            for ii in range(grain, grain_x2):
                if res[jj][ii] > best_concide:
                    best_concide = res[jj][ii]
                    best_ii = ii
                    best_jj = jj
                    if break_first_find and res[jj][ii] > threshold:
                        break
    else:
        for jj in range(grain_y1, len(res)-grain_y2):
            for ii in range(grain, len(res[jj]) - grain_x2):
                if res[jj][ii] > best_concide:
                    best_concide = res[jj][ii]
                    best_ii = ii
                    best_jj = jj
                    if break_first_find and res[jj][ii] > threshold:
                        break
    if best_concide > threshold:
        if b_color:
            sum_b = 0
            for xx in range(w):
                for yy in range(h):
                    sum_b += image[best_jj + yy, best_ii + xx, 0]
            sum_b = 100 * sum_b / h / w / 255

            sum_b_orig = 0
            for xx in range(w):
                for yy in range(h):
                    sum_b_orig += template_img[yy, xx, 0]
            sum_b_orig = 100 * sum_b_orig / h / w / 255

            if sum_b > b_color:
                logger.debug('Подходит %s, качество %.6f, синего цвета = %.5f%%, в оригинале = %.5f%%' % (
                    template_name, best_concide, sum_b, sum_b_orig))
            else:  # картинка не прошла по требованию насыщенности определенным цветом
                if return_quality:
                    return (best_ii, best_jj), None, best_concide
                return False

        if g_color:
            sum_g = 0
            for xx in range(w):
                for yy in range(h):
                    sum_g += image[best_jj + yy, best_ii + xx, 1]
            sum_g = 100 * sum_g / h / w / 255

            sum_g_orig = 0
            for xx in range(w):
                for yy in range(h):
                    sum_g_orig += template_img[yy, xx, 0]
            sum_g_orig = 100 * sum_g_orig / h / w / 255

            if sum_g > g_color:
                logger.debug('Подходит %s, качество %.6f, зеленого цвета = %.5f%%, в оригинале = %.5f%%' % (
                    template_name, best_concide, sum_g, sum_g_orig))
            else:  # картинка не прошла по требованию насыщенности определенным цветом
                if return_quality:
                    return (best_ii, best_jj), None, best_concide
                return False

        if crop:
            h_image, w_image = image.shape[:-1]
            crop_x = best_ii + cropx1
            if crop_x < 0:
                crop_x = 0
            crop_x2 = best_ii + w + cropx2
            if crop_x2 >= w_image:
                crop_x2 = w_image - 1
            crop_y = best_jj + cropy1
            if crop_y < 0:
                crop_y = 0
            crop_y2 = best_jj + h + cropy2
            if crop_y2 >= h_image:
                crop_y2 = h_image - 1
            crop_img = image[crop_y:crop_y2, crop_x:crop_x2]
            cv2.imwrite(img_path[0:-4] + '_crop_%s' % template_name, crop_img)
        logger.debug('Подходит %s, качество %.6f' % (template_name, best_concide))


        if debug:
            cv2.rectangle(image, (best_ii, best_jj), (best_ii + w, best_jj + h), (0, 0, 255), 2)
            coun_unik_name = 1
            while os.path.isfile(img_path[0:-4] + '_debug%d.png' % coun_unik_name):
                coun_unik_name += 1
            cv2.imwrite(img_path[0:-4] + '_debug%d.png' % coun_unik_name, image)

        if return_quality:
            return (best_ii, best_jj), (best_ii + w, best_jj + h), best_concide
        return (best_ii, best_jj), (best_ii + w, best_jj + h)

    logger.debug('Не найден шаблон %s, лучшее совпадение %.6f' % (template_name, best_concide))
    if return_quality:
        return False, None, 0
    return False


def is_collection(obj):
    """ Returns true for any iterable which is not a string or byte sequence.
    """
    if isinstance(obj, str):
        return False
    if isinstance(obj, bytes):
        return False
    try:
        iter(obj)
    except TypeError:
        return False
    try:
        hasattr(None, obj)
    except TypeError:
        return True
    return False


def flatten(list_of_list):
    if list_of_list is None:
        return None
    return list(itertools.chain.from_iterable(x if is_collection(x) else [x] for x in list_of_list if x))

def get_external_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("gmail.com", 80))
    r = (s.getsockname()[0])
    s.close()
    return r

from enum import Enum, EnumMeta


class StrEnumMeta(EnumMeta):
    def __new__(metacls, cls, bases, classdict):
        for member_name in classdict._member_names:
            dict.__setitem__(classdict, member_name, member_name)
        enum_class = super().__new__(metacls, cls, bases, classdict)
        return enum_class

class StrEnum(str, Enum, metaclass=StrEnumMeta):
    def __str__(self):
        return self.name

    def __repr__(self):
        # Need for Django migration generation to work well, because StrEnum is a string type migration serializer uses repr(value) for migration file generation
        return repr(self.name)

def random_str(length=14):
    return ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(length))

def generate_mac():
    return ':'.join('%02x' % random.randrange(256) for _ in range(6))

