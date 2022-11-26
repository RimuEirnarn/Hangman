"""Hangman"""
from csv import reader, writer
from os.path import exists, realpath
from pathlib import Path
from random import choice, randint
from string import punctuation
import sys
from typing import Any, Callable, List, Optional, Tuple, Union
from argh import ArghParser, arg

DEFAULT_DATAPATH = Path(realpath(__file__+'/../data'))
DEFAULT_WPATH = DEFAULT_DATAPATH / "word.csv"
BANNER_ONETIME = """Welcome to Hangman! (c) 2022 RimuEirnarn
When the game is started, you will be prompted to input a data.
The data is space seperated, first data is the index and the second data is the character.
For example: 3 a

3 -> the third character
a -> the guessed character

... or you can just enter a character like: a\n"""
BANNER = "Welcome to Hangman! (c) 2022 RimuEirnarn\n"
HINT = (1, 2, 4)
HINT_FLAG = (3, 7, 15)
CLEAR = "\033[H\033[2J\033[3J"
TupleAny = Tuple[Any, ...]
ListTupleAny = List[TupleAny]
TupleTupleAny = Tuple[Tuple[Any, ...]]
AnyOrString = Union[Any, str]
OptFunc = Optional[Callable[[Any], Union[Any, str]]]
FailHook = Optional[Callable[[Any], Tuple[bool, str]]]


def custom_input(prompt: str,
                 default: str = "",
                 hook: OptFunc = None,
                 fail_hook: FailHook = None) -> AnyOrString:
    """Prompt a input to user, return a 1-sized string or an empty string. It depends on hooks."""
    try:
        returns = input(prompt).lower()
        if fail_hook:
            err = fail_hook(returns)
            if err[0]:
                return hook(default if default == '' else default[0]) if hook is not None \
                    else default if default == '' else default[0]
        if hook:
            return hook(returns)
        return returns
    except (KeyboardInterrupt, IndexError):
        return default if default == '' else default[0]
    except EOFError:
        sys.exit(1)


def read_csv(filename: str, allrow: bool = False) -> Union[TupleAny, TupleTupleAny]:
    """Read a CSV file then return a tuple of tuples or just a tuple."""
    with open(filename, encoding='utf-8') as file:
        rcsv = reader(file)
        returns = []
        for line in rcsv:
            returns.append(tuple(line))

        if len(returns) == 0:
            raise ValueError("No data from CSV file is found.")

        if allrow:
            return tuple(returns)
        return returns[0]


def write_csv(filename: str, data: Union[ListTupleAny, TupleAny, TupleTupleAny]):
    """Write a CSV data to a file."""
    with open(filename, 'w', encoding='utf-8') as file:
        writer_csv = writer(file)  # type: ignore
        if isinstance(data[0], (tuple, list)):
            writer_csv.writerows(data)
        else:
            writer_csv.writerow(data)


def cast(data: Any):
    """Cast a data ot either float, int or itself."""
    try:
        return float(data) if '.' in data else int(data)
    except ValueError:
        return data


def input_hook(data: str) -> AnyOrString:
    """Input hook"""
    data = data.lower()
    if len(data) == 1:
        return 0, data
    if len(data) == 3:
        return cast(data[0]), data[2]
    return 0, data[0]


def padded_print(data):
    """Print stuff"""
    padded = [1]
    for idx in range(1, len(data)+1):
        padded.append(len(str(idx)))

    print(" ".join((a or "_"*padded[idx+1])+" "*(padded[idx+1]-1)
                   for idx, a in enumerate(data)))
    print(" ".join((str(d)+" "*(padded[idx+1]-1)
                    for idx, d in enumerate(range(1, len(data)+1)))))


@arg("--word-list", help="Word list file to use, default to program's word list path.")
def main(word_list: Optional[str] = None):
    """A hangman game."""
    if not exists(DEFAULT_WPATH):
        write_csv(str(DEFAULT_WPATH), ("Apple", "Determination",
                                       "Projectile", "Anime", "Mouse", "Cat", "Project"))

    condition = None
    death = 3
    # Set default data, will be allocated with None (and two helper hints)
    # for the length of randomly selected word.
    chars: List[Union[None, str]] = []
    words = read_csv(word_list or str(DEFAULT_WPATH))

    selected: str = choice(words).lower()
    selected_2 = selected
    sel_hints = HINT[2]
    if len(selected) <= HINT_FLAG[0]:
        sel_hints = HINT[0]
    elif len(selected) <= HINT_FLAG[1]:
        sel_hints = HINT[1]
    elif len(selected) <= HINT_FLAG[2]:
        sel_hints = HINT[2]
    chars.extend((None for _ in selected))
    passed = []
    while len(passed) != sel_hints:
        var_x = randint(0, len(selected)-1)
        if var_x in passed:
            continue
        passed.append(var_x)
        chars[var_x] = selected[var_x]
    print(CLEAR +
          (BANNER_ONETIME if not exists(DEFAULT_DATAPATH / "init") else BANNER))
    with open(DEFAULT_DATAPATH / "init", "w", encoding='utf-8') as file:
        file.write('\0')
    turns = 0
    while True:
        # Print current status
        padded_print(chars)
        print(
            f"You can play until {death} more mistake(s)" if death != 0 else "Game over!", end='')

        char = custom_input("\n\nYour input: ", "-", fail_hook=lambda x: (
            x in punctuation.replace(' ', ''), "The data has a invalid character"))[0]

        # First layer of checks.
        if char == '-':
            death -= 1

        if char not in selected and char not in selected_2 and char != '-':
            death -= 1

        if char in selected_2:
            index = selected_2.index(char)
            chars[index] = char
            selected_2 = selected_2.replace(char, '_', 1)

        # Last check, conditionals.
        if death == 0:
            condition = False
            break
        if ''.join((a or '') for a in chars) == selected:
            condition = True
            break

        turns += 1
        print(CLEAR, end='')

    print(CLEAR, end='')
    padded_print(chars)
    print(
        f"Correct word: {selected}\nGuessed totals: {''.join(((a or '_') for a in chars))}")
    if condition is True:
        print("\n\033[32mYou've won the game!\033[0m")
    else:
        print('\nYou lose, get better \033[32mnext\033[0m try!')


if __name__ == '__main__':
    parser = ArghParser()
    parser.set_default_command(main)
    parser.dispatch()
