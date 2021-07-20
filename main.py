import argparse
import datetime
from enum import Enum
import os
import sys
import tkinter as tk
from tkinter import ttk
import urllib.parse
import webbrowser

from constants import EnterMode, ERASE
from utils.csv_reader import CSVReader
from utils.csv_reader_wrapper import CSVReaderWrapperWithWeakEstimator
from utils.char_label_reader import CharLabelReader
from utils.char_label_writer import CharLabelWriter
from utils.csv_writer import CSVWriter
from utils.decorator import mode

NUM_CHAR_PREVIEW_WIDGET = 4
NUM_ROWS_IN_CHAR_PREVIEW_WIDGET = 15
LABELLED_FILE_NAME = "labelled.txt"
CHAR_LABEL_FILE_NAME = "char_label.txt"


class Token:
    __slots__ = ["word", "first_index", "last_index"]

    def __init__(self, word: str, first_index: int, last_index: int):
        self.word = word
        self.first_index = first_index
        self.last_index = last_index

    def __str__(self):
        return f"{self.word} ({self.first_index}, {self.last_index})"


class AnnotatorApp:

    def __init__(self, input_path, output_dir):
        self.root = None
        self._input_path = input_path
        self._output_dir = output_dir

        # Prepare data
        self._data = CSVReaderWrapperWithWeakEstimator.from_file(path=input_path, sep="\t")
        assert "address" in self._data.get_header(), f"CSV file should have columns 'address'!"
        self._classes = ["prefecture", "city", "ward", "village", "chome", "block", "building", "unit", "floor"]

        # Output Files
        datetime_id = datetime.datetime.now().isoformat().replace(":", ".")
        self._output_path = os.path.join(output_dir, f"{datetime_id}_{LABELLED_FILE_NAME}")
        self._writer = CSVWriter(path=self._output_path, sep="\t", header=["sourceid", "address", *self._classes])
        self._char_label_output_path = os.path.join(output_dir, f"{datetime_id}_{CHAR_LABEL_FILE_NAME}")
        self._char_label_writer = CharLabelWriter(path=self._char_label_output_path)

        self._address = None
        self._address_index = -1

        self._refresh()

    def start(self, resume: bool = False):
        self._init_root()

        style = ttk.Style()
        style.configure("Treeview", font=("Helvetica", 14))
        style.configure("Treeview.Heading", font=("Helvetica", 14, "bold"))

        # Create widgets
        self._init_frames()
        self._init_address_widget()
        self._init_select_label_menu()
        self._init_next_address_widget()
        self._init_dict_preview_widgets()
        self._init_label_preview_widget()
        self._init_clear_widget()

        # Get first address
        self._next_address(write_to_file=False)

        # Start from previous attempt
        if resume:
            self._resume()

        # Start UI
        self.root.mainloop()

    def _resume(self):
        # Get latest path
        all_paths = os.listdir(self._output_dir)
        latest_labelled_path = os.path.join(self._output_dir, sorted((p for p in all_paths if p.endswith("_" + LABELLED_FILE_NAME)))[-2])
        latest_char_label_path = os.path.join(self._output_dir, sorted((p for p in all_paths if p.endswith("_" + CHAR_LABEL_FILE_NAME)))[-2])

        resume_labelled_data = CSVReader.from_file(path=latest_labelled_path, sep="\t")
        print(f"Read labelled data from {latest_labelled_path}.")
        resume_char_label_data = CharLabelReader.from_file(path=latest_char_label_path)
        print(f"Read char-wise label data from {latest_char_label_path}.")
        for i in range(len(resume_labelled_data)):
            labelled_record = resume_labelled_data.read_record(i)
            assert self._address == labelled_record["address"], \
                f"Address in resume record should be same as current input!\n  Expected: {self._address}\n  Actual: {labelled_record['address']}"

            address, char_labels = resume_char_label_data.read_record(i)
            assert self._address == address, \
                f"Address in resume record should be same as current input!\n  Expected: {self._address}\n  Actual: {address}"

            self._writer.append_dict(labelled_record)
            self._char_label_writer.append(address, char_labels)

            self._next_address(write_to_file=False, estimate=False)

    def _init_root(self):
        self.root = tk.Tk()
        self.root.geometry()
        self.root.title("AddressAnnotator")

    def _init_frames(self):
        self._top_frame = tk.Frame(self.root)
        self._middle_frame = tk.Frame(self.root)
        self._bottom_left_frame = tk.Frame(self.root)
        self._bottom_right_frame = tk.Frame(self.root)

        self._top_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W + tk.E, padx=10)
        self._middle_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W + tk.E, padx=10)
        self._bottom_left_frame.grid(row=2, column=0, sticky=tk.W + tk.E, padx=10)
        self._bottom_right_frame.grid(row=2, column=1, padx=10)

    def _init_address_widget(self):
        self.address_title_string_var = tk.StringVar()
        self.address_title = tk.Label(self._top_frame,
                                      textvariable=self.address_title_string_var,
                                      font=("Helvetica", 16, "bold"),
                                      anchor="w")

        self.address_text_widget = tk.Text(self._top_frame,
                                           height=1,
                                           borderwidth=2,
                                           relief="groove",
                                           font=("Helvetica", 24))

        self.address_text_widget.configure(inactiveselectbackground=self.address_text_widget.cget("selectbackground"))

        self.root.bind("<ButtonRelease-1>", self._callback_select_address_end)
        self.address_text_widget.bind("<Key>", lambda a: "break")
        self._bind_widget_to_mode(self.address_text_widget, EnterMode.TEXT_SELECT)

        self.address_link_widget = tk.Label(self._top_frame,
                                            text="Search on Google Map",
                                            cursor="hand2",
                                            fg="Blue",
                                            anchor="w")
        self.address_link_widget.bind("<Button-1>", lambda e: webbrowser.open_new(
            f"https://www.google.co.jp/maps/search/{urllib.parse.quote(self._address)}"))

        self.address_title.grid(row=0, column=0, sticky=tk.W)
        self.address_text_widget.grid(row=1, column=0)
        self.address_link_widget.grid(row=2, column=0, sticky=tk.W)

    @mode(EnterMode.TEXT_SELECT)
    def _callback_select_address_end(self, event):
        try:
            selected_text = self.address_text_widget.selection_get()
            print(selected_text)
            self._selected_token = selected_text
        except tk.TclError:
            pass

    def _init_next_address_widget(self):
        # Button widget to update address
        self.address_set_button = tk.Button(self._top_frame,
                                            text="Next Address",
                                            command=self._next_address,
                                            font=("Helvetica", 16))
        self.address_set_button.grid(row=1, column=1)

    def _next_address(self, write_to_file=True, estimate=True):
        # Write previous record if exists
        if write_to_file:
            # Write to CSV
            self._label_to_words["address"] = self._address
            self._label_to_words["sourceid"] = self._sourceid
            self._writer.append_dict(self._label_to_words)

            # Write to char-label txt file
            self._char_label_writer.append(self._address,
                                           [self._index_to_label.get(i, "o")
                                            for i in range(len(self._address))])

        self._refresh()

        # Read new address
        self._address_index += 1
        record = self._data.read_record(self._address_index, estimate=estimate)
        self._address = record["address"]
        self._sourceid = record["sourceid"]

        # Fill in pre-defined label
        found_index = set()
        for label in self._classes:
            if label in record:
                value = record[label]
                first_index = self._address.find(value)
                if first_index in found_index:
                    first_index = self._address[first_index+1:].find(value) + first_index + 1
                if first_index >= 0:
                    self._update(label, Token(value, first_index, first_index + len(value)))
                    found_index.add(first_index)

        # Update address text
        self.address_title_string_var.set(f"Input Address ({self._address_index + 1} / {len(self._data)})")
        self.address_text_widget.delete(1.0, "end")
        self.address_text_widget.insert(1.0, self._address)

        self._update_preview()

    def _init_select_label_menu(self):
        self._select_label_menu = tk.Menu(self.root, tearoff=False)
        for label in self._classes:
            self._select_label_menu.add_command(label=label, command=self._callback_select_label(label))
        self._select_label_menu.add_command(label=ERASE, command=self._callback_select_label(ERASE))
        self.root.bind("<ButtonRelease-1>", self._popup_label_menu)

    @mode(EnterMode.TEXT_SELECT)
    def _popup_label_menu(self, event):
        try:
            # Get selected text
            selected_text = self.address_text_widget.selection_get()

            # Get index of selected text
            first_index = self.address_text_widget.count("1.0", "sel.first")
            first_index = 0 if first_index is None else first_index[0]
            last_index = self.address_text_widget.count("1.0", "sel.last")
            last_index = 0 if last_index is None else last_index[0]

            self._selected_token = Token(selected_text, first_index, last_index)
        except tk.TclError:
            return
        # If text selected, then popup
        if (self._selected_token is not None) and (self._selected_token.word.strip() != ""):
            # Pop up window at (x, y) of event happening point
            self._select_label_menu.tk_popup(event.x_root, event.y_root)

    def _callback_select_label(self, label):
        def _set_label():
            self._update(label, self._selected_token)
        return _set_label

    def _update(self, label: str, token: Token):
        # Update char-wise label
        for i in range(token.first_index, token.last_index):
            if label == ERASE:
                self._index_to_label[i] = ""
            else:
                for i in range(token.first_index, token.last_index):
                    self._index_to_label[i] = label
        # Construct words based on char-wise label
        self._label_to_words = {label: "" for label in self._classes}
        for i, char in enumerate(self._address):
            label = self._index_to_label.get(i, "")
            if label in self._label_to_words:
                self._label_to_words[label] += char
        self._update_preview()

    def _init_dict_preview_widgets(self):
        self.dict_preview_title = tk.Label(self._middle_frame,
                                           text="Segments",
                                           font=("Helvetica", 16, "bold"),
                                           justify=tk.LEFT)
        self.dict_preview_title.pack(side=tk.TOP, anchor=tk.W)

        self._dict_preview_widgets = ttk.Treeview(self._middle_frame, height=2)

        self._dict_preview_widgets['columns'] = tuple(self._classes)
        # Column Format
        self._dict_preview_widgets.column('#0', width=0, stretch='no')
        for label in self._classes:
            self._dict_preview_widgets.column(label, anchor="w", width="110")
            self._dict_preview_widgets.heading(label, text=label, anchor="w")
        self._dict_preview_widgets.pack(anchor=tk.W)

    def _update_dict_label_preview(self):
        # Refresh
        for i in self._dict_preview_widgets.get_children():
            self._dict_preview_widgets.delete(i)

        # Insert
        self._dict_preview_widgets.insert(parent="", index=0, iid=0,
                                          values=[self._label_to_words[label] for label in self._classes])

    def _init_label_preview_widget(self):
        self.label_preview_title = tk.Label(self._bottom_left_frame,
                                            text="Char-wise Label",
                                            font=("Helvetica", 16, "bold"),
                                            anchor="w")
        self.label_preview_title.grid(row=0, column=0, sticky=tk.W)

        # Have multiple preview widget to show long address
        num_widget = NUM_CHAR_PREVIEW_WIDGET
        self._label_preview_widgets = [ttk.Treeview(self._bottom_left_frame, height=NUM_ROWS_IN_CHAR_PREVIEW_WIDGET)
                                       for _ in range(num_widget)]
        for i, _preview_widget in enumerate(self._label_preview_widgets):
            # Define column list
            _preview_widget['columns'] = ("Char", "Label")
            # Column Format
            _preview_widget.column('#0', width=0, stretch='no')
            _preview_widget.column("Char", anchor="w", width="60")
            _preview_widget.column("Label", anchor="w", width="180")
            # Column Header
            _preview_widget.heading("Char", text="Char", anchor="w")
            _preview_widget.heading("Label", text="Label", anchor="w")

            _preview_widget.grid(row=1, column=i)

    def _update_label_preview(self):
        # Refresh
        for _preview_widget in self._label_preview_widgets:
            for i in _preview_widget.get_children():
                _preview_widget.delete(i)

        # Insert
        for i, char in enumerate(self._address):
            if i >= NUM_CHAR_PREVIEW_WIDGET * NUM_ROWS_IN_CHAR_PREVIEW_WIDGET:
                break
            _widget = self._label_preview_widgets[i // NUM_ROWS_IN_CHAR_PREVIEW_WIDGET]
            if i in self._index_to_label:
                _widget.insert(parent="", index=i % NUM_ROWS_IN_CHAR_PREVIEW_WIDGET,
                               iid=i % NUM_ROWS_IN_CHAR_PREVIEW_WIDGET, values=(char, self._index_to_label[i]))
            else:
                _widget.insert(parent="", index=i % NUM_ROWS_IN_CHAR_PREVIEW_WIDGET,
                               iid=i % NUM_ROWS_IN_CHAR_PREVIEW_WIDGET, values=(char, ""))

    def _update_preview(self):
        self._update_label_preview()
        self._update_dict_label_preview()

    def _init_clear_widget(self):
        # Button widget to clear labels
        self.clear_button = tk.Button(self._bottom_right_frame,
                                      text="Clear",
                                      command=self._callback_clear,
                                      font=("Helvetica", 16))
        self.clear_button.grid(row=0, column=0)

    def _callback_clear(self):
        self._refresh()
        self._update_preview()

    def _refresh(self):
        self.selected_token = None
        self.selected_label = None
        self._label_to_words = {label: "" for label in self._classes}
        self._index_to_label = {}
        self._enter_mode = EnterMode.IDLE

    def _bind_widget_to_mode(self, widget, enter_mode: EnterMode):
        def _set_enter_mode(_enter_mode: EnterMode):
            def _set(event):
                self._enter_mode = _enter_mode
            return _set
        widget.bind("<Enter>", _set_enter_mode(enter_mode))
        widget.bind("<Leave>", _set_enter_mode(EnterMode.IDLE))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_file", type=str, required=True)
    parser.add_argument("-o", "--output_dir", type=str, help="If not specified, use same directory as input file")
    parser.add_argument("-r", "--resume", action="store_true")
    args = parser.parse_args(sys.argv[1:])

    output_dir = args.output_dir if args.output_dir is not None else os.path.dirname(args.input_file)
    app = AnnotatorApp(input_path=args.input_file, output_dir=output_dir)
    app.start(resume=args.resume)


if __name__ == '__main__':
    main()




