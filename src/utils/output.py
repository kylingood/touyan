import os
from rich.console import Console
from rich.text import Text
from tabulate import tabulate
from rich.table import Table
from rich import box
from typing import List
from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, Window, HSplit
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style


def show_logo():
    """显示STARLABS的时尚标志 STARLABS"""
    # Очищаем экран
    os.system("cls" if os.name == "nt" else "clear")

    console = Console()

    # Создаем звездное небо со стилизованным логотипом
    logo_text = """
✦ ˚ . ⋆   ˚ ✦  ˚  ✦  . ⋆ ˚   ✦  . ⋆ ˚   ✦ ˚ . ⋆   ˚ ✦  ˚  ✦  . ⋆   ˚ ✦  ˚  ✦  . ⋆ ✦ ˚ 
. ⋆ ˚ ✧  . ⋆ ˚  ✦ ˚ . ⋆  ˚ ✦ . ⋆ ˚  ✦ ˚ . ⋆  ˚ ✦ . ⋆ ˚  ✦ ˚ . ⋆  ˚ ✦ . ⋆  ˚ ✦ .✦ ˚ . 
·˚ ⋆｡⋆｡. ★ ·˚ ★ ·˚ ⋆｡⋆｡. ★ ·˚ ★ ·˚ ⋆｡⋆｡. ★ ·˚ ★ ·˚ ⋆｡⋆｡. ★ ·˚ ⋆｡⋆｡. ★ ·˚ ★ ·˚ ·˚ ★ ·˚
✧ ⋆｡˚✦ ⋆｡  ███████╗████████╗ █████╗ ██████╗ ██╗      █████╗ ██████╗ ███████╗  ⋆｡ ✦˚⋆｡ 
★ ·˚ ⋆｡˚   ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██║     ██╔══██╗██╔══██╗██╔════╝  ✦˚⋆｡ ˚· 
⋆｡✧ ⋆ ★    ███████╗   ██║   ███████║██████╔╝██║     ███████║██████╔╝███████╗   ˚· ★ ⋆
˚· ★ ⋆｡    ╚════██║   ██║   ██╔══██║██╔══██╗██║     ██╔══██║██╔══██╗╚════██║   ⋆ ✧｡⋆ 
✧ ⋆｡ ˚·    ███████║   ██║   ██║  ██║██║  ██║███████╗██║  ██║██████╔╝███████║   ★ ·˚ ｡
★ ·˚ ✧     ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝   ｡⋆ ✧ 
·˚ ⋆｡⋆｡. ★ ·˚ ★ ·˚ ⋆｡⋆｡. ★ ·˚ ★ ·˚ ⋆｡⋆｡. ★ ·˚ ★ ·˚ ⋆｡⋆｡. ★ ·˚ ⋆｡⋆｡. ★ ·˚ ★ ·˚·˚ ⋆｡⋆｡.
. ⋆ ˚ ✧  . ⋆ ˚  ✦ ˚ . ⋆  ˚ ✦ . ⋆ ˚  ✦ ˚ . ⋆  ˚ ✦ . ⋆ ˚  ✦ ˚ . ⋆  ˚ ✦ . ⋆  ˚ ✦ .. ⋆  ˚ 
✦ ˚ . ⋆   ˚ ✦  ˚  ✦  . ⋆ ˚   ✦  . ⋆ ˚   ✦ ˚ . ⋆   ˚ ✦  ˚  ✦  . ⋆   ˚ ✦  ˚  ✦  . ⋆  ✦"""

    # Создаем градиентный текст
    gradient_logo = Text(logo_text)
    gradient_logo.stylize("bold bright_cyan")

    # Выводим с отступами
    console.print(gradient_logo)
    print()


def show_dev_info():
    """Displays development and version information"""
    console = Console()

    # Создаем красивую таблицу
    table = Table(
        show_header=False,
        box=box.DOUBLE,
        border_style="bright_cyan",
        pad_edge=False,
        width=49,
        highlight=True,
    )

    # Добавляем колонки
    table.add_column("Content", style="bright_cyan", justify="center")

    # Добавляем строки с контактами
    table.add_row("✨ Discord Bot 大逃杀 1.0 ✨")
    table.add_row("─" * 43)
    table.add_row("")
    table.add_row(" Guzi 基于作者 moncici007的源码 新增的功能")
    table.add_row(" GitHub：[link]https://github.com/moncici007[/link]")
    table.add_row(" Guzi 推特 [link]https://x.com/guzibiji[/link]")
    table.add_row("")

    # Выводим таблицу с отступом
    print("   ", end="")
    print()
    console.print(table)
    print()


def show_menu(options: List[str]) -> str:
    """
    Shows numbered menu and returns selected option string.
    """
    print("😎  选择你要做的操作 😎\n")

    # Выводим пронумерованные опции
    for i, option in enumerate(options, 1):
        print(f"[{i}] {option}")

    while True:
        try:
            print("\n")
            choice = int(input("你的选择: "))
            if 1 <= choice <= len(options):
                selected_index = choice - 1
                return options[selected_index]
            else:
                print(f"     ❌ 请输入数据 1 至 {len(options)} 之间的值")
        except ValueError:
            print("     ❌ 请输入一个有效的数字")
