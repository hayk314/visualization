# Author: Hayk Aleksanyan
# read file and tokenize into words

import traceback


class FileReaderFromBinary:
    def __init__(self, log_file=""):
        self.log_file = log_file

    @property
    def name(self):
        return type(self).__name__

    def read_file_into_list_of_row(self, file_path, verbose=0):
        file_lines_decoded = []
        error_msg = []

        try:
            with open(file_path, "rb") as f:
                file_lines_in_bytes = f.readlines()

            for i, entry in enumerate(file_lines_in_bytes):
                try:
                    s = entry.decode()
                    file_lines_decoded.append(s)
                except Exception as ex:
                    msg = "[{}] failed on row={},\n    entry={}, \n    ex={}".format(self.name, i, entry, str(ex))
                    if verbose:
                        print(msg, flush=True)
                    if self.log_file != "":
                        error_msg.append(msg)

                    s = []
                    for b in entry:
                        try:
                            char = chr(b)
                            s.append(char)
                        except Exception as ex:
                            msg = "[{}] failed on row={},\n    byte={}, \n    ex={}".format(self.name, i, b, str(ex))
                            if verbose:
                                print(msg, flush=True)
                            if self.log_file != "":
                                error_msg.append(msg)

                    file_lines_decoded.append("".join(s))

            if error_msg:
                with open(self.log_file, "a") as f:
                    f.write("read_file_into_list_of_row crushed on file {} with this error \n=======\n{}\n=======\n".
                            format(file_path, "\n".join(error_msg)))

        except:
            print(traceback.format_exc())

        if verbose:
            print("[{}] there are {} rows in the file at [{}]".format(self.name, len(file_lines_decoded), file_path),
                  flush=True)

        return file_lines_decoded