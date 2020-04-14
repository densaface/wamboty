import logging
import os
from time import sleep
import shutil
import random
import time
import subprocess
random.seed

from libs.nox import NoxDevice
import libs.common as common

logger = logging.getLogger(__name__)

class Game(object):
    def __init__(self, memu_device: NoxDevice):
        self.device = memu_device

    summoners_data_dir = '/data/data/com.com2us.smon.normal.freefull.google.kr.android.common/'

    def start(self):
        self.device.adb('shell am start -n com.com2us.smon.normal.freefull.google.kr.android.common/com.com2us.smon.normal.freefull.google.kr.android.common.SubActivity')
        sleep(10)

    def stop(self):
        self.device.adb('''shell am force-stop package:com.stgl.global''')

    def input_town(self):
        if self.device.tap_on('input_town', attempts=2):
            if self.device.tap_on('collect', attempts=2, dy=370, threshold=0.79):
                sleep(2)

    def exit_town(self, attempts=1):
        self.chain_taps({'pics': ['back1', 'back2', 'reject_union', {'pic': 'collect', 'dy': 370}, 'exit_town',
                                  {'pic': 'input_town', 'notap': 1}], 'threshold': 0.75, 'end_pic': ['input_town']})
        sleep(2)

    def horse(self):
        if not self.device.is_image('teleport'):
            return False
        ret = self.device.wait_for('horse', one_attempt=True, threshold=0.75)
        if not ret[0]:
            return False
        if ret[1][0][0] > 650:
            self.device.swipe(-200, 0)
            sleep(1)
        if ret[1][0][1] > 310:
            self.device.swipe(0, -200)
            sleep(1)
        if not self.device.tap_on('horse', one_attempt=True, threshold=0.75):
            return False
        return True

    def chain_taps(self, pics, interval_after_tap=0):
        pict_names = ()
        pics_opt = []  # опции поиска картинок (смещение клика или отсутствие клика)
        if type(pics['pics']) is list:
            for pic in pics['pics']:
                if type(pic) is dict:
                    pict_names += (pic['pic'], )
                    pics_opt.append(pic)
                else:
                    pict_names += (pic, )
        else:
            pict_names = pics['pics']

        ret = self.device.wait_for(pict_names, threshold=pics['threshold'], attempts=3)
        coun_attempts = 0
        while True:
            coun_attempts += 3
            if coun_attempts > 100:
                raise Exception('chain_taps timeout')
            if not ret[0]:
                ret = self.device.wait_for(pict_names, threshold=pics['threshold'], attempts=3)
                continue
            tapped = False
            for pic in pics_opt:
                if pic['pic'] == ret[0]:
                    dy = dx = 0
                    if 'dx' in pic:
                        dx = pic['dx']
                    if 'dy' in pic:
                        dy = pic['dy']
                    if 'notap' in pic and pic['notap']:
                        pass
                    else:
                        self.device.tap(ret[1], dx=dx, dy=dy)
                    if 'addtapx' in pic:
                        sleep(1)
                        self.device.tap((pic['addtapx'], pic['addtapy']))
                    tapped = True
                    break
            if not tapped:
                self.device.tap(ret[1])
                if interval_after_tap:
                    sleep(interval_after_tap)
            for pic in pics_opt:
                if pic['pic'] == ret[0]:
                    if 'sleep' in pic:
                        sleep(pic['sleep'])
                    break
            if ret[0] in pics['end_pic']:
                return True
            ret = self.device.wait_for(pict_names, threshold=pics['threshold'], attempts=3)

    def go_to_start(self, attempt = 1):
        if attempt > 20:
            return False
        self.exit_town()
        self.chain_taps({'pics': ('glob_map', 'favorites', 'start', 'start2'), 'threshold': 0.75, 'end_pic': ['start', 'start2']})
        sleep(4)
        self.device.tap((400 + random.randint(-200, 250), 250 + random.randint(-150, 100)))
        sleep(2)
        if self.device.tap_on('explore', one_attempt=True, threshold=0.75):
            self.device.tap_on('explore2', threshold=0.78, attempts=3)
            sleep(6)
            self.device.tap((400 + random.randint(-200, 250), 250 + random.randint(-150, 100)))
        if not self.horse():
            return self.go_to_start(attempt+1)
        self.device.tap_on('autofill', one_attempt=True, threshold=0.75)
        sleep(1)
        self.device.tap_on('go', one_attempt=True, threshold=0.76)
        sleep(1)
        logger.debug('sleeping 4.5 minutes')
        sleep(60*4.5)
        return True

    def search_mine(self, level, attempt=1, attempts=8, type_search='mine_pit'):
        if attempt > attempts:
            return False
        if level < 1:
            return False
        sleep(1)
        self.device.tap_on('search', threshold=0.75)
        for _ in range(10):
            if self.device.tap_on('search_treasure', threshold=0.75, attempts=2):
                break
            if not self.device.tap_on('search', threshold=0.75):
                return False
        self.device.tap_on(type_search, threshold=0.75)
        sleep(1)

        self.device.tap_on('remove_ally', threshold=0.95, attempts=1, dx=15, dy=15)
        if not self.device.is_image('level_mine_' + str(level), threshold=0.85):
            for _ in range(level-1):
                self.device.tap_on('search_plus', threshold=0.9, attempts=2)
                sleep(0.5)
        for ii in range(7-level):
            if self.device.is_image('level_mine_' + str(level), threshold=0.85):
                if not self.device.tap_on(('search_button_gold', 'search_button'), attempts=2):
                    return False
                else:
                    if type_search == 'search_spear':
                        return True
                    if self.device.tap_on('gather', attempts=4):
                        return True
                    if attempt > 7:
                        return False
                    # if int(time.time()) % 2 == 0:
                    #     return self.search_mine(level - 1, attempt + 1, type_search=type_search)
                    # else:
                    return self.search_mine(level, attempt + 1, type_search=type_search)
            self.device.tap_on('search_minus', threshold=0.8, attempts=3)
            sleep(1)

        return False

    def search_monsters(self, level_monsters, search_gold=False):
        self.device.tap_on('search')
        if not self.device.tap_on('search_beast', attempts=3):
            self.device.tap_on('search')
            if not self.device.tap_on('search_beast', attempts=3):
                self.device.tap_on('search')
                if not self.device.tap_on('search_beast', attempts=3):
                    raise Exception('search_monsters error: not found beast picture')
        sleep(1)
        for ii in range(20):
            screenshot_fn = self.device.make_screenshot()
            level = self.get_numbers(screenshot_fn, 'search_plus', 'search_ciph_', permit_except=True,
                                   threshold=0.90, cropx1=35, cropx2=45, cropy2=6)
            if level == -1:
                self.device.tap_on('search')
                self.device.tap_on('search_beast', attempts=3)
                screenshot_fn = self.device.make_screenshot()
                level = self.get_numbers(screenshot_fn, 'search_plus', 'search_ciph_', permit_except=True,
                                       threshold=0.90, cropx1=35, cropx2=45, cropy2=6)
                if level == -1:
                    raise Exception('Not found search button on the map')
            if level == int(level_monsters[0]):
                if search_gold:
                    if not self.device.tap_on(('search_button', 'search_button_gold'), attempts=1):
                        raise Exception('No buttons search_button and search_button_gold') # не должно такого быть
                else:
                    if not self.device.tap_on('search_button', attempts=1):
                        if self.device.is_image('search_button_gold'):
                            self.device.tap((250, 50))
                            return False
                attmpts = 2
                while self.device.wait_for('dragon_mouth', attempts=attmpts)[0]:
                    attmpts = 1
                    sleep(0.1)
                sleep(1)
                return True
            if not self.device.tap_on('search_minus', threshold=0.8, attempts=3):
                self.device.tap_on('search')
                self.device.tap_on('search_beast', attempts=3)
            sleep(1)
        return False

    def end_battle(self, timeout=20):
        for ii in range(timeout):
            ret = self.device.wait_for(('battle_end', 'auto_battle', 'tonus_finished', 'battle_admire'), attempts=2)
            if ret[0]:
                if ret[0] == 'tonus_finished':
                    self.device.tap((380, 80))
                    return 'tonus_finished'
                if ret[0] == 'auto_battle':
                    self.device.tap(ret[1])
                    continue
                if ret[0] == 'battle_admire':
                    self.device.tap(ret[1], dx=-450)
                    return
                sleep(3)  # кликаем чуть позже после нахождения, чтобы анимация не привела к пробуксовке и отставанию скрипта
                if self.device.tap_on('battle_end', dx=-250, one_attempt=True):
                    self.device.tap_on('battle_admire', dx=-450, attempts=3)
                    return
            if ii > timeout/2:
                if not self.device.tap_on('auto_battle', attempts=2, threshold=0.85):
                    self.device.tap((400, 250))
                    self.finger()
            if ii > timeout*2/3 and self.device.wait_for('glob_map', attempts=2)[0]:
                return

    def return_from_collecting(self):
        while self.device.tap_on('collecting', attempts=2, threshold=0.85, dx=180):
            sleep(1)

    # преобразование картинки с цифрами в цифры
    def get_numbers(self, screenshot_fn, img_anchor, pat_ciph, permit_except=True, threshold=0.98,
                    prepared_scr_shot='', cropx1=25, cropy1=1, cropx2=60, cropy2=1, add_symb={}, ciph_distance=4,
                    prefer_x=-1, prefer_y=-1, radius=0,
                    return_int=True, threshold_anchor=0.76,
                    grain=0, grain_x2=0, grain_y1=0, grain_y2=0):
        if not screenshot_fn:
            screenshot_fn = self.device.make_screenshot()
        if not prepared_scr_shot:
            ret = self.device.wait_for(img_anchor, one_attempt=True, threshold=threshold_anchor, prepared_scr_shot=screenshot_fn,
                prefer_x=prefer_x, prefer_y=prefer_y, radius=radius,
                crop=True, cropx1=cropx1, cropy1=cropy1, cropx2=cropx2, cropy2=cropy2,
                grain=grain, grain_x2=grain_x2, grain_y1=grain_y1, grain_y2=grain_y2)
            prepared_scr_shot = screenshot_fn[:-4] + '_crop_%s.png' % img_anchor
            if not ret[0]:
                if permit_except:
                    raise Exception('Not found anchor template %s!' % img_anchor)
                return -1
        resx = ''
        all_res = []
        for ii in range(10):
            try:
                coords = self.device.get_all_images(pat_ciph + str(ii), debug=True, threshold=threshold, method_search=2,
                                                prepared_scr_shot=prepared_scr_shot, delta_coor=6)
                for jj in range(len(coords)):
                    all_res.append(coords[jj] + (ii, ))
            except Exception as e:
                logger.debug(str(e))
        for key in add_symb:
            coords = self.device.get_all_images(pat_ciph + key, debug=True, threshold=threshold, method_search=2,
                                                prepared_scr_shot=prepared_scr_shot, delta_coor=6)
            for jj in range(len(coords)):
                all_res.append(coords[jj] + (add_symb[key],))

        all_res = sorted(all_res, key=lambda tup: tup[0])
        # удаляем похожие цифры, например, 8 похожа на 3, но точность нахождения будет меньше чем у 3
        for ii in reversed(range(1, len(all_res))):
            if abs(all_res[ii][0] - all_res[ii - 1][0]) < ciph_distance:
                if all_res[ii][2] > all_res[ii - 1][2]:
                    all_res = all_res[:ii - 1] + all_res[ii:]
                else:
                    if ii == len(all_res) - 1:
                        all_res = all_res[:ii]
                    else:
                        all_res = all_res[:ii] + all_res[ii+1:]
        for ii in range(len(all_res)):
            resx += str(all_res[ii][3])
        logger.debug("get_numbers text value = " + resx)
        if return_int:
            if not permit_except:
                try:
                    return int(resx)
                except Exception as e:
                    return -1
            return int(resx)
        else:
            return resx

    def get_power(self, permit_except=True, prep_fn=''):
        for ii in range(10):
            if ii == 9:
                raise Exception('get_power error')
            try:
                if prep_fn:
                    screenshot_fn = prep_fn
                else:
                    screenshot_fn = self.device.make_screenshot()
                res = self.get_numbers(screenshot_fn, 'battle_corruption', 'power_ciph_', permit_except=False, threshold=0.8, cropx1=125, cropx2=90, ciph_distance=5)
                break
            except Exception as e:
                logger.debug(str(e))
                sleep(5)
        # if res not in [59488, 273173]:
        #     logger.debug('debme')
        if res == -1:
            if permit_except:
                raise Exception('wrong recommended power')
        return res

    def get_treasure(self):
        deb = 1

    def monitor_acc(self, time_mon):
        self.back()
        ret = self.device.wait_for(('attack_me', 'continue'), threshold=0.78, attempts=time_mon)
        if ret[0]:
            self.device.tap(ret[1])
            if self.device.tap_on('defence', threshold=0.78, attempts=5, dx=-160, dy=33):
                ret = self.device.wait_for(('return_hero_from_res', 'city_bonus'), threshold=0.78, attempts=5)
                if ret[0]:
                    self.device.tap(ret[1])
                    if ret[0] == 'city_bonus':
                        sleep(2)
                        self.device.tap_on('peace_gurdian', threshold=0.78, attempts=5)
                        sleep(2)
                        self.device.tap_on('use_button', threshold=0.78, attempts=5)
                        sleep(2)
            self.back(2)

    def fish(self, acc, fish_count):
        if not self.device.tap_on('fish_high', threshold=0.78, attempts=5):
            logger.debug('Не найдена кнопка fish_high для силы удочки')
            return False
        pull_button = self.device.wait_for('fish_cast', threshold=0.8, attempts=2)
        if not pull_button[0]:
            logger.debug('Не найдена кнопка заброса удочки')
            return False
        for ii in range(fish_count):
            rand_x = pull_button[1][0][0]+random.randint(20, 30)
            rand_y = pull_button[1][0][1]+random.randint(20, 30)
            self.device.adb("shell input touchscreen swipe %d %d %d %d 1500" %
                            (rand_x, rand_y, rand_x, rand_y, ))
            for jj in range(40):
                if jj == 39:
                    if self.device.tap_on('donation', threshold=0.78, attempts=3, dy=-150):
                        logger.debug('Кончились наживки')
                        return
                    break # raise Exception('debug plz') - глюк в игре как будто, рыба и не сорвалась и удочка не заброшена
                fn = self.device.make_screenshot()
                if self.device.wait_for(('fish_on_the_hook', 'fish_rod_bent', 'fishhook_bitten',
                        'fish_bobber_gone', 'fish_sea_shimmering', 'fish_seems_hook', 'fish_float_bobbing'),
                        threshold=0.8, attempts=1, prepared_scr_shot=fn, # templates_exclude='fish_exclude',
                        grain_x2=40, grain_y1=90, grain_y2=175, break_first_find=True)[0]:
                    self.device.tap(pull_button[1])
                    sleep(4)
                    self.device.tap((475, 250))
                    self.device.tap((475, 250))
                    sleep(3)
                    break
        logger.debug('Рыбалка окончена')

    def send_heroes(self, acc, min_load = -2):
        ret_go = self.go_supermine(min_load=min_load)
        if not ret_go == 'check':
            if not ('login_once' in acc and acc['login_once']):
                harvs = ['sawmill', 'sawmill', 'sawmill', 'farmland', 'farmland']
                for jj in range(acc['heroes'] + 1):
                    random.shuffle(harvs)
                    ret = self.get_harvest(harvs, acc, min_load=min_load)
                    if ret in ['check', 'noload']:
                        self.input_town()
                        return ret
        return True

    def grab_twin(self, acc, main_acc, get_food=False, get_wood=False, get_crystalls=False, get_gems=False, only_step1=False, only_step2=False):
        device = self.device
        if only_step1 or (only_step1 is False and only_step2 is False):
            self.relogin_acc(acc)
            device.tap((190, 45))
            if device.wait_for('safe_production_big', threshold=0.78, attempts=3)[0]:
                logger.debug('skip acc by cause of safe mode protection')
                self.back()
                return False
            self.exit_town()
            while self.device.tap_on('hero_return', threshold=0.75, attempts=2, grain=50):
                # while self.device.tap_on(('hero_returning', 'hero_return'), threshold=0.85, template_exclude='hero_return',
                #                          attempts=2):
                sleep(5)
            self.input_town()
            self.get_events()
            self.back()
            self.ellary()
            self.exit_town()
            self.device.tap_on('expand_heroes', one_attempt=True, threshold=0.85)
            while self.device.tap_on(('hero_returning', 'hero_return'), threshold=0.75, attempts=2):
                # while self.device.tap_on(('hero_returning', 'hero_return'), threshold=0.85, template_exclude='hero_return',
                #                          attempts=2):
                sleep(5)
            ret = self.send_heroes(acc, min_load=80000)
            if not ret == 'check':
                self.hide_hero(acc)
            sleep(4)
            # ВЫКЛАДЫВАЕМ ВСЕ НА СТОЛ + СПРЯТАТЬ ГЕРОЕВ + желания эллари + синих крисов достать
            if get_food:
                if not self.device.tap_on('food_small_icon', attempts=2, threshold=0.85):
                    logger.info('Error find picture food_small_icon!!!')
                    return False
                while self.device.tap_on(('use_button_red', 'use_button'), attempts=4, threshold=0.85):
                    sleep(2)
                if not get_wood and not get_crystalls and not get_gems:
                    self.back()
            if get_wood:
                if not get_food:
                    if not self.device.tap_on('food_small_icon', one_attempt=True, threshold=0.85):
                        logger.info('Error find picture food_small_icon!!!')
                        return False
                if not self.device.tap_on('res_info_wood', attempts=4, threshold=0.85):
                    logger.info('Error find picture res_info_wood!!!')
                    return False
                while self.device.tap_on(('use_button_red', 'use_button'), one_attempt=True, threshold=0.85):
                    sleep(2)
                if not get_crystalls and not get_gems:
                    self.back()
            if get_crystalls:
                if not get_food and not get_wood:
                    if not self.device.tap_on('food_small_icon', one_attempt=True, threshold=0.85):
                        logger.info('Error find picture food_small_icon!!!')
                        return False
                if not self.device.tap_on('res_info_blue_cristalls', attempts=4, threshold=0.85):
                    logger.info('Error find picture res_info_blue_cristalls!!!')
                    return False
                while self.device.tap_on(('use_button_red', 'use_button'), one_attempt=True, threshold=0.85):
                    sleep(2)
                if not get_gems:
                    self.back()
            if get_gems:
                if not get_food and not get_wood and not get_crystalls:
                    if not self.device.tap_on('food_small_icon', one_attempt=True, threshold=0.85):
                        logger.info('Error find picture food_small_icon!!!')
                        return False
                if not self.device.tap_on('res_info_red_gems', attempts=3, threshold=0.85):
                    logger.info('Error find picture res_info_red_gems!!!')
                    return False
                while self.device.tap_on('use_button', one_attempt=True, threshold=0.85):
                    sleep(3)
                if not get_gems:
                    self.back()
            logger.info('STEP 1 FINISHED')

        if only_step2 or (only_step1 is False and only_step2 is False):
            self.input_town()
            self.exit_town()
            coors = self.get_coors()
            harvs = ['sawmill', 'sawmill', 'sawmill', 'sawmill', 'farmland']
            for jj in range(acc['heroes']):
                random.shuffle(harvs)
                # self.get_harvest(harvs, acc)
            self.relogin_acc(main_acc)
            self.exit_town()
            # coors = (636, 656)
            self.return_from_collecting()
            self.go_coors(coors)
            coun = 0
            sleep(2)
            self.device.tap((440, 250))
            sleep(1)
            if not self.device.tap_on('scout', threshold=0.78, attempts=3, dx=25, dy=25):
                if self.device.tap_on('explore', one_attempt=True, threshold=0.75):
                    if not self.device.tap_on('explore2', threshold=0.78, attempts=3):
                        sleep(3)
                    else:
                        sleep(6)
                    self.device.tap((440, 250))
                    sleep(1)
                    self.device.tap_on('scout', threshold=0.78, attempts=3, dx=25, dy=25)

            sleep(5)
            self.device.tap_on('expand_heroes', one_attempt=True, threshold=0.85)
            while self.device.tap_on('scout_to', attempts=3, threshold=0.87):
                sleep(2)
            device.tap_on('mail', threshold=0.78, attempts=2)
            sleep(5)
            device.tap_on('excellent_report', threshold=0.9, attempts=10, template_exclude='excellent_report_read')
            sleep(3)
            screenshot_fn = self.device.make_screenshot()
            add_symb = {'5_2': '5', '9_2': '9', '6_2': '6', '0_2': '0', '8_2': '8'}
            res_f = self.get_numbers(screenshot_fn, 'mail_food', 'mail_res_ciph_', grain=50, add_symb=add_symb, cropx1=34,
                                   cropx2=90, ciph_distance=6, threshold=0.99)
            res_w = self.get_numbers(screenshot_fn, 'mail_wood', 'mail_res_ciph_', grain=150, add_symb=add_symb, cropx1=39,
                                   cropx2=90, ciph_distance=6, threshold=0.99)
            res_c = self.get_numbers(screenshot_fn, 'mail_cristalls', 'mail_res_ciph_', grain=150, add_symb=add_symb, cropx1=33,
                                 cropx2=90, ciph_distance=6, threshold=0.99)
            sum_res = res_f + res_w + 5 * res_c
            atacks_count = int((sum_res+500000)/1000000)

            self.back()
            self.back()
            self.device.tap((440, 250))

            sum_load_pow = 0
            all_loads = []
            if device.wait_for('attack_town', threshold=0.78)[0]:      # ВЫСТАВИТЬ ФАРМЯЩИЕ ВОЙСКА, УСТАНОВИТЬ ЧИСЛО БОЕВ, КНОПКА АТАКИ
                for _ in range(999):
                    if device.tap_on('attack_town', threshold=0.78, attempts=3, dy=20):
                        max_load = 0
                        for zz in range(3):
                            if device.tap_on('autofill', threshold=0.78, attempts=2):
                                cur_load = self.get_load_power()
                                if cur_load in all_loads:
                                    break
                                if cur_load > max_load:
                                    max_load = cur_load
                            self.change_set_troops()
                        if cur_load not in all_loads:
                            for zz in range(3):
                                cur_load = self.get_load_power()
                                if cur_load >= max_load:
                                    break
                                self.change_set_troops()

                        cur_load = self.get_load_power()
                        sum_load_pow += cur_load
                        if cur_load not in all_loads:
                            all_loads.append(cur_load)
                        device.tap_on('go', threshold=0.78, attempts=2)
                        # coun += 1
                        # if coun >= atacks_count:
                        #     break
                        if sum_load_pow + 300000 > sum_res:
                            break
                        else:
                            if device.tap_on('check', threshold=0.78, attempts=2):
                                logger.debug('waiting 15 seconds for next atack')
                                logger.debug("attack loaded resources = " + str(sum_load_pow) + " from " + str(sum_res))
                                sleep(10)
                            self.go_coors(coors)
                    else:
                        self.go_coors(coors)
                    sleep(1)
                    device.tap((425, 280))
            sleep(2)
            self.device.tap((400, 250))
            self.device.tap_on('scout', threshold=0.78, attempts=3)
            self.device.tap_on('scout', threshold=0.78, attempts=3)
            logger.debug("attack loaded resources = " + str(sum_load_pow) + " from " + str(sum_res))
            sleep(60*3) # пауза, чтобы герои успели атаковать город и после этого в него заходить
            self.relogin_acc(acc)
            sleep(4)
            device.tap_on('extinguish_fire1', threshold=0.68, attempts=5)
            if not device.tap_on('extinguish_fire', threshold=0.78, attempts=5):
                print('why not found')
            device.tap_on('repare_wall', threshold=0.78, attempts=3)
            self.back()
            self.upgrade_town()
            logger.info('STEP 2 FINISHED')
        return True

    def fill_empty_place(self):
        thres = 0.45  # низкий парог нахождения пустого места, потому что они довольно сильно отличаются друг от друга
        if not self.move_to_img('empty_place', 10, -100, 50, threshold=thres):
            return False
        sleep(2)
        self.device.tap_on('empty_place', threshold=thres, attempts=1, dx=25, dy=25)
        if self.device.tap_on('constract_button', attempts=2):
            if self.build_free_or_help():
                self.device.tap_on('constract_button', attempts=2)
                return self.fill_empty_place()
            return True
        return False

    def fish_market(self):
        for patt in ['fish_market_wood', 'fish_market_food', 'fish_market_cristalls', ]:
            if self.device.tap_on(patt, threshold=0.8, attempts=1, dx=220, dy=35):
                sleep(2)

    def get_coors(self, permit_except=True):
        self.device.tap_on('map_coors', one_attempt=True, threshold=0.76)
        for _ in range(5):
            if not self.device.wait_for('coors_x', attempts=2, threshold=0.76):
                self.device.tap_on('map_coors', one_attempt=True, threshold=0.76)
        screenshot_fn = self.device.make_screenshot()
        add_symb = {'5_2': '5', '8_2': '8', '3_2': '3', '0_2': '0'}
        resx = self.get_numbers(screenshot_fn, 'coors_x', 'coors_ciph_', grain=150, add_symb=add_symb, permit_except=False)
        resy = self.get_numbers(screenshot_fn, 'coors_y', 'coors_ciph_', grain=150, add_symb=add_symb, permit_except=False)
        if resx == -1 or resy == -1:
            return False
        self.device.tap((250, 40))
        return resx, resy

    def go_coors(self, coors):
        for _ in range(3):
            try:
                self.device.tap_on('map_coors', attempts=10, threshold=0.76)
                sleep(1)
                self.device.tap_on('coors_x', attempts=5, threshold=0.76, dx=70, grain=100)
                self.device.tap_on('coors_x', attempts=5, threshold=0.76, dx=70, grain=100)
                self.device._send_event('KEYCODE_DEL', num_ev=5)
                self.device.send_text(coors[0])
                self.device.tap_on('coors_y', attempts=5, threshold=0.76, dx=70, grain=100)
                self.device.tap_on('coors_y', attempts=5, threshold=0.76, dx=70, grain=100)
                self.device._send_event('KEYCODE_DEL', num_ev=5)
                self.device.send_text(coors[1])
                # дважды нажимаем прыжок, потому что первый просто дефокусирует окошко
                self.device.tap_on('jump', one_attempt=True, threshold=0.76)
                if not self.device.tap_on('jump', one_attempt=True, threshold=0.76):
                    raise Exception('Jump error')
                sleep(1)
                for ii in range(9):
                    if ii == 9-1:  # предотвращаем ситуацию, когда зависает переход на смыкающемся драконе
                        raise Exception('Jump error: map_go_hang')
                    if not self.device.wait_for('map_go_hang', one_attempt=True, threshold=0.76)[0]:
                        break
                    sleep(1)

                break
            except Exception as e:
                logger.debug(str(e))
                self.device.stop()
                self.device.start()
                sleep(12)
                self.device.wait_loaded()
                self.device._send_event("KEYCODE_HOME")
                self.device.tap_on('wam_icon', threshold=0.85, false_is_except=True)
                self.clear_dialogs_after_login()
                self.exit_town()

    def get_events(self, attempt=1):
        self.device.tap_on('event_center', threshold=0.8, attempts=3)
        if not self.device.wait_for(('back1', 'back2'), threshold=0.79, attempts=12)[0]:
            return
        if self.device.tap_on('event_road_to_honor', threshold=0.8, attempts=1):
            for _ in range(10):
                if self.device.tap_on('event_red_circle2', threshold=0.63, one_attempt=True):
                    self.device.tap((545, 156))
                if not self.device.tap_on('event_red_circle', threshold=0.7, attempts=3):
                    break
                if self.device.tap_on('event_red_circle2', threshold=0.63, one_attempt=True):
                    self.device.tap((545, 156))
                for _ in range(10):
                    if not self.device.tap_on('event_to_claim', threshold=0.63, one_attempt=True):
                        break
                    sleep(1)

        fn = self.device.make_screenshot()
        if self.device.tap_on('event_war_praparation', threshold=0.8, attempts=1, prepared_scr_shot=fn):
            sleep(2)
            for _ in range(14):
                isRedCircle=False
                for _ in range(3):
                    if self.device.tap_on('event_red_circle4', threshold=0.63, one_attempt=True):
                        isRedCircle = True
                        break
                    self.device.swipe(0, -100, x0=100, y0=200)
                if not isRedCircle:
                    break
                sleep(2)
                for _ in range(10):
                    if not self.device.tap_on('event_to_claim2', threshold=0.63, one_attempt=True):
                        break
                    sleep(1)
            self.back()
            sleep(1)
            fn = self.device.make_screenshot()

        if self.device.tap_on('event_research_carnival', threshold=0.8, attempts=1, prepared_scr_shot=fn):
            sleep(2)
            for _ in range(10):
                self.device.tap_on('event_red_circle4', threshold=0.55, one_attempt=True, dy=20, dx=-20)
                if not self.device.tap_on('event_to_claim2', threshold=0.63, one_attempt=True):
                    break
                sleep(1)
            self.back()
            sleep(1)
            fn = self.device.make_screenshot()

        if self.device.tap_on('event_wanted_order', threshold=0.8, attempts=1, prepared_scr_shot=fn):
            sleep(2)
            for _ in range(10):
                self.device.tap_on('event_red_circle2', threshold=0.63, one_attempt=True, dy=20, dx=-20)
                if not self.device.tap_on('event_to_claim2', threshold=0.63, one_attempt=True):
                    break
                sleep(1)
            self.back()
            sleep(1)
            fn = self.device.make_screenshot()

        if self.device.tap_on('event_chicken_farm', threshold=0.8, attempts=1, prepared_scr_shot=fn):
            for _ in range(10):
                if not self.device.tap_on('event_chicken_hand', threshold=0.64, attempts=4):
                    break
                else:
                    logger.info('hurray: Chicken had got!')

            if self.device.tap_on('event_chicken_pray', threshold=0.8, attempts=3):
                self.device.tap_on('event_chicken_reses', threshold=0.8, attempts=3)
                self.device.tap_on('event_chicken_adv_pray', threshold=0.8, attempts=3)
                self.device.tap_on('event_chicken_adv_pray', threshold=0.8, attempts=3)
                self.device.tap_on('event_chicken_adv_pray', threshold=0.8, attempts=3)
                self.back()
                self.back()

            if self.device.tap_on('event_chicken_graze', threshold=0.8, attempts=3):
                for _ in range(7):
                    self.device.tap_on('troop_plus', threshold=0.63, attempts=2)
                sleep(1)
                self.device.tap_on('use_button', threshold=0.63, attempts=1)
            self.back()
            sleep(1)
            fn = self.device.make_screenshot()

        if self.device.tap_on(('event_elemental_collection', 'event_war_praparation'), threshold=0.8, attempts=1, prepared_scr_shot=fn):
            sleep(2)
            for _ in range(14):
                isRedCircle=False
                for _ in range(5):
                    if self.device.tap_on('event_red_circle2', threshold=0.63, one_attempt=True):
                        isRedCircle = True
                        break
                    self.device.swipe(0, -100, x0=100, y0=200)
                if not isRedCircle:
                    break
                sleep(2)
                for _ in range(10):
                    if not self.device.tap_on('event_to_claim3', threshold=0.63, one_attempt=True):
                        break
                    sleep(1)
            self.back()
            sleep(1)
            fn = self.device.make_screenshot()

        if self.device.tap_on(('event_snow', 'event_maslen'), threshold=0.8, attempts=1, prepared_scr_shot=fn):
            sleep(2)
            for _ in range(14):
                if not self.device.tap_on('event_red_circle3', threshold=0.42, attempts=2, dx=50, dy=25):
                    self.device.tap((530, 40))
                    if not self.device.tap_on('event_red_circle3', threshold=0.42, attempts=2, dx=50, dy=25):
                        break
                self.device.tap((530, 190))
                sleep(2)
                self.device.tap((530, 40))
                if self.device.tap_on('event_red_circle2', threshold=0.63, one_attempt=True):
                    self.device.tap((530, 190))
                    sleep(2)
                    self.device.tap((530, 40))
                for _ in range(10):
                    if not self.device.tap_on('event_to_claim3', threshold=0.63, one_attempt=True):
                        break
                    sleep(1)
            self.back()
            sleep(1)
            fn = self.device.make_screenshot()

        if self.device.tap_on('event_lady_lack', threshold=0.8, attempts=1, prepared_scr_shot=fn):
            if self.device.tap_on('event_lady_free_x1', threshold=0.8, attempts=3):
                sleep(6)
                self.back()
            self.back()
            sleep(1)
            fn = self.device.make_screenshot()

        if self.device.tap_on('event_secret_society', threshold=0.8, attempts=1, prepared_scr_shot=fn):
            for _ in range(3):
                self.device.tap_on('collect_quest3', one_attempt=True, threshold=0.7)
                sleep(2)
                self.device.tap((250, 50))
            self.device.tap((290, 160))
            self.device.tap((250, 50))
            self.back()
            sleep(1)
            fn = self.device.make_screenshot()

        # if self.device.tap_on('research_carnival', threshold=0.8, attempts=2):


        if self.device.tap_on(('harvest_carnival', 'research_carnival'), threshold=0.8, attempts=1, prepared_scr_shot=fn):
            for ii in range(25):
                if not self.device.tap_on('event_red_circle', threshold=0.55, attempts=3):
                    break
                ret = self.device.wait_for('event_red_circle2', threshold=0.63, one_attempt=True)
                if ret[0]:
                    self.device.tap(ret[1])
                    if ret[1][0][0] > 750 and ret[1][0][0] < 780 and ret[1][0][1] > 85 and ret[1][0][0] > 105:
                        sleep(1)
                        self.device.tap((543, 161))  # забираем голдишку
                        sleep(2.5)
                        self.device.tap((250, 20))
                for _ in range(10):
                    if self.device.tap_on('event_to_claim2', threshold=0.63, attempts=2):
                        sleep(3)
                    else:
                        break
            self.device.tap((236, 445))  # забираем сундук с наградами
            sleep(3)
            self.back()
            if self.device.tap_on('harvest_festival', threshold=0.8, attempts=2):
                self.device.tap_on('donate_material', threshold=0.8, attempts=2)
                if self.device.tap_on('confirm_button3', threshold=0.8, attempts=2):
                    sleep(3)
                    self.device.tap((250, 20))
                self.device.tap_on('event_join_party', threshold=0.8, attempts=2)
                self.back()
            sleep(1)
            fn = self.device.make_screenshot()

        if self.device.tap_on('event_adv_road', threshold=0.8, attempts=2, prepared_scr_shot=fn):
            sleep(2)
            self.device.tap((250, 40))
            self.device.tap((250, 40))
            self.device.tap((250, 40))
            for ii in range(30):
                ret = self.device.wait_for(('event_check_box', 'event_confirm_button', 'purchase', 'event_rem_times'), threshold=0.8, attempts=5)
                if not ret[0]:
                    self.back()
                    break
                elif ret[0] == 'event_rem_times':
                    self.device.tap(ret[1], dx=-70, dy=-50)
                    sleep(2)
                elif ret[0] == 'purchase':
                    self.device.tap((250, 40))
                    self.back()
                    break
                else:
                    self.device.tap(ret[1])
            self.back()
        if self.device.tap_on(('event_gomoku', '5stars'), threshold=0.8, one_attempt=True, prepared_scr_shot=fn):
            sleep(3)
            for _ in range(20):
                if not self.device.tap_on('event_gomoku_red_number', threshold=0.60, one_attempt=True):
                    break
                sleep(3)
                for _ in range(10):
                    if not self.device.tap_on('event_to_claim', threshold=0.65, one_attempt=True):
                        self.device.tap((40, 250))
                        break
                    sleep(1.5)
            self.back()
            sleep(1)
            fn = self.device.make_screenshot()

        self.device.tap_on('event_center', threshold=0.8, one_attempt=True, prepared_scr_shot=fn)
        if attempt == 1:
            self.device.swipe(0, -200)
            self.device.swipe(0, -200)
            sleep(2.5)
            self.get_events(attempt+1)
            self.back()
            sleep(1)
            fn = self.device.make_screenshot()

        if self.device.tap_on('royal_hunting', threshold=0.8, attempts=2, prepared_scr_shot=fn):
            self.device.adb("shell input touchscreen swipe 425 250 425 250 7238")
            sleep(3)
            self.device.adb("shell input touchscreen swipe 425 250 425 250 7238")
            sleep(3)
            self.device.adb("shell input touchscreen swipe 425 250 425 250 7238")
            sleep(2)
            self.back()
            # self.device.adb("shell input touchscreen swipe 425 250 425 250 1217")
            sleep(1)
            fn = self.device.make_screenshot()

        self.back()
        if self.device.tap_on(('event_warrior_trial', 'event_warrior_trial2'), threshold=0.7, attempts=2):
            self.device.tap_on('event_war_quick_collect', threshold=0.93, attempts=5, dx=40)
            self.back()
            self.back()
        self.back()
        # if self.device.tap_on('siege_tutorial', threshold=0.65, attempts=2):
        #     self.end_battle()

    def return_main_hero(self, mine_info):
        self.go_coors(mine_info['coors'])
        sleep(3)
        self.device.tap((425, 250))
        sleep(1)
        if self.device.tap_on('return_hero_from_res', threshold=0.78, attempts=5):
            return True
        return False

    def get_load_power(self):
        sleep(1.5)
        screenshot_fn = self.device.make_screenshot()
        add_symb = {}  # '5_2': '5'} # , '8_2': '8', '3_2': '3', '0_2': '0'
        ret = self.device.wait_for(('hero_panda', 'hero_mage', 'hero_archa', 'hero_barbar', 'hero_necro',
                                    'hero_lafia', 'hero_druid', 'hero_phoenix'),
                                   attempts=1, threshold=0.7, prepared_scr_shot=screenshot_fn)  # cropx1=0, cropx2=40, cropy1=35, cropy2=40
        threshold_anchor = 0.67
        if ret[0] == 'hero_panda':
            load_pow = self.get_numbers(screenshot_fn, 'autofill', 'load_ciph_panda_', add_symb={}, cropx1=-120, cropx2=-40, cropy1=-40, cropy2=-30, ciph_distance=6,
                               threshold=0.91, threshold_anchor=threshold_anchor,
                               prefer_x=770, prefer_y=400, radius=40, permit_except=False)
        elif ret[0] == 'hero_mage':
            load_pow = self.get_numbers(screenshot_fn, 'autofill', 'load_ciph_mage_', add_symb={}, cropx1=-120, cropx2=-40, cropy1=-40, cropy2=-30, ciph_distance=6,
                               threshold=0.92, threshold_anchor=threshold_anchor,
                               prefer_x=770, prefer_y=400, radius=40, permit_except=False)
        elif ret[0] == 'hero_archa':
            load_pow = self.get_numbers(screenshot_fn, 'autofill', 'load_ciph_arch_', add_symb={}, cropx1=-120, cropx2=-40, cropy1=-40, cropy2=-30,
                                ciph_distance=6,
                                threshold=0.98, threshold_anchor=threshold_anchor,
                                prefer_x=770, prefer_y=400, radius=40, permit_except=False)
        elif ret[0] == 'hero_barbar':
            load_pow = self.get_numbers(screenshot_fn, 'autofill', 'load_ciph_barb_', add_symb={'8_2': '8', '1_2': '1', '1_3': '1', '4_2': '4', '7_2': '7'}, cropx1=-120, cropx2=-40, cropy1=-40, cropy2=-30,
                                ciph_distance=6,
                                threshold=0.96, threshold_anchor=threshold_anchor,
                                prefer_x=770, prefer_y=400, radius=40, permit_except=False)
        elif ret[0] == 'hero_necro':
            load_pow = self.get_numbers(screenshot_fn, 'autofill', 'load_ciph_necr_', add_symb={}, cropx1=-120, cropx2=-40, cropy1=-40, cropy2=-30, ciph_distance=6,
                                threshold=0.93, threshold_anchor=threshold_anchor,
                                prefer_x=770, prefer_y=400, radius=40, permit_except=False)
        elif ret[0] == 'hero_lafia':
            load_pow = self.get_numbers(screenshot_fn, 'autofill', 'load_ciph_necr_', add_symb={}, cropx1=-120, cropx2=-40, cropy1=-40, cropy2=-30, ciph_distance=6,
                                threshold=0.95, threshold_anchor=threshold_anchor,
                                prefer_x=770, prefer_y=400, radius=40, permit_except=False)
        elif ret[0] == 'hero_druid':
            load_pow = self.get_numbers(screenshot_fn, 'autofill', 'load_ciph_drui_', add_symb={}, cropx1=-120, cropx2=-40, cropy1=-40, cropy2=-30, ciph_distance=6,
                                threshold=0.90, threshold_anchor=threshold_anchor,
                                prefer_x=640, prefer_y=370, radius=200, permit_except=False)
        elif ret[0] == 'hero_phoenix':
            load_pow = self.get_numbers(screenshot_fn, 'autofill', 'load_ciph_mage_', add_symb={}, cropx1=-120, cropx2=-40, cropy1=-40, cropy2=-30, ciph_distance=6,
                                threshold=0.94, threshold_anchor=threshold_anchor,
                                prefer_x=770, prefer_y=400, radius=40, permit_except=False)
        else:
            load_pow = 0
        logger.info('get_load_power = ' + str(load_pow))
        if load_pow < 20000:
            if not self.device.wait_for('check', attempts=1, threshold=0.85)[0]:
                print('debme')
        return load_pow

    def is_free_heroes(self, heroes_count):
        while self.device.tap_on(('exit_town', 'back1', 'back2'), one_attempt=True, threshold=0.85):
            sleep(1)
        if not self.device.wait_for('hero_push_in', attempts=4, threshold=0.85)[0]:
            if not self.device.tap_on('expand_heroes', one_attempt=True, threshold=0.85):
                if self.device.tap_on('exit_town', one_attempt=True, threshold=0.85):
                    self.device.tap_on('expand_heroes', one_attempt=True, threshold=0.85)
            if not self.device.wait_for('hero_push_in', attempts=4, threshold=0.85)[0]:
                raise Exception('Not found status of heroes')
            sleep(1)
        fn = self.device.make_screenshot()
        coords  = self.device.get_all_images('hero_return', debug=True, threshold=0.95, prepared_scr_shot = fn)
        if heroes_count and len(coords) == heroes_count:
            return False
        coords2 = self.device.get_all_images('hero_speedup', debug=True, threshold=0.95, prepared_scr_shot = fn)
        if heroes_count < 6:
            return len(coords) + len(coords2) < heroes_count
        array_exp_list = 0 # стрелка показывает, что еще есть 6ая активность в списке
        if self.device.wait_for('hero_expand_list_actions', attempts=1, threshold=0.85)[0]:
            array_exp_list = 1
        if heroes_count < 7 and len(coords) + len(coords2) + array_exp_list < 7:
            return True
        return not (len(coords) + len(coords2) == heroes_count)

    def expand_hero(self):
        if self.device.tap_on('expand_heroes', one_attempt=True, threshold=0.85, false_is_except=True):
            sleep(2)

    def get_miners(self):
        self.exit_town()
        if not self.device.wait_for('hero_push_in', attempts=2, threshold=0.85):
            self.device.tap_on('expand_heroes', one_attempt=True, threshold=0.85, false_is_except=True)
            sleep(1)
        coords = self.device.get_all_images('hero_mining', debug=True, threshold=0.75)
        return coords

    def return_mine(self, acc, mine_info):
        arr_mining = common.get_array_json_from_file('stats/mining.txt')
        last_mining = -1
        for jj in range(0, len(arr_mining)):
            last_mini = arr_mining[jj]
            if mine_info['coors'] == last_mini['coors']:
                last_mining = jj
                logger.debug("appropriate record: " + str(last_mini))
                break
        if self.go_mine_low(mine_info):
            if last_mining == -1:
                arr_mining.append({'nick': acc['nick'], 'start': int(time.time()), 'end': int(time.time() + 35 * 60),
                                   'end_str': time.asctime(time.localtime(time.time() + 35 * 60)),
                                   'coors': mine_info['coors']})
            else:
                arr_mining[last_mining]['start'] = int(time.time())
                arr_mining[last_mining]['end'] = int(time.time() + 35 * 60)
                arr_mining[last_mining]['end_str'] = time.asctime(time.localtime(time.time() + 35 * 60))
                if 'attacked_str' in arr_mining[last_mining]:
                    arr_mining[last_mining].pop('attacked_str')
            common.save_json_array_to_file(arr_mining, 'stats/mining.txt')

    def atack_mine(self, acc):
        arr_mining = common.get_array_json_from_file('stats/mining.txt')
        last_mining = -1
        for jj in range(0, len(arr_mining)):
            last_mini = arr_mining[jj]
            if last_mini['start'] > time.time() - 30*60 and not 'atacked_str' in last_mini:
                last_mining = jj
                logger.debug("appropriate record: " + str(last_mini))
                break
        if last_mining == -1:
            return False
        # self.relogin_acc(acc)
        # self.exit_town()
        self.go_coors(arr_mining[last_mining]['coors'])
        while time.time() - arr_mining[last_mining]['start'] < 27*60:
            logger.debug("sleeping before atacking %d secs" % int(arr_mining[last_mining]['start'] + 27*60 - time.time()))
            sleep(5)
            return arr_mining[last_mining]
        sleep(3)
        if self.device.is_image('mine_fog', threshold=0.8):
            self.device.tap((420, 240))
            sleep(2)
            if self.device.tap_on('explore', one_attempt=True, threshold=0.85):
                sleep(6)
        self.device.tap((420, 240))
        if self.device.tap_on('attack_town', one_attempt=True, threshold=0.85):
            arr_mining[last_mining]['atacked_str'] = time.asctime(time.localtime(time.time()))
            self.device.tap_on('autofill', attempts=3)
            sleep(1)
            self.device.tap_on('go', one_attempt=True, threshold=0.76)
            sleep(1)
        logger.debug('attacked success')
        return arr_mining[last_mining]

    def get_mine_coors(self):
        coords = self.device.get_all_images('mine_pit_map', debug=True, threshold=0.75)
        mines_info = []
        for ii in range(len(coords)):
            self.device.tap(coords[ii])
        self.get_coors()

    # перемещение карты вокруг заданной точки
    def go_next_place(self, jj):
        if jj == 0:
            self.device.swipe(-200, 100)
            self.device.swipe(-200, 100)
        elif jj == 1:
            self.device.swipe(-150, -150)
        elif jj == 2:
            self.device.swipe(200, -100)
            self.device.swipe(200, -100)
        elif jj == 3:
            self.device.swipe(260, 130)
            self.device.swipe(260, 130)
        elif jj == 4:
            self.device.swipe(-260, 130)
            self.device.swipe(-260, 130)

    def find_mine(self, coors):
        self.go_coors(coors)
        self.device.tap_on('mine_fog', one_attempt=True, threshold=0.75)
        for jj in range(5):
            self.go_next_place(jj)

    def explore_map(self):
        if self.device.tap_on('explore', one_attempt=True, threshold=0.85):
            if not self.device.tap_on('explore2', threshold=0.78, attempts=3):
                sleep(3)
            else:
                sleep(6)
            return True
        return False

    def go_mine_low(self, mine_info, little_troops=True, permit_attack=False):
        self.go_coors(mine_info['coors'])
        sleep(3)
        self.device.tap((425, 250))
        sleep(1)
        self.explore_map()

        self.device.tap((420, 240))
        if not self.device.tap_on('gather', attempts=2):
            if permit_attack and not self.device.tap_on('attack2', attempts=2):
                return False

        if little_troops:
            self.set_little_troops()
        if self.device.tap_on('go', attempts=3, threshold=0.76):
            if not self.device.tap_on('confirm_button2', attempts=3, threshold=0.76, dy=-280):
                return True  # уже идут на руду, отменяем поход
        return False

    def go_mine(self, acc, mine_lvl=1, full_troops=False):
        arr_mining = common.get_array_json_from_file('stats/mining.txt')
        mine_found = False
        last_mining = -1
        for jj in reversed(range(0, len(arr_mining))):
            last_mini = arr_mining[jj]
            if last_mini['nick'] == acc['nick'] and last_mini['start'] > time.time() - 5*60*60 and \
                    last_mini['start'] + 25*60 < time.time():
                last_mining = jj
                logger.debug("appropriate record: " + str(last_mini))
                break
        if last_mining > -1:
            self.go_coors(arr_mining[last_mining]['coors'])
            sleep(3)
            if self.device.is_image('mine_fog', threshold=0.8):
                self.device.tap((420,240))
                sleep(2)
                if self.device.tap_on('explore', one_attempt=True, threshold=0.85):
                    sleep(6)
            self.device.tap((420, 240))
            if self.device.tap_on('gather', attempts=2):
                mine_found = True
            else:
                arr_mining.pop(last_mining)
                common.save_json_array_to_file(arr_mining, 'stats/mining.txt')
                last_mining = -1
        if not mine_found and not self.search_mine(1):
            raise Exception('most likely gold finished')

        self.device.tap((400, 200))
        sleep(1)
        if full_troops:
            self.device.tap_on('troop_confirm', attempts=2, threshold=0.76)

        else:
            if not self.device.is_image(('little_troops', 'little_troops2'), threshold=0.91):
                for ii in range(5):
                    self.device.tap((185 + ii*125, 440))
                    self.device.tap_on('troops_dismiss', attempts=2, threshold=0.76)
                    sleep(1)
                    if ii == 0:
                        self.device.tap_on(('griffon', 'priestess2'), attempts=2, threshold=0.76)
                        sleep(1)
                        self.device.tap((335, 210))
                        sleep(1)
                        self.device.tap_on('troop_confirm', attempts=2, threshold=0.76)
                        sleep(1)
                        if self.device.is_image(('little_troops', 'little_troops2'), threshold=0.91):
                            break
                    self.device.tap((250, 20))
                    sleep(1)
            if not self.device.is_image(('little_troops', 'little_troops2'), threshold=0.91):
                return False
        self.device.tap_on('go', one_attempt=True, threshold=0.76)
        sleep(1)
        res = self.get_coors()
        if last_mining == -1:
            arr_mining.append({'nick': acc['nick'], 'start': int(time.time()), 'end': int(time.time()+35*60),
                               'end_str': time.asctime(time.localtime(time.time()+35*60)), 'coors': [res[0], res[1]]})
        else:
            arr_mining[last_mining]['start'] = int(time.time())
            arr_mining[last_mining]['end'] = int(time.time()+35*60)
            arr_mining[last_mining]['end_str'] = time.asctime(time.localtime(time.time()+35*60))
            if 'attacked_str' in arr_mining[last_mining]:
                arr_mining[last_mining].pop('attacked_str')
        common.save_json_array_to_file(arr_mining, 'stats/mining.txt')
        return True

    def go_spear(self, mine_lvl=1):
        if not self.search_mine(mine_lvl, type_search='search_spear'):
            return False

        self.device.tap((425, 220))
        sleep(1)
        if not self.device.tap_on('auto_combat2', attempts=3, threshold=0.76):
            return False
        if self.device.tap_on('go', attempts=3, threshold=0.76):
            return True
        return False


    def go_mine2(self, mine_lvl=1, full_troops=False):
        if not self.search_mine(mine_lvl):
            return False

        self.device.tap((400, 200))
        sleep(1)
        if full_troops:
            self.device.tap_on('troop_confirm', attempts=2, threshold=0.76)
        else:
            if not self.device.is_image(('little_troops', 'little_troops2'), threshold=0.91):
                for ii in range(5):
                    self.device.tap((185 + ii*125, 440))
                    self.device.tap_on('troops_dismiss', attempts=2, threshold=0.76)
                    sleep(1)
                    if ii == 0:
                        self.device.tap_on(('griffon', 'priestess2'), attempts=2, threshold=0.76)
                        sleep(1)
                        self.device.tap((335, 210))
                        sleep(1)
                        self.device.tap_on('troop_confirm', attempts=2, threshold=0.76)
                        sleep(1)
                        if self.device.is_image(('little_troops', 'little_troops2'), threshold=0.91):
                            break
                    self.device.tap((250, 20))
                    sleep(1)
            if not self.device.is_image(('little_troops', 'little_troops2'), threshold=0.91):
                return False
        if self.device.tap_on('go', attempts=3, threshold=0.76):
            return True
        return False

    # элемент автобитвы: клик по монстрам на карте до завершения битвы
    def start_battle(self, level_monsters, stats_hunter, acc, timeout=20, test_fn='', force_start_battle=False):
        if not 'reputation' in acc:
            acc['reputation'] = 0
        if not 'tonus_statue' in acc:
            acc['tonus_statue'] = 0
        if not 'tonus_fountain' in acc:
            acc['tonus_fountain'] = 0

        if not force_start_battle and acc['reputation'] and stats_hunter['rep'] < 15 and test_fn == '':
            ret = self.device.wait_for('reputation_chest', threshold=0.8, attempts=1)
            if ret[0]:
                self.move_to_img('reputation_chest', 4, 40, 40, threshold=0.8)
                self.device.tap_on('reputation_chest', threshold=0.8, one_attempt=True)
                sleep(1)
                self.move_to_img('horse', 4, 40, 40, threshold=0.8)
                self.device.tap_on('horse', threshold=0.8, one_attempt=True)
                self.device.tap_on('go', threshold=0.8, attempts=2)
                sleep(1)
                ret = self.device.wait_for('confirm_rep', threshold=0.8, attempts=8)
                sleep(1)
                if ret[0]:
                    if not self.device.tap_on('portal_key', threshold=0.8, one_attempt=True):
                        self.device.tap((595,255))
                    self.device.tap(ret[1])
                    stats_hunter['rep'] += 1
                else:
                    stats_hunter['rep'] = 15
        if not force_start_battle and acc['tonus_statue'] and stats_hunter['exp'] < 5 and test_fn=='':
            ret = self.device.wait_for('exp_statue', threshold=0.8, attempts=1)
            if ret[0]:
                self.move_to_img('exp_statue', 4, 40, 40, threshold=0.8)
                # self.device.tap_on('exp_statue', threshold=0.8, one_attempt=True)
                coords = self.device.get_all_images('exp_statue', debug=True, threshold=0.8)
                for ii in range(len(coords)):
                    if coords[ii][1] < 260:
                        self.device.tap(coords[ii], dx=20, dy=30)
                        break
                sleep(1)
                self.move_to_img('horse', 4, 40, 40, threshold=0.8)
                self.device.tap_on('horse', threshold=0.8, one_attempt=True)
                self.device.tap_on('go', threshold=0.8, attempts=2)
                sleep(5)
                stats_hunter['exp'] += 1
        if not force_start_battle and acc['tonus_fountain'] and stats_hunter['attacks'] > 6 and stats_hunter['fountain'] < 10 and test_fn=='':
            ret = self.device.wait_for('fountain', threshold=0.8, attempts=1, grain=100)

            if ret[0]:
                self.move_to_img('fountain', 4, 40, 40, threshold=0.8)
                # self.device.tap_on('fountain', threshold=0.8, one_attempt=True)
                # coords = self.device.get_all_images('fountain', debug=True, threshold=0.8)
                # for ii in range(len(coords)):
                #     if coords[ii][1] < 260 and :
                #       break
                self.device.tap_on('fountain', threshold=0.7, dx=20, dy=30, grain=100)
                sleep(1)
                self.device.tap_on('horse', threshold=0.8, one_attempt=True)
                sleep(1)
                self.device.tap_on('horse', threshold=0.8, one_attempt=True)
                self.device.tap_on('go', threshold=0.8, attempts=2)
                stats_hunter['fountain'] += 1
                sleep(5)

        arr_png = []
        arr_png_dialog = []
        for ii in range(len(level_monsters)):
            # arr_png.append('level_monsters_map_%d' % level_monsters[ii])
            # if level_monsters[ii] in [5, 6, 13]:
            #     arr_png.append('level_monsters_map_%d_2' % level_monsters[ii])  #  дубликаты картинок для разных освещений на карте
            arr_png_dialog.append('level_monsters_dialog_%d' % level_monsters[ii])

        # exclude_lvls = []
        # if 'level_monsters_map_8' in arr_png or 'level_monsters_map_9' in arr_png:
        #     if not 'level_monsters_map_6' in arr_png:
        #         exclude_lvls.append('level_monsters_map_6')
        #     if not 'level_monsters_map_5' in arr_png:
        #         exclude_lvls.append('level_monsters_map_5')
        #         exclude_lvls.append('level_monsters_map_5_2')
        #     if not 'level_monsters_map_3' in arr_png:
        #         exclude_lvls.append('level_monsters_map_3')
        # if 'level_monsters_map_10' in arr_png:
        #     if not 'level_monsters_map_16' in arr_png:
        #         exclude_lvls.append('level_monsters_map_16')
        #     if not 'level_monsters_map_13' in arr_png:
        #         exclude_lvls.append('level_monsters_map_13')
        #         exclude_lvls.append('level_monsters_map_13_2')
        # if 'level_monsters_map_16' in arr_png:
        #     if not 'level_monsters_map_18' in arr_png:
        #         exclude_lvls.append('level_monsters_map_18')
        # if 'level_monsters_map_23' in arr_png:
        #     if not 'level_monsters_map_25' in arr_png:
        #         exclude_lvls.append('level_monsters_map_25')
        #     if not 'level_monsters_map_22' in arr_png:
        #         exclude_lvls.append('level_monsters_map_22')
        #     if not 'level_monsters_map_28' in arr_png:
        #         exclude_lvls.append('level_monsters_map_28')
        # if not len(exclude_lvls):
        #     exclude_lvls = None

        #  ищем полный список картинок, возможно по каким-то мобам кликали случайно и
        #  надо либо убрать диалог, либо вступать в бой
        arr_full = arr_png + arr_png_dialog
        arr_full.append('battle_corruption')
        # threshold_map = 0.85
        # threshold_dialog = 0.9

        mobs_found = -1
        if test_fn:
            screenshot_fn = test_fn
        else:
            screenshot_fn = self.device.make_screenshot()
        coords = self.device.get_all_images('transparent_level_monsters', debug=True, threshold=0.9,
                                            prepared_scr_shot=screenshot_fn, method_search=2,
                                            crop=True, cropx1=7, cropy1=8, cropx2=-5, cropy2=-5, mask='transparent_level_monsters_mask')
        add_symb = {'2_2': '2', '3_2': '3', '3_3': '3', '8_2': '8', '8_3': '8'}
        for ii in range(len(coords)):
            prep_im = screenshot_fn[0:-4] + '_crop_%d_%s.png' % (ii, 'transparent_level_monsters')
            level = self.get_numbers('', '', 'monsters_ciph_', prepared_scr_shot=prep_im, threshold=0.94, permit_except=False, add_symb=add_symb)
            if level in level_monsters:
                mobs_found = ii
                break
        if mobs_found == -1:
            return False

        if True:
            swiped = False
            # выравниваем нахождение искомого объекта по вертикали и горизонтали, чтобы не тапнуть на другие интерфейсные объекты на экране
            coory = coords[mobs_found][1]
            while coory > 250:
                self.myswipe(0, -50, self.device)
                coory -= 50
                sleep(0.5)
                swiped = True
            while coory < 100:
                self.myswipe(0, 50, self.device)
                coory += 50
                sleep(0.5)
                swiped = True

            coorx = coords[mobs_found][0]
            while coorx > 700:
                self.myswipe(-150, 0, self.device)
                coorx -= 150
                sleep(0.5)
                swiped = True
            while coorx < 100:
                self.myswipe(150, 0, self.device)
                coorx += 150
                sleep(0.5)
                swiped = True
            if swiped:
                logger.debug("Картинка монстров была за рамками рабочей зоны, сдвинули в рабочую, ищем заново")
                return self.start_battle(level_monsters, stats_hunter, acc, timeout)
                # ret = self.device.wait_for(tuple(arr_png), threshold=threshold_map, one_attempt=True,
                #                            templates_exclude=exclude_lvls, best_templ=True)
                # if not ret[0]:
                #     ret = self.device.wait_for(tuple(arr_png), threshold=threshold_map, one_attempt=True,
                #                                templates_exclude=exclude_lvls, best_templ=True)
                # if not ret[0]:
                #     return False
            self.device.tap(coords[mobs_found], dy=70, dx=30)

            # отказался от этого условия, потому что часто заслоняется системными сообщениями
            # if not self.device.tap_on(arr_png_dialog, one_attempt=True, threshold=threshold_dialog):
            #     self.device.tap((30, 120))
            #     return False  # если нет диалога с нужным уровнем монстров

            sleep(0.5)
            power = self.get_power(permit_except=False)
            if power == -1:
                if self.explore_map():
                    return self.start_battle(level_monsters, stats_hunter, acc)
                sleep(0.5)
                power = self.get_power(permit_except=False)
                if power == -1:
                    self.device.tap(coords[mobs_found], dy=70, dx=30)
                    if self.explore_map():
                        return self.start_battle(level_monsters, stats_hunter, acc)
                    logger.debug('Не смогли определить рекомендуемую мощь')
                    return False
            if (level < 12 and power > 60000) or \
                    (level < 17 and power > 586000) or \
                    (level < 24 and power > 1046871):
                logger.debug('Слишком большая мощь для целевого уровня %d монстров' % level)
                self.device.tap((350, 20))
                return False
        # elif ret[0] == 'battle_corruption':
        #     # здесь получается повторный поиск arr_png_dialog, потому что в первый раз он мог не найтись
        #     # из-за бегущей строки объявлений на сервере, поэтому второй раз пробуем закрыть объявление и
        #     # и снова искать с каким уровнем битва
        #     # self.device.tap_on('battle_close_adv', one_attempt=True)
        #     power = self.get_power()
        #     if power > 60000:
        #         self.device.tap((350, 20))
        #         return False

        ret = self.go_attack(stats_hunter, timeout)
        if type(ret) == str:
            return ret
        return self.start_battle(level_monsters, stats_hunter, acc)  # снова пытаемся на карте монстров, подходящих для боя

    def go_attack(self, stats_hunter, timeout):
        sleep(1)
        if not self.device.tap_on('auto_combat', one_attempt=True):
            self.device.tap((30, 120))
            return False  # если нет кнопки автобоя, то возможно тапнули на уровень монстров, к бою с которыми нет доступа
        ret = self.device.wait_for(('autofill', 'tonus_finished'), attempts=4, threshold=0.76)
        if ret[0] == 'tonus_finished':
            if stats_hunter['buy_tonus1'] > 0:
                self.device.tap_on('use_tonus', one_attempt=True, threshold=0.76)
                self.device.tap_on('use_button', attempts=2, threshold=0.76)
                self.device.tap_on('use_button_red', attempts=2, threshold=0.76)
                stats_hunter['buy_tonus1'] -= 1
                return
            self.device.tap((380, 80))
            return 'tonus_finished'
        if ret[0]:
            self.device.tap(ret[1])
            sleep(1)
            self.device.tap_on('go', one_attempt=True, threshold=0.76)
            sleep(1)
            while self.device.wait_for('hero_to', one_attempt=True, threshold=0.76)[0]:
                sleep(1)
        stats_hunter['attacks'] += 1
        stats_hunter['swipe_wo_attacks'] = 0
        return self.end_battle(timeout)

    # делаем перетаскивания по экрану с малыми итерациями, чтобы не было проскальзывания
    def myswipe(self, dx, dy, device):
        if dx > 0:
            abs_dx = dx
            multi_x = 1
        else:
            abs_dx = -dx
            multi_x = -1
        if dy > 0:
            abs_dy = dy
            multi_y = 1
        else:
            abs_dy = -dy
            multi_y = -1
        while abs_dx > 0 or abs_dy > 0:
            portion_x = 50
            portion_y = 50
            if not (dx == 0 or dy == 0):
                if abs(dx) > abs(dy):
                    portion_x = int(portion_x * abs(dx) / abs(dy))
                else:
                    portion_y = int(portion_y * abs(dy) / abs(dx))
            if portion_x > abs_dx:
                portion_x = abs_dx
            if portion_y > abs_dy:
                portion_y = abs_dy
            device.swipe(multi_x * portion_x, multi_y * portion_y) # , sleep_sec=1.2)
            abs_dx -= portion_x
            abs_dy -= portion_y
            if abs_dx < portion_x and abs_dy < portion_y:
                break  # слишком короткое перемещение может вызвать тап

    # битвы с монсрами на карте
    # level_monsters - уровень монстров, пока возможен ограниченный набор уровней,
    #       для других нужно делать соответствующие картинки
    def battles(self, level_monsters, stats_hunter, acc):

        def focus_hero():
            self.device.tap_on('expand_heroes', one_attempt=True, threshold=0.85)
            sleep(2)
            if not self.device.tap_on('hero_halting', attempts=3, threshold=0.85):
                raise Exception('debugme')
            dubl_click = True
            sleep(2)
            if not self.device.tap_on('hero_push_in', one_attempt=True, threshold=0.85):
                if self.device.tap_on('expand_heroes', one_attempt=True, threshold=0.85):
                    sleep(1)
                self.device.tap_on('hero_push_in', one_attempt=True, threshold=0.85, false_is_except=True)
            sleep(1)
            return dubl_click
        self.exit_town()

        for ii in range(len(level_monsters)):
            level_monsters[ii] = int(level_monsters[ii])

        self.device.tap_on('expand_heroes', attempts=3, threshold=0.85)
        sleep(1)
        self.device.tap_on('hero_recall', attempts=2, threshold=0.85)  # спрятанного героя возвращаем
        coords = self.device.get_all_images('hero_return', threshold=0.75)
        if len(coords) >= acc['heroes']:
            if not self.device.tap_on('hero_halting', attempts=3, threshold=0.85):
                if self.device.tap_on('hero_return', attempts=3, threshold=0.85):
                    sleep(40)
        search_gold = True
        # if 'search_gold' in acc and acc['search_gold']:
        #     search_gold = True
        if not self.device.tap_on('hero_halting', attempts=3, threshold=0.85):
            while self.device.tap_on('hero_returning', threshold=0.85, template_exclude='hero_return', attempts=1):
                sleep(10)
            if not self.search_monsters(level_monsters, search_gold=search_gold):
                logger.info('free_search_finished')
                return 'free_search_finished'
            self.device.tap((400, 250))
            ret = self.go_attack(stats_hunter, 30)
            if type(ret) == str:
                return ret

            # if not self.go_to_start():
            #     return False

        count_clicks_no_swipe = 0  # подсчитываем сколько топчем на одном участке карты, возможно не можем перейти
        # реку, поэтому просто смещаемся, чтобы в затуманенной области найти место, куда можно перелететь
        permit_explore = False
        coors_click = []
        for ii in range(14):
            for jj in range(5):
                coors_click.append((600-ii*90, 150+jj*60))
        index_click = -1
        dubl_click = False  # после позиционирования героя, надо где-то еще кликнуть, иначе
        # следующий клик не даст возможности переместить героя
        while True:
            # if not permit_swipe:
            #     continue
            time1 = time.time()
            self.device.tap_on('hero_push_in', one_attempt=True, threshold=0.85)
            sleep(1.5)
            # таскаем экран в разных направлениях в поисках подходящих монстров
            ret = self.start_battle(level_monsters, stats_hunter, acc)
            if type(ret) == str:
                return ret
            if acc['tonus_around_dragon']:
                self.myswipe(-300, 150, self.device)
                ret = self.start_battle(level_monsters, stats_hunter, acc)
                if type(ret) == str:
                    return ret
                self.myswipe(-140, -180, self.device)
                ret = self.start_battle(level_monsters, stats_hunter, acc)
                if type(ret) == str:
                    return ret
                self.myswipe(400, -200, self.device)
                ret = self.start_battle(level_monsters, stats_hunter, acc)
                if type(ret) == str:
                    return ret
                self.myswipe(400, 260, self.device)
                ret = self.start_battle(level_monsters, stats_hunter, acc)
                if type(ret) == str:
                    return ret
                self.myswipe(-440, 220, self.device)
                ret = self.start_battle(level_monsters, stats_hunter, acc)
                if type(ret) == str:
                    return ret
                logger.debug('Завершен обход движения по карте вокруг стоящего дракона (%d секунд)' % int(time.time()-time1))

            for ii in range(10):
                if ii == 9:
                    print('debme')
                if stats_hunter['swipe_wo_attacks'] > acc['horse_step'] - 1:
                    if not self.search_monsters(level_monsters, search_gold=search_gold):
                        logger.info('free_search_finished')
                        return 'free_search_finished'
                    self.device.tap((400, 250))
                    ret = self.go_attack(stats_hunter, 30)
                    if type(ret) == str:
                        return ret
                    stats_hunter['swipe_wo_attacks'] = 0
                    ret = self.start_battle(level_monsters, stats_hunter, acc, force_start_battle=True)
                    if type(ret) == str:
                        return ret
                    break  # снова обходим по карте то место, где стоит дракон

                dubl_click = focus_hero()
                self.myswipe(-240 + random.randint(-50, 50), 180 + random.randint(-50, 50), self.device)
                stats_hunter['swipe_wo_attacks'] += 1
                index_click = -1 #  после перемещения экрана заново кликаем из 0ой точки
                if count_clicks_no_swipe > 15:
                    count_clicks_no_swipe = 0
                    permit_explore = True
                index_click += 1
                if index_click >= len(coors_click):
                    index_click = 0
                self.device.tap(coors_click[index_click])
                if dubl_click:
                    sleep(1)
                    self.device.tap(coors_click[index_click])
                    dubl_click = False
                sleep(1)
                if self.device.is_image('battle_corruption', threshold=0.8):
                    self.device.tap((20, 150))
                ret = self.device.wait_for('attack_town', one_attempt=True)
                if ret[0]:
                    if ii < 3:
                        continue
                    # натыкаемся на город противника, переползаем его
                    self.device.tap(ret[1], dx=-60)
                    if not self.search_monsters(level_monsters):
                        return 'free_search_finished'
                    count_clicks_no_swipe = 11
                    ret = self.start_battle(level_monsters, stats_hunter, acc)
                    if type(ret) == str:
                        return ret
                    continue
                #  задаем поиск телепорта и тапа по коню, иначе тап по коню может приводить к посещению разных домиков
                permit_swipe = False
                if self.horse():
                    permit_swipe = True
                if not permit_swipe:
                    ret = self.device.wait_for('explore', one_attempt=True, threshold=0.85)
                    if ret[0]:
                        if permit_explore:  # перелетаем участок, который по суши не удалось преодолеть
                            self.device.swipe(-200, 100, sleep_sec=1.2)
                            self.device.swipe(-200, 100, sleep_sec=1.2)
                            self.device.tap(coors_click[index_click])
                            sleep(1)
                            self.device.tap(coors_click[index_click])
                            # открываем туман
                            if self.device.tap_on('explore', one_attempt=True, threshold=0.85):
                                sleep(6)
                        else:
                            dubl_click = focus_hero()
                            continue
                            # self.device.swipe(50, -25)  # просто пытаемся отползти немного от зоны тумана
                            # self.device.tap(ret[1], dx=-50, dy=25)
                    count_clicks_no_swipe += 1
                else:
                    self.myswipe(-180, 80, self.device)
                    sleep(5)
                    break


    def click_twin_education(self):
        self.device._send_event("KEYCODE_HOME")
        self.device.tap_on('wam_icon', threshold=0.85, false_is_except=True)
        self.device.tap_on('face_all', attempts=1200, threshold=0.85)
        for _ in range(40):
            # первый бой
            self.device.tap((390, 245))
            self.device.tap((640, 245))
            self.device.tap((340, 190))
            self.device.tap((430, 300))
            self.device.tap((810, 440))
            self.device.tap((790, 380))
            self.device.tap((660, 370))

        for _ in range(40):
            # первый домик в замке и дальше по сценарию
            self.device.tap((425, 250))
            self.device.tap((425, 440))
            self.device.tap((435, 270))
            self.device.tap((550, 440))
            self.device.tap((425, 200))
            self.device.tap((450, 250))
            self.device.tap((100, 250))
            self.device.tap((600, 350))
            self.device.tap((760, 420))
            self.device.tap((30, 30))
            self.device.tap((100, 420))  # сбор награды и запрос следующего задания
            self.device.tap((460, 160))
            self.device.tap((260, 450))
            self.device.tap((810, 440))
            self.device.tap((740, 310))
            self.device.tap((630, 450))

        sleep(7)
        for ii in range(300):
            randx = random.randint(50, 800)
            randy = random.randint(80, 450)
            if ii % 50 == 49:  # иногда реклама пакета срывает все обучение
                if self.device.tap_on('package', one_attempt=True, threshold=0.85, dx=-390, dy=-35):
                    if self.device.tap_on('package_ok', one_attempt=True, threshold=0.85):
                        self.device.tap_on('package', one_attempt=True, threshold=0.85, dx=-390, dy=-35)
            self.device.tap((randx, randy))
            self.device.tap((randx, randy))
            self.device.tap((randx, randy))
            if not self.finger() and ii > 200:
                break   # чтобы не вышли, когда рука показывает куда тапнуть, иначе будет зависание в этом месте
            if ii % 2 == 0:
                self.back()
            sleep(0.1)
            logger.debug("Education %d" % ii)

    # искать большую и малую руку на карте, которая показывает куда дапать
    # по умолчанию малая не ищется
    def finger(self, big=1, small=0, scr_fn=''):
        arr_png = []
        if big:
            arr_png = ['reload_game', 'continue', 'retry', 'finger1', 'finger2', 'finger3', 'finger4']
        if small:
            arr_png.append('finger1_small')
        ret = self.device.wait_for(tuple(arr_png), one_attempt=True, prepared_scr_shot=scr_fn)
        if not ret[0]:
            return False
        if ret[0] == 'finger1':
            self.device.tap(ret[1], dx=-20, dy=-20)
            sleep(1.5)
        elif ret[0] == 'finger2':
            self.device.tap(ret[1], dx= 20, dy= 20)
            sleep(1.5)
        elif ret[0] == 'finger3':
            self.device.tap(ret[1], dx=-20, dy= 20)
            sleep(1.5)
        elif ret[0] == 'finger4':
            self.device.tap(ret[1], dx= 20, dy=-20)
            sleep(1.5)
        elif ret[0] == 'finger1_small':
            self.device.tap(ret[1], dx=-10, dy=-10)
            sleep(1.5)
        else:
            self.device.tap(ret[1])  # тапаем по дисконнектам
            sleep(1.5)
        return ret[1]

    def get_mail_body(self, msg):
        text = ""
        if msg.is_multipart():
            html = None
            for part in msg.get_payload():

                # print "%s, %s" % (part.get_content_type(), part.get_content_charset())

                if part.get_content_charset() is None:
                    # We cannot know the character set, so return decoded "something"
                    text = part.get_payload(decode=True)
                    continue

                charset = part.get_content_charset()

                if part.get_content_type() == 'text/plain':
                    text = str(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

                if part.get_content_type() == 'text/html':
                    html = str(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

            if text is not None:
                return text.strip()
            else:
                return html.strip()
        else:
            content = msg.get_content_charset()
            if not content:
                return str(msg)
            text = str(msg.get_payload(decode=True), content,
                           'ignore').encode('utf8', 'replace')
            return text.strip()

    # привязываем аккаунт к эмейлу
    def bind_acc_glob(self, accs, jj):
        for ii in range(10):
            if ii == 0:
                self.device.tap((40, 250))  # иногда застревает на экране окончания битвы
            if ii == 9:
                raise Exception('bind acc error')
            acc = accs[jj]
            login = acc[0:acc.find(':')]
            passw = acc[acc.find(':') + 1:-1]
            try:
                ret = self.bind_acc(login, passw)
                if ii == 0 and not ret:
                    logger.debug('неверная картинка привязки')
                    exit(55)
                if ret == 'Authentication failed':
                    accs[jj] += '\tMail authentication failed\t%s\n' % (time.asctime(time.localtime(time.time())))
                    while self.device.tap_on('back_small', attempts=2):
                        sleep(0.1)
                    self.back()
                    jj += 1
                    continue
                return login
            except Exception as e:
                logger.debug(str(e))
                self.device.stop()
                self.device.start()
                sleep(12)
                self.device._send_event("KEYCODE_HOME")
                sleep(2)
                self.device.tap_on('wam_icon', threshold=0.85, )
                sleep(12)
                self.clear_dialogs_after_login()

    # привязываем аккаунт к эмейлу
    def bind_acc(self, login, passw):
        sleep(1)
        self.device.tap((50, 280))
        sleep(1)
        self.device.tap((50, 280))
        sleep(1)
        self.device.tap_on('input_town', one_attempt=True)
        self.device.tap_on('reject_union', one_attempt=True)
        self.device.tap_on(('face', 'face1', 'face2', 'face3'))
        self.device.tap_on('change_acc', false_is_except=True, attempts=10)
        if not self.device.wait_for('binding_status_not_bind', attempts=2)[0]:
            return False
        self.device.tap_on('bind_account', attempts=2)
        self.device.tap_on('dont_have_these_accounts', attempts=2, dy=8, dx=50)
        self.device.tap_on('email_field')
        self.device.send_text(login)
        self.device.tap_on('send_verif_code')
        sleep(10)

        for _ in range(10):
            try:
                import imaplib, email
                box = imaplib.IMAP4_SSL('imap.mail.ru', )
                box.login(login, passw)
                box.select()  # выбираем папку, по умолчанию - INBOX
                typ, data = box.search(None, 'ALL')
                for num in data[0].split():
                    typ, data = box.fetch(num, '(RFC822)')
                    ret = data[0][1].decode("utf-8")
                    if ret.find('ushelp@efunen.com') == -1:
                        continue
                    ret = ret.replace('=\r\n', '')
                    fi = ret.find('for your operation is: ')
                    if fi == -1:
                        continue
                    code = ret[fi + 23: ret.find('<br', fi)]
                    if len(code) != 6:
                        logger.debug('len(code) != 6: ret = ' + ret)
                    box.store(num, '+FLAGS', '\\Deleted')
                box.close()
                box.logout()
                break

            except Exception as e:
                logger.debug(str(e))
                if str(e).find('Authentication failed. Please verify your account by going') > -1:
                    return 'Authentication failed'
                sleep(60)
                continue
        self.device.tap_on('verification_code')
        self.device.send_text(str(code))
        self.device.tap_on('set_password')
        self.device.send_text('tremtrem')
        self.device.tap_on('confirm_password')
        self.device.send_text('tremtrem')
        self.device.tap_on('confirm_button', threshold=0.85)
        self.device.tap_on('binding_status_bound', false_is_except=True, threshold=0.87)
        return True

    def get_system_mail(self):
        self.device.tap_on('mail', threshold=0.78, attempts=2)
        self.device.tap_on('mail_system', threshold=0.78, attempts=4)
        self.device.tap_on('mail_rewards', threshold=0.78, attempts=2)
        self.back(2)
        self.back(2)
        self.back(2)

    def teleport_on_selected_server(self, acc):
        # взятие тп из почты
        self.get_system_mail()

        self.device.tap_on('exit_town', threshold=0.78, attempts=2)
        self.device.tap_on('exit_town', threshold=0.78, attempts=2)
        sleep(2)
        self.device.tap_on('glob_map', threshold=0.78, attempts=2)
        sleep(2)
        self.device.tap_on('glob_serv2', threshold=0.78, attempts=2)
        self.device.wait_for(('server_sign', 'server_sign_m'), threshold=0.78, attempts=40)
        # self.back()
        # sleep(5)
        if 'kingdom_swipe_x' in acc:
            sum_x = 0
            for _ in range(100):
                self.device.make_screenshot()
                self.device.swipe(-90, 0, 200, 200, 170)
                sum_x += 90
                if sum_x > acc['kingdom_swipe_x']:
                    break
        if 'kingdom_swipe_y' in acc:
            sum_y = 0
            for _ in range(100):
                self.device.make_screenshot()
                self.device.swipe(0, -90, 200, 200, 170)
                sum_y += 90
                if sum_y > acc['kingdom_swipe_y']:
                    break

        server = acc['server']
        if server[0] == 'S':
            server_sign = 'server_sign'
            cropx1 = 16
            server_check_sign = 'server_check_sign'
        elif server[0] == 'M':
            server_sign = 'server_sign_m'
            cropx1 = 21
            server_check_sign = 'server_check_sign_m'
        else:
            raise Exception('Неправильное имя сервера, разрешаются только начинающиеся на S')
        cropx2 = len(server[1:])*9
        server = int(server[1:])

        server_found = False
        for zz in range(50):
            screenshot_fn = self.device.make_screenshot()
            coords = self.device.get_all_images(server_sign, debug=True, threshold=0.7,
                                                prepared_scr_shot=screenshot_fn,
                                                crop=True, cropx1=cropx1, cropy1=-2, cropx2=cropx2, cropy2=2)
            for ii in range(len(coords)):
                prep_im = screenshot_fn[0:-4] + '_crop_%d_%s.png' % (ii, server_sign)
                resx = self.get_numbers('', '', 'server_ciph_', prepared_scr_shot=prep_im, threshold=0.94)
                if resx == server:
                    self.device.tap(coords[ii], dx=-30, dy=-40)
                    server_found = True
                    break
            if server_found:
                break
            self.device.swipe(0, -90, 200, 200, 170)
            self.device.swipe(0, -90, 200, 200, 170)
            self.device.swipe(0, -90, 200, 200, 170)

        # дополнительно проверяем нужное царство на другом экране
        self.device.tap_on('glob_map', threshold=0.78)
        sleep(3)
        screenshot_fn = self.device.make_screenshot()
        res = self.get_numbers(screenshot_fn, server_check_sign, 'server_check_ciph_', permit_except=False, threshold=0.90, cropx1=20)
        if not res == server:
            raise Exception('no check kingdom')
        self.back(120)

        for _ in range(16):
            self.device.swipe(-200, 0)
        self.device.tap((400, 250))
        count_swipe = 0
        while not self.device.tap_on('explore', threshold=0.78, attempts=2):
            self.device.swipe(-200, 0)
            self.device.tap((400, 250))
            count_swipe += 1
            if count_swipe > 15:
                raise Exception('no island to teleport')
        self.device.tap_on('explore2', threshold=0.78, attempts=2)
        sleep(6)
        for ii in range(20):
            if ii == 19:
                raise Exception('teleport error')
            self.device.tap((400, 250))
            if self.device.tap_on('explore', threshold=0.78, attempts=2):
                sleep(6)
            self.device.tap_on(('teleport2', 'teleport_bigger'), threshold=0.78, attempts=2)
            self.device.tap_on(('join_the_kingdom', 'join_the_kingdom2'), threshold=0.78, attempts=2)
            if not self.device.tap_on('confirm_teleport', threshold=0.78, attempts=2):
                self.device.swipe(-100, -80)
            else:
                break

        sleep(15)

    def grow_acc(self, count_cycles=-1):
        def dif_coor(rect1, rect2):
            if abs(100 - rect1[0][0]) < 40 and abs(390 - rect1[0][1]) < 40:
                return False
            if abs(rect1[0][0]-rect2[0][0]) > 40 or abs(rect1[0][1]-rect2[0][1]) > 40:
                return True
            else:
                return False

        # from libs.common import find_template_img
        # find_template_img(r'c:\Users\denis\Pictures\MEmu Photo\wam_20191002-225213.png',
        #                 r'e:\sw\arch\war_magic_bot\war_magic\images\upgrade.png', debug=True)
        # # r = find_template_img(screenshot_path, file, threshold, debug=True)

        old_rect = [[1,1], [1,1]]
        finger_count = 0  # 2 раза кликаем по пальцу, если он координаты не меняет, то надо искать другой объект
        count = 0
        while True:
            count += 1
            if count_cycles > -1 and count > count_cycles:
                return True
            if count > 280:
                return True
            scr_fn = self.device.make_screenshot()
            new_rect = self.finger(small=1, scr_fn=scr_fn)
            if new_rect:
                if dif_coor(new_rect, old_rect):
                    finger_count = 0
                    old_rect = new_rect
                else:
                    finger_count += 1
                if finger_count < 2:
                    sleep(2)
                    continue
                scr_fn = self.device.make_screenshot()
                new_rect = self.finger(small=1)
                if new_rect:
                    if dif_coor(new_rect, old_rect):
                        finger_count = 0
                        old_rect = new_rect
                    else:
                        finger_count += 1
                    if finger_count < 2:
                        sleep(2)
                        continue
            ret1 = self.device.wait_for(('arena_form1', 'arena_form2'), one_attempt=True, threshold=0.88, prepared_scr_shot=scr_fn)
            if ret1[0] in ['arena_form1', 'arena_form2']:
                self.device.tap(ret1[1])
                self.device.tap_on('auto_comission', attempts=2, threshold=0.7)
                self.device.tap((250, 20))
                self.device.tap((250, 20))
                self.device.tap((250, 20))
                if self.device.tap_on('arena_atack', attempts=2, threshold=0.7):
                    sleep(4)
                    self.device.tap((250, 40))
                    self.device.tap_on('arena_close', attempts=2, threshold=0.7)
                self.back()
                self.back()
                continue

            self.device.tap_on('free_build', attempts=2, threshold=0.7, prepared_scr_shot=scr_fn)
            ret1 = self.device.wait_for(('upgrade', 'speedup'), one_attempt=True, threshold=0.73, prepared_scr_shot=scr_fn)
            ret2 = self.device.wait_for('recruit_highlighted', one_attempt=True, threshold=0.80, prepared_scr_shot=scr_fn)
            if not ret1[0]:
                ret1 = self.device.wait_for('upgrade_small_size', one_attempt=True, threshold=0.67, prepared_scr_shot=scr_fn)
            if ret1[0] in ['upgrade', 'upgrade_small_size', 'speedup'] and self.device.wait_for('upgrade_quest',
                        one_attempt=True, threshold=0.70, prepared_scr_shot=scr_fn)[0]:
                self.device.tap(ret1[1])
                sleep(1)
                scr_fn = self.device.make_screenshot()
                if not self.finger(scr_fn=scr_fn):
                    if count > 29 and count % 10 == 0:
                        if self.device.wait_for('build_2_hospital', one_attempt=True, threshold=0.80, prepared_scr_shot=scr_fn)[0]:
                            self.device.stop()
                            self.device.start()
                            sleep(20)
                            self.device._send_event("KEYCODE_HOME")
                            self.device.tap_on('wam_icon', threshold=0.85, false_is_except=True)
                            sleep(20)
                    if ret1[0] == 'speedup' or self.device.tap_on('speedup_red', attempts=2, threshold=0.7, prepared_scr_shot=scr_fn):
                        self.device.tap_on('use_speedup', attempts=2, threshold=0.8)
                        scr_fn = self.device.make_screenshot()
                    elif self.device.tap_on('go_upgrade_next_build', attempts=2, threshold=0.7, prepared_scr_shot=scr_fn):
                        sleep(2)
                        self.finger(small=1, scr_fn=scr_fn)
                        self.device.tap_on('speedup', attempts=2, threshold=0.8)
                        self.device.tap_on('use_speedup', attempts=2, threshold=0.8)
                    self.device.tap_on('free_speedup', attempts=2, threshold=0.8)
                    if self.device.tap_on('upgrade_button', attempts=2):
                        if count_cycles > -1:
                            return True
                        sleep(1.5)
                        self.device.tap((80, 420))
                        sleep(0.5)
                        self.device.tap((80, 420))
                        sleep(1)
                else:
                    sleep(1.5)
                    self.device.tap((80, 420))
                    sleep(0.5)
                    self.device.tap((80, 420))
                    sleep(1)
                    continue
            elif ret2[0] == 'recruit_highlighted' and self.device.wait_for('recruit_quest', one_attempt=True, threshold=0.70)[0]:
                self.device.tap(ret2[1])
                sleep(1)
                self.device.tap_on('recruit2', attempts=2)
            if self.device.tap_on(('horse', 'horse2'), threshold=0.76, one_attempt=True):
                self.device.tap_on('autofill', attempts=3)
                sleep(1)
                self.device.tap_on('go', one_attempt=True, threshold=0.76)
                sleep(1)
            ret = self.device.wait_for('attack', one_attempt=True, threshold=0.8)
            if ret[0]:
                theEnd = False
                power = self.get_power(permit_except=False)
                if power == 10215 or self.device.is_image('6lvl_battle2', threshold=0.94):
                    theEnd = True
                self.device.tap(ret[1])
                self.finger()
                self.device.tap_on('autofill', one_attempt=True)
                self.finger()
                sleep(1)
                self.device.tap_on('go', one_attempt=True, threshold=0.76)
                sleep(1)
                # дважды кликаем, если программа в режиме обучения объясняет куда что нажимать
                self.device.tap_on('go', one_attempt=True, threshold=0.76)
                sleep(1)
                self.end_battle(60)
                if theEnd:
                    return True
            # constract_button - кнопка запуска строительства
            # open - открытие новых земель внутри замка
            # face_women - девушка маячит со своими подсказками
            scr_fn = self.device.make_screenshot()
            if self.device.tap_on(('constract_button', 'open', 'face_women'), one_attempt=True, threshold=0.8, prepared_scr_shot=scr_fn):
                sleep(2)
                scr_fn = self.device.make_screenshot()
            if self.device.tap_on(('back1', 'auto_battle', 'heal', 'return_tomorrow',
                    'retry', 'reload_game', 'continue'), one_attempt=True, threshold=0.76, prepared_scr_shot=scr_fn):
                sleep(2)
                scr_fn = self.device.make_screenshot()
            if self.device.tap_on(('get_guard', 'get_bowmen', 'get_priestess', 'get_knights', 'heal_button'),
                one_attempt=True, threshold=0.76, prepared_scr_shot=scr_fn):
                sleep(2)
                scr_fn = self.device.make_screenshot()
            # # и на всякий случай делаем рандомный клик, чтобы двигаться дальше, если застряли
            # randx = random.randint(2, 845)
            # randy = random.randint(2, 498)
            # self.device.tap((randx, randy))
            self.device.tap((80, 420))  # кликаем в угол, чтобы взять следующее задание
            sleep(3)
        return False

    def get_all_quests(self, acc):
        small = 1
        self.back(3)
        if not self.device.tap_on('quests', threshold=0.75, one_attempt=True, template_exclude='quests2'):
            return False
        sleep(2*small)
        ret = self.device.wait_for(('collect_quest', 'collect_quest2'), one_attempt=True, threshold=0.75)
        while ret[0]:
            self.device.tap(ret[1])
            sleep(small)
            if ret[0] == 'collect_quest2':
                self.device.tap((250, 50))
                for coor in [(238, 165), (341, 165), (445, 165), (548, 165), (651, 165), ]:
                    self.device.tap(coor)
                    sleep(1)
                    self.device.tap((250, 50))
                break

            ret = self.device.wait_for(('collect_quest', 'collect_quest2'), one_attempt=True, threshold=0.75)
        self.back(3)
        return True

    def move_to_img(self, img, attempts, move_x, move_y, threshold=0.73, center_img=True, x0=400, y0=200):
        for ii in range(attempts):
            ret = self.device.wait_for(img, threshold=threshold, one_attempt=True)
            if ret[0]:
                if not center_img:
                    return True
                pt = common.flatten(ret[1])
                if pt[0] > 650:
                    self.device.swipe(-100, 0)
                if pt[1] < 150:
                    self.device.swipe(0, 110)
                if pt[1] > 350:
                    self.device.swipe(0, -110)
                return True
            self.device.swipe(-move_x, -move_y, x0=x0, y0=y0)
        return False

    def set_name(self, name):
        self.back()
        self.back()
        self.back()
        self.device.tap((100, 480))
        sleep(1)
        self.device.tap((100, 480))
        self.device.tap_on('enter_name', attempts=2)
        sleep(1)
        self.device.send_text(name)
        self.device.tap_on('enter_name2', attempts=2)
        self.device.tap_on('enter_name2', attempts=2)

    def alliance_join(self, name):
        if self.device.tap_on('back_small', attempts=2):
            self.back()
        if self.device.tap_on('union', attempts=2):
            if self.device.tap_on('ally_manage', attempts=2):
                self.device.tap_on('ally_quit', attempts=2)
                self.device.tap_on('ally_quit2', attempts=2)
            self.device.tap_on('union', attempts=2)
            self.device.tap_on('ally_enter_search', attempts=2)
            self.device.send_text(name)
            sleep(1)
            self.device.tap_on('ally_search', attempts=2)
            sleep(1)
            self.device.tap_on('ally_search', attempts=2)
            sleep(2)
            self.device.tap((250, 200))
            self.device.tap_on('ally_apply', attempts=2)
            self.back()
            self.back()
            self.back()
            self.back()
            self.back()
            self.back()

    def alliance_trans(self, acc, all_name):
        self.device.tap_on('union', attempts=2)
        sleep(2)
        # трижды кликаем, чтобы прокрутить подсказки в случае первого входа
        self.device.tap_on('union', attempts=2)
        if self.device.tap_on('union_donation', attempts=2):
            ret = self.device.wait_for('union_don_food', attempts=2, threshold=0.85)
            if ret[0]:
                for ii in range(20):
                    self.device.tap(ret[1])
                    sleep(0.3)
            sleep(1)
            self.back()
        if self.device.tap_on('union_shop', template_exclude='union_shop_non_alert', attempts=2):
            sleep(1)
            self.back()     # ПОТРАТИТЬ ОЧКИ СОЮЗА

        if self.device.tap_on('ally_manage', attempts=2):
            self.device.tap_on('ally_quit', attempts=2)
            self.device.tap_on('ally_quit2', attempts=2)
            self.device.tap_on('union', attempts=2)
            self.device.tap_on('ally_enter_search', attempts=2)
            self.device.send_text(all_name)
            self.device.tap_on('ally_search', attempts=2)
            self.device.tap_on('ally_search', attempts=2)
            sleep(2)
            self.device.tap((250, 200))
            self.device.tap_on('ally_apply', attempts=2)
            self.back()
        # if self.device.tap_on('union', attempts=2):         # ПРИНЯТЬ В СОЮЗЕ, СДЕЛАТЬ ИВЕНТ
        #     self.device.tap_on('ally_manage', attempts=2)
        #     self.device.tap_on('ally_quit', attempts=2)
        #     self.device.tap_on('ally_quit2', attempts=2)
        #     self.device.tap_on('union', attempts=2)
        #     self.device.tap_on('ally_enter_search', attempts=2)
        #     self.device.send_text('rhrferm')
        #     self.device.tap_on('ally_search', attempts=2)
        #     self.device.tap_on('ally_search', attempts=2)
        #     sleep(2)
        #     self.device.tap((250, 200))
        #     self.device.tap_on('ally_apply', attempts=2)
        #     self.back()

    def alliance(self, acc, don_army=True, union_shop=True, union_help=True, take_screen=False):
        # self.device.tap_on('donate_army', attempts=2,
        #                    threshold=0.85, b_color=65)
        # self.input_town()
        self.back()
        self.back()
        ret = True
        if don_army and self.device.tap_on('chat', attempts=2, threshold=0.75):
            if self.device.tap_on('chat_donate', attempts=2, threshold=0.85):
                sleep(2)
            # self.device.tap_on('donate_army', attempts=2, threshold=0.85, b_color=3)

            # ret = self.device.wait_for('donate_army', threshold=0.85, one_attempt=True,
            #                            templates_exclude='donate_army_gray', best_templ=True)
            for _ in range(10):
                self.device.swipe(0, 150)
                sleep(0.5)
            for _ in range(3):
                self.device.wait_for('donate_army', attempts=5, threshold=0.85, b_color=65)
                coors_don = self.device.get_all_images('donate_army', threshold=0.97, method_search=2, delta_coor=40)
                for army in ['army_dark_hors', 'army_mages_b', 'army_blue_phenix', 'army_ursa', 'army_dwarven', 'army_elven_archer', 'army_vampire', 'army_griphon']:
                    coors_army = self.device.get_all_images(army, threshold=0.8, method_search=1, delta_coor=40)
                    for coor in coors_army:
                        for coor_button in coors_don:
                            if abs(coor[1] - coor_button[1]) < 30:
                                self.device.long_tap(coor_button, 5000, dx=30, dy=8)
                                sleep(2)
                                coors_don = self.device.get_all_images('donate_army', threshold=0.97, method_search=2, delta_coor=40)
                self.device.swipe(0, -150)
            self.device.tap_on('chat_close', attempts=2)
            sleep(1)
        self.device.tap_on('union', attempts=2, dy=20, dx=20)
        self.device.tap_on('union', attempts=2, dy=20, dx=20)
        sleep(2)
        # трижды кликаем, чтобы прокрутить подсказки в случае первого входа
        self.device.tap((420, 360))
        self.device.tap((420, 360))
        self.device.tap((420, 360))
        don_crystalls = False
        if self.device.tap_on('union_donation', attempts=2):
            # if True:
            if not 'main' in acc or not acc['main']:
                if don_crystalls:
                    self.device.swipe(0, -150)
                    sleep(1)
                    ret = self.device.wait_for('don_crystalls', attempts=2, threshold=0.85)
                    if ret[0]:
                        for ii in range(50):
                            self.device.tap(ret[1])
                            sleep(0.3)
                else:
                    ret = self.device.wait_for(('gold_donate', 'union_don_food'), attempts=2, threshold=0.85)
                    for ii in range(50):
                        if 'gold_don' in acc and acc['gold_don']:
                            self.device.tap(ret[1])
                            if ii > 30:
                                self.device.tap((645, 330))
                                self.device.tap((430, 330))
                        else:
                            self.device.tap((645, 330))
                            self.device.tap((430, 330))
                        if ii and ii % 10 == 0:
                            if self.device.wait_for('donate_cooldown08', attempts=1, threshold=0.9)[0]:
                                break
            else:
                ret = self.device.wait_for(('gold_donate', 'union_don_food'), attempts=2, threshold=0.85)
                if ret[0]:
                    for ii in range(50):
                        self.device.tap(ret[1])
                        sleep(0.3)
                else:
                    ret = False
            sleep(1)
            if take_screen:
                fn = self.device.make_screenshot()
                shutil.copyfile(fn, 'stats_soldier/%s_ally_after_donate.png' % acc['nick'])

            self.back()
        else:
            ret = False
        if union_shop and self.device.tap_on('union_shop', template_exclude='union_shop_non_alert', attempts=2):
            sleep(1)
            fn = self.device.make_screenshot()
            shutil.copyfile(fn, 'stats/shop_ally_%s.png' % acc['nick'])
            self.back()  # просто убираем красную точку
        if union_help and self.device.tap_on('union_help', attempts=2):
            sleep(2)
            self.device.tap((160, 150))
            sleep(0.3)
        self.back()
        self.back()
        return ret

    def hide_hero(self, acc):
        self.back()
        self.input_town()
        if not self.move_to_img('cave', 15, 100, -50):
            return False
        self.device.tap_on('cave', attempts=1)
        self.device.tap_on('cave_hide_pict', attempts=3)
        self.device.tap_on('cave_quick_recall', attempts=3)
        sleep(5)
        for _ in range(10):
            if not self.device.tap_on('cave_quick_hide', attempts=3, template_exclude='cave_quick_recall'):
                break
            sleep(2)
        self.device.tap((40, 250))
        # self.device.tap_on('town_hero', attempts=3)   # не имеет смысл делать в 1 стеке маленькие войска
        # sleep(2)
        # for zz in range(acc['heroes'] + 1):
        #     if self.device.is_image('attack_clear_disable', template_exclude='attack_clear'):
        #         self.device.tap((570, 300))
        #         sleep(2)
        #         continue
        #     # self.set_little_troops(10)
        # self.back()
        return True  # все войска недоступны для редактирования, значит спрятаны

    def return_halt_hero(self, wait_hero=False):
        self.expand_hero()
        if self.device.tap_on('hero_halting', attempts=3, threshold=0.85, dx=175):
            if wait_hero:
                while self.device.wait_for('hero_speedup', threshold=0.75, attempts=3, grain=50)[0]:
                    sleep(3)

    def return_heroes(self, stat):
        is_stationed = False
        while self.device.tap_on('hero_return', threshold=0.85, attempts=2):
            sleep(5)
        for ii in range(20):
            if 'stationed_hero_%d_coors' % ii in stat:
                is_stationed = True
                self.back()
                self.go_coors(stat['stationed_hero_%d_coors' % ii])
                self.device.tap((400, 250))
                self.device.tap_on('reinforce', attempts=4, threshold=0.85)
                self.set_little_troops()
                self.device.tap_on('go', attempts=3, threshold=0.76)
                sleep(1)
            else:
                break
        return is_stationed

    def rehide_hero(self, acc, stat, fn):
        def is_coors_exist(stat, coors_hide):
            for ii in range(12):
                key = 'stationed_hero_%d_coors' % ii
                if key in stat and tuple(stat[key]) == coors_hide:
                    return True
            return False

        self.exit_town()  # перепрятывание войск у союзников
        if not self.device.wait_for('hero_push_in', attempts=4, threshold=0.85)[0]:
            if not self.device.tap_on('expand_heroes', one_attempt=True, threshold=0.85):
                print('debug')
        screenshot_fn = self.device.make_screenshot()
        img_anchor = 'hero_stationed'
        ret = self.device.get_all_images(img_anchor, threshold=0.76,
                                         prepared_scr_shot=screenshot_fn,
                                         crop=True, cropx1=-5, cropy1=-5, cropx2=100, cropy2=5)
        if len(ret) == 0:
            self.device.tap((450, 250))
            sleep(1)
            self.device.tap_on('city_bonus', attempts=2, threshold=0.85)
            screenshot_fn = self.device.make_screenshot()
            guardian = self.device.wait_for('peace_gurdian', threshold=0.85, attempts=6,
                                            prepared_scr_shot=screenshot_fn, crop=True, cropx1=50,
                                            cropy1=25, cropx2=480, cropy2=25)
            if not guardian[0]:
                print('look at this')

            is_stationed = self.return_heroes(stat)
            if is_stationed:
                return True  # не мы ставим щит, а прячемся у других
            prepared_scr_shot = screenshot_fn[:-4] + '_crop_%s.png' % ('peace_gurdian')
            if common.get_color_level(prepared_scr_shot, g_color=60):
                if 'guard' not in acc:
                    return False
                # обновляем щит
                self.device.tap_on('peace_gurdian', attempts=4, threshold=0.85)
                self.device.tap_on('guard_1d', attempts=4, threshold=0.85, dy=20, dx=420)
                self.device.tap_on('confirm_button2', threshold=0.8, attempts=1)
                self.device.tap_on('buy_guard', threshold=0.8, attempts=1)
                if not self.device.tap_on('guardian_ends', threshold=0.8, attempts=4):
                    logger.error('not buy_guard')
                sleep(3)
                self.go_supermine()
                return True
            stat['gurdian_check_success'] = int(time.time())
            stat['gurdian_check_success_str'] = time.asctime(time.localtime(time.time()))
            common.save_json_to_file(stat, fn)
            self.go_supermine()
            return True

        for zz in range(len(ret)):  # сохраняем координаты героев где они прячутся
            prepared_scr_shot = screenshot_fn[:-4] + '_crop_%d_%s.png' % (zz, img_anchor)
            if not common.get_color_level(prepared_scr_shot, g_color=40):
                continue

            self.device.tap(ret[zz])
            sleep(3)
            coors_hide = self.get_coors()

            if not is_coors_exist(stat, coors_hide):
                stat['stationed_hero_%d_coors' % zz] = coors_hide
                stat['stationed_hero_%d_coors_time' % zz] = int(time.time())
                stat['stationed_hero_%d_coors_time_str' % zz] = time.asctime(time.localtime(time.time()))
                common.save_json_to_file(stat, fn)

            self.device.tap_on('hero_stationed', attempts=2, threshold=0.85, dx=200)

        self.return_heroes(stat)
        self.device.tap_on('hero_panel', attempts=2, threshold=0.85)
        for ii in range(5):
            self.change_hero()
            if self.device.tap_on('attack_clear', attempts=2, threshold=0.85, template_exclude='attack_clear_disable'):
                logger.error('alarm: one hero not hide')
        self.back()

    def change_hero(self):
        self.device.tap((575, 300))
        sleep(2)

    def upgrade_town(self):
        if not self.move_to_img('market', 10, 70, -70, x0=200, y0=100):
            if not self.device.tap_on('unlock_hero.png', attempts=1):
                return False
        ret = False
        self.device.tap_on('market', attempts=2, dx=-150)
        if self.device.tap_on('upgrade_small_size', attempts=2):
            self.device.tap_on('stay_page', attempts=1, dx=20, dy=20, threshold=0.95)

            sleep(1)
            scr_fn = self.device.make_screenshot()
            coun = 0
            while self.device.tap_on('go_upgrade_next_build', attempts=2, threshold=0.7, prepared_scr_shot=scr_fn):
                coun += 1
                if coun > 15:
                    break
                sleep(2)
                if not self.finger(1, 1):
                    if not self.finger(1, 1):
                        self.device.tap((425, 250))
                if not self.device.tap_on('upgrade_small_size', attempts=2):
                    if self.device.tap_on('constract_button', attempts=2):
                        if self.build_free_or_help():
                            return self.upgrade_town()
                        return True
                    else:
                        self.device.tap((425, 250))
                        self.device.tap_on('upgrade_small_size', attempts=2)
                        while self.device.tap_on('free_build2', attempts=2, threshold=0.8):
                            sleep(3)

                        if self.device.tap_on('constract_button', attempts=2):
                            if self.build_free_or_help():
                                return self.upgrade_town()
                            self.back()
                            return True
                sleep(2)
                scr_fn = self.device.make_screenshot()
                if self.device.is_image('speedup_red', threshold=0.7, prepared_scr_shot=scr_fn):
                    self.back()
                    return False
                self.finger()

            # if ret1[0] == 'speedup' or self.device.tap_on('speedup_red', attempts=2, threshold=0.7,
            #                                               prepared_scr_shot=scr_fn):
            #     self.device.tap_on('use_speedup', attempts=2, threshold=0.8)
            #     scr_fn = self.device.make_screenshot()
            # elif self.device.tap_on('go_upgrade_next_build', attempts=2, threshold=0.7, prepared_scr_shot=scr_fn):
            #     sleep(2)
            #     self.finger(small=1, scr_fn=scr_fn)
            #     self.device.tap_on('speedup', attempts=2, threshold=0.8)
            #     self.device.tap_on('use_speedup', attempts=2, threshold=0.8)
            # self.device.tap_on('free_speedup', attempts=2, threshold=0.8)
            # if self.device.tap_on('upgrade_button', attempts=2) and count_cycles > -1:
            #     return True

            if self.device.tap_on('upgrade_button', attempts=2, threshold=0.75, prepared_scr_shot=scr_fn):
                ret = True
                sleep(2)
            else:
                print('why not upgrade sity hall ?')
            self.back(2)
            if self.build_free_or_help():
                return self.grow_acc2()
        return ret

    def upgrade_med(self, only_hosp=False):
        self.input_town()
        need_upgrade = not only_hosp
        if need_upgrade:
            if random.randint(0, 5) == 4:
                need_upgrade = False  # в каждом пятом случае пробуем просто лечить войска
            if need_upgrade and self.device.wait_for(('hammer', 'hammer2'), attempts=2, threshold=0.72)[0]:
                need_upgrade = False
        if not self.move_to_img('hospital', 10, -100, 20):
            return False
        self.device.swipe(200, 0)
        self.device.tap_on('heal', attempts=1)
        if random.randint(0, 1):  # случайным образом перемещаемся на нижние лечилки
            self.device.swipe(0, -200)
        coords = self.device.get_all_images('hospital', threshold=0.75)
        if not len(coords):
            return False
        rand_ind = random.randint(0, len(coords)-1)
        self.device.tap(coords[rand_ind])
        if need_upgrade:
            if self.device.tap_on('upgrade_small_size', attempts=2):
                if self.device.tap_on('upgrade_button', attempts=2, threshold=0.75):
                    sleep(3)
                self.back(3)
                if self.build_free_or_help():
                    return self.upgrade_med(only_hosp)
                return True  # можно сделать запуск лечения на другой палатке
            self.device.tap_on('hospital', attempts=2)
        if self.device.tap_on('heal_menu', attempts=2):
            if not self.device.tap_on('heal_button', attempts=2):
                self.back(2)
            else:
                if self.build_free_or_help():
                    return self.upgrade_med(only_hosp)
                self.back()
            return True
        return False

    def build_free_or_help(self):
        ret = self.device.wait_for(('help_union', 'free_build'), attempts=2)
        if ret[0] == 'help_union':
            self.device.tap(ret[1])
        elif ret[0] == 'free_build':
            self.device.tap(ret[1])
            return True
        return False

    def grow_acc2(self):
        self.input_town()
        if self.device.wait_for(('hammer', 'hammer2'), attempts=2, threshold=0.72)[0]:
           return False
        threshold_tulip = 0.68
        tulips = ('tulip_pub', 'tulip_pub2')
        if not self.move_to_img(tulips, 10, 100, -20, threshold=threshold_tulip):
            if not self.move_to_img(tulips, 10, -150, 26, threshold=threshold_tulip):
                self.move_to_img(tulips, 10, 100, -50)
        # кликаем по таверне через академию, потому что последняя более стабильно находится
        if self.device.tap_on('academy', attempts=1, threshold=threshold_tulip, dx=80, dy=30) or \
            self.device.tap_on(tulips, attempts=1, threshold=threshold_tulip):
            if not self.device.tap_on('upgrade_small_size', attempts=3):
                return False

            sleep(1)
            scr_fn = self.device.make_screenshot()
            coun = 0
            while self.device.tap_on('go_upgrade_next_build', attempts=2, threshold=0.7, prepared_scr_shot=scr_fn):
                coun += 1
                if coun > 15:
                    break
                sleep(2)
                if not self.finger(1, 1):
                    if not self.finger(1, 1):
                        self.device.tap((425, 250))
                if not self.device.tap_on('upgrade_small_size', attempts=2):
                    if self.device.tap_on('constract_button', attempts=2):
                        if self.build_free_or_help():
                            return self.grow_acc2()
                        return True
                    else:
                        self.device.tap((425, 250))
                sleep(2)
                scr_fn = self.device.make_screenshot()
                if self.device.is_image('speedup_red', threshold=0.7, prepared_scr_shot=scr_fn):
                    self.back()
                    return False

            # if ret1[0] == 'speedup' or self.device.tap_on('speedup_red', attempts=2, threshold=0.7,
            #                                               prepared_scr_shot=scr_fn):
            #     self.device.tap_on('use_speedup', attempts=2, threshold=0.8)
            #     scr_fn = self.device.make_screenshot()
            # elif self.device.tap_on('go_upgrade_next_build', attempts=2, threshold=0.7, prepared_scr_shot=scr_fn):
            #     sleep(2)
            #     self.finger(small=1, scr_fn=scr_fn)
            #     self.device.tap_on('speedup', attempts=2, threshold=0.8)
            #     self.device.tap_on('use_speedup', attempts=2, threshold=0.8)
            # self.device.tap_on('free_speedup', attempts=2, threshold=0.8)
            # if self.device.tap_on('upgrade_button', attempts=2) and count_cycles > -1:
            #     return True

            if self.device.tap_on('upgrade_button', attempts=2, threshold=0.75, prepared_scr_shot=scr_fn):
                sleep(2)
            self.back(2)
            if self.build_free_or_help():
                return self.grow_acc2()

    def upgrade_stables(self):
        self.input_town()
        if self.device.wait_for(('hammer', 'hammer2'), attempts=2, threshold=0.72)[0]:
           return False
        house = ('knight', )
        if not self.move_to_img(house, 10, 5, -80):
            return False
        coords = self.device.get_all_images(house, threshold=0.75)
        self.device.tap(coords[0])
        if not self.device.tap_on('upgrade_small_size', attempts=2):
            self.device.tap(coords[0])
            if not self.device.tap_on('upgrade_small_size', attempts=2):
                return False
        if self.device.tap_on('upgrade_button', attempts=2, threshold=0.75):
            sleep(3)
        self.back(3)
        if self.build_free_or_help():
            return self.upgrade_stables()
        return True

    def upgrade_wood(self, up_only_safe=False):
        self.input_town()
        if self.device.wait_for(('hammer', 'hammer2'), attempts=2, threshold=0.72)[0]:
           return False
        if up_only_safe:
            if not self.device.wait_for('safe_production', threshold=0.77, attempts=3)[0]:
                return False  # апаем домики только если включен режим защиты ресов
        ferm = 'sawmill_town'
        thresh_ferm = 0.65
        if random.randint(0, 1):
            ferm = ('farm_town', 'farm_town2')
            thresh_ferm = 0.55
        # self.device.swipe(200, 0)
        # self.device.tap_on('heal', attempts=1)
        if random.randint(0, 1):  # случайным образом перемещаемся на нижние лечилки
            self.device.swipe(0, -200)
        sleep(2)
        if not self.move_to_img(ferm, 10, -50, 40, threshold=thresh_ferm):
            if not self.move_to_img(ferm, 10, -50, -40):
                logger.debug('Strange: no res houses found to upgrade')
                return False
        sleep(2)
        coords = self.device.get_all_images(ferm, threshold=thresh_ferm)
        if not len(coords):
            return False
        add_ind = 1
        if len(coords) > 1:
            rand_ind = random.randint(0, len(coords)-1)
            while coords[rand_ind][0] < 80 or coords[rand_ind][1] < 80 or coords[rand_ind][0] > 850 - 80 or coords[rand_ind][1] > 500 - 80:
                rand_ind += add_ind
                if rand_ind >= len(coords):
                    add_ind = -1
                    rand_ind += add_ind
                if rand_ind < 0:
                    return False
        else:
            rand_ind = 0
        self.device.tap(coords[rand_ind])
        if not self.device.tap_on('upgrade_small_size', attempts=2):
            self.device.tap(coords[rand_ind])
            if not self.device.tap_on('upgrade_small_size', attempts=2):
                return False
        if self.device.tap_on('upgrade_button', attempts=2, threshold=0.75):
            sleep(3)
        self.back(3)
        if self.build_free_or_help():
            return self.upgrade_wood(up_only_safe=up_only_safe)
        return True

    def back(self, attempts=1):
        if self.device.tap_on(('back1', 'back2'), threshold=0.79, attempts=attempts):
            sleep(1)

    def collect(self, attempts=1):
        ret = self.device.wait_for(('collect', 'join_events', 'back1', 'back2', 'collect2', 'retry', 'collect3'), threshold=0.85, attempts=attempts)
        if ret[0]:
            if ret[0] == 'collect':
                self.device.tap(ret[1], dy=370)
            elif ret[0] == 'collect3':
                self.device.tap(ret[1], dy=370)
            elif ret[0] == 'join_events':
                self.device.tap(ret[1])
                self.back()
                sleep(1)
                self.back()
            elif ret[0] == 'retry':
                self.device.tap(ret[1])
                self.device.tap(ret[1])
                sleep(1)
                return self.collect()
            else:
                self.device.tap(ret[1])
            sleep(3)

    def clear_dialogs_after_login(self):
        self.chain_taps({'pics': [{'pic': 'sign_in', 'addtapx': 40, 'addtapy': 100}, 'reject_union', {'pic': 'collect', 'dy': 370}, {'pic': 'collect3', 'dy': 370}, 'retry',
                                  'reject_union', 'join_events', 'back1', 'back2', 'exit_town', 'input_town'],
                         'threshold': 0.75, 'end_pic': ['input_town']})
        self.device.tap_on('collect3', threshold=0.78, attempts=6, dy=370)

    def change_set_troops(self):
        ret = self.device.tap_on('hero_change_set_troops', threshold=0.75, attempts=3, dx=10, dy=10)
        if ret:
            sleep(1.5)
        return ret
        # self.device.tap((335, 350))  # меняем сет войск

    def set_little_troops(self, num_troops=1):
        coords = self.device.get_all_images('troop_empty_place', threshold=0.8)
        if len(coords) == 4 and num_troops == 1:  # уже установлены пустые войска
            return True
        if not len(coords) == 5:
            self.change_set_troops()  # меняем сет войск
        self.device.tap_on('attack_clear', threshold=0.78, attempts=3)
        self.device.tap_on('troop_confirm', attempts=2, threshold=0.76)
        self.device.tap_on('attack_clear', threshold=0.78, attempts=3)
        self.device.tap_on('troop_confirm', attempts=2, threshold=0.76)
        if not self.device.tap_on('troop_empty_place', attempts=2, threshold=0.95):
            if self.device.tap_on('check', attempts=2):
                return 'all heroes outside'
            self.back()
            return 'empty troops'
        if not self.device.tap_on(('griffon', 'priestess2', 'troop_horses'), attempts=2, threshold=0.76):
            return 'empty troops'
        sleep(1)
        self.device.tap((330, 210))
        sleep(1)
        if num_troops > 1:      # добавляем немного войск, если 1 солдат, то на стену встанут полным составом
            ret = self.device.wait_for('troop_plus', attempts=2, threshold=0.76, false_is_except=True)
            for _ in range(1, num_troops):
                self.device.tap(ret[1])
        self.device.tap_on('troop_confirm', attempts=2, threshold=0.76)
        sleep(1)
        return True

    def attack_small(self, enemies, jj, attempt=1):
        if not enemies:
            return False
        if jj >= len(enemies):
            jj = 0
        if len(enemies[jj]) > 3 and time.time() - enemies[jj][3] < 60*60:
            sleep(10)  # игнорим час тех, кто отпрыгнул или одел купол
            return self.attack_small(enemies, jj+1, attempt)
        enemy = enemies[jj]
        self.exit_town()
        self.go_coors(enemy)
        sleep(2.5)
        vert_x = 250
        self.device.tap((425, vert_x))
        if self.device.tap_on('explore', attempts=2, threshold=0.85):
            if self.device.tap_on('explore2', attempts=2, threshold=0.85):
                sleep(6)
            else:
                sleep(4)
            vert_x = 210
            self.device.tap((425, vert_x))
            sleep(2.5)
        if not self.device.is_image('colony', threshold=0.78):
            if len(enemies[jj]) > 3:
                enemies[jj][3] = time.time()
            else:
                enemies[jj].append(time.time())
            jj += 1
            # del enemies[jj]  # либо под куполом, либо улетел, удаляем пока
            return self.attack_small(enemies, jj)
        self.device.tap_on('scout', threshold=0.78, attempts=3)
        sleep(2)
        self.device.tap((425, vert_x))
        if self.device.tap_on('rally', threshold=0.78, attempts=3):
            self.device.tap_on('rally_60minutes', threshold=0.78, attempts=3)
            if self.device.tap_on('check', attempts=2):
                return 'all heroes outside'
            if self.set_little_troops() == 'empty troops':
                return 'empty troops'
            sleep(1)
            self.device.tap_on('go', threshold=0.78, attempts=2)
            return True
        # скорее всего моба уже объявлена, поэтому идем на других, либо кликнули на движующуюся армию
        return self.attack_small(enemies, jj+1, attempt + 1)

    def relogin_acc(self, acc):
        small = 1.5
        # self.back()
        try:
            self.chain_taps({'pics': [{'pic': 'collect', 'dy': 370}, 'join_events', 'back1', 'back2',
                                  'collect2', 'retry', 'input_town', {'pic': 'face_all', 'dx': -50, 'dy': 30}], 'threshold': 0.85,
                         'end_pic': ['face_all', ]})
        except Exception as e:
            logger.debug(str(e))
            if str(e).find('error: device not found') > -1:
                self.device.start()
                sleep(15)
                return self.relogin_acc(acc)
            else:
                raise Exception(str(e))
        # self.collect()
        # self.input_town()
        # self.back()
        # self.device.tap_on(('face', 'face1', 'face2', 'face3'))
        sleep(3*small)
        # try:
        #     if self.device.is_image(acc['nick'], threshold=0.92):
        #         self.back()
        #         sleep(small)
        #         return True
        for _ in range(10):
            if not self.device.is_image('change_acc'):
                self.device.tap_on('input_town', one_attempt=True)
                self.device.tap_on('face_all', attempts=15, dx=-50, dy=30)
                self.back()
            else:
                break
        for _ in range(15):
            self.device.tap_on('change_acc', false_is_except=True, attempts=5)
            if self.device.tap_on('change_acc2', attempts=2):
                break
        sleep(small)
        if acc['bound'] == 'google':
            self.device.tap_on('google', one_attempt=True, threshold=0.8)
            self.device.wait_for(acc['gmail'])
            sleep(small)
            if not self.device.tap_on(acc['gmail'], one_attempt=True):
                self.device.tap_on('change_acc', attempts=1)
                self.device.tap_on('change_acc2', attempts=2)
                self.device.tap_on('google', attempts=2, threshold=0.8)
                if not self.device.tap_on(acc['gmail'], one_attempt=True):
                    print('debme')
            sleep(small)
            self.device.tap_on(acc['gmail'], one_attempt=True)
        elif acc['bound'] == 'facebook':
            self.device.tap_on('facebook')
            sleep(2*small)
            if not self.device.tap_on('login_fb_continue', attempts=2):
                self.device.tap_on('telephone')
                sleep(small)
                self.device.send_text(acc['fb_login'])
                self.device.tap_on('facebook_pas')
                sleep(small)
                for symb in acc['fb_pas']:
                    # if symb in ['()<>|;&*\~"\'%%']:
                    #     symb = '\\' + symb
                    if symb in '0123456789':
                        symb = "\\" + symb
                    self.device.send_text(symb)
                    sleep(0.1)
                sleep(small)
                self.device.tap_on('facebook_login_button')
                sleep(small)
                self.device.tap_on('facebook_continue')

        elif acc['bound'] == 'account':
            self.device.tap_on('log_account')
            sleep(small)
            for _ in range(10):
                ret = self.device.wait_for('email_pas_field')
                if not ret or not ret[0]:
                    raise Exception('Email pas field is not found')
                # кликаем выше поля пароля, чтобы попасть в поле логина
                self.device.tap((ret[1][0][0]+290, ret[1][0][1]-90))
                sleep(small)
                self.device.send_del(40)
                if self.device.tap_on('account_field', attempts=1, threshold=0.93):
                    break
            self.device.send_text(acc['login'])
            sleep(small)
            self.device.tap_on('email_pas_field', false_is_except=True)
            sleep(small)
            self.device.send_text(acc['pas'])
            sleep(small)
            self.device.tap_on('email_confirm', attempts=5, threshold=0.8)
            sleep(small)
            self.device.tap_on('email_confirm', attempts=1, threshold=0.8)
            sleep(small)

        elif acc['bound'] == 'mail':
            self.device.tap_on('email')
            sleep(small)
            for _ in range(10):
                ret = self.device.wait_for('email_pas_field')
                if not ret or not ret[0]:
                    raise Exception('Email pas field is not found')
                # кликаем выше поля пароля, чтобы попасть в поле логина
                self.device.tap((ret[1][0][0]+290, ret[1][0][1]-90))
                sleep(small)
                self.device.send_del(40)
                if self.device.tap_on('email_field', attempts=1, threshold=0.93):
                    break
            self.device.send_text(acc['login'])
            sleep(small)
            self.device.tap_on('email_pas_field', false_is_except=True)
            sleep(small)
            self.device.send_text(acc['pas'])
            sleep(small)
            self.device.tap_on('email_confirm', attempts=5, threshold=0.8)
            sleep(small)
            self.device.tap_on('email_confirm', attempts=1, threshold=0.8)
            sleep(small)
        sleep(5)
        self.clear_dialogs_after_login()
        sleep(2.5)
        # self.clear_dialogs_after_login()


    def arena(self, acc):
        self.move_to_img('email_confirm', 10, 100, 100)
        self.device.tap_on('arena')

    # сохраняем статистику об аккаунте
    def save_stat(self, acc, stat):
        self.input_town()
        if self.device.tap_on('inventory', one_attempt=True, threshold=0.85):
            if self.device.tap_on('inventory_other.png', attempts=3, threshold=0.85):
                sleep(2)
                fn = self.device.make_screenshot()
                shutil.copyfile(fn, 'stats/wishes_%s.png' % acc['nick'])
            if self.device.tap_on('inventory_chest.png', attempts=3, threshold=0.85):
                sleep(2)
                fn = self.device.make_screenshot()
                shutil.copyfile(fn, 'stats/maps_%s.png' % acc['nick'])
            self.back(2)
        if self.device.tap_on('food_small_icon', one_attempt=True, threshold=0.85):
            sleep(2)
            self.move_to_img('obtain', 6, 0, 40, threshold=0.8, center_img=False, x0=200)
            sleep(1)
            fn = self.device.make_screenshot()
            shutil.copyfile(fn, 'stats/res_info_food_%s.png' % acc['nick'])
            if self.device.tap_on('res_info_blue_cristalls', attempts=3, threshold=0.85):
                sleep(2)
                self.move_to_img('obtain', 6, 0, 40, threshold=0.8, center_img=False, x0=200)
                sleep(2)
                fn = self.device.make_screenshot()
                shutil.copyfile(fn, 'stats/res_info_cristalls_%s.png' % acc['nick'])
            if self.device.tap_on('res_info_wood', attempts=3, threshold=0.85):
                sleep(2)
                self.move_to_img('obtain', 6, 0, 40, threshold=0.8, center_img=False, x0=200)
                sleep(1)
                fn = self.device.make_screenshot()
                shutil.copyfile(fn, 'stats/res_info_wood_%s.png' % acc['nick'])
                self.device.tap_on('res_info_blue_cristalls', attempts=3, threshold=0.85)

            if self.device.tap_on('res_info_wood', attempts=3, threshold=0.85):
                sleep(2)
                try:
                    stat_wood = common.get_json_from_file('stats/wood_stat.txt')
                    add_symb = {}
                    wood_4k = self.get_numbers(fn, 'res_count_4', 'wood_ciph_', threshold=0.85, cropx1=30, cropy1=35,
                                               cropx2=2, cropy2=36, permit_except=False, add_symb=add_symb)
                    if wood_4k == -1:
                        wood_4k = 0
                    wood_08 = self.get_numbers(fn, 'res_count_8', 'wood_ciph_', threshold=0.85, cropx1=30, cropy1=35,
                                               cropx2=2, cropy2=36, permit_except=False, add_symb=add_symb)
                    if wood_08 == -1:
                        wood_08 = 0

                    self.device.swipe(0, -40, 300, 300)
                    sleep(2)
                    fn = self.device.make_screenshot()
                    wood_50 = self.get_numbers(fn, 'res_count_50', 'wood_ciph_', threshold=0.85, cropx1=30,
                                               cropy1=35, cropx2=2, cropy2=36, permit_except=False, add_symb=add_symb)
                    if wood_50 == -1:
                        wood_50 = 0
                    wood_100 = self.get_numbers(fn, 'res_count_100', 'wood_ciph_', threshold=0.85, cropx1=30,
                                               cropy1=35, cropx2=2, cropy2=36, permit_except=False, add_symb=add_symb)
                    if wood_100 == -1:
                        wood_100 = 0
                    wood_1m = self.get_numbers(fn, 'wood_ciph_1m', 'wood_ciph_', threshold=0.85, cropx1=30,
                                               cropy1=35, cropx2=2, cropy2=36, permit_except=False, add_symb=add_symb)
                    if wood_1m == -1:
                        wood_1m = 0
                    sum_wood = wood_1m * 1000000 + wood_4k * 4000 + wood_100 * 100000 + wood_50 * 50000 + wood_08 * 800
                    item_stat = -1
                    for jj in range(len(stat_wood)):
                        if stat_wood[jj]['nick'] == acc['nick']:
                            item_stat = jj
                            break
                    stat_elem = {'nick': acc['nick'], 'sum_wood': sum_wood, 'sum_wood_time': time.asctime(time.localtime(time.time()))}
                    if item_stat > -1:
                        stat_wood[item_stat] = stat_elem
                    else:
                        stat_wood.append(stat_elem)
                    common.save_json_to_file(stat_wood, 'stats/wood_stat.txt')

                    # stat_wood = common.get_json_from_file('stats/wood_stat2.txt')
                    # stat_wood2 = []
                    # for item in stat_wood.items():
                    #     full_item = {'nick': item[0]}
                    #     full_item.update(item[1])
                    #     stat_wood2.append(full_item)
                    # stat_wood2 = sorted(stat_wood2, key=lambda k: k['sum_wood'], reverse=True)
                    # common.save_json_to_file(stat_wood2, 'stats/wood_stat2.txt')

                except Exception as e:
                    logger.debug(str(e))

            self.back(2)

    def click_top_img(self, pat):
        coords = self.device.get_all_images(pat, threshold=0.78)
        ymin_coor = (0, 0)
        if len(coords):
            if len(coords) > 1:
                rand_ind = random.randint(0, len(coords) - 1)
            else:
                rand_ind = 0
            # for coor in coords:
            #     if ymin_coor[0] < 450 and coor[1] > ymin_coor[1]:
            #         ymin_coor = coor
            self.device.tap(coords[rand_ind])

    def tulip_actions(self, acc, girls, attempt=1):
        small = 1
        # запускаем приключения
        threshold_tulip = 0.68
        tulips = ('tulip_pub', 'tulip_pub2')
        if not self.move_to_img(tulips, 10, 100, -20, threshold=threshold_tulip):
            if not self.move_to_img(tulips, 10, -150, 26, threshold=threshold_tulip):
                self.move_to_img(tulips, 10, 100, -50, threshold=threshold_tulip)
        # кликаем по таверне через академию, потому что последняя более стабильно находится
        if True:
        # if not 'main' in acc or not acc['main']:
            if self.device.tap_on('academy', attempts=1, threshold=threshold_tulip, dx=80, dy=30) or \
                self.device.tap_on(tulips, attempts=1, threshold=threshold_tulip):
                sleep(small)
                self.device.tap_on('adventure', attempts=2, threshold=0.85)
                if self.device.wait_for('adventure_collect', attempts=2, threshold=0.85)[0]:
                    self.device.tap_on('adventure_team', attempts=2, threshold=0.85)
                    sleep(2)
                    fn = self.device.make_screenshot()
                    ret = self.device.wait_for('adventure_rep_gold', prepared_scr_shot=fn, attempts=1, threshold=0.95)
                    if ret[0] and ret[1][1][1] < 200:
                        try:
                            fn2 = self.device.make_screenshot(file_name='gold_adv_%s.png' % acc['nick'])
                            subprocess.Popen('mspaint "' + fn2 + '"')
                        except:
                            pass
                    shutil.copyfile(fn, 'stats/adventure_team_%s.png' % acc['nick'])
                    self.device.swipe(0, -150, 300, 300)
                    sleep(1.5)
                    self.device.tap_on('adv_remove', attempts=2, threshold=0.8)
                    sleep(1.5)
                    self.device.tap_on('adv_remove', attempts=2, threshold=0.8)
                    sleep(1.5)
                    self.device.tap_on('adv_remove', attempts=2, threshold=0.8)
                    sleep(1.5)
                    self.click_top_img('adv_deploy')
                    sleep(1.5)
                    self.click_top_img('adv_deploy')
                    sleep(1.5)
                    self.click_top_img('adv_deploy')
                    sleep(1)
                    self.device.tap((50, 50))
                ret = self.device.wait_for('adventure_collect', attempts=2, threshold=0.85)
                if ret and ret[0]:
                    self.device.tap((ret[1][0][0], ret[1][0][1]))
                    sleep(small)
                    self.device.tap((ret[1][0][0], ret[1][0][1]))
                    sleep(small)
                self.device.tap_on('adventure_start', one_attempt=True, threshold=0.85)
                sleep(small)
                self.device.tap_on('adventure_start', one_attempt=True, threshold=0.85)
                self.back()
            else:
                self.collect()
                if attempt < 4:
                    return self.tulip_actions(acc, girls, attempt+1)
                logger.debug('debug: where tulip')
        if not 'main' in acc or not acc['main']:
            if girls:
                # идем на свидание
                if self.move_to_img(tulips, 10, 100, -50, threshold=threshold_tulip):
                    self.device.tap_on(tulips, one_attempt=True, threshold=threshold_tulip, dy=40)
                    sleep(2)
                    self.device.tap_on('girl', one_attempt=True, threshold=0.64)
                    sleep(2)
                    self.device.tap_on('girl_open', attempts=2, threshold=0.74)  # для открытия новой девушки
                    self.device.tap((44, 117))
                    sleep(2)

                    girl_game = False
                    if not self.device.tap_on('girl_game', attempts=2, threshold=0.74, template_exclude='girl_game_exclude'):
                        self.device.tap_on('girl2', one_attempt=True, threshold=0.74)
                        if self.device.tap_on('girl_game', attempts=2, threshold=0.74,
                                              template_exclude='girl_game_exclude'):
                            girl_game = True
                    else:
                        girl_game = True
                    if girl_game:
                        sleep(3)
                        for kk in range(9):
                            self.device.tap_on('girl_game_start', one_attempt=True, threshold=0.74)
                            sleep(4)
                            self.device.tap((430, 315))
                            self.device.tap((540, 315))
                            sleep(2)

                    if not self.device.tap_on('date', attempts=3, threshold=0.74, template_exclude='nodate'):
                        self.device.tap_on('girl1', one_attempt=True, threshold=0.74)
                        if self.device.tap_on('date', attempts=4, threshold=0.74, template_exclude='nodate'):
                            sleep(4)
                    else:
                        sleep(4)

                    self.device.tap((44, 117))
                    if self.device.tap_on('girl2', attempts=3, threshold=0.74):
                        self.device.tap_on('girl_open', attempts=3, threshold=0.74)
                    self.back(4)
                    self.back()
                else:
                    logger.debug('debug img situation')
                    self.back()

    def ellary(self):
        self.input_town()
        if not self.move_to_img('ellary', 10, 80, -150, threshold=0.74):
            if not self.move_to_img('ellary', 10, -150, 40, threshold=0.74):
                return False
        if self.device.tap_on('ellary', one_attempt=True):
            sleep(1)
            if self.device.tap_on('ellary_wish_icon', one_attempt=True):
                sleep(2)
                coun = 0
                while self.device.is_image('ellary_free_wish', threshold=0.74):
                    self.device.tap_on(('ellary_wood', 'ellary_food', 'ellary_rude'), one_attempt=True)
                    sleep(1)
                    coun += 1
                    if coun > 20:
                        break
                sleep(2)
                self.back()
                self.back()



    # тренируем войска и попутно выполняем мелочевку
    def train_army(self, acc, get_portal, get_treasure, girls):
        small = 3
        sleep(small)
        self.exit_town()
        self.input_town()

        ret = self.device.wait_for(('exit_town', 'back1', 'input_town', 'reject_union', 'collect'), false_is_except=True, threshold=0.77)
        if ret[0] and ret[0] in ['back1', 'input_town']:
            self.back()
            self.device.tap_on('input_town', one_attempt=True)
            if not self.device.wait_for('exit_town', attempts=20)[0]:
                # из-за режима обучения с первого раза может не кликнуться
                self.device.tap_on('input_town', one_attempt=True)
            self.device.wait_for('exit_town', false_is_except=True, attempts=20)

        # забираем награду за онлайн
        self.move_to_img('tower', 5, -150, -150, threshold=0.74)
        if self.move_to_img('tower', 5, 150, 150, threshold=0.74):
            self.device.tap_on('tower', one_attempt=True, threshold=0.85, dx=-80)
            sleep(small)
            self.collect()
            self.device.tap((80, 300))
            sleep(small)
        else:
            logger.debug('debug: where tower')

        # улучшение войск
        if not self.move_to_img('rally_point', 5, -150, -150, threshold=0.74):
            self.move_to_img('rally_point', 7, 100, 100, threshold=0.74)

        if self.move_to_img('rally_point', 5, -150, -150, threshold=0.74):
            self.device.tap_on('rally_point', one_attempt=True, threshold=0.74, dx=30)
            # двойное нажатие на столб, чтобы забрать прошлые улучшенные войска
            if not self.device.tap_on('upgrade_soldiers', attempts=3, threshold=0.85, dx=30):
                self.device.tap_on('rally_point', one_attempt=True, threshold=0.85, dx=30)
                sleep(1)
            sleep(1)
            self.device.tap((150, 140))
            self.device.tap((150, 140))
            self.device.tap((150, 140))
            self.device.tap((150, 140))
            # self.device.tap_on('cancel_button2', one_attempt=True, threshold=0.85)
            # подтверждаем забор войск из армии героев, потому что если не будем этого делать,
            # то у героев останутся неусиленные войска и они так и останутся такими, пока их вручную не вытащить
            self.device.tap_on('confirm_button4', one_attempt=True, threshold=0.85)
            self.device.tap_on('upgrade_button2', attempts=3, threshold=0.85)
            sleep(1)
            self.back()
            self.back()

        self.device.swipe(300, 80)
        self.device.swipe(130, 50)
        # позиционируемся на тренировочных домиках
        if not self.device.is_image('priestess', threshold=0.72):
            if not self.device.is_image('statue'):
                self.device.swipe(5, 20)
                sleep(1)
                self.device.swipe(-70, 210)  # со второй части острова смещаемся вверх на тренировочные домики
                self.device.swipe(-70, 210)
            else:
                self.device.swipe(120, 70)  # позиционируемся на тренировочных домиках
        if 'train' in acc:
            for type_army in acc['train']:  # ['guard', 'crossbow', 'priestess', 'knight']
                if not self.move_to_img(type_army, 3, 0, -40, threshold=0.74):
                    continue
                self.device.tap_on(type_army, one_attempt=True)
                sleep(small)
                if self.device.is_image('speedup'):
                    continue
                if not self.device.is_image('recruit'):
                    self.device.tap_on(type_army, one_attempt=True)
                    sleep(small)
                if self.device.tap_on('recruit', one_attempt=True):
                    sleep(small)
                    if self.device.tap_on('recruit2', one_attempt=True, threshold=0.85):
                        sleep(1.5*small)
                    else:
                        self.back()
                else:
                    debugme = 1
        self.device.tap_on('collect_food', one_attempt=True, threshold=0.85, grain=80)
        sleep(small)

        self.tulip_actions(acc, girls)

        # открываем бесплатный сундук
        if get_treasure:
            self.move_to_img('shop', 5, 70, 20, threshold=0.68)
            if self.device.tap_on('shop', one_attempt=True, threshold=0.8):
                sleep(small)
                self.device.tap_on('treasure', attempts=3, threshold=0.8)
                sleep(small)
                self.device.tap_on('open_for_free', attempts=2, threshold=0.8)
                self.back(4)
            else:
                logger.debug('debug pls')
                self.back()

        # помогаем союзникам (а значит и своим твинкам)
        if self.device.tap_on('hands_union', one_attempt=True):
            sleep(small)

        # чиним стену после пожара
        if self.device.tap_on('repair_wall', one_attempt=True, dx=30):
            self.device.tap_on('repare_wall', attempts=3)
            sleep(small)
            self.back()
            sleep(small)
        else:
            logger.debug('check')
        if get_portal:
            if self.move_to_img('teleport_town', 15, -30, -70, threshold=0.68):
                if self.move_to_img('teleport_key', 3, -30, -70, threshold=0.68):
                    if self.device.tap_on('teleport_key', one_attempt=True):
                        self.device.tap_on('teleport_open_free', attempts=6)
                        sleep(2)
                        self.back()

        # забираем награду за онлайн
        self.move_to_img('tower', 5, -150, -150, threshold=0.74)
        if self.move_to_img('tower', 5, 150, 150, threshold=0.74):
            self.device.tap_on('tower', one_attempt=True, threshold=0.85, dx=-80)
            sleep(small)
            self.collect()
            self.device.tap((80, 300))
            sleep(small)

        # забор бесплатных призывов зверей
        if self.move_to_img('dragon_nest', 8, 150, -150, threshold=0.74):
            self.device.tap_on('dragon_nest', one_attempt=True, threshold=0.85)
            sleep(1.5)
            self.device.tap_on('dragon_grounds', attempts=2, threshold=0.85)
            sleep(0.5)
            if self.device.tap_on('dragon_summon1', attempts=2, threshold=0.85):
                if self.device.tap_on('beast_confirm', attempts=3, threshold=0.85):
                    try:
                        fn2 = self.device.make_screenshot(file_name='new_beast_%s.png' % acc['nick'])
                        subprocess.Popen('mspaint "' + fn2 + '"')
                    except:
                        pass
                    sleep(1.5)
                self.device.tap((50, 50))
                sleep(1.5)
            self.device.tap_on('dragon_normal_summon', attempts=2, threshold=0.85)
            sleep(0.5)
            if self.device.tap_on('dragon_normal_summon', attempts=2, threshold=0.85):
                if self.device.tap_on('dragon_summon1', attempts=2, threshold=0.85):
                    if self.device.tap_on('beast_confirm', attempts=3, threshold=0.85):
                        try:
                            fn2 = self.device.make_screenshot(file_name='new_beast_%s.png' % acc['nick'])
                            subprocess.Popen('mspaint "' + fn2 + '"')
                        except:
                            pass
                        sleep(1.5)
                    self.device.tap((50, 50))
                    sleep(1.5)
                self.back()
            self.back()
            self.back()

    def attack_enemy(self, index_wa, acc, war_attack, attempt=1):
        if attempt > 2:
            raise Exception('wrong train result')
        for _ in range(2):
            self.device.tap_on('union', attempts=2)
            self.device.tap_on('ally_war', attempts=2)
            for _ in range(10):
                self.device.swipe(0, -90)
            ret = ''
            for _ in range(3):
                sleep(2)
                coords = self.device.get_all_images('ally_plus', debug=True, threshold=0.85)
                for coor in coords:
                    if coor[0] < 260:
                        self.device.tap(coor)
                        if self.device.tap_on('check', attempts=2):
                            ret = 'all heroes outside'
                            break
                        ret = self.set_little_troops()
                        if ret == 'empty troops':
                            acc['train'] = ["priestess", ]
                            self.train_army(acc)
                            return index_wa
                        elif ret == 'all heroes outside':
                            break
                        else:
                            sleep(1)
                            self.device.tap_on('go', threshold=0.78, attempts=2)
                self.device.swipe(0, 90)
            if ret == 'all heroes outside':
                break
            ret = self.attack_small(war_attack, index_wa)
            if ret in ['all heroes outside', 'empty troops']:
                if ret == 'empty troops':
                    acc['train'] = ["priestess", ]
                    self.train_army(acc)
                    return index_wa
                break
            index_wa += 1
        return index_wa

    def send_hero(self, templ, acc, attempt, res_val, min_load = -2):
        sleep(2)
        if not self.device.tap_on('gather', attempts=2):
            if not self.device.tap_on('wood', attempts=1, grain=80) or not self.device.tap_on('gather', attempts=2):
                if attempt > 9:
                    return False
                random.shuffle(templ)
                return self.get_harvest(templ, acc, attempt+1)

        if self.device.tap_on('check', attempts=3):
            return 'check'

        self.device.tap_on('autofill', attempts=3)
        load_power = self.get_load_power()

        if load_power < min_load:
            self.device.tap((570, 300))
            sleep(5)
            self.device.tap_on('autofill', attempts=2)
            load_power = self.get_load_power()
            if load_power < min_load:
                self.device.tap((570, 300))
                sleep(5)
                self.device.tap_on('autofill', attempts=2)
                load_power = self.get_load_power()
                if load_power < min_load:
                    return 'noload'

        if not self.device.tap_on('go', one_attempt=True, threshold=0.76):
            if self.device.tap_on('check', attempts=3):
                return 'check'
        logger.info('send_hero on resources is success, resource count = %d' % res_val)
        return True

    # отправляем героя в супершахту
    def go_supermine(self, min_load = -2):
        self.device.tap_on('union', attempts=2, threshold=0.8)
        sleep(2)
        self.device.tap_on('alliance_build', attempts=5, threshold=0.8)
        self.device.tap_on('dismantle', attempts=2, threshold=0.8, dx=50, dy=-50)
        if self.device.tap_on('gather', attempts=6):
            self.device.tap_on('autofill', attempts=3)
            sleep(2)
            load_power = self.get_load_power()
            if load_power < min_load:
                self.device.tap((570, 300))
                sleep(5)
                self.device.tap_on('autofill', attempts=2)
                load_power = self.get_load_power()
                if load_power < min_load:
                    self.device.tap((570, 300))
                    sleep(5)
                    self.device.tap_on('autofill', attempts=2)
                    load_power = self.get_load_power()
                    if load_power < min_load:
                        return False
            if not self.device.tap_on('go', one_attempt=True, threshold=0.76):
                if self.device.tap_on('check', attempts=3):
                    return 'check'
            logger.info('send_hero on supermine')
        return True

    def get_harvest(self, templ, acc, attempt=1, min_load=-2):
        if attempt > 2:
            self.back()
            return False
            # raise Exception('no ' + str(templ))
        small = 3
        sleep(small)
        # перезаходим наружу, чтобы быть в одинаковых корах с нашим городом
        self.input_town()
        self.exit_town(5)
        # if 'shift_farm' in acc:
        #     self.device.swipe(acc['shift_farm'][0], acc['shift_farm'][1])
        # if acc['heroes'] == 1 and self.device.is_image('on_fields'):
        #     logger.debug('Единственный герой на аккаунте уже собирает урожай')
        #     return False
        # cur_templ = ''
        # for ii in range(11):
        #     if ii == 10:
        #         if self.device.is_image('on_fields'):
        #             return False  # не нашли свободное поле, но зато увидели героя в полях, значит процесс сбора идет
        #         return self.get_harvest(templ, acc, attempt+1)
            # ind = attempt % len(templ)
        self.device.tap((430, 289))
        if not self.device.tap_on('list_owns', attempts=4, threshold=0.77, ):
            logger.info('Не найдена пиктограмма списка владений')
            return False
        sleep(1)
        if random.randint(0, 9) % 2 == 0:
            self.device.swipe(0, -140)
            sleep(3)

        res_pict = 'res_pict'
        arr_value_res = []
        arr_value_res2 = []
        add_symb = {'slesh': '/', '8_2': '8', '0_2': '0'}


        for zz in range(10):
            if zz:
                self.device.swipe(0, -80)
                sleep(2)
            screenshot_fn = self.device.make_screenshot()
            # screenshot_fn = r'c:\Users\denis\Pictures\test\wam_MEmu_20191110-001842.png'
            coords = self.device.get_all_images(res_pict, debug=True, threshold=0.7,
                                                prepared_scr_shot=screenshot_fn,
                                                crop=True, cropx1=110, cropy1=-2, cropx2=92, cropy2=2)
            for ii in range(len(coords)):
                prep_im = screenshot_fn[0:-4] + '_crop_%d_%s.png' % (ii, res_pict)
                res_val = self.get_numbers('', '', 'res_ciph_', prepared_scr_shot=prep_im, threshold=0.95,
                                           add_symb=add_symb, ciph_distance=6, return_int=False)
                fi = res_val.find('/')
                if fi > -1:
                    res_val = res_val[:fi]
                try:
                    res_val = int(res_val)
                    if res_val in [600000, 120000, 60000]:
                        self.device.tap((636, coords[ii][1]))
                        return self.send_hero(templ, acc, attempt, res_val, min_load=min_load)
                    arr_value_res.append((res_val, coords[ii]))
                except Exception as e:
                    logger.debug(str(e))
            if not len(arr_value_res):
                continue
            sleep(4)

            screenshot_fn = self.device.make_screenshot()
            coords = self.device.get_all_images(res_pict, debug=True, threshold=0.7,
                                                prepared_scr_shot=screenshot_fn,
                                                crop=True, cropx1=110, cropy1=-2, cropx2=92, cropy2=2)
            for ii in range(len(coords)):
                prep_im = screenshot_fn[0:-4] + '_crop_%d_%s.png' % (ii, res_pict)
                res_val = self.get_numbers('', '', 'res_ciph_', prepared_scr_shot=prep_im, threshold=0.94,
                                           add_symb=add_symb, ciph_distance=7, return_int=False)
                fi = res_val.find('/')
                if fi > -1:
                    res_val = res_val[:fi]
                try:
                    res_val = int(res_val)
                    if res_val == 6000000:
                        self.device.tap((636, coords[ii][1]))
                        return self.send_hero(templ, acc, attempt, res_val, min_load=min_load)
                    arr_value_res2.append((res_val, coords[ii]))
                except Exception as e:
                    logger.debug(str(e))

            # удаляем те шахты, на которых ресурсы уменьшаются и на которых их меньше 20к
            if len(arr_value_res) == len(arr_value_res2):
                for ii in reversed(range(len(arr_value_res))):
                    if arr_value_res[ii][0] > arr_value_res2[ii][0] or arr_value_res2[ii][0] < 20000:
                        del arr_value_res[ii]
                        del arr_value_res2[ii]

            if not arr_value_res:
                continue
            break

        if not arr_value_res:
            logger.debug('Нет подходящих шахт на экране')
            self.back()
            return False

        arr_value_res = sorted(arr_value_res, key=lambda tup: tup[0])
        self.device.tap((636, arr_value_res[-1][1][1]))
        return self.send_hero(templ, acc, attempt, arr_value_res[-1][0], min_load=min_load)

        # if templ[0] == 'sawmill':
        #     if not self.device.tap_on(('sawmill_full', 'food_full'), threshold=0.8, dx=135, dy=-23, attempts=2):
        #         coords = self.device.get_all_images(templ[0], threshold=0.8)
        #         if not len(coords):
        #             coords = self.device.get_all_images('sawmill2', threshold=0.7)
        #         if len(coords):
        #             if len(coords) > 1:
        #                 random.shuffle(coords)
        #             self.device.tap(coords[0], dx=490)
        #         else:
        #             coords = self.device.get_all_images('owns_baloon', debug=True, threshold=0.8)
        #             if len(coords):
        #                 if len(coords) > 1:
        #                     random.shuffle(coords)
        #                 self.device.tap(coords[0])
        #             else:
        #                 self.back()
        # else:
        #     if not self.device.tap_on(('sawmill_full', 'food_full'), threshold=0.8, dx=135, dy=-23, attempts=2):
        #         coords = self.device.get_all_images(templ[0], debug=True, threshold=0.7)
        #         if len(coords):
        #             if len(coords) > 1:
        #                 random.shuffle(coords)
        #             self.device.tap(coords[0], dx=490)
        #         else:
        #             coords = self.device.get_all_images('owns_baloon', debug=True, threshold=0.8)
        #             if len(coords):
        #                 if len(coords) > 1:
        #                     random.shuffle(coords)
        #                 self.device.tap(coords[0])
        #             else:
        #                 self.back()
        #
        # return self.send_hero(templ, acc, attempt)

    def clean_files(self):
        for dir in ('cache','app_webview','databases','no_backup'):
            path_to_delete = os.path.join(self.summoners_data_dir, dir)
            logger.debug(f'Удаляю директорию {path_to_delete}')
            self.device.adb(f'shell rm -r {path_to_delete}')
        logger.debug(f'Удаляем файлы в {self.summoners_data_dir}')
        self.device.adb(f'shell find {self.summoners_data_dir} -maxdepth 1 -type f -delete', timeout=45)
