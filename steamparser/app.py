"""
SteamScraper - a simple Steam scraping app.

This module contains a simple UI.
"""

__version__ = '0.1'

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog
from functools import partial
import time
from datetime import date, datetime
import steam_parser as smp
import exporters as exps

DEFAULT_DAYS = '15-90'
DEFAULT_REVIEWS = 100
MAX_REVIEWS = 100000
SAVEAS_VALUES = ["xlsx", "csv ; (Excel)", "csv /t (GDrive)", "json"]


class Application(tk.Frame):
    released_days_var = DEFAULT_DAYS
    reviews_var = DEFAULT_REVIEWS
    tags_var = ''
    directory = '/'
    tags = ["Indie", "Action", "Adventure", "Casual", "Massively Multiplayer",
            "Racing", "RPG", "Simulation", "Sports", "Strategy",
            "Single-player", "Multi-player", "Online Multi-Player", "Local Multi-Player",
            "Co-op", "Online Co-op", "Local Co-op", "Shared/Split Screen",
            "Demos", "Steam Workshop",
            "VR Only", "VR Supported"]
    gl = None
    fr = None

    def __init__(self, master=None):
        super().__init__(master)

        style = ttk.Style()
        style.configure('TButton', padding=2, width=6)

        Application.released_days_var = tk.StringVar(value=DEFAULT_DAYS)
        Application.reviews_var = tk.StringVar(value=DEFAULT_REVIEWS)
        Application.reviews_var.trace('w', partial(self.int_entry_callback,
                                                   var=Application.reviews_var, minval=0, maxval=MAX_REVIEWS))

        self.grid()
        self.create_widgets()

    def create_widgets(self):
        """Creates all GUI"""
        UI_ROW = 0
        self.period_label = ttk.Label(text="Release period (days)")
        self.period_label.grid(row=UI_ROW, column=0, sticky=tk.E)
        self.period_entry = ttk.Entry(textvariable=Application.released_days_var)
        self.period_entry.grid(row=UI_ROW, column=1)

        UI_ROW += 1
        self.reviews_label = ttk.Label(text="Reviews >")
        self.reviews_label.grid(row=UI_ROW, column=0, sticky=tk.E)
        self.reviews_entry = ttk.Entry(textvariable=Application.reviews_var)
        self.reviews_entry.grid(row=UI_ROW, column=1)

        UI_ROW += 1
        self.tags_label = ttk.Label(text="Select tags:")
        self.tags_label.grid(row=UI_ROW, column=0, sticky=(tk.E, tk.N))
        self.tags_listbox = tk.Listbox(selectmode='extended', width=20, height=10)
        self.tags_listbox.grid(row=UI_ROW, column=1)
        self.scrollbar = ttk.Scrollbar(orient=tk.VERTICAL, command=self.tags_listbox.yview)
        self.scrollbar.grid(row=UI_ROW, column=1, sticky=(tk.E, tk.N, tk.S))
        self.tags_listbox.config(yscrollcommand=self.scrollbar.set)
        self.add_tags(self.tags_listbox)

        UI_ROW += 1
        self.save_as_label = ttk.Label(text="Save As: ")
        self.save_as_label.grid(row=UI_ROW, column=0, sticky=tk.E)
        self.save_method_cb = ttk.Combobox(values=SAVEAS_VALUES, width=17)
        self.save_method_cb.set(SAVEAS_VALUES[0])
        self.save_method_cb.grid(row=UI_ROW, column=1, sticky=tk.W)

        UI_ROW += 1
        self.get_button = ttk.Button(text="GET", style='TButton', command=self.get_apps)
        self.get_button.grid(row=UI_ROW, column=0, sticky=tk.W)

        self.save_button = ttk.Button(text="SAVE", state=tk.DISABLED, style='TButton', command=self.save)
        self.save_button.grid(row=UI_ROW, column=1, sticky=tk.E)

        UI_ROW += 1
        self.progress_bar = ttk.Progressbar(length=240)
        self.progress_bar.grid(row=UI_ROW, columnspan=2)

        UI_ROW += 1
        self.status_label = ttk.Label(text="", font='TkDefaultFont 9 bold')
        self.status_label.grid(row=UI_ROW, columnspan=2)

        UI_ROW += 1
        self.quit_button = ttk.Button(text="QUIT", command=self.quit_app)
        self.quit_button.grid(row=UI_ROW, columnspan=2)

    def add_tags(self, listbox):
        """Get tags from Steam"""
        for tag in Application.tags:
            listbox.insert(tk.END, tag)

    def get_apps(self):
        """Get stats for specified games and convert it into .xlsx format.
        3 steps:
            1. get_suitable_apps(period_range, reviews_num, tags_list, gui) - get games from Steam
            2. get_app_stats(appid) - stats for game from SteamSpy
            3. parse_to_xlsx(apps_data) - write game stats in Excel format
        """
        def clear():
            print("invalid release period input")
            self.status_label.config(text="Invalid input", foreground='red')
            Application.released_days_var.set("")

        # Period entry check
        first_date = date(2004, 11, 16)  # Half-Life 2 release date on Steam
        max_days = (datetime.now().date() - first_date).days
        period = self.period_entry.get().split('-')
        for p in period:
            if not p.isdigit():
                clear()
                return
        if len(period) > 1:
            cond = (len(period) > 2) \
                    or (int(period[0]) > int(period[1])) \
                    or (int(period[0]) not in range(0, max_days)) \
                    or (int(period[1]) not in range(0, max_days))
            if cond:
                clear()
                return
        elif (len(period) == 1) and (period[0] != ''):
            if int(period[0]) not in range(0, max_days):
                clear()
                return

        # Check if entries isn`t empty
        reviews = self.reviews_entry.get()
        if (not period) or (not reviews):
            print("fields is empty!")
            self.status_label.config(text="Invalid input", foreground='red')
            return

        selected_tags = self.tags_listbox.curselection()
        tags = []
        for i in selected_tags:
            tags.append(self.tags_listbox.get(i))
        print(tags)

        # Call functions here
        self.status_label.config(text="Getting data from Steam")
        Application.gl, Application.fr = smp.get_suitable_apps(period, tags, int(reviews), gui=self)
        #self.status_label.config(text="Adding extra info")
        self.status_label.config(text="Completed: " + str(len(Application.gl)) + " games")
        self.save_button.state(['!disabled'])

    def save(self):
        initfile = 'steamscrap_' + time.strftime('%d-%m-%Y_%H-%M')
        # Opens dialog with this parameters
        saveas = SAVEAS_VALUES[self.save_method_cb.current()]
        if saveas == SAVEAS_VALUES[0]:  # xlsx
            ftypes = (('xlsx files', '*.xlsx'), ('all files', '*.*'))
            extension = '.xlsx'
        elif (saveas == SAVEAS_VALUES[1]) or (saveas == SAVEAS_VALUES[2]):  # csv
            ftypes = (('csv files', '*.csv'), ('all files', '*.*'))
            extension = '.csv'
            if saveas == SAVEAS_VALUES[1]:  # semicolon delimiter
                sep = ';'
                initfile += '_sc'
            elif saveas == SAVEAS_VALUES[2]:  # tab delimiter
                sep = '\t'
                initfile += '_tab'
        elif saveas == SAVEAS_VALUES[3]:  # json
            ftypes = (('json files', '*.json'), ('all files', '*.*'))
            extension = '.json'

        f = tk.filedialog.asksaveasfile(initialdir=Application.directory, defaultextension=extension,
                                        filetypes=ftypes, initialfile=initfile)
        if f is None:
            return

        # Keep last dir in current session
        last_dir_id = f.name.rfind('/')
        Application.directory = f.name[0:last_dir_id+1]
        print(Application.directory)

        # Call save funcs
        if saveas == SAVEAS_VALUES[0]:  # xlsx
            exps.save_xlsx(filename=Application.directory+initfile,
                           table_info=Application.fr, games_list=Application.gl)
        elif (saveas == SAVEAS_VALUES[1]) or (saveas == SAVEAS_VALUES[2]):  # csv
            exps.save_csv(filename=Application.directory+initfile,
                          table_info=Application.fr, games_list=Application.gl, separator=sep)
        elif saveas == SAVEAS_VALUES[3]:  # json
            exps.save_json(filename=Application.directory+initfile)

        f.close()

    def progress(self, number):
        self.progress_bar.step(number)
        self.update()

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
    root.geometry('241x330')
    #root.iconbitmap('icon.ico')
    app = Application(master=root)
    app.mainloop()


if __name__ == '__main__':
    main()
