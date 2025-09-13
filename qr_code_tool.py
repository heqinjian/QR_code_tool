
import cv2
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import numpy as np
from pyzbar.pyzbar import decode
import webbrowser
import os
import threading
from PIL import Image, ImageTk, ImageDraw
import qrcode

def put_chinese_text(img, text, position, font_size=1.0, color=(255, 0, 0), thickness=2):
    cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_size, color, thickness)



def generate_qr_code(data, save_path, background_image=None):
    """生成二维码，可选择添加自定义图片背景，并自动调整二维码颜色以匹配背景
    
    参数:
    data: 要编码到二维码的数据
    save_path: 保存路径
    background_image: 可选，背景图片路径
    """
    try:
        # 使用qrcode库生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # 如果没有指定背景图片，生成标准黑白二维码
        if not background_image:
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(save_path)
        else:
            # 生成带有自定义背景的二维码
            # 1. 创建二维码图片(白色背景)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_width, qr_height = qr_img.size
            
            # 2. 打开并调整背景图片大小
            bg_img = Image.open(background_image)
            bg_img = bg_img.resize((qr_width, qr_height), Image.LANCZOS)
            
            # 3. 分析背景图片的主要颜色
            # 转换为RGB模式并获取像素数据
            bg_rgb = bg_img.convert('RGB')
            pixels = list(bg_rgb.getdata())
            
            # 计算背景的平均颜色
            avg_r = sum(p[0] for p in pixels) // len(pixels)
            avg_g = sum(p[1] for p in pixels) // len(pixels)
            avg_b = sum(p[2] for p in pixels) // len(pixels)
            
            # 4. 选择一个与背景颜色相似但对比度足够的颜色作为二维码颜色
            # 计算亮度
            brightness = (0.299 * avg_r + 0.587 * avg_g + 0.114 * avg_b)
            
            # 基于背景亮度选择二维码颜色：
            # - 如果背景较暗（亮度<128），选择稍亮的相似颜色
            # - 如果背景较亮（亮度>=128），选择稍暗的相似颜色
            if brightness < 128:
                # 背景较暗，选择稍亮的颜色
                qr_r = min(255, avg_r + 80) if avg_r + 80 < 255 else max(0, avg_r - 40)
                qr_g = min(255, avg_g + 80) if avg_g + 80 < 255 else max(0, avg_g - 40)
                qr_b = min(255, avg_b + 80) if avg_b + 80 < 255 else max(0, avg_b - 40)
            else:
                # 背景较亮，选择稍暗的颜色
                qr_r = max(0, avg_r - 80) if avg_r - 80 > 0 else min(255, avg_r + 40)
                qr_g = max(0, avg_g - 80) if avg_g - 80 > 0 else min(255, avg_g + 40)
                qr_b = max(0, avg_b - 80) if avg_b - 80 > 0 else min(255, avg_b + 40)
            
            # 5. 创建一个新的图像，用于合成
            result_img = Image.new('RGBA', (qr_width, qr_height), (255, 255, 255, 255))
            
            # 6. 先绘制背景图片
            result_img.paste(bg_img, (0, 0))
            
            # 7. 再绘制二维码，只保留选择的颜色部分，透明化白色背景
            # 将二维码转换为RGBA模式
            qr_rgba = qr_img.convert('RGBA')
            pixels = qr_rgba.load()
            
            # 将白色背景变为透明，二维码部分使用选定的颜色
            for i in range(qr_width):
                for j in range(qr_height):
                    r, g, b, a = pixels[i, j]
                    if r > 200 and g > 200 and b > 200:  # 判断是否为白色
                        pixels[i, j] = (255, 255, 255, 0)  # 设置为透明
                    else:
                        pixels[i, j] = (qr_r, qr_g, qr_b, 255)  # 使用选定的颜色
            
            # 8. 将处理后的二维码叠加到背景上
            result_img.paste(qr_rgba, (0, 0), qr_rgba)
            
            # 9. 保存最终结果
            result_img.save(save_path, 'PNG')
        
    except Exception as e:
        print(f"生成二维码时出错: {str(e)}")
        raise


