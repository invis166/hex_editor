import logging
import argparse
import sys
import curses
import itertools

from modules.editor import HexEditor

logging.basicConfig(filename='log.log', level=logging.DEBUG)

INSERT_MODE = 'insert'
VIEW_MODE = 'view'

OFFSET_COLUMN_LENGTH = 8
COLUMNS = 16

SHIFT_LEFT = 391
SHIFT_RIGHT = 400
SHIFT_DOWN = 548
SHIFT_UP = 547

BACKSPACE_KEY = 8
ENTER_KEY = 10
ESCAPE_KEY = 27
DELETE_KEY = 330
HOME_KEY = 262
END_KEY = 358

CONTROL_KEYS = {
    curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT,
}
SELECTION_KEYS = {
    SHIFT_UP, SHIFT_DOWN, SHIFT_RIGHT, SHIFT_LEFT
}

default_bottom_bar = 'current mode: {} | h for help'
default_upper_bar = 'Offset(h)  00 01 02 03 04 05 06 07  08 09 0a 0b 0c 0d 0e 0f' \
                    '   Decoded text'
help_menu = "'a' for insert mode\n'v' for view mode\n's' for save" \
            "\n'page_up', 'page_down', 'home', 'end', arrows for navigation" \
            "\n'g' for goto\n'f' for find" \
            "\n'h' for open(close) help\n'q' for quit" \
            "\nshift + arrows for selection"


def str_to_bytes(value: str) -> bytes:
    return bytes([int(value[i: i + 2], 16) for i in range(0, len(value), 2)])


def is_correct_hex_symbol(value: int) -> bool:
    return 'a' <= chr(value) <= 'f' or '0' <= chr(value) <= '9'


def is_correct_hex_symbol_or_backspace(value: int) -> bool:
    return is_correct_hex_symbol(value) or value == BACKSPACE_KEY


def init_colors() -> None:
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)


