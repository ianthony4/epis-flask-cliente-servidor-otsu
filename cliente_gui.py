import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, END
import requests
import cv2
import numpy as np
import os
from PIL import Image, ImageTk
import io

SERVER_URL = "https://anthony4.pythonanywhere.com"

def subir_imagen_local():
    file_path = filedialog.askopenfilename(
        title="Selecciona una imagen",
        filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif")]
    )
    if not file_path:
        return

    # Leer la imagen en color (para mostrar y para subir sin procesar)
    img_color = cv2.imread(file_path, cv2.IMREAD_COLOR)
    if img_color is None:
        messagebox.showerror("Error", "No se pudo leer la imagen en color.")
        return

    # Subir imagen SIN procesar al servidor (a la carpeta de imágenes normales)
    with open(file_path, 'rb') as f:
        files = {'image': (os.path.basename(file_path), f, 'image/png')}
        try:
            resp = requests.post(f"{SERVER_URL}/upload", files=files)
            if resp.status_code == 200:
                messagebox.showinfo("Éxito", "¡Imagen original subida correctamente al servidor!")
            else:
                messagebox.showerror("Error", f"Fallo al subir imagen original: {resp.text}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar al servidor: {e}")
            return

    # Procesar la imagen localmente a grises
    img_gray = cv2.cvtColor(img_color, cv2.COLOR_BGR2GRAY)
    mostrar_imagenes_color_gris(img_color, img_gray, "Comparación: Color vs Blanco y Negro Suave")

    # Subir la imagen procesada (grises) a /processed **sin crear archivo temporal**
    _, buffer = cv2.imencode('.png', img_gray)
    gray_name = f"gray_{os.path.basename(file_path)}"
    files = {'image': (gray_name, io.BytesIO(buffer), 'image/png')}
    try:
        resp = requests.post(f"{SERVER_URL}/upload_processed", files=files)
        if resp.status_code == 200:
            messagebox.showinfo("Éxito", "¡Imagen procesada subida correctamente a /processed!")
        else:
            messagebox.showerror("Error", f"Fallo al subir imagen procesada: {resp.text}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo subir la imagen procesada: {e}")

def listar_imagenes_servidor():
    """Descarga la lista de imágenes del servidor y permite elegir una."""
    try:
        resp = requests.get(f"{SERVER_URL}/list_images")
        if resp.status_code != 200:
            raise Exception("No se pudo obtener la lista de imágenes.")
        imagenes = resp.json()
        return imagenes
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return []

def seleccionar_y_procesar_servidor():
    imagenes = listar_imagenes_servidor()
    if not imagenes:
        return

    win = tk.Toplevel()
    win.title("Selecciona una imagen del servidor")
    lb = Listbox(win, width=45)
    for img in imagenes:
        lb.insert(END, img)
    lb.pack(padx=10, pady=10)

    def on_select():
        sel = lb.curselection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona una imagen primero.")
            return
        image_name = lb.get(sel[0])
        win.destroy()
        descargar_y_procesar_en_servidor(image_name)

    tk.Button(win, text="Procesar selección", command=on_select).pack(pady=8)

def descargar_y_procesar_en_servidor(image_name):
    # Descargar la imagen original (COLOR)
    url_original = f"{SERVER_URL}/static/{image_name}"
    response1 = requests.get(url_original)
    if response1.status_code != 200:
        messagebox.showerror("Error", "No se pudo descargar la imagen original.")
        return

    img_color = cv2.imdecode(np.frombuffer(response1.content, np.uint8), cv2.IMREAD_COLOR)

    # Descargar la imagen procesada (grises) desde el servidor
    url_gray = f"{SERVER_URL}/process_gray/{image_name}"
    response2 = requests.get(url_gray)
    if response2.status_code != 200:
        messagebox.showerror("Error", "No se pudo obtener la imagen procesada desde el servidor.")
        return

    img_gray = cv2.imdecode(np.frombuffer(response2.content, np.uint8), cv2.IMREAD_GRAYSCALE)

    # Mostrar ambas
    mostrar_imagenes_color_gris(img_color, img_gray, f"Procesamiento de {image_name}")

    # Guardar la imagen procesada si el usuario quiere
    save_path = filedialog.asksaveasfilename(
        initialfile=f"gray_{image_name}",
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
    )
    if save_path:
        cv2.imwrite(save_path, img_gray)
        messagebox.showinfo("Guardado", f"Imagen procesada guardada como {os.path.basename(save_path)}")

def mostrar_imagenes_color_gris(img_color, img_gray, titulo="Comparación"):
    win = tk.Toplevel()
    win.title(titulo)
    win.configure(bg="#ececec")

    frame = tk.Frame(win, bg="#ececec")
    frame.pack(padx=18, pady=18)

    tk.Label(frame, text="Original (Color)", font=("Arial", 12, "bold"), bg="#ececec").grid(row=0, column=0, padx=10, pady=10)
    tk.Label(frame, text="Blanco y Negro Suave", font=("Arial", 12, "bold"), bg="#ececec").grid(row=0, column=1, padx=10, pady=10)

    size = (300, 300)
    pil_color = Image.fromarray(cv2.cvtColor(img_color, cv2.COLOR_BGR2RGB)).resize(size)
    pil_gray = Image.fromarray(img_gray).convert("L").resize(size)

    im1 = ImageTk.PhotoImage(image=pil_color)
    im2 = ImageTk.PhotoImage(image=pil_gray)
    label1 = tk.Label(frame, image=im1, bg="#ececec")
    label1.image = im1
    label2 = tk.Label(frame, image=im2, bg="#ececec")
    label2.image = im2
    label1.grid(row=1, column=0, padx=10, pady=6)
    label2.grid(row=1, column=1, padx=10, pady=6)

# --------- GUI PRINCIPAL ---------

root = tk.Tk()
root.title("Cliente de procesamiento de imágenes (Color y B/N suave)")

frame = tk.Frame(root, padx=20, pady=30)
frame.pack()

btn_subir = tk.Button(frame, text="Seleccionar y subir imagen local", width=35, command=subir_imagen_local)
btn_subir.pack(pady=10)

btn_descargar = tk.Button(frame, text="Procesar imagen del servidor", width=35, command=seleccionar_y_procesar_servidor)
btn_descargar.pack(pady=10)

tk.Label(frame, text="Servidor: " + SERVER_URL, fg="#337ab7").pack(pady=(15,0))

root.mainloop()
