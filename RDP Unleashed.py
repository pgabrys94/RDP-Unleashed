from datetime import datetime as dt
from cryptography.fernet import Fernet
import paramiko
import os
import json
import subprocess


name = "RDP Unleashed"
version = 1.0
author = "PG"


class Terminal:
    def __init__(self, ip, p, user, pwd):
        """
        :param ip: String
        :param p: Integer
        :param user: String
        :param pwd: String
        :return:
        """
        self.ip = ip
        self.p = p
        self.user = user
        self.pwd = pwd
        self.file = os.path.join(os.getcwd(), "termsrv.dll")
        self.remotepath = os.path.join("C:\\windows\\system32", "termsrv.dll")
        self.temppath = os.path.join("C:\\", "termsrv.dll")
        self.terminal = paramiko.SSHClient()
        self.rdp_off = "net stop umrdpservice && net stop termservice"
        self.rdp_on = "net start termservice"

    def connect(self):
        try:
            self.terminal.set_missing_host_key_policy(paramiko.AutoAddPolicy)
            self.terminal.connect(self.ip, port=self.p, username=self.user, password=self.pwd)
            print("Połączono")
        except Exception as err:
            print("Błąd połączenia: {}".format(err))

    def run(self, command):
        try:
            self.terminal.exec_command(command)
        except Exception as err:
            print("Błąd polecenia: {}".format(err))
        else:
            print("{}: SUKCES".format(command.replace("\n", "")))

    def upload(self, file):
        try:
            sftp = self.terminal.open_sftp()
            sftp.put(file, self.temppath)
            sftp.close()
            self.run('del "{}"'.format(self.remotepath))
            self.run('copy "{}" "{}"'.format(self.temppath, self.remotepath))
            self.run('del "{}"'.format(self.temppath))
        except Exception as err:
            print("Błąd wysyłania: {}".format(err))

    def download(self, file, target_name):
        try:
            sftp = self.terminal.open_sftp()
            sftp.get(file, os.path.join(os.getcwd(), target_name))
            sftp.close()
            print("Pobrano termsrv.dll")
        except Exception as err:
            print("Błąd pobierania: {}".format(err))

    def backup(self):
        try:
            sftp = self.terminal.open_sftp()
            file = os.path.join(os.getcwd(), "backup", "{}-{:%H%M%S}"
                                .format(dt.now().date(), dt.now().time()), "termsrv.dll")
            os.makedirs(os.path.dirname(file), exist_ok=True)
            sftp.get(self.remotepath, file)
            sftp.close()
            print("Utworzono kopię zapasową.")
        except Exception as err:
            print("Błąd pobierania: {}".format(err))

    def close(self):
        self.terminal.close()


class Settings:
    def __init__(self):
        self.ip = None
        self.port = None
        self.user = None
        self.pwd = None
        self.settings = None
        self.template = {"host": self.ip, "port": self.port, "username": self.user, "password": self.pwd}
        self.__secret = os.path.join(os.path.expanduser("~"), ".rdpu.key")

    def __call__(self):
        return {"IP": self.ip, "port": self.port, "username": self.user, "password": self.pwd}

    @property
    def host(self):
        return self.ip

    @host.setter
    def host(self, value):
        self.ip = value

    @property
    def target_port(self):
        return self.port

    @target_port.setter
    def target_port(self, value):
        self.port = value

    @property
    def username(self):
        return self.user

    @username.setter
    def username(self, value):
        self.user = value

    @property
    def password(self):
        if os.path.exists(self.__secret):
            with open(self.__secret, "r") as f:
                key = bytes.fromhex(f.read())
            return Fernet(key).decrypt(bytes.fromhex(self.pwd)).decode()
        else:
            return None

    @password.setter
    def password(self, value):
        with open(self.__secret, "w") as f:
            key = Fernet.generate_key()
            f.write(key.hex())
        self.pwd = Fernet(key).encrypt(value.encode()).hex()

    def read(self, file=os.path.join(os.getcwd(), "config.json")):
        try:
            with open(file, "r") as f:
                self.settings = json.load(f)
                if len(self.settings.keys()) < len(self.template.keys()):
                    json.dump(self.template, f, indent=4)
                else:
                    self.ip = self.settings["host"]
                    self.port = self.settings["port"]
                    self.user = self.settings["username"]
                    self.pwd = self.settings["password"]
        except Exception:
            print("{}Błędna składnia pliku config.json, odtwarzanie za pomocą szablonu...{}".format(yellow, reset))
            with open(file, "w") as f:
                json.dump(self.template, f, indent=4)

    def write(self, file="config.json"):
        with open(file, "r+") as f:
            sett = json.load(f)
            sett["host"] = self.ip
            sett["port"] = self.port
            sett["username"] = self.user
            sett["password"] = self.pwd
            f.seek(0)
            json.dump(sett, f, indent=4)
            f.truncate()


