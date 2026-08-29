from datetime import datetime
import time
import numpy as np # pyright: ignore[reportMissingImports]
import orjson # pyright: ignore[reportMissingImports]
from colorama import just_fix_windows_console, Fore, Back, Style # pyright: ignore[reportMissingModuleSource]
just_fix_windows_console()

right_float = lambda fl, buf, p: f"{f'{fl:.{p}f}':>{buf}}"
right_int = lambda i, buf: f"{str(i):>{buf}}"
right_str = lambda s, buf: f"{s:>{buf}}"
left_float = lambda fl, buf, p: f"{f'{fl:.{p}f}':<{buf}}"

def _min_max_n_values(arr, n):
    sort = np.sort(arr)
    return sort[:n], sort[-n:]

def _fmt_header(cols: list[str], key_buf: int, col_buf: int):
    lines = [f'{"timer summary:":<{key_buf}}    ' + ''.join(f'{c:>{col_buf}}' for c in cols)]
    lines.append('-'*(len(lines[0])))
    return lines

def _highlight_float(val: float, buf: int, p: int, color_bounds: tuple[list[float], list[float], float, float]):
    if val == color_bounds[2]:
        return f'{Fore.LIGHTGREEN_EX}{right_float(val, buf, p)}{Style.RESET_ALL}'
    elif val == color_bounds[3]:
        return f'{Fore.RED}{right_float(val, buf, p)}{Style.RESET_ALL}'
    elif val in color_bounds[0]:
        return f'{Fore.YELLOW}{right_float(val, buf, p)}{Style.RESET_ALL}'
    elif val in color_bounds[1]:
        return f'{Fore.MAGENTA}{right_float(val, buf, p)}{Style.RESET_ALL}'
    else: return right_float(val, buf, p)

def _highlight_int(val: int, buf: int, color_bounds: tuple[list[float], list[float], float, float]):
    if val == color_bounds[2]:
        return f'{Fore.LIGHTGREEN_EX}{right_int(val, buf)}{Style.RESET_ALL}'
    elif val == color_bounds[3]:
        return f'{Fore.RED}{right_int(val, buf)}{Style.RESET_ALL}'
    elif val in color_bounds[0]:
        return f'{Fore.YELLOW}{right_int(val, buf)}{Style.RESET_ALL}'
    elif val in color_bounds[1]:
        return f'{Fore.MAGENTA}{right_int(val, buf)}{Style.RESET_ALL}'
    else: return right_int(val, buf)

def _highlight_toggle(toggle: bool, highlight_f: callable, fmt: callable, *args):
    return highlight_f(*args) if toggle else fmt(*args[:-1])

class timer():
    def __init__(self, verbose: bool = False, precision: int = 7):
        self.start = {}
        self.verbose = verbose
        self.history = { 'total': 0 }
        self.precision = precision
    
    # pretty print
    # amdahl util

    def __repr__(self):
        if not len(self.history) > 1: return 'Timer has no times to report.'

        # get info to print
        timed_keys = [k for k in self.history.keys() if k != 'total']
        stats = np.array([self.summarize(k) for k in timed_keys])
        # toggle at over 12 so fastest/slowest 3 are highlighted
        color_toggle = stats.shape[0] > 11
        colored_values = []

        if color_toggle:
            threshold = int(np.ceil(.2 * stats.shape[0]))
            for i in range(stats.shape[1]):
                _mins, _maxs = _min_max_n_values(stats[:, i], threshold)
                colored_values.append((_mins, _maxs, _mins[0], _maxs[-1]))

        # find the buffers for keys and total col to align the values properly
        max_key_len = max(len(str(k)) for k in self.history.keys())
        max_sum_len = max(len(f'{_sum:.{self.precision}f}') for _sum in stats[:, 0]) + 2

        # format header
        stats_cols = ["total", "average", "std", "median", "counts"]
        formatted_lines = _fmt_header(stats_cols, max_key_len, max_sum_len)

        # for each row in the stats array add key name and timing stats
        # if enough events timed highlight values
        for i in range(stats.shape[0]):
            vals = stats[i, :]
            report_line = [f"  {timed_keys[i]:<{max_key_len}}  "]
            report_line.append(_highlight_toggle(color_toggle, _highlight_float, right_float,
                                                 vals[0], max_sum_len, self.precision, colored_values[0] if color_toggle else None))
            if (count := int(vals[-1])) > 1:
                report_line.extend([_highlight_toggle(color_toggle, _highlight_float, right_float,
                                                      vals[j], max_sum_len, self.precision, colored_values[j])
                                    for j in range(1, stats.shape[1] - 1)])
                report_line.append(_highlight_toggle(color_toggle, _highlight_int, right_int,
                                                     count, max_sum_len, colored_values[-1]))
            formatted_lines.append(''.join(report_line))

        # add total row and footer
        report_str = f'{right_float(self.history['total'] / 60, max_sum_len)} [m]' if self.history['total'] > 60 else f'{right_float(self.history['total'], max_sum_len, self.precision)} [s]'
        formatted_lines.append(f"  {'total':<{max_key_len}}  {report_str}")
        formatted_lines.append(formatted_lines[1])
        
        return "\n".join(formatted_lines)
    
    def __iadd__(self, other: dict):
        # if not a dictionary skip
        if type(other) != dict: return self
        # doesn't add to total because it's assumed that this info is coming 
        # from somewhere timer can't be called, ie in an executable, and it
        # is assumed that the executable call is wrapped in t.ic t.oc
        for key, diff in other.items():
            s = f'  - {key}'
            if s in self.history: self.history[s].append(diff)
            else:                 self.history[s] = [diff]
        return self

    def ic(self, s: str = ''):
        self.start[s] = time.perf_counter()
        if self.verbose: print(f'started{" " + s if s else ""} at: {datetime.now().strftime("%Y/%m/%d %H:%M:%S")}')

    def oc(self, s: str = ''):
        assert s in self.start, f"{s} never started"

        diff = time.perf_counter() - self.start[s]
        if self.verbose: print(f'ended{" " + s if s else ""} at: {datetime.now().strftime("%Y/%m/%d %H:%M:%S")}\n{s + " " if s else ""}took: {diff}')
        if s: 
            self.history['total'] += diff
            if s in self.history: self.history[s].append(diff)
            else:                 self.history[s] = [diff]
        return diff

    def summarize(self, s: str):
        assert s in self.history, f"{s} never timed"

        diffs = self.history[s]
        value = sum(diffs)
        c     = len(diffs)

        ave    = None
        stddev = None
        median = None
        if (c > 1):
            ave    = value / c
            stddev = np.std(diffs)
            median = np.median(diffs)

        return value, ave, stddev, median, c
    
    def to_json(self, fname: str):
        f = open(fname, mode='wb')
        f.write(orjson.dumps(self.history, option=orjson.OPT_INDENT_2))
        f.close()

    def load_json(self, fname: str):
        f = open(fname, mode='rb')
        self.history = orjson.loads(f.read())
        f.close()
