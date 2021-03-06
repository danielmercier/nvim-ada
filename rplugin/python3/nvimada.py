import neovim
import libadalang as lal
from os import listdir, getcwd, walk


def is_project_file(filename):
    return filename.endswith('.gpr')


def is_ada_file(filename):
    return filename.endswith('.adb') or filename.endswith('.ads')


def findGPRFile():
    # Try to find a project file .gpr
    projects = [f for f in listdir(getcwd()) if is_project_file(f)]

    return projects


@neovim.plugin
class Main(object):
    def __init__(self, vim):
        self.vim = vim
        self.ctx = None
        self.auto_provider = False

    def move_cursor(self, line, col):
        # Cursor is 0 based on columns, LAL is 1 based
        self.vim.current.window.api.set_cursor([line, col - 1])

    @neovim.autocmd('BufReadPre')
    def onBufReadPre(self):
        # need to update context if context is auto provider or no context is
        # defined
        if self.auto_provider or (not self.ctx):
            filename = self.vim.current.buffer.api.get_name()
            if is_project_file(filename):
                self.lalInitProject([filename])
            elif is_ada_file(filename):
                projects = findGPRFile()
                if len(projects) == 1:
                    self.lalInitProject(projects)
                else:
                    self.lalInitAuto([])

    @neovim.function('LalInitProject', sync=True)
    def lalInitProject(self, args):
        unit_provider = lal.UnitProvider.for_project(args[0])
        self.ctx = lal.AnalysisContext(unit_provider=unit_provider)
        self.auto_provider = False

    @neovim.function('LalInitAuto', sync=True)
    def lalInitAuto(self, args):
        if not self.auto_provider:
            ada_files = []

            for (_, _, filenames) in walk(getcwd()):
                ada_files.extend([f for f in filenames if is_ada_file(f)])

            unit_provider = lal.UnitProvider.auto(ada_files)
            self.ctx = lal.AnalysisContext(unit_provider=unit_provider)
            self.auto_provider = True

    def cursorNode(self):
        file = self.ctx.get_from_file(self.vim.current.buffer.api.get_name(),
                                      reparse=True)

        (line, col) = self.vim.current.window.api.get_cursor()

        # Cursor is 0 based on columns, LAL is 1 based
        sloc = lal.Sloc(line, col + 1)

        return file.root.lookup(sloc)

    @neovim.function('LalLocate', sync=True)
    def lalLocate(self, args):
        node = self.cursorNode()

        if node is not None:
            reference = None

            if node.parent.is_a(lal.DefiningName):
                # Go to next part for decl if this is a defining name
                reference = node.parent.p_next_part()

                if reference is None:
                    # Try previous part
                    reference = node.parent.p_previous_part()
            elif node.is_a(lal.Name):
                reference = node.p_referenced_defining_name()

            if reference is not None:
                filename = reference.unit.filename
                self.vim.command("edit {}".format(filename))

                line = reference.sloc_range.start.line
                col = reference.sloc_range.start.column

                self.move_cursor(line, col)
        else:
            self.vim.err_write("cannot get node under cursor\n")

    @neovim.function('LalIsDispatching', sync=True)
    def lalIsDispatching(self, args):
        node = self.cursorNode()

        if node is not None:
            if node.is_a(lal.Name):
                self.vim.out_write(str(node.p_is_dispatching_call()) + '\n')
            else:
                self.vim.out_write("not a name\n")
        else:
            self.vim.err_write("cannot get node under cursor\n")
