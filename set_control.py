import configparser


class setControl:
    def __init__(self):
        self.filename = 'setup.ini'
        self.config = configparser.ConfigParser()
        found = self.config.read(self.filename)

        # key는 대문자로 넣기
        self.default_shortcut = {
            'KEY_OPEN': '[Ctrl][A]',
            'KEY_SAVE': '[Ctrl][S]',
            'KEY_SETTING': '[O]',
            'KEY_TEXT': '[F1]',
            'KEY_CROSSLINE': '[F2]',
            'KEY_IMAGE_BEFORE': '[A]',
            'KEY_IMAGE_AFTER': '[D]',
            'KEY_LABEL_BEFORE': '[W]',
            'KEY_LABEL_AFTER': '[S]',
            'KEY_DRAW': '[F]',
            'KEY_SELECT': '[E]',
            'KEY_COPY': '[Ctrl][C]',
            'KEY_PASTE': '[Ctrl][V]',
            'KEY_QUICK': '[Q]',
            'KEY_UNDO': '[R]',
            'KEY_REMOVE': '[C]',
            'KEY_RESTORE': '[Z]',
            'KEY_ALTERNATE_MOUSE': '[X]',
            'KEY_DELETE_FILE': '[Delete]'
        }
        self.custom_shortcut = {}
        if not found:
            self.config['SHORTCUT'] = self.default_shortcut
            self.save_ini()
            self.load_ini()
        else:
            self.load_ini()

    def load_ini(self):
        try:
            print('set.ini 파일 불러오기')
            for section in self.config.sections():
                for key in self.config[section]:
                    val = self.config[section].get(key).strip('[]')
                    val = val.split(']')

                    self.custom_shortcut[key.upper()] = []
                    for x in val:
                        self.custom_shortcut[key.upper()].append(x.strip('[]'))
        except:
            print('setup.ini 파일이 망가져 초기화 하였습니다.')
            self.config['SHORTCUT'] = self.default_shortcut
            self.save_ini()

    def save_ini(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            self.config.write(f)
            print('저장하였습니다.')

    def update_ini(self, new_shortcut):
        self.custom_shortcut = new_shortcut
        if new_shortcut:
            for key, val in new_shortcut.items():
                content = ''
                for x in val:
                    content += '[' + x + ']'
                self.config.set('SHORTCUT', key, content)

        with open(self.filename, 'w', encoding='utf-8') as f:
            self.config.write(f)
            print('저장하였습니다.')


if __name__=='__main__':
    key_control = setControl()