def show_qr_code_preview(image_path, root=None):
    # 检查是否已存在Tk根窗口，如果没有则创建一个
    if root is None or not isinstance(root, tk.Tk):
        # 尝试获取已存在的根窗口
        try:
            root = tk.Tk._default_root
            if root is None:
                root = tk.Tk()
                root.withdraw()  # 隐藏主窗口
        except:
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
    
    # 创建预览窗口
    preview_window = tk.Toplevel(root)
    preview_window.title("二维码预览")
    preview_window.geometry("300x350")
    
    # 确保预览窗口关闭时不会影响主程序
    preview_window.protocol("WM_DELETE_WINDOW", preview_window.destroy)
    
    try:
        # 加载并显示二维码图片
        img = Image.open(image_path)
        img = img.resize((250, 250), Image.LANCZOS)
        
        # 创建PhotoImage对象，并确保它与预览窗口关联
        img_tk = ImageTk.PhotoImage(img, master=preview_window)
        
        # 创建标签并显示图片
        img_label = tk.Label(preview_window, image=img_tk)
        img_label.image = img_tk  # 保持引用，避免被垃圾回收
        img_label.pack(pady=10)
        
        # 添加保存按钮
        save_button = tk.Button(preview_window, text="保存到文件", 
                              command=lambda: save_qr_code(image_path, preview_window))
        save_button.pack(pady=10)
        
    except Exception as e:
        messagebox.showerror("错误", f"无法显示二维码预览: {str(e)}")
        preview_window.destroy()


def save_qr_code(temp_path, preview_window):
    """将生成的二维码保存到用户选择的位置"""
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG图片", "*.png"), ("所有文件", "*.*")]
    )
    
    if file_path:
        try:
            # 复制临时文件到目标位置
            import shutil
            shutil.copy2(temp_path, file_path)
            messagebox.showinfo("成功", f"二维码已保存到:\n{file_path}")
            preview_window.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

def recognize_qr_from_image(img):
    """从图像中识别二维码并返回识别结果"""
    QR_code = decode(img)
    results = []
    for qr in QR_code:
        qr_data = qr.data.decode('utf-8')
        results.append(qr_data)
        # 绘制矩形和识别结果
        point = qr.rect
        cv2.rectangle(img, (point[0], point[1]), 
                     (point[0] + point[2], point[1] + point[3]), 
                     (0, 255, 0), 7)
        put_chinese_text(img, qr_data, (point[0] - 20, point[1] - 20), 0.55, (255, 0, 0), 2)
    return img, results

def ask_user_to_open_url(qr_data, data):
    """询问用户是否要打开识别到的URL链接"""
    # 创建一个临时的tkinter窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 提取域名显示
    url_display = qr_data
    if len(qr_data) > 50:
        url_display = qr_data[:50] + "..."
    
    # 显示询问对话框
    response = messagebox.askyesno(
        title="打开链接",
        message=f"识别到以下链接：\n{qr_data}\n\n是否要打开该链接？"
    )
    
    # 处理用户响应
    if response:
        webbrowser.open(qr_data)
        print(f"已打开链接: {qr_data}")
        return True
    else:
        print(f"用户选择不打开链接: {qr_data}")
        return False
    
    # 销毁临时窗口
    root.destroy()

def upload_image_and_recognize(data):
    """上传图片识别二维码"""
    # 创建临时的tkinter窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 打开文件选择对话框
    file_path = filedialog.askopenfilename(
        title="选择图片文件",
        filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff")]
    )
    
    if file_path:
        # 读取图片
        img = cv2.imread(file_path)
        if img is not None:
            # 识别二维码
            _, results = recognize_qr_from_image(img)
            
            # 处理识别结果
            if results:
                for qr_data in results:
                    if qr_data and qr_data != data[-1]:
                        data.append(qr_data)
                        print(f"识别到新链接: {qr_data}")
                        # 询问用户是否打开链接
                        ask_user_to_open_url(qr_data, data)
            else:
                messagebox.showinfo("识别结果", "未识别到二维码")
                print("未识别到二维码")
        else:
            messagebox.showerror("错误", "无法读取图片文件")
            print("无法读取图片文件")
    
    # 销毁tkinter窗口
    root.destroy()

