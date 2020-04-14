import logging
import os
import sys
import subprocess
import shutil
import time
import traceback

from libs import main_process
import libs.common as common

logger = logging.getLogger(__name__)

ABSOLUTE_PATH = lambda x: os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), x))
os.chdir(os.path.abspath(os.path.dirname(__file__)))

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QThread, pyqtSignal
import design  # конвертированный файл дизайна

class twinRotation(QThread):
    def run(self):
        # self.calc.countChanged.connect(self.onCountChanged)
        self.wam_process.run()

class BotApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.checkBoxTrain.clicked.connect(self.update_checkBox_signals)

        self.buttonStartRotation.clicked.connect(self.twin_rotation)
        self.buttonStopRotation.clicked.connect(self.stop_rotation)
        self.buttonStartTonus.clicked.connect(self.start_tonus)
        self.buttonStopTonus.clicked.connect(self.stop_tonus)
        self.buttonStartGrab.clicked.connect(self.start_grab)
        self.buttonGrabStep1.clicked.connect(self.start_grab_step1)
        self.buttonGrabStep2.clicked.connect(self.start_grab_step2)
        self.buttonStopGrab.clicked.connect(self.stop_grab)
        self.buttonStartMine.clicked.connect(self.start_mine)
        self.buttonStopMine.clicked.connect(self.stop_mine)
        self.buttonStartFish.clicked.connect(self.event_fish)
        self.buttonStopFish.clicked.connect(self.event_fish_stop)
        # ищем файл настроек аккаунтов, если не найдем, берем копию из примера
        if not os.path.isfile('accs.txt'):
            try:
                shutil.copyfile('accs_example.txt', 'accs.txt')
            except Exception as e:
                print(str(e))

        self.buttonTest.clicked.connect(self.button_test)
        self.buttonMakeScreen.clicked.connect(self.make_screenshot)
        self.buttonOpenLog.clicked.connect(self.open_log)
        self.buttonEditAccs.clicked.connect(self.edit_accs)
        emul_name = sys.argv[1] if len(sys.argv) > 1 else 'MEmu'
        second_par = sys.argv[2] if len(sys.argv) > 2 else None
        third_par = sys.argv[3] if len(sys.argv) > 3 else None
        self.wam_process = main_process.WAMWorker(memu_name=emul_name.strip(), second_par=second_par, third_par=third_par)
        self.twinrot = twinRotation()
        self.twinrot.wam_process = self.wam_process

        self.tabWidget.setCurrentIndex(0)
        common.load_accs(self.comboboxTonusAcc)
        common.load_accs(self.comboboxGrabAccFrom)
        common.load_accs(self.comboboxGrabAccTo, set_main=True)
        self.accs = common.load_accs(self.comboboxMineAcc)
        self.on_combobox_tonus_acc_changed()
        self.comboboxTonusAcc.currentTextChanged.connect(self.on_combobox_tonus_acc_changed)

    def change_log_fn(self, fn):
        fileh = logging.FileHandler(fn, 'a')
        formatter = logging.Formatter('%(name)12s - %(levelname)12s: %(message)s')
        fileh.setFormatter(formatter)
        log = logging.getLogger()
        for hdlr in log.handlers[:]:
            log.removeHandler(hdlr)
        log.addHandler(fileh)
        logging.getLogger().addHandler(logging.StreamHandler())

    def twin_rotation(self):
        self.twinrot.wam_process.second_par = ''
        self.twinrot.wam_process.memu_name = self.editEmul.text().strip()
        self.twinrot.wam_process.train = self.checkBoxTrain.isChecked()
        self.twinrot.wam_process.train_power = int(self.editTrainPower.text().strip())
        self.twinrot.wam_process.deep_def = self.checkDeepDef.isChecked()
        self.change_log_fn(self.twinrot.wam_process.memu_name + time.strftime("_%Y%m%d") + '.log')
        try:
            self.twinrot.wam_process.deep_def_days = self.editDeepDef.text().strip().replace(' ', '').split(',')
            for ii in range(len(self.twinrot.wam_process.deep_def_days)):
                self.twinrot.wam_process.deep_def_days[ii] = int(self.twinrot.wam_process.deep_def_days[ii]) - 1
        except Exception as e:
            print(e)
            self.twinrot.wam_process.deep_def_days = []
        self.buttonStartRotation.setEnabled(False)
        self.buttonStopRotation.setEnabled(True)
        self.twinrot.start()

    def stop_rotation(self):
        self.buttonStopRotation.setEnabled(False)
        self.buttonStartRotation.setEnabled(True)
        self.twinrot.terminate()
        logger.debug(f'TWIN ROTATION STOPPED')

    def start_tonus(self):
        try:
            self.twinrot.wam_process.second_par = 'tonus'
            self.twinrot.wam_process.index_acc = self.comboboxTonusAcc.currentIndex()
            self.twinrot.wam_process.memu_name = self.editEmulTonus.text().strip()
            self.twinrot.wam_process.tonus_level = self.editTonusLevel.text().strip()
            self.twinrot.wam_process.horse_step = self.editTonusHorseStep.text().strip()
            self.twinrot.wam_process.rotate = self.checkBoxTonusLoginAndRotate.isChecked()
            self.twinrot.wam_process.tonus_around_dragon = self.checkBoxTonusAroundDragon.isChecked()
            self.twinrot.wam_process.tonus_rep = self.checkBoxTonusReputation.isChecked()
            self.twinrot.wam_process.tonus_statue = self.checkBoxTonusStatue.isChecked()
            self.twinrot.wam_process.tonus_fountain = self.checkBoxTonusFountain.isChecked()
            self.twinrot.wam_process.tonus_buy1 = int(self.editTonusBuy1.text().strip())
            self.change_log_fn(self.twinrot.wam_process.memu_name + time.strftime("_%Y%m%d") + '.log')
            self.buttonStartTonus.setEnabled(False)
            self.buttonStopTonus.setEnabled(True)
            self.twinrot.start()
        except Exception as e:
            common.message_box('Ошибка: ' + str(e))
            e2 = sys.exc_info()
            common.message_box(repr(traceback.extract_tb(e2[2])))

    def start_grab_step1(self):
        self.twinrot.wam_process.grab_only_step1 = True
        self.start_grab()

    def start_grab_step2(self):
        self.twinrot.wam_process.grab_only_step2 = True
        self.start_grab()

    def start_grab(self):
        try:
            self.twinrot.wam_process.second_par = 'grab'
            self.twinrot.wam_process.memu_name = self.editEmulGrab.text().strip()
            self.twinrot.wam_process.index_acc = self.comboboxGrabAccFrom.currentIndex()
            self.twinrot.wam_process.rotate = self.checkBoxGrabLoginAndRotate.isChecked()
            self.twinrot.wam_process.index_acc_main = self.comboboxGrabAccTo.currentIndex()
            self.twinrot.wam_process.grab_get_food = self.checkBoxGrabFood.isChecked()
            self.twinrot.wam_process.grab_get_wood = self.checkBoxGrabWood.isChecked()
            self.twinrot.wam_process.grab_get_crystalls = self.checkBoxGrabBlueCrystalls.isChecked()
            self.twinrot.wam_process.grab_get_gems = self.checkBoxGrabRedGems.isChecked()
            self.change_log_fn(self.twinrot.wam_process.memu_name + time.strftime("_%Y%m%d") + '.log')
            self.buttonStartGrab.setEnabled(False)
            self.buttonGrabStep1.setEnabled(False)
            self.buttonGrabStep2.setEnabled(False)
            self.buttonStopGrab.setEnabled(True)
            self.twinrot.start()
        except Exception as e:
            common.message_box('Ошибка: ' + str(e))
            e2 = sys.exc_info()
            common.message_box(repr(traceback.extract_tb(e2[2])))

    def stop_grab(self):
        self.buttonStopGrab.setEnabled(False)
        self.buttonStartGrab.setEnabled(True)
        self.buttonGrabStep1.setEnabled(True)
        self.buttonGrabStep2.setEnabled(True)
        self.twinrot.terminate()
        self.twinrot.wam_process.grab_only_step1 = False
        self.twinrot.wam_process.grab_only_step2 = False
        logger.debug(f'Stoling FARM STOPPED')

    def stop_tonus(self):
        self.buttonStopTonus.setEnabled(False)
        self.buttonStartTonus.setEnabled(True)
        self.twinrot.terminate()
        logger.debug(f'MONSTERS FARM STOPPED')

    def start_mine(self):
        self.twinrot.wam_process.second_par = 'mine'
        self.twinrot.wam_process.index_acc = self.comboboxMineAcc.currentIndex()
        self.twinrot.wam_process.memu_name = self.editEmulMine.text().strip()
        self.twinrot.wam_process.order_mine = self.editMineLevel.text().strip()
        self.twinrot.wam_process.mine_time = int(self.editMineTime.text().strip())
        self.twinrot.wam_process.mine_rot = self.checkBoxMineRotation.isChecked()
        self.twinrot.wam_process.mine_login = self.checkBoxMineLogin.isChecked()
        self.change_log_fn(self.twinrot.wam_process.memu_name + time.strftime("_%Y%m%d") + '.log')
        self.buttonStartMine.setEnabled(False)
        self.buttonStopMine.setEnabled(True)
        self.twinrot.start()
    def stop_mine(self):
        self.buttonStopMine.setEnabled(False)
        self.buttonStartMine.setEnabled(True)
        self.twinrot.terminate()
        logger.debug(f'MINE COLLECTION STOPPED')

    def event_fish(self):
        self.twinrot.wam_process.second_par = 'fish'
        self.twinrot.wam_process.memu_name = self.editEmulFish.text().strip()
        self.twinrot.wam_process.fish_count = int(self.editFishCount.text().strip())
        self.twinrot.wam_process.interface = True
        self.change_log_fn(self.twinrot.wam_process.memu_name + time.strftime("_%Y%m%d") + '.log')
        self.buttonStartFish.setEnabled(False)
        self.buttonStopFish.setEnabled(True)
        self.twinrot.start()

    def event_fish_stop(self):
        self.buttonStopFish.setEnabled(False)
        self.buttonStartFish.setEnabled(True)
        self.twinrot.terminate()
        logger.debug(f'Stop fish')

    def make_screenshot(self):
        self.twinrot.wam_process.second_par = 'screen'
        self.twinrot.wam_process.memu_name = self.editEmul_2.text()
        self.change_log_fn(self.twinrot.wam_process.memu_name + time.strftime("_%Y%m%d") + '.log')
        self.twinrot.start()

    def button_test(self):
        try:
            self.twinrot.wam_process.second_par = 'test'
            self.twinrot.wam_process.res_test = 1
            self.twinrot.wam_process.memu_name = self.editEmul_2.text()
            self.change_log_fn(self.twinrot.wam_process.memu_name + time.strftime("_%Y%m%d") + '.log')
            self.twinrot.start()
            time.sleep(1)
            while self.twinrot.wam_process.res_test == 1:
                time.sleep(1)

            if self.twinrot.wam_process.res_test == 2:
                common.message_box('Тест пройден успешно')
            else:
                common.message_box('Тест НЕ пройден. Проверьте настройки')
                self.twinrot.wam_process.memu_name = self.editEmul_2.text()
                subprocess.Popen('notepad "' + self.twinrot.wam_process.memu_name + time.strftime("_%Y%m%d") + '.log"')
        except Exception as e:
            common.message_box('Ошибка: ' + str(e))
            e2 = sys.exc_info()
            common.message_box(repr(traceback.extract_tb(e2[2])))

    def edit_accs(self):
        if os.path.isfile('accs.txt'):
            subprocess.Popen('notepad "accs.txt"')
        else:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            # msg.setIconPixmap(pixmap)  # Своя картинка

            msg.setWindowTitle("Информация")
            msg.setText('Не найден файл accs.txt или accs_example.txt. Попробуйте переустановить WamyBoty')
            msg.setInformativeText("Current path = " + os.getcwd())
            # msg.setDetailedText("DetailedText")

            okButton = msg.addButton('Ok', QtWidgets.QMessageBox.AcceptRole)
            # msg.addButton('Отмена', QtWidgets.QMessageBox.RejectRole)

            msg.exec()
            # if msg.clickedButton() == okButton:
            #     print("Yes")
            # else:
            #     print("No")

    def open_log(self):
        self.twinrot.wam_process.memu_name = self.editEmul_2.text()
        subprocess.Popen('notepad "' + self.twinrot.wam_process.memu_name + time.strftime("_%Y%m%d") + '.log"')

    def on_combobox_tonus_acc_changed(self):
        try:
            levels = str(self.accs[self.comboboxTonusAcc.currentIndex()]['monster_battles'])
            levels = levels.strip('[').strip(']')
            self.editTonusLevel.setText(levels)
        except Exception as e:
            self.editTonusLevel.setText('23')

    def update_checkBox_signals(self):
        self.twinrot.wam_process.train = self.checkBoxTrain.isChecked()
        self.twinrot.wam_process.train = int(self.editTrainPower.text().strip())

def main():
    emul_name = sys.argv[1] if len(sys.argv) > 1 else 'MEmu'
    second_par = sys.argv[2] if len(sys.argv) > 2 else None
    third_par = sys.argv[3] if len(sys.argv) > 3 else None
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(name)12s - %(levelname)12s: %(message)s',
        # stream=sys.stderr,
        filename=emul_name.strip() + time.strftime("_%Y%m%d") + '.log'
    )
    logging.getLogger().addHandler(logging.StreamHandler())

    if second_par == 'interface' or len(sys.argv) < 2:
        app = QtWidgets.QApplication(sys.argv)
        window = BotApp()
        window.show()
        app.exec_()
    else:
        c = main_process.WAMWorker(memu_name=emul_name.strip(), second_par=second_par, third_par=third_par)
        c.run()

if __name__ == '__main__':
    main()
    sys.exit()
