from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import QLabel
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.utils import platform

# 适配安卓应用显示背景
Window.clearcolor = (0.96, 0.96, 0.96, 1)

class BatchCalculatorApp(App):
    def build(self):
        self.title = '批次计算器'
        
        # 整体采用主滚动视图，避免手机软件盘弹出时遮挡输入框
        root_scroll = ScrollView(size_hint=(1, 1))
        
        main_layout = BoxLayout(
            orientation='vertical', 
            padding=[12, 16, 12, 16], 
            spacing=10, 
            size_hint_y=None
        )
        main_layout.bind(minimum_height=main_layout.setter('height'))
        
        # 1. 标题栏（适合手机屏幕占比）
        title_label = QLabel(
            text='[b]批次计算器[/b]',
            markup=True,
            font_size='20sp',
            color=(0.1, 0.1, 0.1, 1),
            size_hint_y=None,
            height=36,
            halign='center'
        )
        main_layout.add_widget(title_label)

        # 2. 表单输入区（优化比例，增加 input_type 唤起手机数字键盘）
        form_layout = GridLayout(cols=2, spacing=8, size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter('height'))

        def create_input(placeholder, is_int=False):
            return TextInput(
                hint_text=placeholder,
                multiline=False,
                input_filter='int' if is_int else 'float',  # 限制数字输入
                input_type='number',                        # 手机端优先弹数字键盘
                font_size='16sp',
                size_hint_y=None,
                height=44,
                padding=[8, 10, 8, 10]
            )

        def create_label(text):
            return QLabel(
                text=text, 
                color=(0.2, 0.2, 0.2, 1), 
                size_hint_x=0.35,
                font_size='14sp',
                halign='left',
                valign='middle'
            )

        # 添加表单组件[span_1](start_span)[span_1](end_span)
        form_layout.add_widget(create_label('下限值 (a):'))
        self.input_a = create_input('a > 0, 如: 10.0')
        form_layout.add_widget(self.input_a)

        form_layout.add_widget(create_label('上限值 (b):'))
        self.input_b = create_input('b > a, 如: 20.0')
        form_layout.add_widget(self.input_b)

        form_layout.add_widget(create_label('总批数 (x):'))
        self.input_x = create_input('整数 x > 0', is_int=True)
        form_layout.add_widget(self.input_x)

        form_layout.add_widget(create_label('小数位数 (w):'))
        self.input_w = create_input('截断位数，可空', is_int=True)
        form_layout.add_widget(self.input_w)

        form_layout.add_widget(create_label('本金 (m):'))
        self.input_m = create_input('本金 m，可空')
        form_layout.add_widget(self.input_m)

        main_layout.add_widget(form_layout)

        # 3. 计算按钮（加大按键高宽，方便触控）
        self.calc_btn = Button(
            text='开始计算',
            background_normal='',
            background_color=(0.17, 0.36, 0.56, 1),
            color=(1, 1, 1, 1),
            font_size='17sp',
            bold=True,
            size_hint_y=None,
            height=48
        )
        self.calc_btn.bind(on_press=self.calculate)
        main_layout.addWidget(self.calc_btn)

        # 4. 状态提示
        self.status_label = QLabel(
            text='提示：点击绿色数值单元格可自动复制',
            color=(0.4, 0.4, 0.4, 1),
            font_size='13sp',
            size_hint_y=None,
            height=28,
            halign='center'
        )
        main_layout.add_widget(self.status_label)

        # 5. 表头
        header_layout = GridLayout(cols=3, size_hint_y=None, height=36)
        header_layout.add_widget(QLabel(text='[b]批次(i)[/b]', markup=True, color=(0.1, 0.1, 0.1, 1), font_size='14sp'))
        header_layout.add_widget(QLabel(text='[b]取值(r)[/b]', markup=True, color=(0.1, 0.1, 0.1, 1), font_size='14sp'))
        header_layout.add_widget(QLabel(text='[b]买入额(n)[/b]', markup=True, color=(0.1, 0.1, 0.1, 1), font_size='14sp'))
        main_layout.add_widget(header_layout)

        # 6. 表格数据展示区
        self.table_grid = GridLayout(cols=3, spacing=4, size_hint_y=None)
        self.table_grid.bind(minimum_height=self.table_grid.setter('height'))
        main_layout.add_widget(self.table_grid)

        root_scroll.add_widget(main_layout)
        return root_scroll

    def truncate_decimal(self, val_float, decimals=None):
        raw_str = f"{val_float:.12f}".rstrip('0').rstrip('.')
        if decimals is None:
            return raw_str

        if '.' in raw_str:
            integer_part, decimal_part = raw_str.split('.')
            if decimals == 0:
                return integer_part
            else:
                decimal_part = decimal_part.ljust(decimals, '0')[:decimals]
                return f"{integer_part}.{decimal_part}"
        else:
            if decimals == 0:
                return raw_str
            else:
                return f"{raw_str}." + "0" * decimals

    def calculate(self, instance):
        self.table_grid.clear_widgets()
        
        try:
            a = float(self.input_a.text.strip())
            b = float(self.input_b.text.strip())
            x = int(self.input_x.text.strip())
        except ValueError:
            self.status_label.text = '错误：请正确填写 a, b, x！'
            return

        if a <= 0 or b <= a or x <= 0:
            self.status_label.text = '错误：需满足 a > 0, b > a, x > 0'
            return

        # 解析 w
        w_text = self.input_w.text.strip()
        w_val = None
        if w_text != "":
            try:
                w_val = int(w_text)
                if w_val < 0:
                    self.status_label.text = '错误：w 必须 >= 0'
                    return
            except ValueError:
                self.status_label.text = '错误：w 必须为整数'
                return

        # 解析 m
        m_text = self.input_m.text.strip()
        m_val = None
        if m_text != "":
            try:
                m_val = float(m_text)
                if m_val <= 0:
                    self.status_label.text = '错误：m 必须 > 0'
                    return
            except ValueError:
                self.status_label.text = '错误：m 必须为有效数值'
                return

        n_val = (m_val / x) if m_val is not None else None

        for i in range(x):
            r_val = a if x == 1 else a + ((b - a) / (x - 1)) * i
            r_str = self.truncate_decimal(r_val, w_val)
            n_str = f"{n_val:.10f}".rstrip('0').rstrip('.') if n_val is not None else "-"

            # i 单元格
            lbl_i = QLabel(text=str(i), color=(0.2, 0.2, 0.2, 1), font_size='13sp', size_hint_y=None, height=44)
            
            # r 单元格（支持点击复制）
            btn_r = Button(
                text=r_str, 
                background_normal='', 
                background_color=(0.82, 0.92, 0.82, 1), 
                color=(0, 0, 0, 1), 
                font_size='13sp', 
                size_hint_y=None, 
                height=44
            )
            btn_r.bind(on_press=lambda btn, val=r_str: self.copy_to_clipboard(val, 'r'))

            # n 单元格（支持点击复制）
            btn_n = Button(
                text=n_str, 
                background_normal='', 
                background_color=(0.82, 0.92, 0.82, 1) if n_str != "-" else (0.9, 0.9, 0.9, 1), 
                color=(0, 0, 0, 1), 
                font_size='13sp', 
                size_hint_y=None, 
                height=44
            )
            if n_str != "-":
                btn_n.bind(on_press=lambda btn, val=n_str: self.copy_to_clipboard(val, 'n'))

            self.table_grid.add_widget(lbl_i)
            self.table_grid.add_widget(btn_r)
            self.table_grid.add_widget(btn_n)

        self.status_label.text = '计算成功！点击绿色单元格复制数值。'

    def copy_to_clipboard(self, val, name):
        Clipboard.copy(val)
        self.status_label.text = f'已复制 {name} 的值: {val}'

if __name__ == '__main__':
    BatchCalculatorApp().run()
