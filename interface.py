import tkinter
from tkinter import ttk, filedialog, messagebox
from recorder import Recorder


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

        # 第一行 直播链接
        ttk.Label(control_frame, text="直播链接:").grid(row=0, column=0, sticky=tkinter.W, padx=5, pady=5)
        # 链接输入框
        self.link_entry = ttk.Entry(control_frame, width=50)
        self.link_entry.grid(row=0, column=1, sticky=tkinter.EW, padx=5, pady=5)
        # 木几萌
        self.link_entry.insert(0, "https://live.bilibili.com/27004785")

        # 第二行 输出目录
        ttk.Label(control_frame, text="输出目录:").grid(row=1, column=0, sticky=tkinter.W, padx=5, pady=5)

        dir_frame = tkinter.Frame(control_frame)
        dir_frame.grid(row=1, column=1, sticky=tkinter.EW, padx=5, pady=5)

        # 输出目录输入框
        self.directory_entry = ttk.Entry(dir_frame)
        self.directory_entry.pack(side="left", fill="x", expand=True)
        # 默认输出目录
        self.directory_entry.insert(0, "./record")
        # 选择输出目录按钮
        ttk.Button(dir_frame, text="选择输出目录", width=12, command=self.select_directory).pack(side="left", padx=5)

        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=tkinter.EW, pady=10)

        ttk.Button(button_frame, text="添加任务", command=self.add_recorder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="删除选中", command=self.delete_recorder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="启动选中", command=self.start_recorder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="停止选中", command=self.stop_recorder).pack(side="left", padx=5)

        control_frame.columnconfigure(1, weight=1)

        list_frame = ttk.LabelFrame(self.root, text="录制任务列表", padding=10)
        list_frame.pack(fill="both", padx=10, pady=10, expand=True)

        # 创建Treeview
        columns = ("id", "link", "output", "status", "time")
        self.recorder_tree = ttk.Treeview(list_frame, columns=columns, height=15, show="headings")

        self.recorder_tree.column("id", width=50, anchor="center")
        self.recorder_tree.column("link", width=250, anchor="w")
        self.recorder_tree.column("output", width=200, anchor="w")
        self.recorder_tree.column("status", width=80, anchor="center")
        self.recorder_tree.column("time", width=150, anchor="center")

        self.recorder_tree.heading("id", text="任务编号")
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
        self.recorder_tree.tag_configure("stopped", foreground="red")

        # 绑定事件
        self.recorder_tree.bind("<Delete>", lambda e: self.delete_recorder(True))
        self.recorder_tree.bind("<Button-3>", self.show_context_menu)

        # 右键菜单
        self.context_menu = tkinter.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="启动任务", command=self.start_recorder)
        self.context_menu.add_command(label="停止任务", command=self.stop_recorder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除任务", command=self.delete_recorder)

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

        link = self.link_entry.get().strip()
        output = self.directory_entry.get().strip()

        if not link:
            messagebox.showinfo("提示", "请输入直播链接")
            return

        if not output:
            messagebox.showinfo("提示", "请选择输出目录")
            return

        self.identify_counter += 1
        recorder = Recorder(link, output, self.identify_counter)
        self.recorders.append(recorder)

        # 刷新列表显示
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

        self.refresh_recorder_list()

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

        self.refresh_recorder_list()

    def refresh_recorder_list(self):
        """刷新列表显示"""

        # 清空现有项目
        for item in self.recorder_tree.get_children():
            self.recorder_tree.delete(item)

        # 添加所有任务
        for index, recorder in enumerate(self.recorders):
            status = recorder.status

            self.recorder_tree.insert("", tkinter.END, tags=(recorder.identify, status.tag), values=(
                index + 1,
                recorder.link,
                recorder.output,
                status.text,
                recorder.created_time
            ))


def create_window():
    root = tkinter.Tk()
    interface = Interface(root)
    root.mainloop()
    return interface
