import curses


def main_window(stdscr: curses.window):
    key = -1
    cursor_x = 0
    cursor_y = 0

    stdscr.clear()
    stdscr.refresh()

    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

    info_bar_text = "'q' for exit | 'i' for insert mode | 'r' for replace mode"

    while key != ord('q'):
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # рисуем смещения
        for i in range(height - 1):
            stdscr.addstr(i, 0, '00000000 | ')
            stdscr.addstr(i, len('00000000 | '), 'AA ' * 8 + ' BB' * 8 + ' | ' + '.' * 16)

        # рисуем панель с информацией
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(height-1, 0, info_bar_text)
        stdscr.addstr(height-1, len(info_bar_text), " " * (width - len(info_bar_text) - 1))
        stdscr.attroff(curses.color_pair(3))

        stdscr.refresh()

        key = stdscr.getch()


def main():
    curses.wrapper(main_window)


if __name__ == '__main__':
    main()
