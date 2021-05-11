from time import time
import tkinter as tk
from tkinter import *


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
        if self.visible == 1 and time() - self.lastMotion > self.delay:
            self.visible = 2
        if self.visible == 2:
            self.deiconify()

    def move(self, event):
        """
        Processes motion within the widget.
        Arguments:
          event: The event that called this function
        """
        self.lastMotion = time()
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

    def hide(self, event=None):
        """
        Hides the ToolTip.  Usually this is caused by leaving the widget
        Arguments:
          event: The event that called this function
        """
        self.visible = 0
        self.withdraw()

    def _update(self, msg):
        """
        Updates the Tooltip with a new message.
        """
        self.msgVar.set(msg)


if __name__ == '__main__':
    root = Tk()
    b1 = Button(root, text='Button 1', width=10, height=2)
    b1.pack(anchor=N)
    ToolTip(b1, 'Consolas 12', 'This is a button -> Button-1')
    b2 = Button(root, text='Button 2', width=10, height=2)
    b2.pack(anchor=N)
    ToolTip(b2, 'Consolas 12', 'This is a button -> Button-2')
    b3 = Button(root, text='Button 2', width=10, height=2)
    b3.pack(anchor=N)
    ToolTip(b3, 'Consolas 12', 'This is a button -> Button-3')

    def show_info(_text):
        label.configure(text=_text)
        ttip = ToolTip(text_widget, 'Consolas 12', text, msgfunc=lambda a=None: label.cget('text'), follow=True)

    text_widget = tk.Text(root)
    label = tk.Label(root)

    label.pack(side="top", fill="x")
    text_widget.pack(fill="both", expand=True)

    color_list = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
    for color in color_list:
        tag = color
        text = color
        text_widget.insert("end", text+"\n", (tag, ))
        text_widget.tag_configure(tag, background=color, foreground="white")
        text_widget.tag_bind(tag, "<Enter>",
                             lambda event, _color=color: show_info(_color))
        text_widget.tag_bind(tag, "<Leave>",
                             lambda event, _color=color: show_info(""))

    root.mainloop()
