import curses
import logging

from modules.editor import HexEditor


logging.basicConfig(filename='log.log', level=logging.DEBUG)

OFFSET_COLUMN_LENGTH = 8
COLUMNS = 16

ENTER_KEY = 10
ESCAPE_KEY = 27


def str_to_bytes(value: str) -> bytes:
    return int.to_bytes(int(value, 16), 1, 'little')


def is_correct_symbol(value: str):
    return 'a' <= value <= 'f' or '0' <= value <= '9'


def init_colors() -> None:
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)


class HexEditorUI:
    def __init__(self, filename: str):
        self.editor = HexEditor(filename)

        self.data = b''
        self.current_offset = 0
        self.key = -1

        self.height = 0
        self.width = 0

        self.upper_bar = 'Offset(h)  00 01 02 03 04 05 06 07  08 09 0a 0b 0c 0d 0e 0f   Decoded text'
        self.info_bar = "'q' for exit | 'i' for insert mode | 'r' for replace mode | page up | page down"
        self.separator = ' | '

        self._offset_str_len = OFFSET_COLUMN_LENGTH + len(self.separator)
        self._bytes_str_len = COLUMNS * 2 + COLUMNS
        self._decoded_bytes_str_len = len(self.separator) + COLUMNS
        self._total_line_len = self._offset_str_len \
                               + self._bytes_str_len \
                               + self._decoded_bytes_str_len

        self.upper_bar_underline = '-' * (self._total_line_len - 9)

        self.cursor_x = self._offset_str_len + 1
        self.cursor_y = 2

        self._x_offset = 0

        self.stdscr: curses.window = None

    def main(self, stdscr: curses.window) -> None:
        self.stdscr = stdscr
        init_colors()
        self.height, self.width = stdscr.getmaxyx()

        while self.key != ord('q'):
            self.handle_key()
            self.stdscr.clear()
            self.draw()

            self.key = stdscr.getch()

    def draw(self) -> None:
        self.stdscr.addstr(0, 0, self.upper_bar)
        self.stdscr.addstr(1, 9, self.upper_bar_underline)
        for line in range(self.height - 1):
            to_read = min(COLUMNS,
                          self.editor.file_size
                          - self.current_offset
                          - line * COLUMNS)
            self.data = self.editor.get_nbytes(
                self.current_offset + line * COLUMNS, to_read)
            self.draw_offset(line)
            self.draw_bytes(line)
            self.draw_decoded_bytes(line)
            if self.current_offset + line * COLUMNS + COLUMNS > self.editor.file_size:
                break
        self.draw_info_bar()
        self.draw_label()
        self.stdscr.move(self.cursor_y, self.cursor_x)

        self.stdscr.refresh()

    def handle_key(self) -> None:
        control_keys = {curses.KEY_UP, curses.KEY_DOWN,
                        curses.KEY_LEFT, curses.KEY_RIGHT}
        if self.key in control_keys:
            self.handle_cursor()
        elif self.key == curses.KEY_NPAGE:
            self._change_offset((self.height - 3) * 16)
        elif self.key == curses.KEY_PPAGE:
            self._change_offset(-(self.height - 3) * 16)
        elif self.key == ord('r'):
            self.handle_replace()
        elif self.key == ord('i'):
            self.handle_insert()

    def draw_label(self) -> None:
        if self._is_cursor_in_bytes():
            x_coord = self._offset_str_len \
                      + self._bytes_str_len \
                      + self._x_offset + len(self.separator)
            first = self.stdscr.inch(self.cursor_y, x_coord)
            self.stdscr.addch(self.cursor_y, x_coord, first, curses.color_pair(2))
        else:
            x_coord = self._offset_str_len + self._x_offset * 3 + self._x_offset // 8 + 1
            first = self.stdscr.inch(self.cursor_y, x_coord - 1)
            second = self.stdscr.inch(self.cursor_y, x_coord)
            self.stdscr.addch(self.cursor_y, x_coord - 1, first, curses.color_pair(2))
            self.stdscr.addch(self.cursor_y, x_coord, second, curses.color_pair(2))



    def draw_offset(self, y: int) -> None:
        offset_str = '{0:0{1}x}{2}'.format(self.current_offset + y * COLUMNS,
                                           OFFSET_COLUMN_LENGTH,
                                           self.separator)
        self.stdscr.addstr(min(y + 2, self.height - 1), 0, offset_str)

    def draw_bytes(self, y: int) -> None:
        bytes_str = f"{self.data[:COLUMNS // 2].hex(' ')} " \
                    f" {self.data[COLUMNS // 2:].hex(' ')}"
        self.stdscr.addstr(min(y + 2, self.height - 1), self._offset_str_len,
                           bytes_str)

    def draw_decoded_bytes(self, y: int) -> None:
        decoded_str = '{}{}'.format(self.separator, ''.join(
            map(lambda x: chr(x) if 0x20 <= x <= 0x7e else '.', self.data)))
        self.stdscr.addstr(min(y + 2, self.height - 1),
                           self._offset_str_len + self._bytes_str_len,
                           decoded_str)

    def draw_info_bar(self) -> None:
        self.stdscr.attron(curses.color_pair(3))
        self.stdscr.addstr(self.height - 1, 0, self.info_bar)
        self.stdscr.addstr(self.height - 1, len(self.info_bar),
                           " " * (self.width - len(self.info_bar) - 1))
        self.stdscr.attroff(curses.color_pair(3))

    def handle_cursor(self) -> None:
        dx = dy = 0
        if self.key == curses.KEY_LEFT:
            if self.cursor_x > self._offset_str_len + 1:
                self._x_offset = (self._x_offset - 1) % COLUMNS
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
        elif self.key == curses.KEY_RIGHT:
            if self.cursor_x < self._total_line_len - 1:
                self._x_offset = (self._x_offset + 1) % COLUMNS
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
        elif self.key == curses.KEY_UP:
            dy = -1
        elif self.key == curses.KEY_DOWN:
            dy = 1

        self.cursor_x = min(max(self.cursor_x + dx, self._offset_str_len + 1),
                            self._total_line_len - 1)
        if self.cursor_y + dy == self.height - 1:
            self._change_offset(COLUMNS)
        elif self.cursor_y + dy <= 1:
            self._change_offset(-COLUMNS)
        else:
            self.cursor_y += dy

    def handle_replace(self) -> None:
        self.stdscr.move(self.cursor_y, self.cursor_x)

        if self._is_cursor_in_bytes():
            self._handle_replace_bytes()
        else:
            self._handle_replace_decoded()

    def handle_insert(self) -> None:
        if self._is_cursor_in_bytes():
            self._handle_insert_bytes()
        else:
            self._handle_insert_decoded()

    def _is_cursor_in_bytes(self) -> bool:
        return (self._offset_str_len
                <= self.cursor_x <=
                self._bytes_str_len + self._offset_str_len - 1)

    def _change_offset(self, value: int) -> None:
        if self.current_offset + value > self.editor.file_size:
            return

        self.current_offset = max(0, self.current_offset + value)

    def _get_file_offset(self) -> int:
        return self.current_offset + (self.cursor_y - 2) * 16 + self._x_offset

    def _handle_insert_bytes(self) -> None:
        while not is_correct_symbol(first_key := self.stdscr.getkey()):
            pass
        self.editor.insert(self._get_file_offset(), str_to_bytes(first_key))
        self.stdscr.clear()
        self.draw()

        second_key = self.stdscr.getch()
        if second_key == ENTER_KEY:
            return
        elif second_key == ESCAPE_KEY:
            self.editor.remove(self._get_file_offset(), 1)
            return
        else:
            second_key = chr(second_key)
            while not is_correct_symbol(second_key):
                second_key = self.stdscr.getkey()
            self.editor._model.search_region(self._get_file_offset()).data = str_to_bytes(first_key + second_key)
            self.stdscr.clear()
            self.draw()

        while (last_key := self.stdscr.getch()) not in {ENTER_KEY, ESCAPE_KEY}:
            pass
        if last_key == ENTER_KEY:
            return
        elif last_key == ESCAPE_KEY:
            self.editor.remove(self._get_file_offset(), 1)

    def _handle_insert_decoded(self) -> None:
        first_key = self.stdscr.getkey()
        self.editor.insert(self._get_file_offset(), first_key.encode())
        self.stdscr.clear()
        self.draw()

        while (last_key := self.stdscr.getch()) not in {ENTER_KEY, ESCAPE_KEY}:
            pass
        if last_key == ENTER_KEY:
            return
        elif last_key == ESCAPE_KEY:
            self.editor.remove(self._get_file_offset(), 1)

    def _handle_replace_bytes(self) -> None:
        before = self.stdscr.inch(self.cursor_y, self.cursor_x - 1) \
                 + self.stdscr.inch(self.cursor_y, self.cursor_x)

        while not is_correct_symbol(first_key := self.stdscr.getkey()):
            pass
        self.stdscr.addch(self.cursor_y, self.cursor_x, first_key)
        self.stdscr.addch(self.cursor_y, self.cursor_x - 1, '0')
        self.stdscr.refresh()

        second_key = self.stdscr.getch()
        if second_key == ENTER_KEY:
            self.editor.replace(self._get_file_offset(),
                                str_to_bytes(first_key))
            return
        elif second_key == ESCAPE_KEY:
            self.stdscr.addstr(self.cursor_y, self.cursor_x - 1, chr(before))
            return
        else:
            second_key = chr(second_key)
            while not is_correct_symbol(second_key):
                second_key = self.stdscr.getkey()
            self.stdscr.addstr(self.cursor_y, self.cursor_x - 1, first_key)
            self.stdscr.addstr(self.cursor_y, self.cursor_x, second_key)

        self.stdscr.move(self.cursor_y, self.cursor_x)
        while (last_key := self.stdscr.getch()) not in {ENTER_KEY, ESCAPE_KEY}:
            pass
        if last_key == ENTER_KEY:
            self.editor.replace(self._get_file_offset(),
                                str_to_bytes(first_key + second_key))
        elif last_key == ESCAPE_KEY:
            self.stdscr.addstr(self.cursor_y, self.cursor_x - 1, chr(before))

    def _handle_replace_decoded(self) -> None:
        before = self.stdscr.inch(self.cursor_y, self.cursor_x)

        first_key = self.stdscr.getkey()
        self.stdscr.addch(self.cursor_y, self.cursor_x, first_key)
        self.stdscr.refresh()

        self.stdscr.move(self.cursor_y, self.cursor_x)
        while (last_key := self.stdscr.getch()) not in {ENTER_KEY, ESCAPE_KEY}:
            pass
        if last_key == ENTER_KEY:
            self.editor.replace(self._get_file_offset(), first_key.encode())
        elif last_key == ESCAPE_KEY:
            self.stdscr.addstr(self.cursor_y, self.cursor_x - 1, chr(before))


def main():
    app = HexEditorUI('ui.py')
    curses.wrapper(app.main)


if __name__ == '__main__':
    main()