def start_camera_recognition(data):
    """启动摄像头识别二维码"""
    # 初始化摄像头
    cap = cv2.VideoCapture(0)
    
    print("摄像头识别已启动! 按ESC键或点击窗口上的叉退出")
    
    while True:
        success, img = cap.read()
        if not success:
            print("无法获取摄像头图像")
            break
        
        # 识别摄像头中的二维码
        img_with_results, results = recognize_qr_from_image(img)
        
        # 处理识别结果
        for qr_data in results:
            if qr_data and qr_data != data[-1]:
                data.append(qr_data)
                print(f"识别到新链接: {qr_data}")
                # 在主线程中创建一个临时tkinter窗口来显示对话框
                root = tk.Tk()
                root.withdraw()
                ask_user_to_open_url(qr_data, data)
                root.destroy()
        
        # 显示摄像头窗口
        cv2.imshow('Camera', img_with_results)
        
        # 检查按键
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC键退出
            break
        
        # 检查窗口是否被关闭
        try:
            # 当窗口被关闭时，getWindowProperty会返回-1
            prop = cv2.getWindowProperty('Camera', cv2.WND_PROP_VISIBLE)
            if prop < 1:
                break
        except:
            # 如果窗口已经不存在，会抛出异常
            break
    
    # 释放资源
    cap.release()
    cv2.destroyAllWindows()

def on_upload_image(data, main_window):
    """处理上传图片按钮点击事件"""
    main_window.withdraw()  # 隐藏主窗口
    upload_image_and_recognize(data)
    main_window.deiconify()  # 显示主窗口

def on_start_camera(data, main_window):
    """处理启动摄像头按钮点击事件"""
    main_window.withdraw()  # 隐藏主窗口
    # 在新线程中运行摄像头识别，避免GUI卡顿
    camera_thread = threading.Thread(target=lambda: 
        (start_camera_recognition(data), main_window.deiconify()))
    camera_thread.daemon = True
    camera_thread.start()




def on_generate_qr_code():
    """处理生成二维码的逻辑"""
    # 创建输入窗口
    input_window = tk.Tk()
    input_window.title("生成二维码")
    input_window.geometry("450x300")  # 增加窗口高度以容纳更多控件
    
    # 设置中文字体
    if os.name == 'nt':  # Windows系统
        font = ('SimHei', 12)
    else:
        font = ('Arial', 12)
    
    # 创建标签和输入框
    label = tk.Label(input_window, text="请输入要生成二维码的内容:", font=font)
    label.pack(pady=10)
    
    text_input = tk.Entry(input_window, width=45, font=font)
    text_input.pack(pady=5)
    
    # 添加背景图片选择功能
    background_path = [None]  # 使用列表存储，以便在内部函数中修改
    
    # 创建背景图片选择按钮和显示标签
    def select_background():
        file_path = filedialog.askopenfilename(
            title="选择背景图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp")]
        )
        if file_path:
            background_path[0] = file_path
            # 显示选择的文件路径（只显示文件名部分）
            file_name = os.path.basename(file_path)
            background_label.config(text=f"已选择背景图片: {file_name}")
    
    # 创建按钮框架用于背景图片选择
    background_frame = tk.Frame(input_window)
    background_frame.pack(pady=5, fill=tk.X, padx=50)
    
    background_button = tk.Button(background_frame, text="选择背景图片", 
                                command=select_background, font=font, width=15)
    background_button.pack(side=tk.LEFT)
    
    background_label = tk.Label(background_frame, text="未选择背景图片", 
                              font=font, fg="gray")
    background_label.pack(side=tk.LEFT, padx=10)
    
    # 创建生成按钮
    def generate_and_preview():
        data = text_input.get().strip()
        if not data:
            messagebox.showwarning("警告", "请输入二维码内容")
            return
        
        try:
            # 创建临时文件路径
            temp_path = os.path.join(os.getenv('TEMP', '.'), 'temp_qr.png')
            
            # 确保临时目录存在
            temp_dir = os.path.dirname(temp_path)
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            # 输出调试信息
            preview_content = data[:100] + ("..." if len(data) > 100 else "")
            print(f"最终编码内容: {preview_content}")
            
            if background_path[0]:
                print(f"二维码类型: 自定义背景")
                print(f"使用背景图片: {background_path[0]}")
            else:
                print(f"二维码类型: 静态")
            
            # 生成二维码（支持自定义背景）
            generate_qr_code(data, temp_path, background_path[0])
            
            # 验证生成的文件是否存在
            if not os.path.exists(temp_path):
                raise FileNotFoundError(f"二维码文件未成功生成: {temp_path}")
            
            # 显示预览
            show_qr_code_preview(temp_path, input_window)
        except Exception as e:
            messagebox.showerror("错误", f"生成二维码失败: {str(e)}")
            print(f"二维码生成错误详情: {type(e).__name__}: {str(e)}")  # 在控制台输出详细错误信息
    
    generate_button = tk.Button(input_window, text="生成二维码", 
                              command=generate_and_preview, font=font)
    generate_button.pack(pady=15)
    
    # 启动输入窗口循环
    input_window.mainloop()