class HexEditorUI:
    def __init__(self, filename: str, is_readonly=False):
        self.editor = HexEditor(filename, is_readonly)

        self.selected = [None, None]
        self.clipboard = b''
        self.data = b''
        self.filename = filename

        self.current_offset = 0  # смещение, соответствующее первому байту на экране
        self.key = -1
        self.height = 0
        self.width = 0
        self.bytes_rows = 0

        self.is_readonly = is_readonly
        self._is_in_help = False
        self._bottom_bar_draw_queue = []

        self.current_mode = 'view'
        self.separator = ' | '
        self.upper_bar = default_upper_bar
        self.bottom_bar = default_bottom_bar.format(self.current_mode)

        self._offset_str_len = OFFSET_COLUMN_LENGTH + len(self.separator)
        self._bytes_str_len = COLUMNS * 2 + COLUMNS
        self._decoded_bytes_str_len = len(self.separator) + COLUMNS
        self._total_line_len = (self._offset_str_len
                                + self._bytes_str_len
                                + self._decoded_bytes_str_len)
        self.upper_bar_underline = '-' * (self._total_line_len - 9)

        self.cursor_x = self._offset_str_len + 1
        self.cursor_y = 2

        self._x_offset = 0

        self.stdscr: curses.window = None

    def main(self, stdscr: curses.window) -> None:
        self.stdscr = stdscr
        init_colors()
        self.height, self.width = stdscr.getmaxyx()
        self.bytes_rows = self.height - 3

        while self.key != ord('q'):
            self.handle_key()
            self.stdscr.clear()
            self.draw()

            self.key = stdscr.getch()

    def draw(self) -> None:
        self._is_in_help = False
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
        if self._bottom_bar_draw_queue:
            self.bottom_bar = self._bottom_bar_draw_queue.pop()
        else:
            self.bottom_bar = default_bottom_bar.format(self.current_mode)
        self.draw_bottom_bar()
        self.draw_label()
        self.draw_selected_bytes()
        if self.key == ord('h'):
            self.handle_help()

        self.stdscr.move(self.cursor_y, self.cursor_x)

        self.stdscr.refresh()

    def handle_key(self) -> None:
        if self.key in CONTROL_KEYS:
            self.clear_selected()
            self.handle_cursor()
        elif self.key == ord('c') and self.selected[0] is not None:
            self.handle_copy()
        elif self.key in SELECTION_KEYS:
            self.handle_select()
        elif self.key == curses.KEY_NPAGE:
            self.clear_selected()
            self._increment_offset(self.bytes_rows * 16)
        elif self.key == curses.KEY_PPAGE:
            self.clear_selected()
            self._increment_offset(-self.bytes_rows * 16)
        elif self.key == ord('v'):
            self.current_mode = VIEW_MODE
        elif self.current_mode == INSERT_MODE:
            self.handle_insert_mode()
        elif self.key == ord('a') and not self.is_readonly:
            self.current_mode = INSERT_MODE
        elif self.key == ord('h'):
            if self._is_in_help:
                self.key = -1
                self._is_in_help = False
        elif self.key == ord('g'):
            self.clear_selected()
            self.handle_goto()
        elif self.key == ord('s'):
            self.handle_save()
        elif self.key == ord('f'):
            self.clear_selected()
            self.handle_search()
        elif self.key == HOME_KEY:
            self.clear_selected()
            self._increment_offset(-self.current_offset)
        elif self.key == END_KEY:
            self.clear_selected()
            new_offset = (self.editor.file_size
                          - (self.bytes_rows * COLUMNS
                             - (16 - self.editor.file_size % 16)))
            self._increment_offset(new_offset - self.current_offset)
        else:
            logging.log(level=logging.DEBUG, msg=f'unknown key {self.key}')

    def draw_label(self) -> None:
        if self._is_cursor_in_bytes():
            x_coord = self._offset_str_len \
                      + self._bytes_str_len \
                      + self._x_offset + len(self.separator)
            first = self.stdscr.inch(self.cursor_y, x_coord)
            self.stdscr.addch(self.cursor_y, x_coord, first,
                              curses.color_pair(2))
        else:
            x_coord = self._offset_str_len + self._x_offset * 3 + self._x_offset // 8 + 1
            first = self.stdscr.inch(self.cursor_y, x_coord - 1)
            second = self.stdscr.inch(self.cursor_y, x_coord)
            self.stdscr.addch(self.cursor_y, x_coord - 1, first,
                              curses.color_pair(2))
            self.stdscr.addch(self.cursor_y, x_coord, second,
                              curses.color_pair(2))

    def draw_selected_bytes(self) -> None:
        if self.selected[0] is None:
            return
        start = min(self.selected)
        end = max(self.selected)
        for offset in range(start, end + 1):
            if not self._is_offset_on_screen(offset):
                continue
            y, x = self._get_coords_by_offset(offset)
            first = self.stdscr.inch(y, x)
            second = self.stdscr.inch(y, x - 1)
            decoded_char_x = (self._total_line_len
                              - self._decoded_bytes_str_len + 3
                              + offset % 16)
            third = self.stdscr.inch(y, decoded_char_x)
            self.stdscr.addch(y, x, first, curses.color_pair(1))
            self.stdscr.addch(y, x - 1, second, curses.color_pair(1))
            self.stdscr.addch(y, decoded_char_x, third, curses.color_pair(1))

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

    def draw_bottom_bar(self) -> None:
        self.stdscr.attron(curses.color_pair(3))
        self.stdscr.addstr(self.height - 1, 0, self.bottom_bar)
        self.stdscr.addstr(self.height - 1, len(self.bottom_bar),
                           " " * (self.width - len(self.bottom_bar) - 1))
        self.stdscr.attroff(curses.color_pair(3))

    def handle_copy(self) -> None:
        start, end = min(self.selected), max(self.selected)
        self.clipboard = self.editor.get_nbytes(start, end - start + 1)
        self.clear_selected()
        logging.log(msg=f'clipboard: {self.clipboard}', level=logging.DEBUG)

    def handle_paste(self) -> None:
        if self.clipboard == b'':
            return
        self.editor.insert(self._get_cursor_offset(), self.clipboard)

    def handle_cut(self) -> None:
        if self.selected[0] is None:
            return
        start, end = min(self.selected), max(self.selected)
        self.clipboard = self.editor.get_nbytes(start, end - start + 1)
        self.clear_selected()
        self.editor.remove(start, end - start + 1)

    def handle_select(self) -> None:
        if self.selected[0] is None:
            self.selected = [self._get_cursor_offset(),
                             self._get_cursor_offset()]
        elif self.key == SHIFT_RIGHT:
            if self.selected[-1] < self.selected[0]:
                self.selected[-1] += 1
            elif self.selected[-1] != self.editor.file_size - 1:
                self.selected[-1] += 1
        elif self.key == SHIFT_LEFT:
            if self.selected[-1] > self.selected[0]:
                self.selected[-1] -= 1
            elif self.selected[-1] != 0:
                self.selected[-1] -= 1
        if self.key == SHIFT_DOWN:
            self.selected[-1] += 16
            self.selected[-1] = min(self.selected[-1], self.editor.file_size - 1)
        elif self.key == SHIFT_UP:
            self.selected[-1] -= 16
            self.selected[-1] = max(0, self.selected[-1])

        if self.selected[-1] < self.current_offset:
            self._increment_offset(-16)
        elif self.selected[-1] > self.current_offset + self.bytes_rows * 16:
            self._increment_offset(16)

    def handle_save(self) -> None:
        self.bottom_bar = self.filename
        self.draw_bottom_bar()
        filename = list(self.filename)
        cursor_x = len(filename)
        self.stdscr.move(self.height - 1, cursor_x)
        self.stdscr.refresh()
        for symbol in self.get_user_input():
            if symbol == 8 and cursor_x:
                filename.pop(cursor_x - 1)
                cursor_x -= 1
            elif symbol == ESCAPE_KEY:
                return
            elif symbol == curses.KEY_LEFT:
                cursor_x = max(0, cursor_x - 1)
            elif symbol == curses.KEY_RIGHT:
                cursor_x = min(len(filename), cursor_x + 1)
            elif symbol != 8:
                filename.insert(cursor_x, chr(symbol))
                cursor_x += 1
            self.bottom_bar = ''.join(filename)
            self.draw_bottom_bar()
            self.stdscr.move(self.height - 1, cursor_x)
            self.stdscr.refresh()
        self.editor.save_changes(''.join(filename))
        self._bottom_bar_draw_queue.append('saved')

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
                if self._get_cursor_offset() + 1 == self.editor.file_size:
                    return
                self._x_offset = (self._x_offset + 1) % COLUMNS

            if self._is_cursor_in_bytes():
                if (
                        self.cursor_x == COLUMNS + COLUMNS // 2 - 2 + self._offset_str_len
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
            if self._get_cursor_offset() + COLUMNS + 1 > self.editor.file_size:
                return
            dy = 1

        self.cursor_x = min(max(self.cursor_x + dx, self._offset_str_len + 1),
                            self._total_line_len - 1)
        if self.cursor_y + dy == self.height - 1:
            self._increment_offset(COLUMNS)
        elif self.cursor_y + dy <= 1:
            self._increment_offset(-COLUMNS)
        else:
            self.cursor_y += dy

    def handle_insert(self) -> None:
        if self._is_cursor_in_bytes():
            self._handle_insert_bytes()
        else:
            self._handle_insert_decoded()

    def handle_delete(self) -> None:
        self.editor.remove(self._get_cursor_offset(), 1)

    def handle_backspace(self) -> None:
        self.editor.remove(max(self._get_cursor_offset() - 1, 0), 1)
        self.key = curses.KEY_LEFT
        self.handle_cursor()

    def handle_insert_mode(self) -> None:
        if self.key in CONTROL_KEYS:
            self.handle_cursor()
        elif self.key == DELETE_KEY:
            self.clear_selected()
            self.handle_delete()
        elif self.key == BACKSPACE_KEY:
            self.clear_selected()
            self.handle_delete()
        elif self.key == ord('k'):
            self.handle_cut()
        elif self.key == ord('p'):
            self.handle_paste()
        elif self._is_cursor_in_bytes():
            self.clear_selected()
            self._handle_insert_bytes()
        else:
            self.clear_selected()
            self._handle_insert_decoded()

    def _is_offset_on_screen(self, offset: int) -> bool:
        return (self.current_offset
                <= offset <
                self.current_offset + self.bytes_rows * 16)

    def _is_correct_offset(self, offset: int) -> bool:
        return 0 <= offset <= self.editor.file_size

    def _convert_offset_to_x_pos(self, offset) -> int:
        offset = offset % 16
        if self._is_cursor_in_bytes():
            return self._offset_str_len + offset * 3 + offset // 8 + 1
        else:
            return self._offset_str_len \
                   + self._bytes_str_len \
                   + offset + len(self.separator)

    def _move_cursor_to_offset(self, offset: int) -> None:
        self.cursor_y, self.cursor_x = self._get_coords_by_offset(offset)
        self._x_offset = offset % 16

    def _get_coords_by_offset(self, offset: int) -> tuple:
        y = 2 + (offset - self.current_offset) // 16
        x = self._convert_offset_to_x_pos(offset)

        return y, x

    def _is_cursor_in_bytes(self) -> bool:
        return (self._offset_str_len
                <= self.cursor_x <=
                self._bytes_str_len + self._offset_str_len - 1)

    def _increment_offset(self, value: int) -> None:
        if self.current_offset + value > self.editor.file_size:
            return

        self.current_offset = max(0, self.current_offset + value)

    def _get_cursor_offset(self) -> int:
        """Offset по положению курсора"""
        return self.current_offset + (self.cursor_y - 2) * 16 + self._x_offset

    def _handle_insert_bytes(self) -> None:
        counter = itertools.count()
        user_input = []
        stop_keys = CONTROL_KEYS.union(SELECTION_KEYS)
        stop_keys.add(ord('v'))
        buffer = []
        if self.key == ord('v'):
            self.current_mode = VIEW_MODE
            return
        if is_correct_hex_symbol_or_backspace(self.key):
            buffer.append(self.key)
        for symbol in itertools.chain(buffer, self.get_user_input(
                filter=is_correct_hex_symbol_or_backspace, stop_keys=stop_keys)):
            if symbol == BACKSPACE_KEY:
                self.handle_delete()
                break
            if next(counter) % 2 - 1:
                user_input.append('0')
                user_input.append(chr(symbol))
                self.editor.insert(self._get_cursor_offset(),
                                   str_to_bytes(''.join(user_input)))
                self.stdscr.clear()
                self.draw()
            else:
                del user_input[-2]
                user_input.append(chr(symbol))
                self.editor.replace(self._get_cursor_offset(),
                                    str_to_bytes(''.join(user_input)))
                self.stdscr.clear()
                self.draw()
                user_input = []  #
        if self.key == ord('v'):
            self.current_mode = VIEW_MODE
        elif self.key in SELECTION_KEYS:
            self.handle_select()
        else:
            self.handle_cursor()

    def _handle_insert_decoded(self) -> None:
        stop_keys = CONTROL_KEYS.union((ord('v'),))
        if self.key == ord('v'):
            self.current_mode = VIEW_MODE
            return
        for symbol in itertools.chain((self.key,), self.get_user_input(stop_keys=stop_keys)):
            if symbol == BACKSPACE_KEY:
                self.handle_delete()
                break
            self.editor.insert(self._get_cursor_offset(), chr(symbol).encode('utf-8'))
            self.stdscr.clear()
            self.draw()
        if self.key == ord('v'):
            self.current_mode = VIEW_MODE
        else:
            self.handle_cursor()

    def handle_help(self) -> None:
        self._is_in_help = True
        lines = help_menu.split('\n')
        self.stdscr.attron(curses.color_pair(1))
        for i, line in enumerate(lines):
            self.stdscr.addstr(2 + i, 0,
                               line + ' ' * (self._total_line_len - len(line)))
        self.stdscr.attroff(curses.color_pair(1))

    def handle_goto(self) -> None:
        user_input = []
        self.bottom_bar = 'goto (h): '
        self.draw_bottom_bar()
        for symbol in self.get_user_input(filter=is_correct_hex_symbol_or_backspace):
            if symbol == BACKSPACE_KEY and len(user_input):
                user_input.pop()
            elif symbol != BACKSPACE_KEY:
                user_input.append(chr(symbol))
            self.bottom_bar = f'goto (h): {"".join(user_input)}'
            self.draw_bottom_bar()
        logging.log(msg=user_input, level=logging.DEBUG)
        offset = int("".join(user_input), 16)
        self._increment_offset((offset - offset % 16) - self.current_offset)
        self._move_cursor_to_offset(offset)

    def handle_search(self) -> None:
        user_input = []
        self.bottom_bar = 'search (h): '
        self.draw_bottom_bar()
        stop_keys = {ENTER_KEY, ESCAPE_KEY}
        counter = itertools.count()
        for symbol in self.get_user_input(
                filter=is_correct_hex_symbol_or_backspace, stop_keys=stop_keys):
            if symbol == BACKSPACE_KEY and not user_input:
                continue
            if next(counter) % 2 - 1:
                if symbol == BACKSPACE_KEY and len(user_input) >= 2:
                    user_input[-1] = user_input[-2]
                    user_input[-2] = '0'
                elif symbol != BACKSPACE_KEY:
                    user_input.append('0')
                    user_input.append(chr(symbol))
            else:
                if symbol == BACKSPACE_KEY and len(user_input) >= 2:
                    del user_input[-2:]
                elif symbol != BACKSPACE_KEY:
                    del user_input[-2]
                    user_input.append(chr(symbol))
            self.bottom_bar = f'search (h): {"".join(user_input)}'
            self.draw_bottom_bar()
        if self.key == ESCAPE_KEY:
            return

        query = ''.join(user_input)
        logging.log(msg=f'trying to find {str_to_bytes(query)}',
                    level=logging.DEBUG)
        if (offset := self.editor.search(str_to_bytes(query))) == -1:
            logging.log(msg=f'query {query} not found', level=logging.DEBUG)
            self._bottom_bar_draw_queue.append('not found')
            return
        logging.log(msg=f'found at offset {offset}', level=logging.DEBUG)
        self.current_offset = offset - offset % COLUMNS
        self._move_cursor_to_offset(offset)

    def clear_selected(self) -> None:
        if self.selected[0] is None:
            return
        if not self._is_offset_on_screen(self.selected[0]):
            self._increment_offset(self.selected[0]
                                   - self.selected[0] % 16
                                   - self.current_offset
                                   - self.bytes_rows // 2 * 16)
        self._move_cursor_to_offset(self.selected[0])
        self.selected = [None, None]

    def get_user_input(self, filter=lambda x: True,
                       stop_keys=(ENTER_KEY,)) -> int:
        """Считывает пользовательский ввод до нажатия stop_keys(по
           умолчанию ENTER). Если передан предикат filter, то считывает
           только символы, удовлетворяющие ему"""
        while (key := self.stdscr.getch()) not in stop_keys:
            if filter(key):
                yield key
        self.key = key


def main():
    # parser = argparse.ArgumentParser(description="Hex editor")
    # parser.add_argument('filename', help='name of editing file')
    # parser.add_argument('-r', '--read-only', action='store_false',
    #                     help='if passed, open file in read only mode')
    # args = parser.parse_args(sys.argv[1])
    # app = HexEditorUI(filename=args.filename, is_readonly=args.read_only)
    app = HexEditorUI('alabai.png')
    curses.wrapper(app.main)


if __name__ == '__main__':
    main()
