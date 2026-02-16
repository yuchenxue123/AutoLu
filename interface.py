import signal
import sys
import tkinter
from tkinter import ttk, filedialog, messagebox
from recorder import Recorder, SegmentsRecorder


class Interface:
    def __init__(self, root: tkinter.Tk):
        self.root = root
        self.root.title("直播录制")
        self.root.geometry("900x600")
        self.root.resizable(True, True)

        # 储存所有录制器实例
        self.recorders = []

        # 唯一标识符
        # 只增不减，保证唯一性
        self.identify_counter = 0

        # 一些控件
        self.name_entry = None
        self.link_entry = None
        self.directory_entry = None
        self.recorder_tree = None
        self.context_menu = None

        # 初始化界面
        self.setup()

    def setup(self):
        # 控制面板
        control_frame = ttk.LabelFrame(self.root, text="创建新任务", padding=10)
        control_frame.pack(fill="x", padx=10, pady=10)

        # 第一行 名字
        ttk.Label(control_frame, text="主播名称:").grid(row=0, column=0, sticky=tkinter.W, padx=5, pady=5)
        self.name_entry = ttk.Entry(control_frame, width=50)
        self.name_entry.grid(row=0, column=1, sticky=tkinter.EW, padx=5, pady=5)
        # 木几萌
        self.name_entry.insert(0, "木几萌")

        # 第二行 直播链接
        ttk.Label(control_frame, text="直播链接:").grid(row=1, column=0, sticky=tkinter.W, padx=5, pady=5)
        # 链接输入框
        self.link_entry = ttk.Entry(control_frame, width=50)
        self.link_entry.grid(row=1, column=1, sticky=tkinter.EW, padx=5, pady=5)
        # 木几萌
        self.link_entry.insert(0, "https://live.bilibili.com/27004785")

        # 第三行 输出目录
        ttk.Label(control_frame, text="输出目录:").grid(row=2, column=0, sticky=tkinter.W, padx=5, pady=5)

        dir_frame = tkinter.Frame(control_frame)
        dir_frame.grid(row=2, column=1, sticky=tkinter.EW, padx=5, pady=5)

        # 输出目录输入框
        self.directory_entry = ttk.Entry(dir_frame)
        self.directory_entry.pack(side="left", fill="x", expand=True)
        # 默认输出目录
        self.directory_entry.insert(0, "./record")
        # 选择输出目录按钮
        ttk.Button(dir_frame, text="选择输出目录", width=12, command=self.select_directory).pack(side="left", padx=5)

        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=tkinter.EW, pady=10)

        ttk.Button(button_frame, text="添加任务", command=self.add_recorder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="删除选中", command=self.delete_recorder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="启动选中", command=self.start_recorder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="停止选中", command=self.stop_recorder).pack(side="left", padx=5)

        control_frame.columnconfigure(1, weight=1)

        list_frame = ttk.LabelFrame(self.root, text="录制任务列表", padding=10)
        list_frame.pack(fill="both", padx=10, pady=10, expand=True)

        # 创建录制列表
        columns = ("id", "name", "link", "output", "status", "time")
        self.recorder_tree = ttk.Treeview(list_frame, columns=columns, height=15, show="headings")

        self.recorder_tree.column("id", width=50, anchor="center")
        self.recorder_tree.column("name", width=80, anchor="center")
        self.recorder_tree.column("link", width=250, anchor="w")
        self.recorder_tree.column("output", width=150, anchor="w")
        self.recorder_tree.column("status", width=80, anchor="center")
        self.recorder_tree.column("time", width=150, anchor="center")

        self.recorder_tree.heading("id", text="任务编号")
        self.recorder_tree.heading("name", text="主播名称")
        self.recorder_tree.heading("link", text="链接")
        self.recorder_tree.heading("output", text="输出目录")
        self.recorder_tree.heading("status", text="状态")
        self.recorder_tree.heading("time", text="创建时间")

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.recorder_tree.yview)
        self.recorder_tree.configure(yscrollcommand=scrollbar.set)

        # 布局
        self.recorder_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 特殊标签
        self.recorder_tree.tag_configure("running", foreground="green")
        self.recorder_tree.tag_configure("failed", foreground="red")

        # 绑定事件
        self.recorder_tree.bind("<Delete>", lambda e: self.delete_recorder(True))
        self.recorder_tree.bind("<Button-3>", self.show_context_menu)

        # 右键菜单
        self.context_menu = tkinter.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="启动任务", command=self.start_recorder)
        self.context_menu.add_command(label="停止任务", command=self.stop_recorder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除任务", command=self.delete_recorder)

        self.root.after(500, lambda b: self._poll_list(), None)

    def show_context_menu(self, event):
        """显示右键菜单"""

        item = self.recorder_tree.identify_row(event.y)
        if item:
            if item not in self.recorder_tree.selection():
                self.recorder_tree.selection_set(item)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def select_directory(self):
        """选择输出目录"""

        directory = filedialog.askdirectory(title="选择输出目录")

        if directory:
            self.directory_entry.delete(0, tkinter.END)
            self.directory_entry.insert(0, directory)

    def add_recorder(self):
        """添加新录制器"""

        name = self.name_entry.get().strip()
        link = self.link_entry.get().strip()
        output = self.directory_entry.get().strip()

        if not name:
            messagebox.showinfo("提示", "请输入主播名称")
            return

        if not link:
            messagebox.showinfo("提示", "请输入直播链接")
            return

        if not output:
            messagebox.showinfo("提示", "请选择输出目录")
            return

        self.identify_counter += 1
        from recorder import config
        recorder = Recorder(name, link, output, self.identify_counter) if str(config.get("mode")) == "segment" else SegmentsRecorder(name, link, output, self.identify_counter)
        self.recorders.append(recorder)

        self.refresh_recorder_list()

    def delete_recorder(self, from_event=False):
        """删除选中任务"""

        selection = self.recorder_tree.selection()

        if not selection:
            if not from_event:
                messagebox.showinfo("提示", "请先选择要删除的任务")
            return

        for item in selection:
            identify = int(self.recorder_tree.item(item, "tags")[0])
            recorder = next((r for r in self.recorders if r.identify == identify), None)
            if recorder:
                recorder.stop()
                self.recorders.remove(recorder)
            self.recorder_tree.delete(item)

        self.refresh_recorder_list()

    def start_recorder(self):
        """启动选中录制器"""

        selection = self.recorder_tree.selection()

        if not selection:
            messagebox.showinfo("提示", "请先选择要启动的任务")
            return

        for item in selection:
            identify = int(self.recorder_tree.item(item, "tags")[0])
            recorder: Recorder = next((r for r in self.recorders if r.identify == identify), None)
            if recorder:
                recorder.start()

    def stop_recorder(self):
        """停止选中录制器"""

        selection = self.recorder_tree.selection()

        if not selection:
            messagebox.showinfo("提示", "请先选择要停止的任务")
            return

        for item in selection:
            identify = int(self.recorder_tree.item(item, "tags")[0])
            recorder: Recorder = next((r for r in self.recorders if r.identify == identify), None)
            if recorder:
                recorder.stop()

    def refresh_recorder_list(self):
        """刷新列表显示"""

        items = list(self.recorder_tree.get_children())

        # 更新或插入
        for i, recorder in enumerate(self.recorders):
            status = recorder.status
            values = (
                i + 1,
                recorder.name,
                recorder.link,
                recorder.output,
                status.text,
                recorder.time.strftime("%Y-%m-%d %H:%M:%S")
            )
            tags = (str(recorder.identify), status.tag)

            if i < len(items):
                item = items[i]
                self.recorder_tree.item(item, values=values, tags=tags)
            else:
                self.recorder_tree.insert("", tkinter.END, tags=tags, values=values)

    def _poll_list(self):
        """实时刷新"""
        try:
            self.refresh_recorder_list()
        finally:
            self.root.after(500, lambda b: self._poll_list(), None)

def __register_close_callback(interface: Interface):
    def cleanup():
        for recorder in interface.recorders:
            recorder.cleanup()

    import atexit
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda s, f: (cleanup(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda s, f: (cleanup(), sys.exit(0)))

def create_window():
    root = tkinter.Tk()
    interface = Interface(root)
    __register_close_callback(interface)
    root.mainloop()
    return interface
