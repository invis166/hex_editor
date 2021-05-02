import curses

from modules.editor import HexEditor

OFFSET_COLUMN_LENGTH = 8
COLUMNS = 16


class HexEditorUI:
    def __init__(self, filename: str):
        self.editor = HexEditor(filename)

        self.data = b''
        self.current_offset = 0
        self.key = 'None'

        self.height = 0
        self.width = 0

        self.info_bar = "'q' for exit | 'i' for insert mode | 'r' for replace mode"
        self.separator = ' | '

        self._offset_str_len = OFFSET_COLUMN_LENGTH + len(self.separator)
        self._bytes_str_len = COLUMNS * 2 + COLUMNS
        self._decoded_bytes_str_len = len(self.separator) + COLUMNS
        self._total_line_len = self._offset_str_len \
                               + self._bytes_str_len \
                               + self._decoded_bytes_str_len

        self.cursor_x = self._offset_str_len + 1
        self.cursor_y = 0

        self.stdscr: curses.window = None

    def main(self, stdscr: curses.window) -> None:
        self.stdscr = stdscr
        self.init_colors()

        while self.key != 'q':
            self.handle_key()

            self.height, self.width = stdscr.getmaxyx()

            for y in range(self.height - 1):
                self.data = self.editor.get_nbytes(
                    self.current_offset + y * COLUMNS, COLUMNS)
                self.draw_offset(y)
                self.draw_bytes(y)
                self.draw_decoded_bytes(y)

            self.draw_info_bar()

            stdscr.move(self.cursor_y, self.cursor_x)

            stdscr.refresh()

            self.key = stdscr.getkey()

    def handle_key(self) -> None:
        control_keys = {'KEY_UP', 'KEY_DOWN', 'KEY_LEFT',
                        'KEY_RIGHT'}
        if self.key in control_keys:
            self.handle_cursor()
        if self.key == 'PAGE_DOWN':
            self.current_offset = self.height - 1

    def draw_offset(self, y: int) -> None:
        offset_str = '{0:0{1}x}{2}'.format(self.current_offset + y * COLUMNS,
                                           OFFSET_COLUMN_LENGTH,
                                           self.separator)
        self.stdscr.addstr(y, 0, offset_str)

    def draw_bytes(self, y: int) -> None:
        bytes_str = f"{self.data[:COLUMNS // 2].hex(' ')} " \
                    f" {self.data[COLUMNS // 2:].hex(' ')}"
        self.stdscr.addstr(y, self._offset_str_len, bytes_str)

    def draw_decoded_bytes(self, y) -> None:
        decoded_str = '{}{}'.format(self.separator, ''.join(
            map(lambda x: chr(x) if 0x20 <= x <= 0x7e else '.', self.data)))
        self.stdscr.addstr(y, self._offset_str_len + self._bytes_str_len,
                           decoded_str)

    def draw_info_bar(self):
        self.stdscr.attron(curses.color_pair(3))
        self.stdscr.addstr(self.height - 1, 0, self.info_bar)
        self.stdscr.addstr(self.height - 1, len(self.info_bar),
                           " " * (self.width - len(self.info_bar) - 1))
        self.stdscr.attroff(curses.color_pair(3))

    def handle_cursor(self):
        dx = dy = 0
        if self.key == 'KEY_LEFT':
            if self._is_cursor_in_bytes():
                if self.cursor_x == COLUMNS + COLUMNS // 2 + 2 + self._offset_str_len:
                    # прыгаем через два пробела между блоками по 8 байт
                    dx = -4
                else:
                    dx = -3
            elif self.cursor_x == self._offset_str_len + self._bytes_str_len + 3:
                # прыгаем через разделитель после блока байт
                dx = -4
            else:
                dx = -1
        elif self.key == 'KEY_RIGHT':
            if self._is_cursor_in_bytes():
                if (self.cursor_x == COLUMNS + COLUMNS // 2 - 2 + self._offset_str_len
                        or self.cursor_x == self._offset_str_len + self._bytes_str_len - 1):
                    # прыгаем через два пробела между блоками по 8 байт или
                    # через разделитель после блока байт
                    dx = 4
                else:
                    dx = 3
            else:
                dx = 1
        elif self.key == 'KEY_UP':
            dy = -1
        elif self.key == 'KEY_DOWN':
            dy = 1

        self.cursor_x = min(max(self.cursor_x + dx, self._offset_str_len + 1),
                            self._total_line_len - 1)
        self.cursor_y = min(max(self.cursor_y + dy, 0), self.height - 1 - 1)

    def _is_cursor_in_bytes(self):
        return (self._offset_str_len
                <= self.cursor_x <=
                self._bytes_str_len + self._offset_str_len - 1)

    def init_colors(self):
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)


def main():
    app = HexEditorUI('alabai.png')
    curses.wrapper(app.main)


if __name__ == '__main__':
    main()
