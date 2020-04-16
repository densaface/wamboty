#!/usr/bin/env python3

import json
import logging
import os
from concurrent.futures.process import ProcessPoolExecutor
from random import shuffle
from time import sleep
import sys, traceback
import random

random.seed
import time
import shutil
from datetime import datetime

from libs.game import Game
from libs.memu import MemuController, MemuDevice
# from libs.nox import NoxController
from libs.common import get_external_ip, random_str
import libs.common as common
import subprocess

if getattr(sys, 'frozen', False):
    ABSOLUTE_PATH = lambda x: os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(sys.executable)), x[3:]))
elif __file__:
    ABSOLUTE_PATH = lambda x: os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), x))

logger = logging.getLogger(__name__)


class WAMWorker(object):

    def __init__(self, memu_name='MemuPlayer', second_par=None, third_par=None):
        self.second_par = second_par
        self.third_par = third_par
        self.memu_name = memu_name
        self.my_ip = None
        self.executor = None
        self.memu = None
        self.train = False
        self.train_power = 1200000
        self.fish_count = 0
        self.interface = False
        self.deep_def = True
        self.deep_def_days = [5, 6]


    def work(self):
        logger.debug('work dir: ' + ABSOLUTE_PATH('..\\'))

        os.chdir(ABSOLUTE_PATH('..\\'))

        device = self.memu.get_device(self.memu_name)
        if not device:
            logger.debug('Не найден эмулятор с именем ' + self.memu_name)
            common.message_box('Не найден эмулятор с именем ' + self.memu_name)
            return 0
        if self.second_par == 'screen':
            fn = device.make_screenshot()
            subprocess.Popen('mspaint "' + fn + '"')
            return 0
        if self.second_par == 'test':
            if device.wait_for('change_acc', attempts=1)[0]:
                self.res_test = 2
            else:
                self.res_test = 3
            return 0
        if not device and not self.second_par == 'create':
            raise Exception(f'Нет memu с названием {self.memu_name}')

        game = Game(device)
        accs = common.get_json_from_file('accs.txt')
        # prep_im = 'C:\\Users\\denis\\Pictures\\MEmu Photo\\wam_MEmu4_20191108-204827_crop_0_server_sign_m.png'
        # resx = game.get_numbers('', '', 'server_ciph_', prepared_scr_shot=prep_im, threshold=0.94)
        if device:
            device.clean_screenshots_dir()

        if self.second_par == 'monitor':
            main_acc = None
            for jj in range(0, len(accs)):
                if 'main' in accs[jj]:
                    main_acc = accs[jj]
                    break
            if not device.block_acc(main_acc):
                logger.debug('Not blocked wam account')
                exit(0)
            game.relogin_acc(main_acc)
            try:
                os.remove('twins/old_block_' + device.name + '.txt')
            except:
                pass
            while True:
                game.monitor_acc(10)
            exit(0)

        if self.second_par == 'create':
            fn = r'twins\full_mails.txt'
            f = open(fn, 'r')
            accs = f.readlines()
            f.close()

            opts = common.get_json_from_file('twins/create_twin_opts.txt')
            if not 'server' in opts:
                raise Exception("Set server option to transfer twin account")
            for jj in range(len(accs)):
                acc = accs[jj]
                if acc.find('sixth_mobs_attacked') > -1 or acc.find('Mail authentication failed') > -1 \
                        or acc.find('other server') > -1:
                    continue
                if not device:
                    self.memu.create_device()
                    device = self.memu.get_device(self.memu_name)
                    device.recreate1(delete_old=False)
                else:
                    device.recreate1()
                device = self.memu.get_device(self.memu_name)
                device.recreate2('c:\\wam\\arch\\')
                for _ in range(10):
                    try:
                        device = self.memu.get_device(self.memu_name)
                        game.device = device
                        game.click_twin_education()
                        break
                    except Exception as e:
                        logger.debug(str(e))
                        sleep(15)
                game.teleport_on_selected_server(opts)
                game.grow_acc()
                login = game.bind_acc_glob(accs, jj)
                game.alliance_join('ttt')
                game.get_system_mail()
                game.set_name(login[:login.find('@')])
                game.exit_town()
                coors = game.get_coors()
                accs[jj] = accs[jj].rstrip('\n')
                accs[jj] += '\tsixth_mobs_attacked\t%s\t%s\n' % (time.asctime(time.localtime(time.time())), str(coors))
                f = open(fn, 'w')
                f.writelines(accs)
                f.close()
                # game.go_coors([661, 629])
                logger.debug('acc saved')
            exit(0)

        if self.second_par == 'soldier_adventure':
            for zz in range(100):
                fn = r'twins\full_mails.txt'
                f = open(fn, 'r')
                accs = f.readlines()
                f.close()
                for jj in range(len(accs)):
                    acc = accs[jj]
                    if acc.find('sixth_mobs_attacked') == -1:
                        continue
                    login = acc[0:acc.find(':')]
                    # passw = acc[acc.find(':') + 1:-1]
                    acc = {'nick': login[0:login.find('@')], "bound": "mail", "login": login, "pas": "tremtrem", "gold_don": 0}
                    if not device.block_acc(acc):
                        print('not blocked acc for soldier_adventure')
                        continue
                    time1 = time.time()
                    try:
                        fn = 'stats/' + acc['nick'] + '.txt'
                        stat = common.get_json_from_file(fn)
                        if common.is_stat_more_dif_time(stat, 5 * 60 * 60, 'alliance') and not 'main' in acc:
                            game.relogin_acc(acc)
                            sleep(2)
                            device.tap_on('collect_food', one_attempt=True, threshold=0.85, grain=80)
                            if not game.alliance(acc, don_army=False, union_shop=False, union_help=False):
                                game.alliance_join('tt3')
                                if not game.alliance(acc, don_army=False, union_shop=False, union_help=False):
                                    print('debugme')
                            stat['alliance'] = int(time.time())
                            stat['alliance_str'] = time.asctime(time.localtime(time.time()))
                            common.save_json_to_file(stat, fn)
                            if not device.tap_on('event_center', threshold=0.8, attempts=2):
                                fn = device.make_screenshot()
                                shutil.copyfile(fn, 'stats_soldier/%s_not_found_event_center.png' % acc['nick'])
                                continue
                            sleep(1.5)
                            device.tap((100, 30))
                            if not device.tap_on('event_soldier', threshold=0.8, attempts=3):
                                fn = device.make_screenshot()
                                shutil.copyfile(fn, 'stats_soldier/%s_event_soldier.png' % acc['nick'])
                                continue
                            sleep(1.5)
                            for _ in range(10):
                                device.tap((100,  30))
                            fn = device.make_screenshot()
                            if device.is_image('event_chances_0', threshold=0.98, prepared_scr_shot=fn):
                                fn2 = device.make_screenshot()
                                shutil.copyfile(fn2, 'stats_soldier/%s_event_chances_0.png' % acc['nick'])
                            shutil.copyfile(fn, 'stats_soldier/%s.png' % acc['nick'])
                            device.tap((485, 400))
                            sleep(0.5)
                            fn = device.make_screenshot()
                            shutil.copyfile(fn, 'stats_soldier/elite_%s.png' % acc['nick'])
                            game.back()
                            game.back()
                            game.back()

                            # time2 = time.time() - time1
                            logger.debug('go to next acc, full time = %d seconds' % int(time.time() - time1))
                    except Exception as ex:
                        for zz in range(10):
                            if zz == 9:
                                raise Exception('error of restart activity')
                            try:
                                logger.debug("Error in twin soldier_adventure")
                                logger.debug(ex)
                                e2 = sys.exc_info()
                                logger.debug(repr(traceback.extract_tb(e2[2])))
                                device = self.memu.get_device(self.memu_name)
                                if not device.tap_on('retry', one_attempt=True):
                                    game.collect()
                                    # if not 'notgrow' in acc:
                                    #     game.grow_acc(15)
                                    device.stop()
                                    device.start()
                                    sleep(12)
                                    device.wait_loaded()
                                    device._send_event("KEYCODE_HOME")
                                    device.tap_on('wam_icon', threshold=0.85, false_is_except=True)
                                break
                            except Exception as e3:
                                logger.debug(e3)
                                e3 = sys.exc_info()
                                logger.debug(repr(traceback.extract_tb(e3[2])))

                        sleep(30)
            exit(0)

        if self.second_par == 'soldier_adventure2':
            fn = r'twins\full_mails.txt'
            f = open(fn, 'r')
            accs = f.readlines()
            f.close()
            for jj in range(len(accs)):
                acc = accs[jj]
                if acc.find('sixth_mobs_attacked') == -1:
                    continue
                login = acc[0:acc.find(':')]
                acc = {'nick': login[0:login.find('@')], "bound": "mail", "login": login, "pas": "tremtrem"}
                if not device.block_acc(acc):
                    print('not blocked acc for soldier_adventure2: ' + login)
                    continue
                time1 = time.time()
                try:
                    fn = 'stats/' + acc['nick'] + '.txt'
                    stat = common.get_json_from_file(fn)
                    if os.path.isfile('stats_soldier/%s_not_found_event_center.png' % acc['nick']):

                        # for _ in range(12):
                        #     game.upgrade_town()
                        #     if device.is_image('event_center', threshold=0.8):
                        #         break
                        game.relogin_acc(acc)

                        if not device.tap_on('event_center', threshold=0.8, attempts=2):
                            fn = device.make_screenshot()
                            shutil.copyfile(fn, 'stats_soldier/%s_not_found_event_center.png' % acc['nick'])
                            continue
                        sleep(1.5)
                        device.tap((100, 30))
                        if not device.tap_on('event_soldier', threshold=0.8, attempts=3):
                            fn = device.make_screenshot()
                            shutil.copyfile(fn, 'stats_soldier/%s_event_soldier.png' % acc['nick'])
                            continue
                        sleep(1.5)
                        for _ in range(10):
                            device.tap((100, 30))
                        fn = device.make_screenshot()
                        if device.is_image('event_chances_0', threshold=0.98, prepared_scr_shot=fn):
                            fn2 = device.make_screenshot()
                            shutil.copyfile(fn2, 'stats_soldier/%s_event_chances_0.png' % acc['nick'])
                        shutil.copyfile(fn, 'stats_soldier/%s.png' % acc['nick'])
                        device.tap((485, 400))
                        sleep(0.5)
                        fn = device.make_screenshot()
                        shutil.copyfile(fn, 'stats_soldier/elite_%s.png' % acc['nick'])
                        game.back()
                        game.back()
                        game.back()
                        os.remove('stats_soldier/%s_not_found_event_center.png' % acc['nick'])

                        # time2 = time.time() - time1
                        logger.debug('go to next acc, full time = %d seconds' % int(time.time() - time1))
                except Exception as ex:
                    for zz in range(10):
                        if zz == 9:
                            raise Exception('error of restart activity')
                        try:
                            logger.debug("Error in twin rotation")
                            logger.debug(ex)
                            e2 = sys.exc_info()
                            logger.debug(repr(traceback.extract_tb(e2[2])))
                            device = self.memu.get_device(self.memu_name)
                            if not device.tap_on('retry', one_attempt=True):
                                game.collect()
                                # if not 'notgrow' in acc:
                                #     game.grow_acc(15)
                                device.stop()
                                device.start()
                                sleep(12)
                                device.wait_loaded()
                                device._send_event("KEYCODE_HOME")
                                device.tap_on('wam_icon', threshold=0.85, false_is_except=True)
                            break
                        except Exception as e3:
                            logger.debug(e3)
                            e3 = sys.exc_info()
                            logger.debug(repr(traceback.extract_tb(e3[2])))

                    sleep(30)
            exit(0)

        if self.second_par == 'treasure':
            # cycle_start = 14
            main_acc = accs[0]
            device2 = self.memu.get_device(self.third_par)
            twin = Game(device2)
            # if not device2.block_acc(accs[cycle_start]):
            #     continue

            changed_place = False
            if changed_place:
                game2 = twin
                twin = game
                game = game2

            screenshot_fn = r'c:\Users\denis\Pictures\test\wam_MEmu5_20200303-170807.png'
            add_symb = {} # '5_2': '5'} # , '8_2': '8', '3_2': '3', '0_2': '0'
            # power = game.get_power(permit_except=False)
            # test = game.get_load_power()
            # print(game.get_numbers('', 'hero_load', 'load_ciph_', add_symb={}, cropx1=34, cropx2=110, ciph_distance=6, threshold=0.97, threshold_anchor=0.6,
            #                        prefer_x=640, prefer_y=370, radius=40,))
            # print(game.get_numbers('', ('hero_load', 'hero_load_archa'), 'load_ciph_', add_symb={}, cropx1=34, cropx2=110, ciph_distance=6, threshold=0.88, threshold_anchor=0.6,
            #                        prefer_x=640, prefer_y=370, radius=40,))
            # print(twin.get_numbers(screenshot_fn, 'mail_wood', 'mail_res_ciph_', grain=150, add_symb=add_symb, cropx1=39, cropx2=90, ciph_distance=6, threshold=0.99))
            # print(twin.get_numbers(screenshot_fn, 'mail_cristalls', 'mail_res_ciph_', grain=150, add_symb=add_symb, cropx1=33, cropx2=90, ciph_distance=6, threshold=0.99))

            if not game.device.block_acc(main_acc):
                logger.debug('Not blocked acc' + str(main_acc))
                exit(0)

            # game.relogin_acc(main_acc)
            # twin.relogin_acc(accs[cycle_start]) twin.send_hero_on_treasure(accs[cycle_start])
            treasure_send = 0  # сколько было успешно послано на сокровища на твине
            while True:
                while not game.is_free_heroes(main_acc['heroes']):
                    sleep(10)
                coords = twin.device.get_all_images('treasur_flag', debug=True, threshold=0.7)
                if len(coords):
                    ind_r = 0
                    if len(coords) > 1:
                        ind_r = random.randint(0, len(coords)-1)
                    twin.device.tap(coords[ind_r])
                    sleep(3)
                    twin.device.tap((425, 250))
                    if not twin.device.tap_on('treasur_find', threshold=0.78, attempts=2):
                        sleep(2)
                        twin.device.tap((425, 250))
                        if not twin.device.tap_on('treasur_find', threshold=0.78, attempts=2):
                            twin.device.tap_on('glob_map', threshold=0.78, attempts=3)
                            sleep(2)
                            twin.device.tap_on('treasur_find', threshold=0.78, attempts=3)
                            sleep(2)
                            continue
                    if twin.device.tap_on('check', threshold=0.78, attempts=2):
                        sleep(2)
                        twin.device.tap_on('glob_map', threshold=0.78, attempts=3)
                        sleep(2)
                        twin.device.tap_on('treasur_find', threshold=0.78, attempts=3)
                        sleep(15)
                        continue
                    twin.set_little_troops()
                    sleep(1)
                    twin.device.tap_on('go', threshold=0.78, attempts=3)
                    if twin.device.tap_on('check', threshold=0.78, attempts=3):
                        twin.device.tap_on('glob_map', threshold=0.78, attempts=3)
                        twin.device.tap_on('treasur_find', threshold=0.78, attempts=3)
                        sleep(15)
                        continue
                    else:
                        treasure_send += 1
                else:
                    if twin.device.wait_for('treasur_identify', threshold=0.85, attempts=1)[0]:
                        logger.debug('Treasure searching complete successfully!')
                        device.tap_on('mail', threshold=0.78, attempts=2)
                        device.tap_on('mail_system', threshold=0.78, attempts=4)
                        for _ in range(600):
                            device.swipe(0, -200, speed=340)
                        logger.debug('Treasure searching complete successfully!')
                        exit(0)

                coors = twin.get_coors(permit_except=False)
                if not coors:
                    continue
                for zz in range(4):
                    if zz == 3:
                        raise Exception('error go coors')
                    try:
                        game.go_coors(coors)
                        break
                    except:
                        pass
                while True:
                    game.device.tap((425, 250))
                    sleep(0.5)
                    if game.device.tap_on('attack2', one_attempt=True):
                        game.device.tap_on('go', threshold=0.78, attempts=3)
                        twin.device.tap_on('glob_map', threshold=0.78, attempts=3)
                        twin.device.tap_on('treasur_find', threshold=0.78, attempts=3)
                        break
                if treasure_send == 6:
                    logger.debug('Treasure searching complete successfully!')
                    device.tap_on('mail', threshold=0.78, attempts=2)
                    device.tap_on('mail_system', threshold=0.78, attempts=4)
                    for _ in range(600):
                        device.swipe(0, -200, speed=340)
                    logger.debug('Treasure searching complete successfully!')
                    exit(0)

        if self.second_par == 'mine':
            main_acc = None

            try:
                index_acc = self.index_acc
                main_acc = accs[index_acc]
                order_mine = self.order_mine
                mine_time = self.mine_time
                mine_rot = self.mine_rot
                mine_login = self.mine_login
            except:
                mine_time = 30
                order_mine = '4, 1'
                mine_rot = True
                mine_login = False
                for jj in range(0, len(accs)):
                    if 'main' in accs[jj]:
                        main_acc = accs[jj]
                        break

            mine_levels = order_mine.replace(' ', '').split(',')
            if not mine_time in [30, 40, 50]:
                mine_time = 0
            mine_time2 = mine_time
            if mine_time > 30:
                mine_time2 = mine_time % 30

            while True:
                    while not datetime.utcnow().weekday() in [1, 3]:
                        print('Ждем подходящий день недели')
                        sleep(20)

                    if not device.block_acc(main_acc):
                        logger.debug('Waiting for unblocking acc: ' + str(main_acc))
                        sleep(2)
                        continue

                    if mine_login:
                        game.relogin_acc(main_acc)
                        game.exit_town()
                        game.device.tap_on('expand_heroes', attempts=3, threshold=0.85)
                        game.return_from_collecting()

                    while True:
                        try:
                            heroes = main_acc['heroes']
                            # game.is_free_heroes(heroes)
                            for jj in range(len(mine_levels)):
                                mine_lvl = int(mine_levels[jj])
                                while game.is_free_heroes(heroes):
                                    if mine_time:
                                        # если мы близко к времени генерации новой руды, мы ждем несколько минут
                                        # и после этого запускаем поиск
                                        while ((int(time.strftime("%M")) + 60) % 30) - mine_time2 in [-1, -2, -3]:
                                            game.monitor_acc(1)
                                    if not game.go_mine2(mine_lvl, True) and jj == len(mine_levels) - 1:
                                        game.monitor_acc(60*4)
                            if game.is_free_heroes(heroes):
                                continue
                            if mine_rot and ((int(time.strftime("%M")) + 60) % 30) - (mine_time % 30) in [10,11,12,13]:
                                game.train_army(main_acc, False, 0, 0)
                                game.exit_town()
                            else:
                                game.monitor_acc(30)
                        except Exception as ex:
                            for zz in range(10):
                                if zz == 9:
                                    raise Exception('error of restart activity')
                                try:
                                    logger.debug("Error in mine")
                                    logger.debug(ex)
                                    e2 = sys.exc_info()
                                    logger.debug(repr(traceback.extract_tb(e2[2])))
                                    device = self.memu.get_device(self.memu_name)
                                    if not device.tap_on('retry', one_attempt=True):
                                        game.collect()
                                        # if not 'notgrow' in acc:
                                        #     game.grow_acc(15)
                                        device.stop()
                                        device.start()
                                        sleep(12)
                                        device.wait_loaded()
                                        device._send_event("KEYCODE_HOME")
                                        device.tap_on('wam_icon', threshold=0.85, false_is_except=True)
                                    break
                                except Exception as e3:
                                    logger.debug(e3)
                                    e3 = sys.exc_info()
                                    logger.debug(repr(traceback.extract_tb(e3[2])))

                            sleep(30)
                        continue
            exit(0)

        if self.second_par == 'spear':
            main_acc = None
            for jj in range(0, len(accs)):
                if 'main' in accs[jj]:
                    main_acc = accs[jj]
                    break
            cycle_start = 1
            while True:
                acc = accs[cycle_start]
                if not device.block_acc(main_acc):
                    continue
                device2 = self.memu.get_device(self.third_par)
                twin = Game(device2)
                if not device2.block_acc(acc):
                    continue

                # device3 = self.memu.get_device('MEmu')
                # twin2 = Game(device3)

                # try:
                #     os.remove('twins/old_block_' + device.name + '.txt')
                # except:
                #     pass

                # game.relogin_acc(main_acc)
                # game.exit_town()
                # twin.relogin_acc(acc)
                # twin.exit_town()
                # twin2.relogin_acc(acc2)
                # twin2.exit_town()

                # game.go_spear(4, True)

                # забираем у твина кости
                if game.device.tap_on('little_time_5', threshold=0.78, attempts=3):
                    twin_coors = twin.get_coors()
                    game.go_mine_low({'coors': twin_coors}, little_troops=False, permit_attack=True)

                # пересаживаем на кости твина, основой отступаем
                ret = game.get_coors()
                if not game.device.tap_on('return_hero_from_res', threshold=0.78, attempts=3):
                    print('debug me')
                # while not game.is_free_heroes(main_acc['heroes']):
                #     sleep(5)
                # # # sleep(140)
                # game.go_mine_low({'coors': ret}, False, permit_attack=True)
                # game.go_mine_low({'coors': ret2}, False, permit_attack=True)
                # # ret2 = game.get_coors()
                # sleep(2*60*60)
                twin.go_mine_low({'coors': ret}, little_troops=True)
                print('done')

                # game.go_mine_low({'coors': [721,594]}, little_troops=False, permit_attack=True)
                # twin.go_mine2(acc, 3, True)

                # while True:
                #     while not int(time.strftime("%M")) % 30 == 0:
                #         sleep(2)
                #     # for _ in range(2):
                #     twin.go_mine2(acc, 3, full_troops=False)
                #     sleep(120)
                while True:
                    if game.is_free_heroes(main_acc['heroes']):
                        while int(time.strftime("%M")) % 30 in [27, 28, 29]:
                            sleep(2)
                        if not game.go_spear(4, True):
                            if game.is_free_heroes(main_acc['heroes']):
                                if not game.go_mine2(1, True):
                                    game.monitor_acc(60 * 4)
                        if game.is_free_heroes(main_acc['heroes']):
                            continue
                        game.monitor_acc(30)
                    else:
                        logger.debug('')
                    if int(time.strftime("%M")) % 30 in [10, 11, 12, 13]:
                        game.train_army(main_acc)
                        game.exit_town()
                    else:
                        game.monitor_acc(30)
                    continue
                    # for jj in range(acc['heroes']):

                    # ret = twin.go_mine(acc)
                    # ret = twin.go_mine(acc)

                    # twin.relogin_acc(acc2)
                    # twin.exit_town()
                    # ret = twin.go_mine(acc2)
                    # ret = twin.go_mine(acc2)

                    mine_info = game.atack_mine(main_acc)
                    if mine_info['nick'] == mine_info['nick']:
                        ret = game.return_main_hero(mine_info)
                        ret = twin.return_mine(acc, mine_info)
                        ret = game.return_main_hero(mine_info)
                    ret = game.return_mine(main_acc)
                    ret = twin.go_mine(acc)

                    ret = game.atack_mine(main_acc)
                    ret = game.atack_mine(main_acc)
                    ret = game.atack_mine(main_acc)
                    logger.debug('success')
            # cycle_start = 0
            exit(0)

        if self.second_par == 'grab':
            cycle_start = 5
            try:
                cycle_start = self.index_acc
                main_acc = accs[self.index_acc_main]
                interface = True
                get_food = self.grab_get_food
                get_wood = self.grab_get_wood
                get_crystalls = self.grab_get_crystalls
                get_gems = self.grab_get_gems
                try:
                    only_step1 = self.grab_only_step1
                except:
                    only_step1 = False
                try:
                    only_step2 = self.grab_only_step2
                except:
                    only_step2 = False
                rotate = self.rotate
            except Exception as e:
                # запуск в консоли (вне интерфейса)
                interface = False
                get_food = False
                get_wood = True
                get_crystalls = True
                get_gems = False
                only_step1 = False
                only_step2 = False
                rotate = True
            if not interface:
                main_acc = None
                for jj in range(0, len(accs)):
                    if 'main' in accs[jj]:
                        main_acc = accs[jj]
                        break
            for ii in range(cycle_start, len(accs)):
                acc = accs[ii]
                # deb = game.get_load_power()
                if not interface and 'main' in acc and acc['main']:
                    logger.debug('основу пропускаем')
                    continue
                if rotate and 'main' in acc and acc['main']:
                    logger.debug('основу пропускаем')
                    continue
                if 'login_once' in acc:
                    continue
                while not device.block_acc(main_acc):
                    logger.debug('Not blocked main_acc')
                    sleep(10)
                while not device.block_acc(acc):
                    logger.debug('Not blocked acc' + str(acc))
                    sleep(10)
                logger.debug("work with acc at %s: %s" % (time.asctime(time.localtime(time.time())), str(acc)))
                game.grab_twin(acc, main_acc, get_food=get_food, get_wood=get_wood, get_crystalls=get_crystalls, get_gems=get_gems, only_step1=only_step1, only_step2=only_step2)
                if interface and not rotate:
                    break
                if not rotate:
                    break
            return True

        if self.second_par == 'fish':
            if self.interface:
                acc = {}
                logger.debug("work with acc at %s: %s" % (time.asctime(time.localtime(time.time())), str(acc)))
                game.fish(acc, self.fish_count)
                return
            else:
                cycle_start = 17
                self.fish_count = 50
                for ii in range(cycle_start, len(accs)):
                    acc = accs[ii]
                    if 'main' in acc and acc['main']:
                        continue
                    while not device.block_acc(acc):
                        logger.debug('Not blocked acc' + str(acc))
                        sleep(10)
                        # exit(0)
                    logger.debug("work with acc at %s: %s" % (time.asctime(time.localtime(time.time())), str(acc)))
                    game.relogin_acc(acc)
                    try:
                        os.remove('twins/old_block_' + device.name + '.txt')
                    except:
                        pass
                    # logger.debug("work with acc at %s: %s" % (time.asctime(time.localtime(time.time())), str(acc)))
                    game.device.tap_on('event_center', threshold=0.8, attempts=3)
                    if not game.device.tap_on('event_fish', threshold=0.8, attempts=1):
                        game.device.swipe(0, -200)
                        game.device.swipe(0, -200)
                        if not game.device.tap_on('event_fish', threshold=0.8, attempts=1):
                            logger.debug('Not found fish event')
                            continue
                    sleep(3)
                    if game.device.tap_on('fish_market', threshold=0.8, attempts=1):
                        sleep(3)
                        if not 'main' in acc:
                            game.fish_market()
                        game.back()
                    game.fish(acc, self.fish_count)
                    if not 'main' in acc:
                        game.fish_market()
            return

        if self.second_par == 'fish2':
            fn = r'twins\full_mails.txt'
            f = open(fn, 'r')
            accs2 = f.readlines()
            f.close()
            for jj in range(len(accs2)):
                acc = accs2[jj]
                if acc.find('sixth_mobs_attacked') == -1:
                    continue
                login = acc[0:acc.find(':')]
                acc = {'nick': login[0:login.find('@')], "bound": "mail", "login": login, "pas": "tremtrem"}

                # избегаем акков из главного списка акков
                acc_in_main_list = False
                for zz in range(len(accs)):
                    if 'login_once' in accs[zz]:
                        continue
                    if accs[zz]['nick'] == login:
                        acc_in_main_list = True
                        break
                if acc_in_main_list:
                    continue

                if not device.block_acc(acc):
                    print('not blocked acc for soldier_adventure2: ' + login)
                    continue
                time1 = time.time()
                try:
                    fn = 'stats/' + acc['nick'] + '.txt'
                    stat = common.get_json_from_file(fn)
                    if common.is_stat_more_dif_time(stat, 8 * 60 * 60, 'alliance') and not 'main' in acc:
                        game.relogin_acc(acc)
                        if not game.alliance(acc, don_army=False, union_shop=False, union_help=False):
                            print('debme')
                            game.alliance(acc, don_army=False, union_shop=False, union_help=False)
                        stat['alliance'] = int(time.time())
                        stat['alliance_str'] = time.asctime(time.localtime(time.time()))
                        common.save_json_to_file(stat, fn)
                except Exception as e:
                    logger.debug("Error in fish2")
                    logger.debug(ex)
                    e2 = sys.exc_info()
                    logger.debug(repr(traceback.extract_tb(e2[2])))

        if self.second_par == 'tonus':  # расходывание ТОНУСА
            try:
                index_acc = self.index_acc
                reputaion = self.tonus_rep
                tonus_statue = self.tonus_statue
                tonus_fountain = self.tonus_fountain
                tonus_around_dragon = self.tonus_around_dragon
                buy_tonus1 = self.tonus_buy1
                rotate = self.rotate
            except:
                index_acc = 1
                reputaion = 0
                tonus_statue = 0
                tonus_fountain = 0
                tonus_around_dragon = 0
                buy_tonus1 = 0
                rotate = 1
            # cycle_start = random.randint(0, len(accs) - 1)
            while True:
                for ii in range(index_acc, len(accs)):
                    acc = accs[ii]
                    # acc = accs[ii]
                    if rotate and 'main' in acc and acc['main']:
                        continue
                    if ii != index_acc and 'monster_battles' not in acc:
                        continue
                    if not device.block_acc(acc):
                        logger.debug('Not blocked acc')
                        sleep(10)
                        continue
                    fn = 'stats/' + acc['nick'] + '.txt'
                    stat = common.get_json_from_file(fn)
                    if True:
                    # if common.is_stat_more_dif_time(stat, 3 * 60 * 60, 'tonus_finished'):
                        for kk in range(10):
                            try:
                                if rotate:
                                    game.relogin_acc(acc)
                                    try:
                                        os.remove('twins/old_block_' + device.name + '.txt')
                                    except:
                                        pass

                                stats_hunter = {'attacks': 0, 'exp': 0, 'rep': 0, 'fountain': 0,
                                                'swipe_wo_attacks': 0, 'buy_tonus1': buy_tonus1}
                                if ii == index_acc:
                                    try:
                                        levels = self.tonus_level.replace(' ', '').split(',')
                                        acc['horse_step'] = int(self.horse_step)
                                    except:
                                        levels = acc['monster_battles']
                                        acc['horse_step'] = 0
                                else:
                                    levels = acc['monster_battles']
                                    acc['horse_step'] = 0

                                #  РЯД ТЕСТОВ
                                # game.search_monsters([7])
                                # power = game.get_power(permit_except=False, prep_fn=r'c:\Users\denis\Pictures\test\wam_MEmu6_20200121-200154.png')
                                # ret = game.start_battle(levels, stats_hunter, acc, test_fn=r'c:\Users\denis\Pictures\test\wam_MEmu6_20200122-072318.png')
                                # ret = game.start_battle(levels, stats_hunter, acc, test_fn=r'c:\Users\denis\Pictures\test\wam_MEmu3_20200120-075350_2.png')

                                acc['reputation'] = reputaion
                                acc['tonus_statue'] = tonus_statue
                                acc['tonus_fountain'] = tonus_fountain
                                acc['tonus_around_dragon'] = tonus_around_dragon
                                ret = game.battles(levels, stats_hunter, acc)
                                game.return_halt_hero()
                                if type(ret) == str:  # возможно просто бесплатные поиски кончились
                                    logger.debug(ret)
                                    stat['tonus_finished'] = int(time.time()); stat['tonus_result'] = ret
                                    stat['tonus_finished_str'] = time.asctime(time.localtime(time.time()))
                                    common.save_json_to_file(stat, fn)
                                break
                            except Exception as e:
                                logger.debug(str(e))
                                e = sys.exc_info()
                                logger.debug(repr(traceback.extract_tb(e[2])))
                                if not device.tap_on('retry', one_attempt=True):
                                    device.stop()
                                    device.start()
                                    sleep(12)
                                    device.wait_loaded()
                                    device._send_event("KEYCODE_HOME")
                                    device.tap_on('wam_icon', threshold=0.85, false_is_except=True)
                                    game.clear_dialogs_after_login()

                        if not 'main' in acc or not acc['main']:
                            game.upgrade_med(True)
                        # game.get_all_quests(acc)
                        # os.remove('twins/block_' + device.name + '.txt')
                    logger.debug('end one acc')
                    try:
                        os.remove('twins/block_' + device.name + '.txt')
                        os.remove('twins/old_block_' + device.name + '.txt')
                    except:
                        pass
                    if not rotate:
                        return True
                index_acc = 0

        # war_attack = [
        #     [619, 665, 'Larry'],
        #     [621, 665, 'LarryFarm'],
        #     [621, 667, 'Arkanion_ml_fermLarry'],
        #     [611, 662, 'LordSergey77'],
        #     [606, 685, 'Suffix'],
        #     [620, 638, 'Лис'],
        #     [597, 671, 'Vlad_vhole'],
        #     [626, 634, 'postrig'],
        #     [598, 661, 'alpha_pro'],
        #     [581, 672, '7links7'],
        #     [620, 643, 'supra_prime'],
        #     [606, 688, 'hatsya'],
        #     # [603, 674, 'Пупс'],
        # ]
        # index_wa = int(time.time()) % len(war_attack)


        cycle_start = random.randint(0, len(accs) - 1)
        # cycle_start = 0  # РОТАЦИЯ ТВИНОВ
        for zz in range(9999):
            logger.debug('new cycle')
            for ii in range(cycle_start, len(accs)):
                acc = accs[ii]

                hour = int(time.strftime("%H"))
                # if 'main' in acc and acc['main']:
                #     continue
                # if 'main' in acc and not (hour > 1 and hour < 11):
                #     continue  # на основе действия только ночью
                if 'main' in acc:
                    deep_def = False
                else:
                    if not self.deep_def:
                        deep_def = False
                    else:
                        if datetime.utcnow().weekday() in self.deep_def_days or datetime.now().weekday() in self.deep_def_days:
                            deep_def = True
                        else:
                            deep_def = False

                # while game.fill_empty_place():
                #     pass

                if not device.block_acc(acc):
                    continue
                try:
                    logger.debug("work with acc at %s: %s" % (time.asctime(time.localtime(time.time())), str(acc)))
                    fn = 'stats/' + acc['nick'] + '.txt'
                    stat = common.get_json_from_file(fn)
                    if 'login_once' in acc: # and acc['login_once'] and \
                            # 'last_login' in stat and stat['last_login'] == time.strftime("%Y%m%d"):
                        continue  # только раз в сутки входим на ряд акков

                    time1 = time.time()

                    # game.alliance(acc)

                    game.relogin_acc(acc)


                    # game.get_events()  # test

                    try:
                        os.remove('twins/old_block_' + device.name + '.txt')
                    except:
                        pass

                    if 'grow_sity_hall' in acc and acc['grow_sity_hall']:
                        game.upgrade_town()
                        if common.is_stat_more_dif_time(stat, 3 * 24 * 60 * 60, 'fill_empty_place'):
                            while game.fill_empty_place():
                                pass
                            stat['fill_empty_place'] = int(time.time())
                            stat['fill_empty_place_str'] = time.asctime(time.localtime(time.time()))
                            common.save_json_to_file(stat, fn)
                        if common.is_stat_more_dif_time(stat, 4 * 60 * 60, 'upgrade_res'):
                            game.upgrade_wood()
                            stat['upgrade_res'] = int(time.time())
                            stat['upgrade_res_str'] = time.asctime(time.localtime(time.time()))
                            common.save_json_to_file(stat, fn)

                    game.monitor_acc(1)

                    # использование магии для получения ресурсов
                    if common.is_stat_more_dif_time(stat, 12 * 60 * 60, 'res_mage') or \
                            ('login_once' in acc and acc['login_once']):
                        game.device.tap_on('book_mage', attempts=3, threshold=0.85)
                        game.device.tap_on('book_harvest', attempts=3, threshold=0.85)
                        if game.device.tap_on('book_use', attempts=3, threshold=0.85):
                            game.back()
                            game.back()
                            stat['res_mage'] = int(time.time())
                            stat['res_mage_str'] = time.asctime(time.localtime(time.time()))
                            common.save_json_to_file(stat, fn)
                        game.back()

                    if (not 'main' in acc or not acc['main']) and common.is_stat_more_dif_time(stat, 8 * 60 * 60, 'fish_market'):
                        game.device.tap_on('event_center', threshold=0.8, attempts=3)
                        game.move_to_img('event_fish', 5, 0, 100)
                        if game.device.tap_on('event_fish', threshold=0.8, attempts=1):
                            if game.device.tap_on('fish_market', threshold=0.8, attempts=3):
                                sleep(3)
                                if not 'main' in acc:
                                    game.fish_market()
                                fn_scr = game.device.make_screenshot()
                                shutil.copyfile(fn_scr, 'stats/fish_%s.png' % acc['nick'])
                                game.back()
                                game.back()
                                game.back()
                                stat['fish_market'] = int(time.time())
                                stat['fish_market_str'] = time.asctime(time.localtime(time.time()))
                                common.save_json_to_file(stat, fn)

                    if not deep_def and (not 'main' in acc or not acc['main']):
                        # if zz < 2:
                        game.exit_town()
                        if not 'main' in acc or not acc['main']:
                            game.device.tap_on('expand_heroes', attempts=3, threshold=0.85)
                            game.device.tap_on('hero_recall', attempts=2, threshold=0.85)  # todo: не отменять собирание руды
                            game.return_from_collecting()
                            game.device.tap_on('hero_stationed', attempts=2, threshold=0.85, dx=200)
                        mine_time = [27, 28, 29]
                        if not datetime.now().weekday() in [1,3] and int(time.strftime("%M")) % 30 in mine_time + [0, 1, 2]:
                            while int(time.strftime("%M")) % 30 in mine_time:
                                 sleep(2)
                            game.exit_town()
                            game.go_mine2(1, True)
                            logger.debug('check rude send')
                    # if not 'main' in acc and not 'noattack_enemy' in acc:
                    #     index_wa = game.attack_enemy(index_wa, acc, war_attack)
                    #     game.device.tap_on('mail', threshold=0.78, attempts=2)
                    #     sleep(4)
                    #     fn = game.device.make_screenshot()
                    #     shutil.copyfile(fn, 'stats/army_attack_%s_%s.png' % (acc['nick'], datetime.now().strftime("%Y%m%d-%H%M%S")))
                    #     game.back()

                    try:
                        os.remove('twins/old_block_' + device.name + '.txt')
                    except:
                        pass
                    time2 = time.time() - time1

                    # if 'attack' in acc or acc['attack']:
                    # if not 'notgrow' in acc or not acc['notgrow']:
                    #     game.grow_acc2()
                    if 'grow_stables' in acc and acc['grow_stables']:
                        game.upgrade_stables()
                    if 'grow_res' in acc and acc['grow_res'] and not game.upgrade_wood():
                        logger.debug('not upgrade_wood')
                    if not device.wait_for(('hammer', 'hammer2'), attempts=2, threshold=0.72)[0]:
                        logger.debug('no build process now !!!')
                    if common.is_stat_more_dif_time(stat, 3 * 60 * 60, 'alliance'):
                        game.alliance(acc)
                        stat['alliance'] = int(time.time())
                        stat['alliance_str'] = time.asctime(time.localtime(time.time()))
                        common.save_json_to_file(stat, fn)

                    if (common.is_stat_more_dif_time(stat, 18 * 60 * 60, 'ellary') and (hour >= 21 or hour < 3)) or \
                            ('login_once' in acc and acc['login_once']):
                        game.ellary()
                        stat['ellary'] = int(time.time())
                        stat['ellary_str'] = time.asctime(time.localtime(time.time()))
                        common.save_json_to_file(stat, fn)

                    # if 'upgrade_med' in acc and acc['upgrade_med']:
                    # game.arena(acc)
                    if common.is_stat_more_dif_time(stat, 2 * 60 * 60, 'get_events') and not 'main' in acc:
                        game.get_all_quests(acc)
                        game.get_events()
                        if (not 'main' in acc or not acc['main']) and (not 'nomed_upgrade' in acc or not acc['nomed_upgrade']):
                            game.upgrade_med()
                        stat['get_events'] = int(time.time())
                        stat['get_events_str'] = time.asctime(time.localtime(time.time()))
                        common.save_json_to_file(stat, fn)

                    get_portal = False
                    if common.is_stat_more_dif_time(stat, 12 * 60 * 60, 'portal') or \
                            ('login_once' in acc and acc['login_once']):
                        get_portal = True

                    get_treasure = False  # заглядываем в тайник раз в 8 часов
                    if ('main' in acc and acc['main']) or common.is_stat_more_dif_time(stat, 8 * 60 * 60, 'treasure') or \
                            ('login_once' in acc and acc['login_once']):
                        get_treasure = True
                        stat['treasure'] = int(time.time())
                        stat['treasure_str'] = time.asctime(time.localtime(time.time()))
                        common.save_json_to_file(stat, fn)

                    girls = False  # девушек посещаем 4 раза в сутки
                    if common.is_stat_more_dif_time(stat, 6 * 60 * 60, 'girls') or \
                            ('login_once' in acc and acc['login_once']):
                        girls = True
                        stat['girls'] = int(time.time())
                        stat['girls_str'] = time.asctime(time.localtime(time.time()))
                        common.save_json_to_file(stat, fn)

                    game.back()
                    if 'train' in acc:
                        game.input_town()
                        add_symb = {'1_2': '1'}
                        pow = game.get_numbers('', 'face_all', 'toppower_ciph_', cropx1=34, add_symb=add_symb, cropx2=110, ciph_distance=6, threshold=0.92, permit_except=False)
                        if pow == -1:
                            sleep(3) # возможно красный фон не дал нормально считать цифры, просто ждем 3 секунды, чтобы этот фон ушел
                            pow = game.get_numbers('', 'face_all', 'toppower_ciph_', cropx1=34, add_symb=add_symb,
                                                   cropx2=110, ciph_distance=6, threshold=0.92, permit_except=False)
                        if pow < 20000:
                            print('debme')
                        if pow > self.train_power or pow == -1:
                            acc.pop('train')
                    game.train_army(acc, get_portal, get_treasure, girls)
                    if get_portal:
                        stat['portal'] = int(time.time())
                        stat['portal_str'] = time.asctime(time.localtime(time.time()))
                        common.save_json_to_file(stat, fn)
                    if hour > 2 and hour < 6:
                        if not 'main' in acc or not acc['main']:
                            game.get_system_mail()
                    time5 = time.time()
                    if deep_def:
                        game.hide_hero(acc)
                        game.rehide_hero(acc, stat, fn)
                    else:
                        game.send_heroes(acc)
                        time6 = time.time()
                        logger.debug("durance get_harvest = %d seconds" % int(time6 - time5))

                    if int(time.strftime("%H")) % 2 == 0:
                        if not 'main' in acc or not acc['main']:
                            game.upgrade_med(True)
                    stat['last_login'] = time.strftime("%Y%m%d")
                    common.save_json_to_file(stat, fn)
                    game.save_stat(acc, stat)
                    # для ивентов, где нужна смена альянса
                    # game.alliance_trans(acc)
                    # game.exit_town()
                    # game.go_coors([639, 676])
                    game.monitor_acc(1)
                    logger.debug('go to next acc, full time = %d seconds' % int(time.time() - time1))
                except Exception as ex:
                    for zz in range(10):
                        if zz == 9:
                            raise Exception('error of restart activity')
                        try:
                            logger.debug("Error in twin rotation")
                            logger.debug(ex)
                            e2 = sys.exc_info()
                            logger.debug(repr(traceback.extract_tb(e2[2])))
                            device = self.memu.get_device(self.memu_name)
                            if not device.tap_on('retry', one_attempt=True):
                                game.collect()
                                if not 'notgrow' in acc:
                                    game.grow_acc(5)
                                device.stop()
                                device.start()
                                sleep(12)
                                device.wait_loaded()
                                device._send_event("KEYCODE_HOME")
                                device.tap_on('wam_icon', threshold=0.85, false_is_except=True)
                            break
                        except Exception as e3:
                            logger.debug(e3)
                            e3 = sys.exc_info()
                            logger.debug(repr(traceback.extract_tb(e3[2])))

                    sleep(30)
            cycle_start = 0

    def restart_executor(self):
        if self.executor:
            for pid in self.executor._processes.keys():
                os.system(f'Taskkill /PID {pid} /F')
            self.executor.shutdown(True)
        self.executor = ProcessPoolExecutor(max_workers=1)

    def run(self):

        self.my_ip = get_external_ip()
        self.restart_executor()
        # self.nox = NoxController()
        self.memu = MemuController()
        self.work()
