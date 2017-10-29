#!/usr/bin/python
# Python Steam scraper

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog
from functools import partial
import time
import SteamMiniParser_02 as smp


DEFAULT_DAYS = '3-15'
DEFAULT_REVIEWS = 10

class Application(tk.Frame):
    indie_switch_var = 0
    released_days_var = DEFAULT_DAYS
    reviews_var = DEFAULT_REVIEWS
    tags_var = ""
    pb_var = 0
    directory = "/"
    tags = ["Action", "Adventure", "Casual", "Massively Multiplayer", 
            "Racing", "RPG", "Simulation", "Sports", "Strategy",
            "Single-player", "Multi-player", "Online Multi-Player", "Local Multi-Player", 
            "Co-op", "Online Co-op", "Local Co-op," "Shared/Split Screen",
            "Demos", "Steam Workshop",
            "VR Only", "VR Supported"]

    def __init__(self, master = None):
        super().__init__(master)

        style = ttk.Style()
        style.configure("TButton", padding=2, width=6)

        Application.indie_switch_var = tk.IntVar(value=1)

        Application.released_days_var = tk.StringVar(value=DEFAULT_DAYS)
        Application.released_days_var.trace("w", partial(self.int_entry_callback,
                                                         var=Application.released_days_var, minval=0, maxval=1825))

        Application.reviews_var = tk.StringVar(value=DEFAULT_REVIEWS)
        Application.reviews_var.trace("w", partial(self.int_entry_callback,
                                                   var=Application.reviews_var, minval=0, maxval=100000))

        Application.pb_var = tk.IntVar()

        self.grid()
        self.create_widgets()
    
    def create_widgets(self):
        """Creates all GUI"""
        self.indie_switch = ttk.Checkbutton(text="Only indie", variable=Application.indie_switch_var, onvalue=1, offvalue=0)
        self.indie_switch.grid(row=0, columnspan=2)

        self.period_label = ttk.Label(text="Released (days) >")
        self.period_label.grid(row=1, column=0, sticky=tk.E)
        self.period_entry = ttk.Entry(textvariable=Application.released_days_var)
        self.period_entry.grid(row=1, column=1)

        self.reviews_label = ttk.Label(text="Reviews >")
        self.reviews_label.grid(row=2, column=0, sticky=tk.E)
        self.reviews_entry = ttk.Entry(textvariable=Application.reviews_var)
        self.reviews_entry.grid(row=2, column=1)

        self.tags_label = ttk.Label(text="Tags:")
        self.tags_label.grid(row=3, column=0, sticky=tk.E)
        self.tags_listbox = tk.Listbox(selectmode="extended", width=20, height=10)
        # self.scrollbar = tk.Scrollbar(self.tags_listbox, orient=tk.VERTICAL)
        # self.tags_listbox.config(yscrollcommand=self.scrollbar.set)
        self.tags_listbox.grid(row=3, column=1, sticky=tk.W)
        # self.scrollbar.grid(row=3, column=1, sticky=tk.E)
        self.add_tags(self.tags_listbox)

        self.get_button = ttk.Button(text="GET", style="TButton", command=self.get_apps)
        self.get_button.grid(row=4, column=0, sticky=tk.W)

        self.save_button = ttk.Button(text="SAVE", state=tk.DISABLED, style="TButton", command=self.save)
        self.save_button.grid(row=4, column=1, sticky=tk.E)

        self.progress_bar = ttk.Progressbar(length=220, variable=Application.pb_var)
        self.progress_bar.grid(row=5, columnspan=2)

        self.quit_button = ttk.Button(text="QUIT", command=self.quit_app)
        self.quit_button.grid(row=6, columnspan=2)

    def progress(self, number):
        self.progress_bar.step(number)
        self.update()

    def add_tags(self, listbox):
        """Get tags from Steam"""
        #tags = ["zero", "first", "second"]
        for tag in Application.tags:
            listbox.insert(tk.END, tag)

    def get_apps(self):
        """Get stats for specified games and convert it into .xlsx format. 
        3 steps:
            1. get_suitable_apps(b_indie, period_days, reviews_num, tags_list) - get games from Steam
            2. get_app_stats(appid) - stats for game from SteamSpy
            3. parse_to_xlsx(data) - write game stats in Excel format
        """
        period = self.period_entry.get()
        reviews = self.reviews_entry.get()
        if (not period) or (not reviews):
            print("fields is empty!")
            return
        
        gamestype = Application.indie_switch_var
        selected_tags = self.tags_listbox.curselection()
        tags = []
        for i in selected_tags:
            tags.append(self.tags_listbox.get(i))
        print(tags)
        print("GET")
        self.progress_bar.step()
        self.compl_label = ttk.Label(text="Completed")
        self.compl_label.grid(row=4, column=1, sticky=tk.W)
        self.save_button.state(["!disabled"])

        gl = smp.get_suitable_apps(gamestype, period.split('-'), tags, int(reviews), gui=self)

    def save(self):
        date = time.strftime("%d-%m-%Y")
        initfile = "steamscrap_" + date
        ftypes = (("xlsx files", "*.xlsx"), ("all files", "*.*"))
        f = tk.filedialog.asksaveasfile(initialdir=Application.directory, defaultextension=".xlsx",
                                        filetypes=ftypes, initialfile=initfile)
        if f is None:
            return
        lastidx = f.name.rfind("/")
        Application.directory = f.name[0:lastidx]
        print(Application.directory)
        f.close()
        

    def int_entry_callback(*args, var, minval, maxval):
        """Entry checker for int values in specified range"""
        value = var.get()
        if not value:
            print("empty")
            return
        if (not value.isdigit()) or (int(value) > maxval) or (int(value) < minval):
            var.set("")

    def quit_app(self):
        root.destroy()


def main():
    global root
    root = tk.Tk()
    root.title("Steam scraper")
    root.geometry("230x310")
    app = Application(master=root)
    app.mainloop()


if __name__ == "__main__":
    main()
