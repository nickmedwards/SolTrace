from datetime import datetime
import time
import numpy as np # pyright: ignore[reportMissingImports]
import orjson # pyright: ignore[reportMissingImports]

right_float = lambda fl, buf, p: f"{f'{fl:.{p}f}':>{buf}}"
right_int = lambda i, buf: f"{str(i):>{buf}}"
right_str = lambda s, buf: f"{s:>{buf}}"
left_float = lambda fl, buf, p: f"{f'{fl:.{p}f}':<{buf}}"

class timer():
    def __init__(self, verbose: bool = False, precision: int = 7):
        self.start = {}
        self.verbose = verbose
        self.history = { 'total': 0 }
        self.precision = precision

    def __repr__(self):
        if not len(self.history) > 1: return 'Timer has no times to report.'

        # 1. Find the maximum key length to align the values properly
        max_key_len = max(len(str(k)) for k in self.history.keys())
        max_sum_len = max(len(f'{sum(v):.{self.precision}f}') for k, v in self.history.items() if k != 'total') + 2
        
        formatted_lines = [f'{"timer summary:":<{max_key_len}}    {"total":>{max_sum_len}}{"average":>{max_sum_len}}{"std":>{max_sum_len}}{"median":>{max_sum_len}}{"counts":>{max_sum_len}}']
        formatted_lines.append('-'*(len(formatted_lines[0])))
        
        # 2. Iterate through all keys except 'total'
        for key, diffs in self.history.items():
            if key != 'total':
                value = sum(diffs)
                report_str = f"  {str(key):<{max_key_len}}  {right_float(value, max_sum_len, self.precision)}"
                if (c := len(diffs)) > 1: 
                    report_str += right_float(value/c, max_sum_len, self.precision)
                    report_str += right_float(np.std(diffs), max_sum_len, self.precision)
                    report_str += right_float(np.median(diffs), max_sum_len, self.precision)
                    report_str += right_int(c, max_sum_len)
                formatted_lines.append(report_str)
                
        # 3. Append 'total' at the very end if it exists in the dictionary
        report_str = f'{(self.history['total'] / 60):.{self.precision}f} [m]' if self.history['total'] > 60 else f'{self.history['total']:.{self.precision}f} [s]'
        report_str = f'{right_float(self.history['total'] / 60, max_sum_len)} [m]' if self.history['total'] > 60 else f'{right_float(self.history['total'], max_sum_len, self.precision)} [s]'
        formatted_lines.append(f"  {'total':<{max_key_len}}  {report_str}")
        
        return "\n".join(formatted_lines)
    
    # pretty print
    # amdahl util
    
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