def check_payload():
    if os.path.exists(os.path.join(os.getcwd(), "termsrv.dll")):
        return True
    else:
        return False


def check_backup(param="check"):
    backups_dir = os.path.join(os.getcwd(), "backup")
    fresh_backup = None
    try:
        if os.path.exists(backups_dir):
            for directory in os.listdir(backups_dir):
                for file in os.listdir(os.path.join(backups_dir, directory)):
                    backup_file = os.path.join(backups_dir, directory, file)
                    if fresh_backup is None:
                        fresh_backup = backup_file
                    elif os.path.getctime(backup_file) > os.path.getctime(fresh_backup):
                        fresh_backup = backup_file
            if param == "check":
                return True
            elif param == "get_file":
                return fresh_backup
            else:
                raise Exception("Unknown argument '{}'".format(param))
        else:
            raise Exception("Backup directory is non existent")
    except Exception:
        return False


def check_target():
    try:
        for setting in list(settings()):
            if settings()[setting] is None:
                raise Exception("Value is None: '{}'".format(setting))
        if not settings.port.isdigit():
            raise Exception("Port number is incorrect: '{}'".format(settings.port))
        elif not settings.ip.replace(".", "").isdigit():
            raise Exception("Ip address is incorrect: '{}'".format(settings.ip))
    except Exception:
        return False
    else:
        return True


def execute():
    if check_target() and check_payload():
        try:
            connection = Terminal(settings.host, settings.target_port, settings.username, settings.password)
            print("Łączenie...")
            connection.connect()
            print("Zatrzymywanie usługi pulpitu zdalnego...")
            connection.run(connection.rdp_off)
            print("Tworzenie kopii zapasowej oryginalnego pliku...")
            connection.backup()
            print("Wysyłanie pliku: {}...".format(connection.file))
            connection.upload(connection.file)
            print("Uruchamianie usługi pulpitu zdalnego...")
            connection.run(connection.rdp_on)
            print("Zamykanie połaczenia...")
            connection.close()
            print("Gotowe.")
        except Exception as err:
            print("Błąd: {}".format(err))


def get_payload():
    if check_target():
        try:
            connection = Terminal(settings.host, settings.target_port, settings.username, settings.password)
            print("Łączenie...")
            connection.connect()
            print("Pobieranie oryginalnego pliku...")
            connection.download(connection.remotepath, "termsrv.dll")
            print("Zamykanie połączenia...")
            connection.close()
            print("Gotowe.")
        except Exception as err:
            print("Błąd: {}".format(err))


def restore():
    if check_target() and check_backup():
        try:
            connection = Terminal(settings.host, settings.target_port, settings.username, settings.password)
            print("Łączenie...")
            connection.connect()
            print("Zatrzymywanie usługi pulpitu zdalnego...")
            connection.run("net stop termservice\n")
            print("Przywracanie oryginalnego pliku...")
            backup_file = check_backup("get_file")
            connection.upload(backup_file)
            os.remove(backup_file)
            os.rmdir(os.path.dirname(backup_file))
            print("Uruchamianie usługi pulpitu zdalnego...")
            connection.run("net start termservice\n")
            print("Zamykanie połaczenia...")
            connection.close()
            print("Gotowe")
        except Exception as err:
            print("Błąd: {}".format(err))


