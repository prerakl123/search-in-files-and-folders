import threading
from tkinter import ttk
from tkinter import *
import tkinter as tk
from tkinter import filedialog as tk_fd
from tkinter import messagebox as tk_mb
import os
import sys
import time
from ctypes import windll

FALSE = False
TRUE = True
DONE = 'Done'


class PlaceHolderEntry(Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color='grey', **kwargs):
        Entry.__init__(self, master, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()


class ToolTip(tk.Toplevel):
    """
    Provides a ToolTip widget for tkinter.
    To apply a ToolTip to any tkinter widget, simply pass the widget to the
    ToolTip constructor
    """
    def __init__(self, wdgt, tooltip_font, msg=None, msgfunc=None, delay=0.5, follow=True):
        """
        Initialize the ToolTip

        Arguments:
          wdgt:         The widget this ToolTip is assigned to
          tooltip_font: Font to be used
          msg:          A static string message assigned to the ToolTip
          msgfunc:      A function that retrieves a string to use as the ToolTip text
          delay:        The delay in seconds before the ToolTip appears(may be float)
          follow:       If True, the ToolTip follows motion, otherwise hides
        """
        self.wdgt = wdgt

        # The parent of the ToolTip is the parent of the ToolTip's widget
        self.parent = self.wdgt.master
        
        # Initalise the Toplevel
        tk.Toplevel.__init__(self, self.parent, bg='black', padx=1, pady=1)
        
        # Hide initially
        self.withdraw()

        # The ToolTip Toplevel should have no frame or title bar
        self.overrideredirect(True)

        # ToolTip should be displayed on the top of everything
        self.wm_attributes('-topmost', True)

        # The msgVar will contain the text displayed by the ToolTip
        self.msgVar = tk.StringVar()
        if msg is None:
            self.msgVar.set('No message provided')
        else:
            self.msgVar.set(msg)

        self.msgFunc = msgfunc
        self.delay = delay
        self.follow = follow
        self.visible = 0
        self.lastMotion = 0
        # The text of the ToolTip is displayed in a Message widget
        tk.Message(self, textvariable=self.msgVar, bg='#FFFFDD', font=tooltip_font, aspect=1000).grid()

        # Add bindings to the widget.  This will NOT override
        # bindings that the widget already has
        self.wdgt.bind('<Enter>', self.spawn, '+')
        self.wdgt.bind('<Leave>', self.hide, '+')
        self.wdgt.bind('<Motion>', self.move, '+')

    def spawn(self, event=None):
        """
        Spawn the ToolTip.  This simply makes the ToolTip eligible for display.
        Usually this is caused by entering the widget

        Arguments:
          event: The event that called this funciton
        """
        self.visible = 1
        # The after function takes a time argument in milliseconds
        self.after(int(self.delay * 1000), self.show)

    def show(self):
        """
        Displays the ToolTip if the time delay has been long enough
        """
        if self.visible == 1 and time.time() - self.lastMotion > self.delay:
            self.visible = 2
        if self.visible == 2:
            self.deiconify()

    def move(self, event):
        """
        Processes motion within the widget.
        Arguments:
          event: The event that called this function
        """
        try:
            self.lastMotion = time.time()
            # If the follow flag is not set, motion within the
            # widget will make the ToolTip disappear
            #
            if self.follow is False:
                self.withdraw()
                self.visible = 1

            # Offset the ToolTip some pixels away form the pointer
            # screen_hw = (int(self.wdgt.winfo_screenheight()), int(self.wdgt.winfo_screenwidth()))
            # if tuple((screen_hw[0]-100, screen_hw[1]-100)) < self.wdgt.winfo_pointerxy() < screen_hw or \
            #         tuple(reversed(tuple((screen_hw[0]-100, screen_hw[1]-100)))) < \
            #         tuple(reversed(self.wdgt.winfo_pointerxy())) < tuple(reversed(screen_hw)):
            # self.geometry('+%i+%i' % (event.x_root-int(len(self.msgVar.get())), event.y_root-10))
            # else:
            self.geometry('+%i+%i' % (event.x_root+8, event.y_root+18))
            try:
                # Try to call the message function.  Will not change
                # the message if the message function is None or
                # the message function fails
                self.msgVar.set(self.msgFunc())
            except:
                pass
            self.after(int(self.delay * 1000), self.show)
        except Exception:
            pass

    def hide(self, event=None):
        """
        Hides the ToolTip.  Usually this is caused by leaving the widget
        Arguments:
          event: The event that called this function
        """
        self.visible = 0
        # self.withdraw()
        self.destroy()

    def _update(self, msg):
        """
        Updates the Tooltip with a new message.
        """
        self.msgVar.set(msg)


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
        self.after(100, lambda: self.bind_all('<Control-e>', lambda _=None: self.search_entry.focus_force()))
        self.after(100, lambda: self.bind_all('<F4>', lambda _=None: self.folder_entry.focus_force()))
        self.after(100, lambda: self.bind_all('<Control-w>', lambda _=None: self.destroy()))

        self.ez_py = ez_py
        self.search_history = SearchHistory()
        self.search_results = self.Results()
        self.x = None
        self.y = None
        self.tree_iid = 0
        self.last_search_index = 0
        self.start_time = None
        self.end_time = None
        self.search_time = ''

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
        self.search_entry = PlaceHolderEntry(self.entry_frame, placeholder='Enter keyword to be searched...', color='gray64',
                                             font='Helvetica 12', highlightbackground='black', highlightthickness=1)
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

        self.search_button.bind('<Enter>', set_search_tooltip)

        self.extension_intvar = IntVar()
        self.subfolder_intvar = IntVar()
        self.configurations_frame = Frame(self.entry_frame)
        self.extension_checkbutton = Checkbutton(self.configurations_frame, text='Search with specific extension : ',
                                                 variable=self.extension_intvar, onvalue=1, offvalue=0,
                                                 command=self.configure_extension, font='Helvetica 11')
        self.extension_entry = Entry(self.configurations_frame, width=7, font='Helvetica 10')
        self.extension_entry.bind('<Enter>', lambda _=None: ToolTip(
            self.extension_entry, 'Helvetica 8', msg='Extensions are case specific! Providing extensions\nwithout'
                                                     ' a dot may give results for files ending\nwith the provided'
                                                     ' entry', delay=0.7, follow=False))
        self.extension_entry.insert(0, self.suffix)
        self.configure_extension()
        # self.entry_separator = ttk.Separator(self.configurations_frame, orient=VERTICAL)
        self.search_in_subfolders_checkbutton = Checkbutton(self.configurations_frame, variable=self.subfolder_intvar,
                                                            text='Search in all folders and subfolders', onvalue=1,
                                                            offvalue=0, font='Helvetica 11', width=25)
        self.folder_frame = Frame(self.configurations_frame)
        self.folder_entry = Entry(self.folder_frame, font='Helvetica 10', highlightbackground='black',
                                  highlightthickness=1)
        self.folder_entry.insert(0, self.rootdir)
        self.browse_button = Button(self.folder_frame, font='Helvetica 10', text='Browse', command=self.select_rootdir)
        self.browse_button.bind('<Enter>', lambda _=None: ToolTip(
            self.browse_button, 'Helvetica 8', msg='Select the folder to search in.\n(default folder will be the'
                                                   ' \n.exe containing folder)', follow=False))

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

        self.description_frame = Frame(self.result_frame)
        self.files_searched_label = Label(self.description_frame, text='Files Searched: None', font='Consolas 10',
                                          fg='gray30', anchor=W, justify=LEFT)
        self.folders_searched_label = Label(self.description_frame, text='Folders Searched: None', font='Consolas 10',
                                            fg='gray30', anchor=W, justify=LEFT)
        self.hits_label = Label(self.description_frame, font='Consolas 10', text='Hits: None', fg='gray30',
                                anchor=W, justify=LEFT)
        self.files_skipped_label = Label(self.description_frame, font='Consolas 10', text='Files Skipped: None',
                                         fg='gray30', anchor=W, justify=LEFT)
        self.search_time_label = Label(self.description_frame, text='Elapsed Time: None', font='Consolas 10',
                                       fg='gray30', anchor=W, justify=LEFT)
        self.start_time_label = Label(self.description_frame, text='Search Started At: None', font='Consolas 10',
                                      fg='gray30', anchor=W, justify=LEFT)
        self.end_time_label = Label(self.description_frame, text='Search Ended At: None', font='Consolas 10',
                                    fg='gray30', anchor=W, justify=LEFT)
        self.reset_label = Label(self.description_frame, text='Reset Search Fields', font='Consolas 10', anchor=W,
                                 justify=LEFT, fg='RoyalBlue4')
        self.clear_results_label = Label(self.description_frame, font='Consolas 10', text='Clear Results and Reset',
                                         fg='RoyalBlue4', anchor=W, justify=LEFT)
        self.stop_label = Label(self.description_frame, text='Stop Search', font='Consolas 10', fg='RoyalBlue4',
                                anchor=W, justify=LEFT)
        self.show_skipped_files_label = Label(self.description_frame, text='Show Skipped Files', font='Consolas 10',
                                              fg='RoyalBlue4', anchor=W, justify=LEFT)

        self.reset_label.bind('<Enter>', lambda _=None: self.reset_label.config(font='Consolas 10 underline',
                                                                                cursor='hand2'))
        self.reset_label.bind('<Leave>', lambda _=None: self.reset_label.config(font='Consolas 10'))
        self.reset_label.bind('<ButtonPress-1>', lambda _=None: self.reset_label.config(fg='black'))
        self.reset_label.bind('<ButtonRelease-1>', self.reset)

        self.clear_results_label.bind('<Enter>', lambda _=None: self.clear_results_label.config(
            font='Consolas 10 underline', cursor='hand2'))
        self.clear_results_label.bind('<Leave>', lambda _=None: self.clear_results_label.config(font='Consolas 10'))
        self.clear_results_label.bind('<ButtonPress-1>', lambda _=None: self.clear_results_label.config(fg='black'))
        self.clear_results_label.bind('<ButtonRelease-1>', self.reset_and_clear)

        self.stop_label.bind('<Enter>', lambda _=None: self.stop_label.config(
            font='Consolas 10 underline', cursor='hand2'))
        self.stop_label.bind('<Leave>', lambda _=None: self.stop_label.config(font='Consolas 10'))
        self.stop_label.bind('<ButtonPress-1>', lambda _=None: self.stop_label.config(fg='black'))
        self.stop_label.bind('<ButtonRelease-1>', self.stop)

        self.show_skipped_files_label.bind('<Enter>', lambda _=None: self.show_skipped_files_label.config(
            font='Consolas 10 underline', cursor='hand2'))
        self.show_skipped_files_label.bind('<Leave>', lambda _=None: self.show_skipped_files_label.config(
            font='Consolas 10'))
        self.show_skipped_files_label.bind('<ButtonPress-1>', lambda _=None: self.show_skipped_files_label.config(
            fg='black'))
        self.show_skipped_files_label.bind('<ButtonRelease-1>', self.show_skipped_files)

        self._create_widgets()
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

    def _create_widgets(self):
        self.title_frame.pack(side=TOP, fill=X)
        self.title_label.pack(side=LEFT)
        self.exit_label.pack(side=RIGHT)
        self.entry_frame.pack(side=TOP, fill=X, padx=2, pady=2)
        self.frame_separator.pack(fill=BOTH, pady=5, padx=2)
        self.result_frame.pack(side=BOTTOM, fill=BOTH, expand=True, padx=2, pady=2)
        self.configurations_frame.pack(side=BOTTOM, fill=X, pady=2, padx=2)
        self.folder_frame.pack(side=BOTTOM, fill=X, padx=2, pady=2)
        self.extension_checkbutton.pack(side=LEFT, padx=2, pady=2)
        self.extension_entry.pack(side=LEFT, pady=2, ipady=2)
        self.search_in_subfolders_checkbutton.pack(side=LEFT, padx=28, pady=2, anchor=W)
        self.browse_button.pack(side=RIGHT, anchor=E, padx=2, pady=2)
        self.folder_entry.pack(side=RIGHT, anchor=W, pady=2, padx=2, ipady=2, fill=X, expand=True)
        # self.entry_separator.pack(side=RIGHT, pady=2, padx=3, fill=BOTH)
        self.search_entry.pack(side=LEFT, fill=X, expand=True, padx=2, pady=2, ipady=4)
        self.search_button.pack(side=RIGHT, padx=2, pady=2)

        self.description_frame.pack(side=BOTTOM, fill=BOTH, padx=2, pady=2)
        self.files_searched_label.grid(row=0, column=0, sticky=W, padx=20, pady=1)
        self.folders_searched_label.grid(row=1, column=0, sticky=W, padx=20, pady=1)
        self.hits_label.grid(row=2, column=0, sticky=W, padx=20, pady=1)
        self.files_skipped_label.grid(row=3, column=0, sticky=W, padx=20, pady=1)
        self.search_time_label.grid(row=0, column=1, sticky=W, padx=20, pady=1)
        self.start_time_label.grid(row=1, column=1, sticky=W, padx=20, pady=1)
        self.end_time_label.grid(row=2, column=1, sticky=W, padx=20, pady=1)
        self.reset_label.grid(row=0, column=2, sticky=W, padx=20, pady=1)
        self.clear_results_label.grid(row=1, column=2, sticky=W, padx=20, pady=1)
        self.stop_label.grid(row=2, column=2, sticky=W, padx=20, pady=1)
        self.show_skipped_files_label.grid(row=3, column=2, sticky=W, padx=20, pady=1)

        self.v_scrollbar.pack(side=RIGHT, fill=BOTH, padx=2, pady=2)
        self.h_scrollbar.pack(side=BOTTOM, fill=BOTH, padx=2, pady=2)
        self.result_tree.pack(side=BOTTOM, fill=BOTH, expand=True, padx=2, pady=2)

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
        self.searching = FALSE
        self._update()

    def configure_extension(self, event=None):
        if self.extension_intvar.get() == 0:
            self.extension_entry.config(state=DISABLED)
        else:
            self.extension_entry.config(state=NORMAL)

    def count_search_time_elapsed(self, event=None):
        if self.searching == TRUE:
            if self.start_time is not None:
                time_diff = time.time() - self.start_time[1]
                for unit in ['second', 'minute', 'hour']:
                    if time_diff / 60 < 1:
                        self.search_time = f"{round(time_diff)} {unit}s"
                        break
                    else:
                        time_diff /= 60
            self.after(100, self.count_search_time_elapsed)
        elif self.searching == FALSE:
            self.search_time = 0
        elif self.searching == DONE:
            self.search_time = 0

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def insert_search_results(self, event=None):
        """"""
        total_results = self.search_results.total_hits
        if total_results == 0:
            pass
        elif self.last_search_index == total_results:
            pass
        else:
            values = self.search_results.results[self.last_search_index:total_results]
            self.insert_search_results_into_tree(values=values)
            self.last_search_index = len(self.result_tree.get_children())

        if self.searching == TRUE:
            self.after(25, self.insert_search_results)
        elif self.searching == FALSE:
            del self.threads
            self.threads = []
            self.last_search_index = 0
        elif self.searching == DONE:
            del self.threads
            self.threads = []
            self.last_search_index = 0

    def insert_search_results_into_tree(self, event=None, values=None):
        for value in values:
            self.result_tree.insert('', END, self.tree_iid, values=value)
            self.tree_iid += 1

    def insert_result(self, event=None):
        self.result_tree.delete(*self.result_tree.get_children())
        for value in self.search_results.results:
            self.result_tree.insert('', END, self.tree_iid, values=value)
            self.tree_iid += 1

    def reset(self, event=None):
        self.search_entry.config(state=NORMAL)
        self.search_entry.delete(0, END)
        self.reset_label.config(fg='RoyalBlue4')

    def reset_and_clear(self, event=None):
        self.clear_results_label.config(fg='RoyalBlue4')
        self.search_entry.config(state=NORMAL)
        self.search_entry.delete(0, END)
        self.result_tree.delete(*self.result_tree.get_children())
        self.search_time_label.config(text='Elapsed Time: None')
        self.start_time_label.config(text='Search Started At: None')
        self.end_time_label.config(text='Search Ended At: None')
        self.files_searched_label.config(text='Files Searched: None')
        self.folders_searched_label.config(text='Folders Searched: None')
        self.files_skipped_label.config(text='Files Skipped: None')
        self.hits_label.config(text='Hits: None')
        self.clear_result_tree()

    def search(self, event=None):
        self.result_tree.delete(*self.result_tree.get_children())
        string_to_search = self.search_entry.get()
        suffix = None
        subfolders = False

        if self.extension_intvar.get() == 1:
            suffix = self.extension_entry.get()
        rootdir = self.folder_entry.get() if len(self.folder_entry.get()) > 1 else self.rootdir
        if self.subfolder_intvar.get() == 1:
            subfolders = True
        if not os.path.isdir(rootdir):
            tk_mb.showerror('Search in Files', f'Folder "{rootdir}" does not exist. Please check the address again.')
            return

        self._create_threads(
            [
                {'target': self.search_in_files, 'args': (string_to_search, rootdir, suffix, subfolders), 'kwargs': {}},
                {'target': self.insert_search_results, 'args': (), 'kwargs': {}},
                {'target': self._update, 'args': (), 'kwargs': {}},
                {'target': self.count_search_time_elapsed, 'args': (), 'kwargs': {}}
            ]
        )

        for process in self.threads:
            process.start()

    def search_in_files(self, string_to_search, rootdir=None, suffix=None, subfolders: bool = True):
        """
        Get line from files with suffix as file type along with line numbers,
        which contain the string
        """
        del self.search_results
        self.search_results = self.Results()
        if not rootdir:
            rootdir = self.rootdir

        self.start_time = [time.strftime('%H:%M:%S'), time.time()]
        self.searching = TRUE

        result = []
        skipped = []
        files_searched = 0
        files_skipped = 0
        folders_searched = 0

        limit = 30 + len(string_to_search) + 30
        if subfolders:
            for folder, dirs, files in os.walk(rootdir):
                folders_searched += 1
                for file in files:
                    files_searched += 1
                    if suffix is not None:
                        if file.endswith(suffix):
                            fullpath = os.path.join(folder, file)
                            line_number = 0
                            try:
                                with open(fullpath, 'r', encoding='utf-8') as f:
                                    try:
                                        for line in f:
                                            if self.searching == TRUE:
                                                line_number += 1
                                                if line.__contains__(string_to_search):
                                                    ind = line.find(string_to_search) + len(string_to_search)
                                                    start = ind - 30 if ind > limit else 0
                                                    end = ind + 30 if ind > limit else limit
                                                    result.append((os.path.abspath(fullpath), line_number,
                                                                   line[start:end]))
                                                    self.search_results.results = result
                                                    self.search_results.total_hits = len(result)
                                                    break
                                    except UnicodeDecodeError as uni_err:
                                        files_skipped += 1
                                        skipped.append((os.path.abspath(fullpath), uni_err))
                                        self.search_results.skipped = skipped
                                        continue
                                    self.search_results.files_skipped = files_skipped
                            except PermissionError as perm_err:
                                files_skipped += 1
                                skipped.append((os.path.abspath(fullpath), perm_err))
                                self.search_results.skipped = skipped
                                continue
                            self.search_results.files_skipped = files_skipped
                        self.search_results.files_searched = files_searched
                    else:
                        fullpath = os.path.join(folder, file)
                        line_number = 0
                        try:
                            with open(fullpath, 'r', encoding='utf-8') as f:
                                try:
                                    for line in f:
                                        if self.searching == TRUE:
                                            line_number += 1
                                            if line.__contains__(string_to_search):
                                                ind = line.find(string_to_search) + len(string_to_search)
                                                start = ind - 30 if ind > limit else 0
                                                end = ind + 30 if ind > limit else limit
                                                result.append((os.path.abspath(fullpath), line_number, line[start:end]))
                                                self.search_results.results = result
                                                self.search_results.total_hits = len(result)
                                                break
                                except UnicodeDecodeError as uni_err:
                                    files_skipped += 1
                                    skipped.append((os.path.abspath(fullpath), uni_err))
                                    self.search_results.skipped = skipped
                                    continue
                                self.search_results.files_skipped = files_skipped
                        except PermissionError as perm_err:
                            files_skipped += 1
                            skipped.append((os.path.abspath(fullpath), perm_err))
                            self.search_results.skipped = skipped
                            continue
                        self.search_results.files_skipped = files_skipped
                    self.search_results.files_searched = files_searched
                self.search_results.folders_searched = folders_searched
        else:
            self.search_results.folders_searched = 1
            for file in os.listdir(rootdir):
                if os.path.isdir(file):
                    pass
                else:
                    if suffix is not None:
                        files_searched += 1
                        if file.endswith(suffix):
                            fullpath = os.path.join(rootdir, file)
                            line_number = 0
                            try:
                                with open(fullpath, 'r', encoding='utf-8') as f:
                                    try:
                                        for line in f:
                                            if self.searching == TRUE:
                                                line_number += 1
                                                if line.__contains__(string_to_search):
                                                    ind = line.find(string_to_search) + len(string_to_search)
                                                    start = ind - 30 if ind > limit else 0
                                                    end = ind + 30 if ind > limit else limit
                                                    result.append(
                                                        (os.path.abspath(fullpath), line_number, line[start:end]))
                                                    self.search_results.results = result
                                                    self.search_results.total_hits = len(result)
                                                    break
                                    except UnicodeDecodeError as uni_err:
                                        files_skipped += 1
                                        skipped.append((os.path.abspath(fullpath), uni_err))
                                        self.search_results.skipped = skipped
                                        continue
                                    self.search_results.files_skipped = files_skipped
                            except PermissionError as perm_err:
                                files_skipped += 1
                                skipped.append((os.path.abspath(fullpath), perm_err))
                                self.search_results.skipped = skipped
                                continue
                            self.search_results.files_skipped = files_skipped
                        self.search_results.files_searched = files_searched
                    else:
                        files_searched += 1
                        fullpath = os.path.join(rootdir, file)
                        line_number = 0
                        try:
                            with open(fullpath, 'r', encoding='utf-8') as f:
                                try:
                                    for line in f:
                                        if self.searching == TRUE:
                                            line_number += 1
                                            if line.__contains__(string_to_search):
                                                ind = line.find(string_to_search) + len(string_to_search)
                                                start = ind - 30 if ind > limit else 0
                                                end = ind + 30 if ind > limit else limit
                                                result.append(
                                                    (os.path.abspath(fullpath), line_number, line[start:end]))
                                                self.search_results.results = result
                                                self.search_results.total_hits = len(result)
                                                break
                                except UnicodeDecodeError as uni_err:
                                    files_skipped += 1
                                    skipped.append((os.path.abspath(fullpath), uni_err))
                                    self.search_results.skipped = skipped
                                    continue
                                self.search_results.files_skipped = files_skipped
                        except PermissionError as perm_err:
                            files_skipped += 1
                            skipped.append((os.path.abspath(fullpath), perm_err))
                            self.search_results.skipped = skipped
                            continue
                        self.search_results.files_skipped = files_skipped
                        self.search_results.files_searched = files_searched

        self.searching = DONE
        self.end_time = [time.strftime('%H:%M:%S'), time.time()]

        self.search_results.searched_keyword = string_to_search
        self.search_results.searched_dir = rootdir
        self.search_results.skipped = skipped
        self.search_results.files_searched = files_searched
        self.search_results.files_skipped = files_skipped
        self.search_results.total_hits = len(result)
        self.search_results.folders_searched = folders_searched

        self.search_history.append(self.search_results)

    def select_rootdir(self):
        askdir = tk_fd.askdirectory(initialdir=self.folder_entry.get())
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

    def show_skipped_files(self, event=None):
        iid = 0
        skipped_files_window = Toplevel()
        skipped_files_window.transient(self)
        skipped_files_window.title('Skipped Files')
        skipped_files_window.geometry('900x500')
        v_scrollbar = Scrollbar(skipped_files_window)
        h_scrollbar = Scrollbar(skipped_files_window, orient=HORIZONTAL)
        skipped_files_tree = ttk.Treeview(skipped_files_window, yscrollcommand=v_scrollbar.set,
                                          xscrollcommand=h_scrollbar.set)
        skipped_files_tree['columns'] = ['0', '1']
        skipped_files_tree['show'] = 'headings'
        heading_list = ['Skipped File', 'Reason']
        skipped_files_tree.heading('0', text='Skipped File')
        skipped_files_tree.heading('1', text='Reason')
        skipped_files_tree.column('0', width=1000)
        skipped_files_tree.column('1', width=600)

        v_scrollbar.config(command=skipped_files_tree.yview)
        h_scrollbar.config(command=skipped_files_tree.xview)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        skipped_files_tree.pack(side=BOTTOM, fill=BOTH, expand=True)
        skipped_files_window.focus_force()
        try:
            for value in self.search_results.skipped:
                skipped_files_tree.insert('', END, iid, values=value)
                iid += 1
        except AttributeError:
            pass
        self.show_skipped_files_label.config(fg='RoyalBlue4')

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def stop(self, event=None):
        self.searching = FALSE
        self.stop_label.config(fg='RoyalBlue4')
        try:
            self.end_time_label.config(text=f"Search Ended At: {self.end_time[0]}")
        except TypeError or AttributeError or Exception:
            self.end_time_label.config(text=f"Search Ended At: {time.strftime('%H:%M:%S')}")

    def _update(self, event=None):
        try:
            self.files_searched_label.config(text=f'Files Searched: {self.search_results.files_searched}')
            self.hits_label.config(text=f'Hits: {self.search_results.total_hits}')
            self.folders_searched_label.config(text=f'Folders Searched: {self.search_results.folders_searched}')
            self.files_skipped_label.config(text=f'Files Skipped: {self.search_results.files_skipped}')
            self.search_time_label.config(text=f"Elapsed Time: {self.search_time}")
            self.start_time_label.config(text=f'Search Started At: {self.start_time[0]}')
            self.end_time_label.config(text='Search Ended At: ...')
        except AttributeError:
            pass
        self.search_entry.config(state=DISABLED)
        self.search_button.config(state=DISABLED)
        self.extension_entry.config(state=DISABLED)
        self.search_in_subfolders_checkbutton.config(state=DISABLED)
        self.folder_entry.config(state=DISABLED)
        self.extension_checkbutton.config(state=DISABLED)
        self.browse_button.config(state=DISABLED)
        if self.searching == TRUE:
            self.after(10, self._update)
        elif self.searching == DONE:
            self.end_time_label.config(text=f"Search Ended At: {self.end_time[0]}")
            self.search_entry.config(state=NORMAL)
            self.search_button.config(state=NORMAL)
            self.extension_entry.config(state=NORMAL)
            self.search_in_subfolders_checkbutton.config(state=NORMAL)
            self.folder_entry.config(state=NORMAL)
            self.extension_checkbutton.config(state=NORMAL)
            self.browse_button.config(state=NORMAL)
            self.search_time = ''
        elif self.searching == FALSE:
            self.search_entry.config(state=NORMAL)
            self.search_button.config(state=NORMAL)
            self.extension_entry.config(state=NORMAL)
            self.search_in_subfolders_checkbutton.config(state=NORMAL)
            self.folder_entry.config(state=NORMAL)
            self.extension_checkbutton.config(state=NORMAL)
            self.browse_button.config(state=NORMAL)
            self.search_time = ''


class SearchHistory(list):
    pass


def main():
    FindInFiles()
    mainloop()


if __name__ == '__main__':
    main()
