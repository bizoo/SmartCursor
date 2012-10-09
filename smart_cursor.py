import sublime
import sublime_plugin


stack_views = {}


class SmartCursorView(object):
    def __init__(self, view):
        self.view = view
        # self.sel = None
        self.selcol = None
        self.selmodcol = None
        self.last_selmod = None

    def save_sel(self):
        # self.sel = list(self.view.sel())
        self.selcol = []
        for sel in list(self.view.sel()):
            self.selcol.append(self.view.rowcol(sel.begin()))

    def save(self):
        if not self.selmodcol and self.selcol is not None:
            self.selmodcol = self.selcol[:]

    def reset(self):
        self.selmodcol = None

    def save_reset(self):
        self.last_selmod = list(self.view.sel())[:]

    def check_reset(self):
        if self.last_selmod is not None and self.last_selmod != list(self.view.sel()):
            self.reset()
        elif self.selmodcol:
            for sel, selmod in zip(self.view.sel(), self.selmodcol):
                if self.view.rowcol(sel.begin())[0] != selmod[0]:
                    self.reset()

    def get_new_sel(self):
        new_sel = []
        if self.selmodcol is not None:
            if len(self.view.sel()) == len(self.selmodcol):
                for sel, selmod in zip(self.view.sel(), self.selmodcol):
                    last_row, last_col = selmod
                    row, col = self.view.rowcol(sel.begin())
                    newpos = self.view.text_point(row, last_col)
                    endlinepos = self.view.line(sel.begin()).end()
                    # last edit pos is beyond the end of line, we replace it with the end of line pos.
                    # there's no way currently to put the cursor at the right position without changing everything.
                    if newpos > endlinepos:
                        newpos = endlinepos
                    new_sel.append(newpos)
        return new_sel


def stack_view(view):
    if not view.id() in stack_views:
        stack_views[view.id()] = SmartCursorView(view)
    return stack_views[view.id()]


class SmartCursorListener(sublime_plugin.EventListener):
    def on_close(self, view):
        if view.id() in stack_views:
            stack_views[view.id()].view = None
            del stack_views[view.id()]

    def on_selection_modified(self, view):
        stack = stack_view(view)
        stack.check_reset()
        stack.save_sel()

    def on_modified(self, view):
        stack = stack_view(view)
        stack.save_reset()
        stack.save()


class SmartCursorCommand(sublime_plugin.TextCommand):
    def run(self, edit, cmd="", **kwargs):
        stack = stack_view(self.view)
        new_sel = stack.get_new_sel()
        if new_sel:
            self.view.sel().clear()
            for sel in new_sel:
                self.view.sel().add(sel)
        self.view.run_command(cmd, kwargs)



# type a char or paste from clipboard:
# on_modified (23, 15)
# on_selected (23, 15)
# undo:
# on_selected (23, 14)
# on_modified (23, 14)