def target():
    def set_value(*values):
        """
        :param values: "host", "port", "user", "pwd"
        """
        stop = False
        for value in values:
            if stop:
                break
            while True:
                uin = input("\n<[Enter] by powrócić> Wprowadź {}: ".format(value_ids[value]))
                if uin == "":
                    print(cancel)
                    stop = True
                    break
                elif value == list(value_ids)[0]:
                    octets = uin.split(".")
                    if len(octets) == 4 and all((num.isdigit() and int(num) in range(0, 256)) for num in octets):
                        print("{}OK{}".format(green, reset))
                        settings.host = uin
                        break
                    else:
                        print("{}Błąd{} - niepoprawna wartość: {}".format(red, reset, uin))
                elif value == list(value_ids)[1]:
                    if uin.isdigit() and int(uin) in range(0, 65536):
                        print("{}OK{}".format(green, reset))
                        settings.target_port = uin
                        break
                    else:
                        print("{}Błąd{} - wartość musi mieścić sie w zakresie 0 - 65535.\nPodana wartość: {}"
                              .format(red, reset, uin))
                elif value == list(value_ids)[2]:
                    print("{}OK{}".format(green, reset))
                    settings.username = uin
                    break
                elif value == list(value_ids)[3]:
                    print("{}OK{}".format(green, reset))
                    settings.password = uin
                    break
            settings.write()
    value_ids = {"host": "adres IP", "port": "port SSH", "user": "nazwę użytkownika", "pwd": "hasło"}

    if not check_target():
        set_value(*list(value_ids))
    else:
        while True:
            print("\n{0:}\nCel: {1}:{2}\nUżytkownik: {3}\n{0}\n"
                  .format(separator, settings.ip, settings.port, settings.user))
            for index, vid in enumerate(value_ids.keys()):
                print("[{}] - Zmień {}".format(index + 1, value_ids[vid]))
            print("\n[Enter] - powrót")
            try:
                choice = input("\nWybierz opcję, [Enter] zatwierdza: ")
                if choice == "":
                    print(cancel)
                    break
                else:
                    set_value(list(value_ids)[int(choice) - 1])

            except Exception:
                print(try_again)


def patching(param="patch"):
    patch = "B80001000089813806000090"
    command = 'wmic datafile where name="{}" get Version /value'.format(os.path.join(os.getcwd(), "termsrv.dll")
                                                                        .replace("\\", "\\\\"))
    result = subprocess.check_output(command, shell=True, text=True)

    with open("termsrv.dll", "rb") as f:
        data = f.read().hex().upper()
    if param == "patch":
        uin = (input(f"Wprowadź kod heksadecymalny dla termsrv.dll {result.strip().replace('Version=', 'wersji ')}: ")
               .replace(" ", "")).upper()
        if len(uin) == 24 and uin in data:
            data.replace(uin, patch)
            with open("termsrv.dll", "wb") as f:
                f.write(bytes.fromhex(data))
                f.close()
        elif uin == "":
            print(cancel)
        else:
            print("\nNie znaleziono wskazanej sygnatury. Upewnij się, że posiadasz kod dla właściwej wersji pliku.")
            print(cancel)
    elif param == "check":
        return patch in data


# Główna część kodu:
running = True
green = "\033[92m"
red = "\033[91m"
blue = "\033[94m"
yellow = "\033[93m"
reset = "\033[0m"
welcome = "{} v{} by {}".format(name, version, author)
separator = "-" * len(welcome)
cancel = "\n{}Powrót...{}".format(blue, reset)
try_again = "{0}\n{1:^{width}}\n{0}".format(separator, "Spróbuj ponownie.", width=len(separator))
print("{0}\n{1}\n{0}\n".format(separator, welcome))

##
settings = Settings()
settings.read()
while running:
    print("\ntermsrv.dll: {}\n"
          .format("{}GOTOWY{}".format(green, reset) if check_payload() and patching("check") else "{}NIEGOTOWY{}"
                  .format(red, reset)))
    full_opt = {"Wykonaj": execute, "Przywróć poprzednią wersję": restore,
                "Wskaż cel": target, "Zmień cel": target, "Wyjdź": None, "Pobierz plik z serwera": get_payload,
                "Patchowanie": patching}
    opt = ["Wskaż cel", "Wyjdź"]
    if check_target():
        opt[0] = list(full_opt)[3]
        opt.insert(1, "Pobierz plik z serwera")
    if check_backup() and check_target() and os.listdir(os.path.join(os.getcwd(), "backup")):
        opt.insert(0, "Przywróć poprzednią wersję")
    if check_payload() and check_target():
        opt.insert(0, "Wykonaj")
        opt.insert(1, "Patchowanie")

    for o in opt:
        print("[{}] - {}".format(opt.index(o) + 1, o))

    u_in = input("\nWybierz opcję, [Enter] zatwierdza: ")
    try:
        if int(u_in) <= 0:
            raise Exception("input less or equal to 0")
        elif list(full_opt)[4] == opt[int(u_in) - 1] and u_in != "0":
            break
        else:
            full_opt[opt[int(u_in) - 1]]()
    except Exception:
        print(try_again)
