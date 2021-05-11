import threading
from tkinter import ttk
from tkinter import *
from tkinter import filedialog as tk_fd
from tkinter import messagebox as tk_mb
import os
import sys
from ctypes import windll
from Tooltip import ToolTip

FALSE = False
TRUE = True
DONE = 'Done'


class FindInFiles(Tk):
    """
    Find anything in files by specifying the folder
    """
    class Results:
        searched_keyword = ''
        searched_dir = ''
        results = []
        skipped = []
        files_searched = 0
        files_skipped = 0
        total_hits = 0
        folders_searched = 0

    def __init__(self, ez_py=None):
        Tk.__init__(self)
        self.geometry('950x680+150+5')
        self.overrideredirect(1)
        # self.wm_attributes('-topmost', 1)
        self.config(highlightbackground='black', highlightthickness=1)
        self.after(10, lambda: self.set_appwindow(self))

        self.ez_py = ez_py
        self.search_history = SearchHistory()
        self.search_results = self.Results()
        self.x = None
        self.y = None
        self.tree_index = self.tree_iid = 0

        self.rootdir = sys.executable.rstrip('\\python.exe').rstrip('\\pythonw.exe')
        self.suffix = '.py'
        self.searching = FALSE

        self.title_frame = Frame(self, bg='gray38', relief=RAISED, bd=3)
        self.title_frame.bind("<ButtonPress-1>", self.start_move)
        self.title_frame.bind("<ButtonRelease-1>", self.stop_move)
        self.title_frame.bind("<B1-Motion>", self.do_move)

        self.title_label = Label(self.title_frame, text='Search in Files', font='Helvetica 12', bg='gray38',
                                 fg='white')
        self.title_label.bind("<ButtonPress-1>", self.start_move)
        self.title_label.bind("<ButtonRelease-1>", self.stop_move)
        self.title_label.bind("<B1-Motion>", self.do_move)

        self.exit_label = Label(self.title_frame, text='✕', bd=0, font='Consolas 12', bg='gray38', width=2)
        self.exit_label.bind('<Enter>', lambda _=None: [
            ToolTip(self.exit_label, 'Helvetica 8', 'Close', follow=False),
            self.exit_label.config(bg='red')
        ])
        self.exit_label.bind('<Leave>', lambda _=None: self.exit_label.config(bg=self.title_frame['background']))
        self.exit_label.bind('<ButtonPress-1>', lambda _=None: self.exit_label.config(bg='red3'))
        self.exit_label.bind('<ButtonRelease-1>', lambda _=None: self.quit())

        self.entry_frame = Frame(self, highlightbackground='black', highlightthickness=1)
        self.result_frame = Frame(self, highlightbackground='black', highlightthickness=1)
        self.search_entry = Entry(self.entry_frame, font='Helvetica 12', highlightbackground='black',
                                  highlightthickness=1)
        self.search_entry.bind('<Return>', self.search)
        self.search_entry.bind('<Enter>', lambda _=None: ToolTip(
            self.search_entry, 'Helvetica 8', msg='Enter the string to be searched.\nSearch is case specific. Search\n'
                                                  'string with less than 5 characters\nmay take more amount of time',
            delay=0.7, follow=False))
        self.search_button = Button(self.entry_frame, font='Helvetica 10', text='Search', command=self.search)

        def set_search_tooltip(event=None):
            entry = self.search_entry.get()
            folder = self.folder_entry.get()
            len_entry = len(entry)
            len_folder = len(folder)

            if len_entry > 30:
                ind = 30
                while ind < len_entry:
                    if ind > len_entry:
                        ind = len_entry
                    entry = entry[:ind] + '\n' + entry[ind:]
                    ind += 30

            if len_folder > 30:
                ind = 30
                while ind < len_folder:
                    if ind > len_folder:
                        ind = len_folder
                    folder = folder[:ind] + '\n' + folder[ind:]
                    ind += 30

            search_msg = f'Search for " {entry} "\nin all the files and folders of\n' \
                         f'" {folder} "\nending with " {self.extension_entry.get()} "' if \
                self.extension_intvar.get() > 0 else f'Search for " {entry} "\nin all the files and ' \
                                                     f'folders of\n" {folder} "' if \
                len(entry) > 0 else f'Search in files and folders of\n" {folder} "'
            ToolTip(self.search_button, 'Helvetica 8', msg=search_msg, delay=0.7, follow=False)

        self.after(1000, set_search_tooltip)
        self.search_button.bind('<Enter>', set_search_tooltip)

        self.extension_intvar = IntVar()
        self.configurations_frame = Frame(self.entry_frame, highlightbackground='black', highlightthickness=1)
        self.extension_checkbutton = Checkbutton(self.configurations_frame, text='Search with specific extension',
                                                 variable=self.extension_intvar, onvalue=1, offvalue=0,
                                                 command=self.configure_extension, font='Helvetica 11')
        self.extension_entry = Entry(self.configurations_frame, width=7, font='Helvetica 10',
                                     highlightbackground='black', highlightthickness=1)
        self.extension_entry.bind('<Enter>', lambda _=None: ToolTip(
            self.extension_entry, 'Helvetica 8', msg='Extensions are case specific! Providing extensions\nwithout'
                                                     ' a dot may give results for files ending\nwith the provided'
                                                     ' entry', delay=0.7, follow=False))
        self.extension_entry.insert(0, self.suffix)
        self.configure_extension()
        self.entry_separator = ttk.Separator(self.configurations_frame, orient=VERTICAL)
        self.folder_entry = Entry(self.configurations_frame, font='Helvetica 10',
                                  highlightbackground='black', highlightthickness=1)
        self.folder_entry.bind('<Enter>', lambda _=None: ToolTip(self.folder_entry, 'Helvetica 8',
                                                                 msg=self.folder_entry.get(), follow=False))
        self.folder_entry.insert(0, self.rootdir)
        self.browse_button = Button(self.configurations_frame, font='Helvetica 10', text='Browse',
                                    command=self.select_rootdir)
        self.browse_button.bind('<Enter>', lambda _=None: ToolTip(
            self.browse_button, 'Helvetica 8', msg='Select the folder to search in.\n(default folder will be the'
                                                   ' original\npython.exe containing folder)', follow=False))

        self.frame_separator = ttk.Separator(self, orient=HORIZONTAL)

        self.v_scrollbar = Scrollbar(self.result_frame)
        self.h_scrollbar = Scrollbar(self.result_frame, orient=HORIZONTAL)
        self.result_tree = ttk.Treeview(self.result_frame, yscrollcommand=self.v_scrollbar.set,
                                        xscrollcommand=self.h_scrollbar.set)
        self.result_tree['columns'] = ['0', '1', '2']
        self.result_tree['show'] = 'headings'
        self.heading_list = ['File', 'Line No', 'Line Preview']
        for i in range(len(self.heading_list)):
            self.result_tree.heading(str(i), text=self.heading_list[i])
        self.result_tree.column('0', width=1000, anchor=W)
        self.result_tree.column('1', width=100, anchor=N)
        self.result_tree.column('2', width=500, anchor=W)
        self.v_scrollbar.config(command=self.result_tree.yview)
        self.h_scrollbar.config(command=self.result_tree.xview)

        self.style = ttk.Style()
        self.style.configure("Treeview.Heading", font=('Helvetica', 10))
        self.style.configure("Treeview.Column", font=('Consolas', 12))

        self.description_frame = Frame(self.result_frame, highlightbackground='black', highlightthickness=1)
        self.desc_label = Label(self.description_frame, font='Consolas 10', justify=LEFT, highlightbackground='black',
                                highlightthickness=1, fg='gray50',
                                text='Double Click on any row to open in EZ_PY or right click for more options')
        self.searching_label = Label(self.description_frame, font='Consolas 10', justify=LEFT, fg='gray30',
                                     text='Press "Search" or hit Enter key to search', width=40)
        self.searching_label.bind('<Enter>', self.on_searching_label_enter)
        self.searching_label.bind('<Leave>', self.on_searching_label_leave)
        self.searching_label.bind('<ButtonPress-1>', lambda _=None: self.searching_label.config(fg='black'))
        self.searching_label.bind('<ButtonRelease-1>', lambda _=None: [self.on_searching_label_button_1(_),
                                                                       self.searching_label.config(fg='gray30')])

        self.clear_label = Label(self.description_frame, text='Clear Results', font='Consolas 10', fg='gray30',
                                 justify=LEFT)
        self.clear_label.bind('<Enter>', lambda _=None: self.clear_label.config(font='Consolas 10 underline',
                                                                                cursor='hand2'))
        self.clear_label.bind('<Leave>', lambda _=None: self.clear_label.config(font='Consolas 10'))
        self.clear_label.bind('<ButtonPress-1>', lambda _=None: self.clear_label.config(fg='black'))
        self.clear_label.bind('<ButtonRelease-1>', lambda _=None: [self.clear_result_tree(_),
                                                                   self.clear_label.config(fg='gray30')])

        self.result_count_label = Label(self.description_frame, font='Consolas 10', justify=LEFT, fg='gray30',
                                        text='Files Searched: None\t\tHits: None\nFolders Searched: None\t\tFiles'
                                             ' Skipped: None')

        self.create_widgets()
        self.center_window(self)

        self.threads = []

    def _create_threads(self, target_list: list):
        """
        `target_list` should contain a list of dict objects and
        in each dict object there should be three key-value pairs:

        `target`: the target method or function
        `args`:   args for the `target`
        `kwargs`: kwargs for the `target`
        """
        del self.threads
        self.threads = []

        for target in target_list:
            if not isinstance(target['args'], tuple):
                raise ValueError('args for a function should be in a tuple form')
            if not isinstance(target['kwargs'], dict):
                raise ValueError('kwargs for a function should be in a dictionary form')
            if not isinstance(target['target'], object):
                raise ValueError('target should be a function')
            self.threads.append(threading.Thread(target=target['target'], args=target['args'], kwargs=target['kwargs']))

    @staticmethod
    def center_window(win: Tk or Toplevel):
        """
        centers a tkinter window
        :param win: the main window or Toplevel window to center
        """
        win.update_idletasks()
        width = win.winfo_width()
        frm_width = win.winfo_rootx() - win.winfo_x()
        win_width = width + 2 * frm_width
        height = win.winfo_height()
        titlebar_height = win.winfo_rooty() - win.winfo_y()
        win_height = height + titlebar_height + frm_width
        x = win.winfo_screenwidth() // 2 - win_width // 2
        y = win.winfo_screenheight() // 2 - win_height // 2
        win.geometry('+{}+{}'.format(x, y))
        win.deiconify()

    def clear_result_tree(self, event=None):
        self.search_results = None
        self.result_tree.delete(*self.result_tree.get_children())
        self.search_entry.delete(0, END)
        self.searching_label.config(text='Press "Search" or hit Enter key to search', font='Consolas 10',
                                    width=41, cursor='')
        self.searching = FALSE
        self._update()

    def configure_extension(self, event=None):
        if self.extension_intvar.get() == 0:
            self.extension_entry.config(state=DISABLED)
        else:
            self.extension_entry.config(state=NORMAL)

    def create_widgets(self):
        self.title_frame.pack(side=TOP, fill=X)
        self.title_label.pack(side=LEFT)
        self.exit_label.pack(side=RIGHT)
        self.entry_frame.pack(side=TOP, fill=X, padx=2, pady=2)
        self.frame_separator.pack(fill=BOTH, pady=10, padx=2)
        self.result_frame.pack(side=BOTTOM, fill=BOTH, expand=True, padx=2, pady=2)
        self.configurations_frame.pack(side=BOTTOM, fill=X, pady=2, padx=2)
        self.extension_checkbutton.pack(side=LEFT, padx=2, pady=2)
        self.extension_entry.pack(side=LEFT, padx=2, pady=2, ipady=2)
        self.browse_button.pack(side=RIGHT, padx=2, pady=2)
        self.folder_entry.pack(side=RIGHT, pady=2, padx=2, ipady=2, fill=X, expand=True)
        self.entry_separator.pack(side=RIGHT, pady=2, padx=3, fill=BOTH)
        self.search_entry.pack(side=LEFT, fill=X, expand=True, padx=2, pady=2, ipady=4)
        self.search_button.pack(side=RIGHT, padx=2, pady=2)
        self.description_frame.pack(side=BOTTOM, fill=BOTH, padx=2, pady=2)
        self.desc_label.pack(side=BOTTOM, anchor=W, expand=True)
        self.searching_label.pack(side=BOTTOM, anchor=W, padx=2, pady=2, expand=True)
        self.clear_label.pack(side=BOTTOM, anchor=W, padx=2, pady=2, expand=True)
        self.result_count_label.pack(side=BOTTOM, anchor=W, padx=2, pady=2, expand=True)
        self.v_scrollbar.pack(side=RIGHT, fill=BOTH, padx=2, pady=2)
        self.h_scrollbar.pack(side=BOTTOM, fill=BOTH, padx=2, pady=2)
        self.result_tree.pack(side=BOTTOM, fill=BOTH, expand=True, padx=2, pady=2)

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def insert_search_results(self, event=None):
        try:
            # print('>', tuple(self.result_tree.item(self.result_tree.get_children()[-1])['values']))
            # print('>>>', tuple(self.search_results.results[-1]))
            if tuple(self.result_tree.item(self.result_tree.get_children()[-1])['values']) != tuple(
                    self.search_results.results[-1]
            ):
                self.result_tree.insert('', self.tree_index, self.tree_iid, values=self.search_results.results[-1])

        except IndexError:
            try:
                self.result_tree.insert('', self.tree_index, self.tree_iid, values=self.search_results.results[-1])
            except IndexError:
                pass

        self.tree_index = self.tree_iid = self.tree_index + 1
        # self.result_tree.yview_moveto(1)
        if self.searching == TRUE:
            self.after(1, self.insert_search_results)
        elif self.searching == FALSE:
            del self.threads
            self.threads = []
        elif self.searching == DONE:
            del self.threads
            self.threads = []

    def insert_skipped_files(self, event=None):
        self.searching_label.config(text='Inserting Skipped Files...')
        self.result_tree.delete(*self.result_tree.get_children())
        for value in self.search_results.skipped:
            self.result_tree.insert('', self.tree_index, self.tree_iid, values=(value, '', ''))
            self.tree_index = self.tree_iid = self.tree_index + 1

    def insert_result(self, event=None):
        self.result_tree.delete(*self.result_tree.get_children())
        for value in self.search_results.results:
            self.result_tree.insert('', self.tree_index, self.tree_iid, values=value)
            self.tree_index = self.tree_iid = self.tree_index + 1

    def on_searching_label_button_1(self, event=None):
        if self.searching == TRUE:
            self.searching = FALSE
            self.search_results = None
        elif self.searching == DONE:
            if self.searching_label.cget('text') == 'Show Skipped Files':
                self.insert_skipped_files()

    def on_searching_label_enter(self, event=None):
        if self.searching == TRUE:
            self.searching_label.config(cursor='hand2')
            self.searching_label.config(text='Stop?', font='Consolas 10 underline', width=12)
        elif self.searching == DONE:
            self.searching_label.config(cursor='hand2')
            self.searching_label.config(text='Show Skipped Files', font='Consolas 10 underline', width=18)

    def on_searching_label_leave(self, event=None):
        if self.searching == TRUE:
            self.searching_label.config(text='Searching...', font='Consolas 10', width=12)
        elif self.searching == FALSE:
            self.searching_label.config(text='Press "Search" or hit Enter key to search', font='Consolas 10',
                                        width=41, cursor='')
        else:
            self.searching_label.config(text='Search Complete!', font='Consolas 10', width=16)

    def search(self, event=None):
        self.result_tree.delete(*self.result_tree.get_children())

        string_to_search = self.search_entry.get()
        suffix = None
        if self.extension_intvar.get() == 1:
            suffix = self.extension_entry.get()
        rootdir = self.folder_entry.get() if len(self.folder_entry.get()) > 1 else self.rootdir
        if not os.path.isdir(rootdir):
            tk_mb.showerror('Search in Files', f'Folder "{rootdir}" does not exist. Please check the address again.')
            return
        if suffix is not None:
            self._create_threads(
                [
                    {'target': self.search_with_extension, 'args': (string_to_search, rootdir, suffix), 'kwargs': {}},
                    {'target': self.insert_search_results, 'args': (),                                  'kwargs': {}},
                    {'target': self._update,               'args': (),                                  'kwargs': {}}
                ]
            )
        else:
            self._create_threads(
                [
                    {'target': self.search_without_extension, 'args': (string_to_search, rootdir), 'kwargs': {}},
                    {'target': self.insert_search_results,    'args': (),                          'kwargs': {}},
                    {'target': self._update,                  'args': (),                          'kwargs': {}}
                ]
            )
        for process in self.threads:
            process.start()

    def search_with_extension(self, string_to_search, rootdir=None, suffix=None):
        """
        Get line from files with suffix as file type along with line numbers,
        which contain the string
        """
        del self.search_results
        self.search_results = self.Results()
        if not rootdir:
            rootdir = self.rootdir
        if not suffix:
            suffix = self.suffix

        self.searching = TRUE
        self.searching_label.config(text='Searching...', font='Consolas 10', width=12)

        result = []
        skipped = []
        files_searched = 0
        files_skipped = 0
        folders_searched = 0

        limit = 30 + len(string_to_search) + 30
        for folder, dirs, files in os.walk(rootdir):
            folders_searched += 1
            for file in files:
                files_searched += 1
                if file.endswith(suffix):
                    fullpath = os.path.join(folder, file)
                    line_number = 0
                    with open(fullpath, 'r', encoding='utf-8') as f:
                        try:
                            for line in f:
                                if self.searching == TRUE:
                                    line_number += 1
                                    if line.__contains__(string_to_search):
                                        ind = line.find(string_to_search)
                                        start = ind - 30 if ind > limit else 0
                                        end = ind + 30 if ind > limit else limit
                                        result.append((os.path.abspath(fullpath), line_number, line[start:end]))
                                        self.search_results.results = result
                                        self.search_results.total_hits = len(result)
                                        break
                        except UnicodeDecodeError:
                            files_skipped += 1
                            skipped.append(os.path.abspath(fullpath))
                            continue
                        self.search_results.files_skipped = files_skipped
                self.search_results.files_searched = files_searched
            self.search_results.folders_searched = folders_searched

        self.searching = DONE
        self.searching_label.config(text='Search Complete!', font='Consolas 10', width=16)
        self.search_results.searched_keyword = string_to_search
        self.search_results.searched_dir = rootdir
        self.search_results.skipped = skipped
        self.search_results.files_searched = files_searched
        self.search_results.files_skipped = files_skipped
        self.search_results.total_hits = len(result)
        self.search_results.folders_searched = folders_searched

        self.search_history.append(self.search_results)

    def search_without_extension(self, string_to_search, rootdir=None):
        """
        Get line from files as file type along with line numbers,
        which contain the string
        """
        del self.search_results
        self.search_results = self.Results()
        if not rootdir:
            rootdir = self.rootdir

        self.searching = TRUE
        self.searching_label.config(text='Searching...', font='Consolas 10', width=12)

        result = []
        skipped = []
        files_searched = 0
        files_skipped = 0
        folders_searched = 0

        limit = 30 + len(string_to_search) + 30
        for folder, dirs, files in os.walk(rootdir):
            folders_searched += 1
            for file in files:
                files_searched += 1
                fullpath = os.path.join(folder, file)
                line_number = 0
                with open(fullpath, 'r', encoding='utf-8') as f:
                    try:
                        for line in f:
                            if self.searching == TRUE:
                                line_number += 1
                                if line.__contains__(string_to_search):
                                    ind = line.find(string_to_search)
                                    start = ind - 30 if ind > limit else 0
                                    end = ind + 30 if ind > limit else limit
                                    result.append((os.path.abspath(fullpath), line_number, line[start:end]))
                                    self.search_results.results = result
                                    self.search_results.total_hits = len(result)
                                    break
                    except UnicodeDecodeError:
                        files_skipped += 1
                        skipped.append(fullpath)
                        continue
                    self.search_results.files_skipped = files_skipped
                self.search_results.files_searched = files_searched
            self.search_results.folders_searched = folders_searched

        self.searching = DONE
        self.searching_label.config(text='Search Complete!', font='Consolas 10', width=16)
        self.search_results.searched_keyword = string_to_search
        self.search_results.searched_dir = rootdir
        self.search_results.skipped = skipped
        self.search_results.files_searched = files_searched
        self.search_results.files_skipped = files_skipped
        self.search_results.total_hits = len(result)
        self.search_results.folders_searched = folders_searched
        self.search_history.append(self.search_results)

    def select_rootdir(self):
        askdir = tk_fd.askdirectory()
        if len(askdir) > 0:
            self.rootdir = askdir
        self.folder_entry.delete(0, END)
        self.folder_entry.insert(0, self.rootdir)

    @staticmethod
    def set_appwindow(_root):
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080

        hwnd = windll.user32.GetParent(_root.winfo_id())
        style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        style = style & ~WS_EX_TOOLWINDOW
        style = style | WS_EX_APPWINDOW
        res = windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
        # re-assert the new window style
        _root.wm_withdraw()
        _root.after(10, lambda: _root.wm_deiconify())

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def _update(self, event=None):
        try:
            self.result_count_label.config(text=f'Files Searched: {self.search_results.files_searched}\t\t'
                                                f'Hits: {self.search_results.total_hits}\n'
                                                f'Folders Searched: {self.search_results.folders_searched}\t\t'
                                                f'Files Skipped: {self.search_results.files_skipped}')
        except AttributeError:
            pass
        self.search_entry.config(state=DISABLED)
        self.search_button.config(state=DISABLED)
        self.extension_entry.config(state=DISABLED)
        self.folder_entry.config(state=DISABLED)
        self.extension_checkbutton.config(state=DISABLED)
        self.browse_button.config(state=DISABLED)
        if self.searching == TRUE:
            self.after(10, self._update)
        elif self.searching == FALSE:
            self.search_entry.config(state=NORMAL)
            self.search_button.config(state=NORMAL)
            self.extension_entry.config(state=NORMAL)
            self.folder_entry.config(state=NORMAL)
            self.extension_checkbutton.config(state=NORMAL)
            self.browse_button.config(state=NORMAL)
            self.result_count_label.config(text='Files Searched: None\t\tHits: None\nFolders Searched: None\t\tFiles'
                                                ' Skipped: None')


class SearchHistory(list):
    pass


def main():
    FindInFiles()
    mainloop()


if __name__ == '__main__':
    main()
    # sr1 = s.search_without_extension('abc', '..')
    # print(sr1.files_searched, sr1.files_skipped, sr1.total_hits)
    # sr2 = s.search_with_extension('abc', '..')
    # print(sr2.files_searched, sr2.files_skipped, sr2.total_hits)
