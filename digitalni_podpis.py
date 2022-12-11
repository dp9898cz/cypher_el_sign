import sys
import hashlib
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox, QFileDialog)
from PyQt5 import QtGui, uic
from PyQt5 import QtWidgets
from sympy import randprime, totient
from math import gcd
from random import randint
import base64
from zipfile import ZipFile
import os
from shutil import copy2, SameFileError
import time
import datetime
from pathlib import Path



class TooManyFiles(Exception):
    pass


qtCreatorFile = "gui.ui"  # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class MyApp(QMainWindow, Ui_MainWindow):


    def generate_key(self):

        p = randprime(10 ** 19, 10 ** 20 - 1)
        q = randprime(10 ** 19, 10 ** 20 - 1)
        while q == p:
            q = randprime(10 ** 19, 10 ** 20 - 1)

        n = p * q

        euler = (p - 1) * (q - 1)

        e = randint(1, euler)
        while gcd(e, euler) != 1:
            e = randint(1, euler)

        d = pow(e, -1, euler)

        n_d_e = []
        n_d_e.append(str(n))
        n_d_e.append(str(d))
        n_d_e.append(str(e))
        return n_d_e

    def check_for_empty_input(self, my_text, msg):
        if my_text == [''] or my_text == '':
            self.error_message(msg)
            return -1

    def encrypt(self, my_text, n, d):
        my_text = self.split_into_list(my_text)
        i = 0
        for item in my_text:
            my_text[i] = pow(item, int(d), int(n))
            i += 1
        return my_text

    def decrypt(self, my_text, n, e):
        i = 0
        for item in my_text:
            my_text[i] = pow(int(item), int(e), int(n))
            i += 1
        return my_text

    def split_into_list(self, my_text):
        temp = []
        encrypted_list = []
        encrypted_segment = ''
        i = 0
        for character in my_text:
            if i == 5:
                for item in temp:
                    encrypted_segment += item
                encrypted_list.append(int(encrypted_segment, 2))
                encrypted_segment = ''
                temp = []
                i = 0
            temp.append(bin(ord(character))[2:].zfill(10))
            i += 1
        if temp:
            for item in temp:
                encrypted_segment += item
            encrypted_list.append(int(encrypted_segment, 2))

        return encrypted_list

    def encodeButton_clicked(self, my_text, n, d):
        try:
            my_text = self.encrypt(my_text, n, d)
            finished_text = ''
            for item in my_text:
                finished_text += str(item) + ' '
            finished_text = finished_text.rstrip()
            return finished_text
        except ValueError:
            self.error_message('Nastala nějaká chyba :(')

    def decode_transformation(self, my_text):
        decoded_text = ''
        i = 0
        for item in my_text:
            my_text[i] = bin(int(item))[2:].zfill(50)
            i += 1
        temp = []
        for item in my_text:
            temp = [item[i:i + 10] for i in range(0, len(item), 10)]
            i = 0
            for item in temp:
                temp[i] = chr(int(item, 2))
                i += 1
            for item in temp:
                decoded_text += str(item)
        return decoded_text

    def decodeButton_clicked(self, my_text, n, e):
        try:
            my_text = my_text.split(' ')
            my_text = self.decrypt(my_text, n, e)
            my_text = self.decode_transformation(my_text)
            return my_text
        except ValueError:
            self.error_message('Nastala nějaká chyba :(')

    def get_hash(self, file):
        BLOCK_SIZE = 65536
        file_hash = hashlib.sha3_512()
        with open(file, 'rb') as f:
            fb = f.read(BLOCK_SIZE)
            while len(fb) > 0:
                file_hash.update(fb)
                fb = f.read(BLOCK_SIZE)
        return (file_hash.hexdigest())

    # vyber souboru
    def openFileNameDialog(self):
        fileName = QFileDialog.getOpenFileName()
        if fileName:
            return fileName[0]

    def get_program_path(self):
        head, tail = os.path.split(__file__)
        return head

    # cesta souboru pro podpis
    def chooseFileButton_clicked(self):
        file = self.openFileNameDialog()
        self.filePath.setText(file)

    # cesta slozky pro zip
    def chooseDirectoryButton_clicked(self):
        file = self.openDirectoryNameDialog()
        self.DirectoryPath.setText(file)

    # cesta pro klic
    def chooseKeyFileButton_clicked(self):
        file = self.openFileNameDialog()
        self.keyPath.setText(file)

    def copy_file(self, file):
        try:
            program_path = self.get_program_path()
            copy2(file, program_path)
        except SameFileError:
            pass

    def generateKeyFilesButton_clicked(self):
        try:
            n_d_e = self.generate_key()
            n = n_d_e[0]
            d = n_d_e[1]
            e = n_d_e[2]

            with open('PrivateKey.priv', 'w') as f:
                f.write(n + '\n')
                f.write(d)
            with open('PublicKey.pub', 'w') as f:
                f.write(n + '\n')
                f.write(e)
            self.message('Okno', 'Soubory s klíči se úspěšně uložily do složky s tvým kódem.')
        except:
            self.message('Okno', 'Nastala nějaká chyba :(')

    def sign_file(self):
        # vytvořit hash ze souboru
        file_path = self.filePath.text()
        if len(file_path):
            hashcode = self.get_hash(file_path)
        else:
            return self.message('Chyba', 'Nebyl vybrán žádný soubor k podepsání.')
        
        # vzít klice ze souboru
        try:
            key_file = self.keyPath.text()
            n_d = []
            with open(key_file) as f:  # brani klicu ze souboru
                for line in f:
                    n_d.append(line)
            n = n_d[0].rstrip()
            d = n_d[1]
        except FileNotFoundError as e:
            print(e)
            self.message('Chyba', 'Soubor s klíči není vybrát nebo neexistuje!')
            

        # encode hashe pomoci RSA
        hashcode = self.encodeButton_clicked(hashcode, n, d)
        hashcode = base64.b64encode(bytes(hashcode, "utf-8"))
        head, tail = os.path.split(file_path)
        
        with open('podpis.sign', 'wb+') as f:
            f.write(hashcode)
            
        # vytvoreni zipu
        zip_obj = ZipFile('podpis.zip', 'w')
        zip_obj.write('podpis.sign')
        zip_obj.write(file_path, arcname=tail)
        zip_obj.close()

        os.remove('podpis.sign')

        # get file stats
        size = str(os.path.getsize(file_path))
        date = os.path.getmtime(file_path)
        date2 = time.ctime(date)
        #date3 = time.strptime(date2) #todo odkomentovat, na linuxu nefunnguje
        #finalDate = str(time.strftime("%Y-%m-%d %H:%M:%S", date3)) #todo odkomentovat, na linuxu nefunnguje
        file_name = os.path.basename(file_path)
        nameSuffix = str(os.path.splitext(file_name))

        self.Name_suffix.setText(nameSuffix)
        #self.Date.setText(finalDate) #todo odkomentovat, na linuxu nefunguje
        self.File_size.setText(size)

        self.message('Úspěch', 'Potřebné soubory byly úspěšně vloženy do podpis.zip')

    def verify_file(self):
        # vzit klice ze souboru
        key_file = "PublicKey.pub"
        n_e = []
        try:
            with open(key_file) as f:  # brani klicu ze souboru
                for line in f:
                    n_e.append(line)
            n = n_e[0].rstrip()
            e = n_e[1]
        except FileNotFoundError as e:
            print(e)
            self.message('Chyba', 'Soubor s public key neexistuje!')
        
        # zjisti co je co v zipu
        try:
            zip_file = self.filePath.text()
            with ZipFile('podpis.zip', 'r') as my_zip:
                zip_files = my_zip.namelist()
        except Exception as e:
            print(e)
            self.message('Chyba', 'Nastala chyba při práci s zip souborem!')

        # kontrola zipu
        if len(zip_files) > 2:
            return self.message('Chyba', 'Too many files!')


        signature = zip_files.index('podpis.sign')
        signature = zip_files.pop(signature)
        file = zip_files.pop(0)
        
        try:
            with ZipFile('podpis.zip', 'r') as my_zip:
                hashcode = my_zip.read(signature)
                my_zip.extract(file)
        except Exception as e:
            print(e)
            self.message('Chyba', 'Nastala chyba při práci s zip souborem!')
        
        new_hashcode = self.get_hash(file)
        hashcode = base64.b64decode(hashcode)
        hashcode = self.decodeButton_clicked(hashcode.decode("utf-8"), n, e)
        hashcode = hashcode.replace('\x00', '')
        if hashcode == new_hashcode:
            self.message('Okno', 'Úspěch! Hash je stejný.')
        else:
            self.message('Okno', 'Smůla, hash je jiný. ')


    def message(self, title, message):
        error_message = QMessageBox()
        error_message.setText(message)
        error_message.setWindowTitle(title)
        error_message.exec()

    # def help(self):
    #     error_message = QMessageBox()
    #     error_message.setText('Do prvního políčka nejprve vložíš soubor k podepsání,\n'
    #                           'do pole s klíčem vložíš soukromý klíč. A podepíšeš.\n'
    #                           '\n'
    #                           'Po podepsání do prvního pole vložíš zip soubor k ověření,\n'
    #                           'a do pole s klíčem dáš veřejný klíč. A ověříš.\n'
    #                           '\n'
    #                           'Ez as that')
    #     error_message.setWindowTitle('Chceš pomoct?')
    #     error_message.exec()

    # def signRadio_clicked(self):
    #     print()
    #
    # def verificationRadio_clicked(self):
    #     print()


    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.chooseFileButton.clicked.connect(self.chooseFileButton_clicked)
        self.chooseKeyFileButton.clicked.connect(self.chooseKeyFileButton_clicked)
        self.generateKeyFilesButton.clicked.connect(self.generateKeyFilesButton_clicked)
        self.signButton.clicked.connect(self.sign_file)
        #self.signRadio.clicked.connect(self.signRadio_clicked)
        #self.verificationRadio.clicked.connect(self.verificationRadio_clicked)
        self.verifyButton.clicked.connect(self.verify_file)
        #self.Help.clicked.connect(self.help)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())