def show_scan_menu():
    """显示扫描二维码子菜单"""
    scan_window = tk.Tk()
    scan_window.title("扫描二维码")
    scan_window.geometry("400x300")
    scan_window.resizable(False, False)
    
    # 设置中文字体
    if os.name == 'nt':  # Windows系统
        font = ('SimHei', 12)
    else:
        font = ('Arial', 12)
    
    # 创建标题标签
    title_label = tk.Label(scan_window, text="选择扫描方式", font=(font[0], 16, "bold"))
    title_label.pack(pady=20)
    
    # 存储已识别链接的数据
    data = ['link']
    
    # 创建上传图片按钮
    upload_button = tk.Button(scan_window, text="上传图片识别", command=lambda: [scan_window.destroy(), upload_image_and_recognize(data)], 
                             width=20, height=2, font=font)
    upload_button.pack(pady=10)
    
    # 创建启动摄像头按钮
    def start_camera_task():
        scan_window.destroy()
        # 在新线程中运行摄像头识别，避免GUI卡顿
        camera_thread = threading.Thread(target=lambda: start_camera_recognition(data))
        camera_thread.daemon = True
        camera_thread.start()
        
    camera_button = tk.Button(scan_window, text="启动摄像头识别", command=start_camera_task, 
                             width=20, height=2, font=font)
    camera_button.pack(pady=10)
    
    # 创建返回按钮
    back_button = tk.Button(scan_window, text="返回", command=scan_window.destroy, 
                          width=20, height=2, font=font)
    back_button.pack(pady=10)
    
    # 启动子菜单循环
    scan_window.mainloop()




def show_main_menu():
    """显示主菜单"""
    # 创建主窗口
    main_window = tk.Tk()
    main_window.title("二维码工具")
    main_window.geometry("400x300")
    main_window.resizable(False, False)
    
    # 设置窗口居中
    main_window.update_idletasks()
    width = main_window.winfo_width()
    height = main_window.winfo_height()
    x = (main_window.winfo_screenwidth() // 2) - (width // 2)
    y = (main_window.winfo_screenheight() // 2) - (height // 2)
    main_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    # 设置中文字体
    if os.name == 'nt':  # Windows系统
        font = ('SimHei', 12)
    else:
        font = ('Arial', 12)
    
    # 创建标题标签
    title_label = tk.Label(main_window, text="二维码工具", font=(font[0], 20, "bold"))
    title_label.pack(pady=30)
    
    # 创建按钮框架
    button_frame = tk.Frame(main_window)
    button_frame.pack(pady=20)
    
    # 创建生成二维码按钮
    generate_button = tk.Button(button_frame, text="生成二维码", 
                              command=on_generate_qr_code, width=20, height=2, font=font)
    generate_button.pack(pady=10)
    
    # 创建扫描二维码按钮
    scan_button = tk.Button(button_frame, text="扫描二维码", command=show_scan_menu, 
                          width=20, height=2, font=font)
    scan_button.pack(pady=10)
    
    # 创建退出按钮
    exit_button = tk.Button(main_window, text="退出", command=main_window.destroy, 
                          width=10, font=font)
    exit_button.pack(pady=10)
    
    # 启动主循环
    main_window.mainloop()



def main():
    """主函数"""
    # 显示主菜单
    show_main_menu()

if __name__ == "__main__":
    main()